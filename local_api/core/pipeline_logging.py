"""Privacy-safe terminal events for a résumé processing run."""
import logging
import os
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import Lock

from uvicorn.logging import DefaultFormatter


HEADER = 'X-Resume-Run'
LOGGER = logging.getLogger('uvicorn.error.resume_pipeline')


@dataclass
class PipelineTrace:
    run_id: str
    attempts: int = 0
    completions: int = 0
    lock: Lock = field(default_factory=Lock)

    def next_attempt(self, completion):
        with self.lock:
            self.attempts += 1
            self.completions += int(completion)
            return self.attempts


trace = ContextVar('resume_pipeline_trace', default=None)


def event(level, name, **metrics):
    if not LOGGER.isEnabledFor(level):
        return
    current = trace.get()
    fields = ' '.join(f'{key}={value}' for key, value in metrics.items())
    LOGGER.log(level, 'run=%s event=%s %s', current.run_id if current else '-', name, fields,
               extra={'pipeline_run': current.run_id if current else '-', 'pipeline_event': name,
                      'pipeline_metrics': metrics})


def readable_message(name, m):
    """Translate pipeline events without inspecting résumé content."""
    stages = {
        'extraction': 'Starting Stage 1 · Read the document',
        'local_sections': 'Starting Stages 2–4 · Detect and group blocks locally',
        'section_review': 'Starting Stages 2–4 · Detect, group and review block placement',
        'schema_mapping': 'Starting Stages 5–7 · Map, validate and export fields',
        'schema_query': 'Query mapped fields',
        'standardization': 'Standardize mapped fields',
        'provider_connection': 'Check the DeepSeek connection',
    }
    if name == 'stage_io':
        titles = ('Document extraction', 'Section detection and classification', 'Record grouping',
                  'Recovery and source ownership', 'Schema mapping and field extraction',
                  'Evidence validation and review', 'Standardization and JSON export')
        return f"Stage {m['number']} · {titles[m['number']-1]} | In: {m['inputs']} | Out: {m['outputs']}"
    if name == 'stage_detail':
        return (f"Stage {m['number']} · {m['subject']} | In: {m['inputs']} | "
                f"Out: {m['outputs']} | Method: {m['method']}.")
    if name == 'section_contents':
        return f"Stage 2 · {m['section']} — {m['count']} source spans"
    if name == 'section_placement':
        page = f"page {m['page']}" if m['page'] is not None else 'page unknown'
        context = f" · context: element e{m['context']}" if m['context'] is not None else ''
        model = ''
        if m['candidate']:
            scores = ', '.join(f'{key} {m[key]:.3f}' for key in ('similarity', 'margin') if m[key] is not None)
            model = f" · model suggested {m['candidate']}" + (f' ({scores})' if scores else '')
        return (f"Stage 2 · {m['block']} ({page}, lane {m['lane']})\n"
                f"    Input: {m['text']}\n"
                f"    Assigned to: {m['section']}\n"
                f"    Why: {m['reason']} [{m['assignment']}]{context}{model}")
    if name == 'field_trace':
        sources = '; '.join(m['sources']) or 'no source span recorded'
        return f"Stage 5 field · {m['field']} | In: {sources} | Out: {m['value']} | Method: {m['origin']}."
    if name == 'grouping_guide':
        return ('Stage 3 details · A block is a source text span. e12:0:75 means '
                'element index 12, characters 0 through 74. Group numbers are local to each section.')
    if name == 'record_group':
        return (f"Stage 3 group · {m['section']} #{m['group']} ({m['kind']}) | "
                f"Blocks: {', '.join(m['blocks']) or 'none'}.")
    if name == 'grouped_block':
        page = f"page {m['page']}" if m['page'] is not None else 'page unknown'
        preview = f" | Text: {m['preview']}" if m['preview'] is not None else ''
        return (f"Stage 3 block · {m['block']} ({page}) | {m['section']} → {m['placement']}"
                f"{preview}")
    if name == 'stage_started':
        return stages.get(m['stage'], m['stage'])
    if name == 'stage_finished':
        return (f"Finished in {m['elapsed_ms']/1000:.1f}s · HTTP {m['status']} · "
                f"DeepSeek completions attempted: {m['completion_attempts']} "
                f"(all provider requests: {m['provider_attempts']}).")
    if name == 'local_extraction':
        return f"Read {m['elements']} text elements using {m['strategy']} extraction."
    if name == 'local_sections':
        return (f"Local grouping placed {m['assigned']} blocks in {m['sections']} sections "
                f"in {m['elapsed_ms']/1000:.1f}s. {m['unresolved']} blocks still need a section.")
    if name == 'block_needs_review':
        page = f"page {m['page']}" if m['page'] is not None else 'page unknown'
        reason = 'possible section heading' if m['boundary'] else 'section evidence was inconclusive'
        return f"Check block {m['block']} ({page}): {reason}. Local suggestion: {m['candidate']}."
    if name == 'section_block_counts':
        detail = ', '.join(f"{section.replace('_', ' ')} {count}" for section, count in m['counts'].items())
        return f"Blocks by section: {detail or 'none'}."
    if name == 'more_unresolved_blocks':
        return f"{m['remaining']} more unresolved blocks are listed in the section results."
    if name == 'block_move_proposed':
        page = f"page {m['page']}" if m['page'] is not None else 'page unknown'
        return f"DeepSeek suggests block {m['block']} ({page}): {m['previous']} → {m['destination']}."
    if name == 'section_review_plan':
        mode = 'the unresolved blocks' if m['mode'] == 'unresolved_contextual_review' else 'the whole document'
        return f"DeepSeek will review {mode}: {m['targets']} blocks, {m['unresolved']} currently unresolved."
    if name == 'section_review_routes':
        if not m['changes']:
            return 'DeepSeek proposed no section changes in this pass.'
        return 'DeepSeek proposed moves: ' + ', '.join(
            f"{count} block(s) {route.replace('->', ' → ')}" for route, count in m['changes'].items()) + '.'
    if name == 'structural_review_plan':
        return f"Found {m['ambiguous_items']} record ownership questions for structural review."
    if name == 'review_outcome':
        return (f"Placement review: {m['section_status'] or 'not run'}, {m['changed']} blocks changed. "
                f"Record review: {m['structure_status'] or 'not run'}. Still unresolved: {m['unresolved']}.")
    if name == 'deterministic_mapping':
        return (f"Local field rules built {m['records']} records and extracted {m['extracted_fields']} field entries. "
                f"{m['missing_required']} required fields are missing.")
    if name == 'field_review_plan':
        return f"DeepSeek field review will inspect {m['sections']} sections in {m['batches']} batches."
    if name == 'field_review_batch':
        return f"Checking field review batch {m['batch']}: {', '.join(m['sections'])}."
    if name == 'required_fields_missing':
        return f"Required fields to check: {', '.join(m['fields'])}."
    if name == 'provider_attempt':
        label = 'completion' if m['kind'] == 'completion' else 'connection check'
        return f"DeepSeek {label} request #{m['number']} · sent {m['input_bytes']:,} bytes."
    if name == 'provider_response':
        usage = f" · {m['prompt_tokens']:,} input tokens" if 'prompt_tokens' in m else ''
        return f"DeepSeek request #{m['number']} replied in {m['elapsed_ms']/1000:.1f}s{usage}."
    if name == 'schema_mapping_failure':
        reason = {
            'validated_record_boundary_changed': 'DeepSeek changed which source blocks belong to a validated record',
            'validated_record_omitted': 'DeepSeek left out a validated record',
        }.get(m['code'], m['message'])
        return f"Field review rejected at {m['path']} in the review response: {reason.rstrip('.')}."
    if name == 'mapping_outcome':
        outcome = 'Export kept local values for work the provider review could not finish' if m['fallback'] else (
            'Export needs review' if m['requires_review'] else 'Export ready')
        return f"{outcome}. Field review: {m['field_review_status']}. Validation notices: {m['warnings']}."
    if name == 'provider_failed':
        return f"DeepSeek request #{m['number']} failed: {m['code'].replace('_', ' ')}."
    if name == 'review_budget_exhausted':
        return f"Stopped {m['stage'].replace('_', ' ')} after reaching the request limit."
    if name == 'section_review_failed':
        return f"Section review could not complete ({m['code'].replace('_', ' ')}). Local placement was retained."
    return None


