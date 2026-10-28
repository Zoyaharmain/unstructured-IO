"""Allowlisted diagnostics: never serialize exception inputs, source text or keys."""
import json
import logging
import os
import re
from uuid import uuid4
from pydantic import ValidationError
from local_api.schemas.subschema_spec import SUBSCHEMAS

logger = logging.getLogger(__name__)
SAFE_PARTS = {'sections', 'section_schemas', 'records', 'fields', 'missing', 'attributes',
              'items', 'value', 'evidence', 'source_ids', 'quote', 'data', 'name', 'status', 'record_id'}
SAFE_PARTS |= set(SUBSCHEMAS) | {name for fields in SUBSCHEMAS.values() for name in fields}
MESSAGES = {
    'json_parsing': 'Provider response is not valid JSON.',
    'response_model_validation': 'A response value has the wrong type or shape.',
    'parent_schema_validation': 'A required parent section is missing or duplicated.',
    'subschema_validation': 'The response violates the child-field schema.',
    'subschema_path_validation': 'The requested parent.child query path is not defined.',
    'source_evidence_validation': 'A field value or quote is not supported by its own source record.',
    'record_ownership_validation': 'Record source ownership is missing, overlapping, or foreign.',
    'source_binding_validation': 'The supplied sections do not match the extracted source.',
    'configuration_error': 'Review configuration is invalid.',
    'provider_error': 'The configured provider could not complete field review.',
    'request_budget': 'The review exceeded its configured request or context limit.',
    'internal_error': 'An internal error interrupted field mapping.',
}
CODE_MESSAGES = {
    'unsupported_employer_context': 'A capability, tool or client mention does not establish an employer.',
    'invalid_section': 'Each section must contain only category and records; records must be an array.',
    'scalar_multiple_values': 'A scalar field contains more than one value.',
    'string_child_type': 'This child field requires a literal string value.',
    'numeric_child_type': 'This child field requires a numeric value supported by source evidence.',
    'missing_source_status': 'Missing-source statuses must match exactly the empty fields.',
    'missing_or_unknown_fields': 'A record omits required field definitions or contains unknown fields.',
    'field_not_array': 'Each field must contain an array of source-backed items.',
    'section_coverage': 'A supplied parent section was omitted or duplicated.',
    'overlapping_records': 'Two records claim the same source block.',
    'heading_as_record': 'A section heading was used as record content.',
    'unsupported_value': 'The field value is absent from its own evidence quotes.',
    'unsupported_number': 'The numeric value is absent from its own evidence quotes.',
    'invalid_or_cross_record_quote': 'The quote is absent from the source or belongs to another record.',
}
PYDANTIC_MESSAGES = {'missing': 'A required response property is missing.',
    'extra_forbidden': 'The response contains an unknown property.',
    'string_type': 'A string value is required.', 'float_type': 'A numeric value is required.',
    'list_type': 'An array is required.', 'dict_type': 'An object is required.',
    'too_short': 'A required collection or string is empty.',
    'literal_error': 'The response contains an unsupported status.',
    'value_error': 'The response violates a schema invariant.',
    'finite_number': 'Numeric values must be finite.'}


def safe_path(parts):
    if isinstance(parts, str): parts = parts.strip('/').split('/')
    return '/' + '/'.join(str(p) if isinstance(p, int) or isinstance(p, str) and p.isdigit() and len(p) <= 5 and int(p) <= 10000
                          else p if p in SAFE_PARTS else 'unknown_field' for p in parts)


class MappingValidationError(ValueError):
    def __init__(self, category, code, path=(), exception_type='ValueError', field=None, evidence_analysis=None):
        self.evidence_analysis = {k: v for k, v in (evidence_analysis or {}).items()
            if k in {'item_index', 'value_length', 'evidence_count'} and type(v) is int
            or k in {'literal_in_record', 'whitespace_match_in_record', 'all_quotes_valid'} and type(v) is bool}
        analysis = evidence_analysis or {}
        refs = analysis.get('evidence_source_ids')
        if isinstance(refs, list) and all(isinstance(ref, str) and re.fullmatch(r'e\d{1,8}:\d{1,10}:\d{1,10}', ref) for ref in refs):
            self.evidence_analysis['evidence_source_ids'] = refs[:100]
        lengths = analysis.get('evidence_quote_lengths')
        if isinstance(lengths, list) and all(type(n) is int and 0 <= n <= 10_000_000 for n in lengths):
            self.evidence_analysis['evidence_quote_lengths'] = lengths[:100]
        self.category = category
        self.code = code
        self.path = safe_path(path)
        self.exception_type = exception_type
        self.field = field if field in {name for fields in SUBSCHEMAS.values() for name in fields} else None
        super().__init__(MESSAGES[category])


