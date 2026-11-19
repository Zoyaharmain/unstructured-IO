"""Observational, terminal-first pipeline tracing. Never logs source text or credentials."""
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import threading
import time
from uuid import uuid4

logger = logging.getLogger('resume.pipeline')
_context = ContextVar('resume_trace', default=None)
_stage = ContextVar('resume_stage', default=('request', None))
_parent = ContextVar('resume_parent_decision', default=None)
_lock = threading.RLock()


def configure_logging():
    level = getattr(logging, os.getenv('RESUME_LOG_LEVEL', 'INFO').upper(), logging.INFO)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
    logger.propagate = False


@dataclass
class Context:
    run_id: str
    root: Path
    inventory: str | None = None
    fields: dict = field(default_factory=dict)


def start(run_id=None):
    root = Path(os.getenv('RESUME_TRACE_DIR', '/tmp/resume-pipeline-traces'))
    if not (isinstance(run_id, str) and re.fullmatch('[0-9a-f]{32}', run_id)
            and (root / run_id / 'state.json').is_file()):
        run_id = uuid4().hex
    context = Context(run_id, root)
    return context, _context.set(context)


def reset(token):
    _context.reset(token)


def emit(event, *, level=logging.INFO, **fields):
    """Only callers' explicit safe signals are serialized. I/O failures never affect parsing."""
    context = _context.get()
    if context is None or os.getenv('RESUME_TRACE_ENABLED', 'true').lower() != 'true':
        return
    row = {'run_id': context.run_id, 'event_id': uuid4().hex, 'event': event,
           'stage': _stage.get()[0], 'parent_decision_id': _parent.get(),
           'timestamp_ns': time.time_ns(), **fields}
    if event == 'decision':
        row['decision_id'] = row['event_id']
    try:
        directory = context.root / context.run_id
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with _lock, open(directory / 'state.json', 'a+', opener=lambda p, f: os.open(p, f, 0o600)) as state:
            fcntl.flock(state, fcntl.LOCK_EX)
            state.seek(0)
            saved = json.loads(state.read() or '{}')
            row['sequence'] = saved.get('sequence', 0) + 1
            saved['sequence'] = row['sequence']
            state.seek(0); state.truncate(); json.dump(saved, state); state.flush()
            with open(directory / 'events.jsonl', 'a', encoding='utf-8',
                      opener=lambda p, f: os.open(p, f, 0o600)) as output:
                output.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
            logger.log(level, json.dumps(row, ensure_ascii=False, default=str))
            fcntl.flock(state, fcntl.LOCK_UN)
    except Exception:
        try:
            logger.warning('run_id=%s trace_storage_unavailable', context.run_id)
            logger.log(level, json.dumps(row, default=str))
        except Exception:
            pass
    return row['event_id']


