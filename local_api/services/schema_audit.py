"""Read-only browser adapter for the existing source-bound schema judge."""
from local_api.services.decision_trace import traced
from copy import deepcopy
import json
import os
import traceback
from pathlib import Path
from uuid import uuid4

from local_api.services.review_chunking import run_schema_audit, new_budget, binding
from local_api.services.llm_section_review import ReviewSettings, call_deepseek

SAFE_ERRORS = {
    'request_budget_exhausted', 'unreviewable_chunk', 'incomplete_audit_coverage',
    'invalid_audit_contract', 'invalid_audit_finding', 'foreign_audit_source',
    'provider_or_audit_validation_failed', 'invalid_configuration',
    'authentication_failed', 'insufficient_balance', 'provider_forbidden',
    'rate_limited', 'provider_unavailable', 'provider_http_error', 'incomplete_response',
}


@traced('schema_audit_adapter', 'automatic_schema_audit')
def audit_mapping(elements, sections, mapped, *, requested, settings=None, transport=None):
    """Return compact public findings; retain detailed requests/results privately.

    Neither the mapping nor its source structures are modified, including by an
    injected audit implementation. A clean audit does not certify correctness.
    """
    public = {'status': 'not_requested', 'outcome': 'unknown', 'findings': [],
              'partial_findings': [], 'coverage': {'expected_units': 0, 'checked_units': 0,
              'chunks_planned': 0, 'chunks_completed': 0}, 'provider_calls': 0, 'errors': []}
    if not requested:
        return public
    identifier = uuid4().hex
    diagnostic_dir = Path(os.getenv('RESUME_AUDIT_LOG_DIR', '/tmp/resume-schema-audits')) / identifier
    saved = True

    def save(name, value):
        nonlocal saved
        try:
            diagnostic_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            path = diagnostic_dir / (name + '.json')
            with open(path, 'x', encoding='utf-8', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
                json.dump(value, stream, ensure_ascii=False, default=str)
        except (OSError, TypeError, ValueError):
            saved = False

    calls, provider_error = 0, None
    try:
        settings = settings or ReviewSettings.from_env()
        if not settings.enabled or not settings.api_key:
            public.update(status='not_configured', errors=[{
                'code': 'not_configured', 'message': 'Schema audit requires enabled DeepSeek credentials.'}])
            return public
        settings.validate()
        budget = new_budget(settings)
        section_calls = sections.metadata.get('llm_review', {}).get('provider_calls', 0)
        structure_calls = sections.metadata.get('structure_review', {}).get('provider_calls', 0)
        field_calls = max(mapped.meta.get('provider_calls', 0), mapped.meta.get('field_review', {}).get('provider_calls', 0))
        prior = section_calls + structure_calls + field_calls
        key = binding(elements)['source_inventory_sha256']
        budget.total = prior
        budget.documents[key] = prior
        budget.passes[(key, 0)] = prior
        schema = {'data': mapped.data.model_dump(mode='json'),
                  'section_schemas': [s.model_dump(mode='json') for s in mapped.section_schemas],
                  'meta': {k: deepcopy(mapped.meta.get(k, [] if k == 'missing_required_fields' else {}))
                           for k in ('missing_required_fields', 'field_evidence')}}
        save('input', {'elements': [e.model_dump(mode='json') for e in elements],
                       'sections': sections.model_dump(mode='json'), 'schema': schema,
                       'prior_provider_calls': prior})

        def recorded(config, messages):
            nonlocal calls, provider_error
            calls += 1
            save(f'call-{calls:03d}-request', {'model': config.model, 'messages': messages})
            try:
                content = (transport or call_deepseek)(config, messages)
                save(f'call-{calls:03d}-response', {'content': content})
                return content
            except Exception as exc:
                code = str(exc)
                provider_error = code if code in SAFE_ERRORS else 'provider_or_audit_validation_failed'
                save(f'call-{calls:03d}-error', {'type': type(exc).__name__, 'code': provider_error,
                     'traceback': traceback.format_exc().replace(config.api_key, '<redacted>')})
                raise

        # Detached copies protect the live mapping and ownership from mutation.
        result = run_schema_audit(deepcopy(elements), sections.model_copy(deep=True),
                                  schema, settings, recorded, budget=budget)
        save('result', result)
        coverage = result.get('coverage', {})
        checked = result.get('checked_ids', [])
        checked_set = set(checked)
        chunks = coverage.get('chunks', [])
        public.update(status=result['status'], findings=result.get('findings', []),
                      partial_findings=result.get('partial_findings', []), provider_calls=calls,
                      coverage={'expected_units': len(coverage.get('original_target_ids', [])),
                                'checked_units': len(checked), 'chunks_planned': len(chunks),
                                'chunks_completed': sum(all(t['id'] in checked_set for t in c['targets']) for c in chunks),
                                'source_inventory_sha256': coverage.get('binding', {}).get('source_inventory_sha256'),
                                'plan_sha256': coverage.get('plan_sha256'),
                                'blocked_units': len(coverage.get('blocked', []))})
        if result['status'] == 'complete':
            public['outcome'] = 'issues_found' if public['findings'] else 'no_findings'
        else:
            reason = provider_error or result.get('reason')
            code = reason if reason in SAFE_ERRORS else 'provider_or_audit_validation_failed'
            public['errors'] = [{'code': code, 'message': 'Schema audit did not complete; mapped output was retained.'}]
    except Exception as exc:
        code = str(exc)
        code = code if code in SAFE_ERRORS else 'audit_planning_or_validation_failed'
        public.update(status='incomplete', provider_calls=calls,
                      errors=[{'code': code, 'message': 'Schema audit could not complete; mapped output was retained.'}])
        detail = traceback.format_exc()
        if settings and settings.api_key:
            detail = detail.replace(settings.api_key, '<redacted>')
        save('failure', {'type': type(exc).__name__, 'code': code, 'traceback': detail})
    finally:
        public['diagnostic'] = {'id': identifier, 'saved': saved}
        save('summary', public)
        public['diagnostic']['saved'] = saved
    return public