def fail(category, code, path=(), field=None, evidence_analysis=None):
    raise MappingValidationError(category, code, path, field=field, evidence_analysis=evidence_analysis)


def diagnose(exc, stage, path=()):
    diagnostic = {'id': uuid4().hex, 'category': 'internal_error',
                  'exception_type': type(exc).__name__, 'code': 'internal_error',
                  'path': safe_path(path), 'validation_message': MESSAGES['internal_error']}
    if isinstance(exc, MappingValidationError):
        diagnostic.update(category=exc.category, code=exc.code, path=exc.path,
                          exception_type=exc.exception_type, field=exc.field, validation_message=CODE_MESSAGES.get(exc.code, MESSAGES[exc.category]))
        if exc.evidence_analysis:
            diagnostic['evidence_analysis'] = exc.evidence_analysis
    elif isinstance(exc, json.JSONDecodeError):
        diagnostic.update(category='json_parsing', code='invalid_json',
                          validation_message=MESSAGES['json_parsing'], line=exc.lineno, column=exc.colno)
    elif isinstance(exc, ValidationError):
        errors = exc.errors(include_input=False, include_context=False, include_url=False)
        issue = errors[0] if errors else {}
        category = stage if stage in {'parent_schema_validation', 'subschema_validation'} else 'response_model_validation'
        diagnostic.update(category=category, code=issue.get('type', 'invalid_response'),
            path=safe_path(tuple(path) + tuple(issue.get('loc', ()))),
            validation_message=PYDANTIC_MESSAGES.get(issue.get('type'), MESSAGES[category]),
            issue_count=len(errors))
    elif stage in {'provider_error', 'configuration_error', 'request_budget', 'source_binding_validation', 'subschema_path_validation'} or (
            stage == 'response_model_validation' and isinstance(exc, (ValueError, TypeError, KeyError, AttributeError))):
        diagnostic.update(category=stage, code=stage, validation_message=MESSAGES[stage])
    diagnostic['stage'] = stage if stage in MESSAGES else 'internal_error'
    path_parts = diagnostic['path'].strip('/').split('/')
    if not diagnostic.get('field') and 'fields' in path_parts:
        position = path_parts.index('fields') + 1
        if position < len(path_parts) and path_parts[position] in {name for fields in SUBSCHEMAS.values() for name in fields}:
            diagnostic['field'] = path_parts[position]
    # Raw str(exc), repr(exc), traceback locals, provider bodies and error inputs
    # are intentionally excluded, including from server-side logs.
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', diagnostic['exception_type']):
        diagnostic['exception_type'] = 'Exception'
    return diagnostic


def record_failure(exc, stage, path=(), *, attempt=None, recovered=False):
    diagnostic = diagnose(exc, stage, path)
    diagnostic.update(attempt=attempt, recovered=recovered)
    logger.warning('schema_mapping_failure %s', json.dumps(diagnostic, sort_keys=True))
    return diagnostic


def client_diagnostic(diagnostic):
    if os.getenv('RESUME_APP_ENV', 'production').casefold() == 'development':
        return diagnostic
    # These values are fixed codes/registry field names, never source text.
    # Keep the reason actionable even when development details are disabled.
    return {k: diagnostic[k] for k in ('id', 'category', 'code', 'field', 'validation_message', 'recovered')
            if k in diagnostic}


def mapping_result(mapped, *, fallback=False):
    counts = mapped.meta.get('source_coverage_ledger', {}).get('status_counts', {})
    omitted_provider_items = any(r.get('code') in {'unsupported_list_item_pruned',
        'unsupported_optional_scalar_pruned', 'scalar_multiple_values_truncated'}
        for r in mapped.meta.get('field_review', {}).get('evidence_repairs', []))
    needs_review = bool(omitted_provider_items or mapped.meta.get('missing_required_fields') or counts.get('present_but_unmapped')
                        or counts.get('present_but_ambiguous') or mapped.meta.get('needs_review'))
    return {'status': 'fallback_used' if fallback else 'needs_review' if needs_review else 'success',
            'usable': True, 'requires_review': fallback or needs_review, 'fallback_used': fallback,
            'meaning': 'Source-bound output is available for inspection; this does not certify field accuracy.'}