def bind_elements(elements):
    """Reject cross-document correlation, without rejecting or changing processing."""
    context = _context.get()
    if context is None or not elements:
        return
    try:
        inventory = hashlib.sha256(json.dumps([e.model_dump(mode='json') for e in elements],
                                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if context.inventory == inventory:
            return
        emit('inventory_binding_start')
        with _lock, open(context.root / context.run_id / 'state.json', 'r+') as state:
            fcntl.flock(state, fcntl.LOCK_EX)
            saved = json.load(state)
            previous = saved.get('inventory_sha256')
            if previous is None or previous == inventory:
                saved['inventory_sha256'] = inventory
                state.seek(0); state.truncate(); json.dump(saved, state)
            else:
                context.run_id = uuid4().hex
            fcntl.flock(state, fcntl.LOCK_UN)
        if previous and previous != inventory:
            emit('correlation_rebound', level=logging.WARNING, reason='source_inventory_mismatch')
            bind_elements(elements)
        else:
            context.inventory = inventory
            emit('source_inventory', elements=len(elements), inventory_sha256=inventory)
    except Exception:
        pass


def uncertainty(state='not_calibrated'):
    return {'state': state, 'probability': None, 'method': None, 'calibration_version': None}


def decision(kind, **data):
    data.setdefault('confidence', uncertainty())
    emit('decision', level=logging.DEBUG, decision_type=kind,
         **data)


def _view(value):
    """Safe section/record ownership only; no actual source or field values."""
    if hasattr(value, 'owners'):
        return {sid: {'section': o.section, 'record_id': o.record, 'fields': o.fields,
                      'evidence_state': o.status} for sid, o in value.owners.items()}
    if not hasattr(value, 'sections') or not isinstance(value.sections, list):
        return {}
    result = {}
    for section in value.sections:
        records = {i: r.entry_id for r in section.entries for i in r.block_indices}
        for i, block in enumerate(section.blocks):
            sid = f'e{block.source_element_index}:{block.start}:{block.end}'
            result[sid] = {'section': section.category, 'record_id': records.get(i),
                           'rule': block.assignment, 'candidate': block.candidate_section,
                           'similarity': block.similarity, 'margin': block.margin,
                           'reviewed_by_llm': block.reviewed_by_llm,
                           'boundary_source_id': block.boundary_source_id,
                           'context_source_element_index': block.context_source_element_index,
                           'boundary_candidate': block.boundary_candidate,
                           'pending_boundary_id': block.pending_boundary_id,
                           'llm_action': block.llm_action}
    for block in value.needs_review:
        result[f'e{block.source_element_index}:{block.start}:{block.end}'] = {
            'section': None, 'record_id': None, 'rule': block.assignment}
    return result


def _report(before, value):
    after = _view(value)
    for sid, selected in after.items():
        if before.get(sid) != selected:
            decision('ownership', source_ids=[sid], before=before.get(sid), after=selected,
                     confidence=uncertainty('evidence_only'))
    if hasattr(value, 'section_schemas'):
        for si, section in enumerate(value.section_schemas):
            for ri, record in enumerate(section.records):
                for ai, attribute in enumerate(record.attributes):
                    key = (section.category, record.record_id, attribute.name)
                    selected = {'evidence_state': attribute.status,
                        'value_fingerprint': hashlib.sha256(json.dumps([item.value for item in attribute.items], sort_keys=True).encode()).hexdigest()}
                    context = _context.get()
                    with _lock:
                        before_field = context.fields.get(key) if context else None
                        if context: context.fields[key] = selected
                    decision('field_mapping', section=section.category, record_ids=[record.record_id],
                             field=attribute.name, evidence_state=attribute.status,
                             source_ids=list(dict.fromkeys(q.source_id for item in attribute.items for q in item.evidence)),
                             item_count=len(attribute.items), confidence=uncertainty('evidence_only'),
                             before=before_field, after=selected,
                             value_ref=f'/section_schemas/{si}/records/{ri}/attributes/{ai}')
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        emit('validation_result', errors=value, confidence=uncertainty('evidence_only'))
    if isinstance(value, tuple) and len(value) == 4 and hasattr(value[0], 'model_dump'):
        for warning in value[3]:
            decision('standardization', field=warning.field, rule=warning.warning_type,
                     evidence_state=warning.severity, applied=warning.applied)
    metadata = getattr(value, 'metadata', None) or getattr(value, 'meta', None)
    if isinstance(metadata, dict):
        for name in ['llm_review', 'structure_review', 'field_review', 'schema_audit']:
            state = metadata.get(name, {})
            if state:
                emit('review_outcome', review_stage=name, status=state.get('status'),
                     provider_calls=state.get('provider_calls', 0),
                     accepted=len(state.get('accepted_operations', [])),
                     rejected=len(state.get('rejected_operations', [])),
                     semantic_correctness='unmeasured')
    if isinstance(value, dict) and 'findings' in value and 'coverage' in value:
        coverage = value.get('coverage', {})
        emit('audit_outcome', status=value.get('status'),
             findings=len(value.get('findings', [])), partial_findings=len(value.get('partial_findings', [])),
             expected_units=coverage.get('expected_units', len(coverage.get('original_target_ids', []))),
             checked_units=coverage.get('checked_units', len(value.get('checked_ids', []))),
             provider_calls=value.get('provider_calls', 0), semantic_correctness='unmeasured')


def traced(stage, trigger=None, *, detail=False):
    """Decorate stage boundaries without changing arguments, results or exceptions."""
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            effective_trigger = ('existing_unresolved_followup' if kwargs.get('_targeted') else trigger) or _stage.get()[1]
            token = _stage.set((stage, effective_trigger))
            parent_token = None
            begin = time.monotonic()
            before = {}
            try:
                for arg in args:
                    if hasattr(arg, 'elements') and arg.elements:
                        bind_elements(arg.elements)
                    try:
                        before = before or _view(arg)
                    except Exception:
                        pass
                event_id = emit('stage_start', level=logging.DEBUG if detail else logging.INFO,
                                function=fn.__name__, module=fn.__module__, line=fn.__code__.co_firstlineno,
                                trigger=effective_trigger, confidence_based_routing=False)
                parent_token = _parent.set(event_id)
                value = fn(*args, **kwargs)
                if type(value).__name__ == 'ExtractionResponse' and value.elements:
                    bind_elements(value.elements)
                    emit('extraction_result', requested_strategy=value.strategy,
                         element_count=len(value.elements), source_accuracy='unknown')
                if _context.get():
                    try:
                        _report(before, value)
                        if fn.__name__ == 'entry_groups':
                            for record in value:
                                blocks = args[0]
                                decision('record_group', section=args[1], record_ids=[record['entry_id']],
                                         rule=record.get('boundary_reason'),
                                         source_ids=[f'e{blocks[i].source_element_index}:{blocks[i].start}:{blocks[i].end}' for i in record['block_indices']])
                    except Exception:
                        emit('trace_observation_unavailable', level=logging.WARNING)
                emit('stage_end', level=logging.DEBUG if detail else logging.INFO,
                     status='returned', duration_ms=round((time.monotonic()-begin)*1000, 3))
                return value
            except Exception as exc:
                emit('stage_failure', level=logging.ERROR, error_type=type(exc).__name__,
                     duration_ms=round((time.monotonic()-begin)*1000, 3))
                raise
            finally:
                if parent_token is not None:
                    _parent.reset(parent_token)
                _stage.reset(token)
        return wrapper
    return decorate


def provider_trace(fn):
    @wraps(fn)
    def wrapper(settings, path, body=None):
        call_id, begin = uuid4().hex, time.monotonic()
        stage, trigger = _stage.get()
        targets, signals, target_ids = [], [], []
        try:
            if isinstance(body, dict):
                for message in body.get('messages', []):
                    payload = json.loads(message.get('content', ''))
                    if isinstance(payload, dict):
                        for target in payload.get('targets', payload.get('spans', [])):
                            sid = target.get('source_id', target.get('id'))
                            target_ids.append(sid)
                            targets.extend(target.get('source_ids', []) or ([sid] if sid and re.fullmatch(r'e\d+:\d+:\d+', sid) else []))
                            signals.append({'target_id': sid, 'similarity': target.get('similarity'),
                                            'margin': target.get('margin'),
                                            'ownership_state': target.get('owner', {}).get('status')})
                        if isinstance(payload.get('sections'), list):
                            for section in payload['sections']:
                                targets.extend(b['source_id'] for b in section.get('blocks', []) if 'source_id' in b)
        except Exception:
            pass
        emit('llm_call_start', call_id=call_id, provider='DeepSeek', model=settings.model,
             trigger=trigger or ('connection_check' if body is None else 'existing_review_logic'),
             requirement='mandatory_within_reviewed_mode' if trigger in {
                 'reviewed_mode_complete_section_review', 'automatic_schema_audit'} else
                 'optional_requested_review' if trigger == 'review_fields_requested' else 'conditional_existing_logic',
             source_ids=targets, decision_ids=[_parent.get()] if _parent.get() else [],
             confidence=uncertainty(), confidence_based_routing=False)
        emit('llm_call_signals', level=logging.DEBUG, call_id=call_id,
             target_ids=target_ids, available_signals=signals)
        try:
            result = fn(settings, path, body)
            raw_usage = result.get('usage') if isinstance(result, dict) else None
            usage = {k: v for k, v in raw_usage.items() if isinstance(v, (int, float))} if isinstance(raw_usage, dict) else {}
            emit('llm_call_end', call_id=call_id, status='provider_returned',
                 latency_ms=round((time.monotonic()-begin)*1000, 3), token_usage=usage or None,
                 semantic_correctness='unmeasured')
            return result
        except Exception as exc:
            code = str(exc)
            safe_code = code if code in {'authentication_failed', 'rate_limited', 'provider_unavailable',
                'insufficient_balance', 'provider_forbidden', 'incomplete_response', 'invalid_response',
                'model_unavailable', 'request_budget_exhausted', 'response_too_large'} else None
            emit('llm_call_error', level=logging.ERROR, call_id=call_id, error_type=type(exc).__name__,
                 error_code=safe_code, latency_ms=round((time.monotonic()-begin)*1000, 3), token_usage=None)
            raise
    return wrapper
