"""Bounded feedback orchestration for the individual resume checker."""
import hashlib
import json
from dataclasses import replace

from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.llm_section_review import review_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.section_recovery import recover_sections
from local_api.services.source_accounting import account_source
from local_api.services.source_validation import validate_result


def fingerprint(sections, schema):
    # Exclude diagnostic reasons, confidence and counters: they are not progress.
    hierarchy = [
        {'category': parent['category'],
         'records': [
             {'record_id': record['record_id'],
              'source_ids': record.get('source_ids', []),
              'attributes': [
                  {'name': attribute['name'],
                   'items': [{'value': item['value'],
                              'status': item.get('status'),
                              'evidence': item.get('evidence', [])}
                             for item in attribute.get('items', [])]}
                  for attribute in record.get('attributes', [])]}
             for record in parent.get('records', [])],
         'residual_blocks': parent.get('residual_blocks', [])}
        for parent in schema.get('section_schemas', [])]
    return hashlib.sha256(json.dumps({
        'sections': [(s.category, [(b.source_element_index, b.start, b.end, b.text) for b in s.blocks],
                      [(e.entry_id, e.block_indices, e.fields) for e in s.entries]) for s in sections.sections],
        'unknown': [(b.source_element_index, b.start, b.end, b.text) for b in sections.needs_review],
        'data': schema['data'],
        'hierarchy': hierarchy,
    }, sort_keys=True).encode()).hexdigest()


def run_feedback(request, local, settings, source, transport, audit_fn, save_pass, *, request_budget=None, document_sha256=None):
    """Each retry re-enters local recovery, strict LLM placement, mapping and audit.

    Extraction remains bound to the immutable source inventory. Audit findings
    inform review, never bypass source validators or directly overwrite fields.
    """
    from local_api.services.review_chunking import new_budget
    request_budget = request_budget or new_budget(settings)
    sections = local
    history = []
    feedback = {}
    previous = None
    stop = 'local_only'
    # Invalid-response retries share this outer budget with unresolved feedback.
    single = replace(settings, recovery_attempts=0)
    for index in range(1 + (settings.recovery_attempts if settings.enabled else 0)):
        candidate = sections.model_copy(deep=True)
        if index:
            candidate = recover_sections(request, candidate)
        errors = validate_result(request.elements, candidate)
        if errors:
            raise ValueError('Recovery source validation failed: ' + ', '.join(errors))

        candidate = review_sections(request, candidate, settings=single, transport=transport,
                                    _budget=request_budget, _pass_id=index, feedback=feedback,
                                    document_sha256=document_sha256)
        errors = validate_result(request.elements, candidate)
        if errors:
            raise ValueError('Reviewed source validation failed: ' + ', '.join(errors))
        state = candidate.metadata.get('llm_review', {})
        # Retain the preceding complete review if a later review fails.
        failed = settings.enabled and state.get('status') != 'complete'
        if not failed or not index:
            sections = candidate
        schema = map_schema(SchemaMappingRequest(elements=request.elements, sections=sections, source=source)).model_dump(mode='json')
        audit = audit_fn(sections, schema) if settings.enabled and not failed else {'status': 'disabled' if not settings.enabled else 'not_run', 'findings': []}
        accounting = account_source(request.elements, sections)
        next_feedback = {
            'unresolved_meaningful_spans': accounting['unresolved_meaningful_spans'],
            'missing_required_fields': schema['meta']['missing_required_fields'],
            'schema_findings': audit['findings'],
        }
        if not failed or not feedback:
            feedback = next_feedback
        # A rejected placement response must not erase the last valid audit's
        # concerns before the next retry. Include its exact validation causes.
        if failed:
            feedback = {**feedback, 'placement_validation_failures': state.get('validation_failures', [])}
        current = fingerprint(sections, schema)
        row = {'pass': index + 1, 'section_review': state, 'audit_status': audit['status'],
               **feedback, 'fingerprint': current, 'previous_valid_result_retained': bool(failed and index)}
        history.append(row)
        save_pass(index + 1, sections, schema, audit, row)
        if not settings.enabled:
            stop = 'local_only'
            break
        if failed:
            stop = 'section_review_failed'
            # Only invalid provider placements merit an immediate retry.
            if state.get('error_code') in {'invalid_assignments', 'incomplete_response'} and index < settings.recovery_attempts:
                continue
            break
        if audit['status'] != 'complete':
            absent_fields = schema.get('meta', {}).get('source_coverage_ledger', {}).get('field_statuses', {})
            missing_fields = schema.get('meta', {}).get('missing_required_fields', [])
            all_absent = bool(missing_fields) and all(absent_fields.get(f) == 'absent_in_source' for f in missing_fields)
            if not all_absent:
                stop = 'schema_audit_failed'
                break
        if not any(feedback.values()):
            stop = 'no_pending_diagnostics'
            break
        if current == previous:
            stop = 'no_source_or_mapping_progress'
            break
        previous = current
        stop = 'recovery_budget_exhausted'
    return sections, schema, audit, {'passes': history, 'stop_reason': stop,
        'provider_coverage_status': ('not_requested' if not settings.enabled else 'complete' if history[-1]['section_review'].get('status')=='complete' and history[-1]['audit_status']=='complete' else 'incomplete'),
        'request_budget_events': list(request_budget.events),
        'original_pdf_verified': False, 'status': 'needs_review'}