class ReadablePipelineFormatter(DefaultFormatter):
    def formatMessage(self, record):
        if hasattr(record, 'pipeline_event'):
            message = readable_message(record.pipeline_event, record.pipeline_metrics)
            if message is not None:
                record.message = f'[{record.pipeline_run[:8]}] {message}'
        return super().formatMessage(record)




def stage_io(number, inputs, outputs):
    event(logging.INFO, 'stage_io', number=number, inputs=inputs, outputs=outputs)


def stage_detail(number, subject, inputs, outputs, method):
    event(logging.DEBUG, 'stage_detail', number=number, subject=subject,
          inputs=inputs, outputs=outputs, method=method)


def values_enabled():
    return trace.get() is not None and os.getenv('RESUME_LOG_VALUES', '').lower() == 'true'


def trace_fields(mapped, elements, *, origin, baseline=None, fallback_categories=()):
    """Show literal, bounded previews only when explicitly enabled."""
    import re
    if not LOGGER.isEnabledFor(logging.DEBUG):
        return
    show_text = values_enabled()
    data = mapped.data.model_dump()
    evidence = mapped.meta.get('field_evidence', {})
    previous = baseline.data.model_dump() if baseline is not None else {}

    def lookup(tree, path):
        for token in re.findall(r'[^.\[\]]+', path):
            if isinstance(tree, dict):
                tree = tree.get(token)
            elif isinstance(tree, list) and token.isdecimal() and int(token) < len(tree):
                tree = tree[int(token)]
            else:
                return None
        return tree

    ordered = sorted(evidence, key=lambda path: (path != 'contact.full_name', not path.startswith('contact.')))
    for path in ordered:
        value = lookup(data, path)
        if value is None or isinstance(value, (list, dict)):
            continue
        field_origin = origin
        if baseline is not None:
            category = 'personal_information' if path.startswith('contact.') else re.split(r'[.\[]', path)[0]
            if category in fallback_categories:
                field_origin = 'local fallback'
            elif lookup(previous, path) == value and baseline.meta.get('field_evidence', {}).get(path) == evidence[path]:
                field_origin = 'review agreed with local fields and evidence'
        sources = []
        for ref in evidence[path]:
            match = re.fullmatch(r'e(\d+):(\d+):(\d+)', ref)
            if match:
                index, start, end = map(int, match.groups())
                if index < len(elements):
                    sources.append(f'{ref} {elements[index].text[start:min(end, start + 100)]!r}' if show_text else ref)
        event(logging.DEBUG, 'field_trace', field=path, origin=field_origin,
              value=repr(str(value)[:100]) if show_text else '[value hidden]', sources=sources)
