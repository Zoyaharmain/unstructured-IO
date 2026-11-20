"""Map source-bound blocks; explicit review_fields enables grounded DeepSeek mapping."""
from fastapi import APIRouter, HTTPException
import json
import os
from starlette.concurrency import run_in_threadpool
from local_api.schemas.mapping import SchemaMappingResponse, ReviewedSubschemaQueryRequest, ReviewedSchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.decision_trace import emit, stage_summary, trace_enabled
from local_api.vendor.handoff_schema.models import ResumeSchema
from local_api.vendor.handoff_schema.schema_spec import get_full_schema_mapping
from local_api.schemas.subschemas import SectionSchema
from local_api.schemas.subschema_spec import hierarchy_definition
from local_api.services.subschema_validation import query_subschemas
from local_api.services.schema_diagnostics import record_failure, client_diagnostic, mapping_result
from pydantic import ValidationError

router=APIRouter(prefix='/api/v1/resume/schema',tags=['Resume schema mapping'])


def mapping_error(exc, category='source_binding_validation'):
    diagnostic = record_failure(exc, 'response_model_validation' if isinstance(exc, ValidationError) else category)
    return HTTPException(422, detail={
        'message': 'Schema mapping or query input was rejected. See the diagnostic reference.',
        'mapping_result': {'status': 'failed', 'usable': False, 'requires_review': True, 'fallback_used': False},
        'diagnostic': client_diagnostic(diagnostic)})


def trace_export_fields(export, mapped):
    import logging
    import re

    if not trace_enabled():
        return
    aliases = {('education', 'start_year'): 'start_date', ('education', 'graduation_year'): 'end_date',
               ('certifications', 'issue_year'): 'issue_date'}
    data = export.get('data', {})
    evidence = mapped.meta.get('field_evidence', {})
    statuses = mapped.meta.get('field_source_status', {})
    for path in dict.fromkeys([*evidence, *statuses]):
        if not isinstance(path, str):
            continue
        tokens = re.findall(r'[^.\[\]]+', path)
        if len(tokens) < 2 or tokens[0] not in data:
            continue
        tokens[-1] = aliases.get((tokens[0], tokens[-1]), tokens[-1])
        item = data
        for token in tokens:
            if isinstance(item, dict) and token in item:
                item = item[token]
            elif isinstance(item, list) and token.isdecimal() and int(token) < len(item):
                item = item[int(token)]
            else:
                break
        else:
            destination = 'data' + ''.join(f'[{t}]' if t.isdecimal() else f'.{t}' for t in tokens)
            emit('export_field', level=logging.DEBUG, path=destination, source_ids=evidence.get(path, []),
                 status=statuses.get(path, 'No field status recorded'),
                 preview=repr(item)[:160] if os.getenv('RESUME_LOG_VALUES', '').lower() == 'true' else None)


@router.get('/definition')
def definition():
    return ResumeSchema.model_json_schema()


@router.get('/standardized-definition')
def standardized_definition():
    from local_api.services.standardization.consumer import ConsumerResume
    return ConsumerResume.model_json_schema()


@router.get('/mapping')
def mapping():
    spec=get_full_schema_mapping()
    spec['integration']={'input':'Existing extracted elements plus SectionResponse',
                         'provider_calls':0,'mapping_mode':'existing_blocks_schema_mapping',
                         'record_boundaries':'Preserved from supplied section entries',
                         'unknown_required_strings':'Empty string; see meta.missing_required_fields',
                         'confidence':'Handoff fixed heuristic scores; not probabilities'}
    spec['integration']['optional_field_review'] = 'POST with review_fields=true uses configured DeepSeek, validates exact citations, and derives legacy/subschema fields together.'
    return spec


@router.get('/subschema-definition')
def subschema_definition():
    definition = SectionSchema.model_json_schema()
    definition['x-hierarchy'] = hierarchy_definition()
    return definition


@router.post('/query')
async def query_existing_sections(request: ReviewedSubschemaQueryRequest):
    # Reuse source binding and mapping; never trust client-provided citations.
    try:
        try:
            query_subschemas([], request.query_path, request.record_id)
        except ValueError as exc:
            raise mapping_error(exc, 'subschema_path_validation') from None
        if request.review_fields:
            from local_api.services.llm_schema_mapping import map_with_field_review
            mapped = await run_in_threadpool(map_with_field_review, request)
        else:
            mapped = await run_in_threadpool(map_schema, request)
        matches = query_subschemas(mapped.section_schemas, request.query_path, request.record_id)
        return {'query_path': request.query_path, 'matches': matches, 'provider_calls': mapped.meta.get('provider_calls', 0),
                'mapping_result': mapped.meta.get('mapping_result', mapping_result(mapped)),
                'field_review': mapped.meta.get('field_review', {'status': 'not_requested', 'provider_calls': 0})}
    except ValueError as exc:
        raise mapping_error(exc) from None


@router.post('',response_model=SchemaMappingResponse)
async def map_existing_sections(request: ReviewedSchemaMappingRequest):
    try:
        if request.review_fields:
            from local_api.services.llm_schema_mapping import map_with_field_review
            mapped = await run_in_threadpool(map_with_field_review, request)
        else:
            mapped = await run_in_threadpool(map_schema,request)
        mapped.meta['mapping_result'] = mapping_result(mapped,
            fallback=mapped.meta.get('mapping_result', {}).get('fallback_used', False))
        field_review = mapped.meta.get('field_review', {})
        stage_summary(5, f'{len(request.sections.sections)} source sections',
                      f'{sum(len(s.records) for s in mapped.section_schemas)} schema records; '
                      f'{len(mapped.meta.get("field_evidence", {}))} field entries with source references; '
                      f'field review {field_review.get("status", "not requested")} ({field_review.get("provider_calls", 0)} calls)',
                      'deterministic field mapping plus any accepted provider review')
        from local_api.services.standardization.service import standardize_resume_data
        from local_api.services.standardization.mapping import mapping_input, attach_mapping_findings
        std_resume, metadata, status, warnings = standardize_resume_data(mapping_input(mapped))
        mapped.standardized_data = std_resume
        metadata.source_evidence = mapped.meta.get("field_evidence", {})
        mapped.schema_version = metadata.schema_version
        mapped.standardization_metadata = metadata
        mapped.validation_status = status
        mapped.warnings = warnings
        attach_mapping_findings(mapped, warnings)
        if mapped.meta.get('reviewed_sections') or mapped.section_schemas:
            from local_api.schemas.sections import SectionResponse
            reviewed = SectionResponse.model_validate(mapped.meta.get('reviewed_sections') or request.sections.model_dump(mode='json'))
            reviewed.metadata['field_review'] = mapped.meta.get('field_review', {})
            reviewed.metadata['field_review_issues'] = [
                {'kind':'field','section':section.category,'record_id':record.record_id,
                 'field':attribute.name,'source_ids':record.source_ids,
                 'reason':f'{attribute.name}: source mapping requires review ({attribute.status}).'}
                for section in mapped.section_schemas for record in section.records for attribute in record.attributes
                if attribute.status in {'unresolved','ambiguous','unmapped'} or any(item.status=='needs_review' for item in attribute.items)]
        else:
            reviewed = request.sections.model_copy(deep=True)
        from local_api.services.schema_audit import audit_mapping
        audit = await run_in_threadpool(audit_mapping, request.elements, reviewed, mapped,
                                        requested=request.review_fields)
        mapped.meta['schema_audit'] = audit
        stage_summary(6, 'mapped fields, record boundaries and source spans',
                      f'Read-only schema audit {audit["status"]}; {audit.get("provider_calls", 0)} calls; '
                      f'{len(audit.get("findings", []))} findings; '
                      f'{audit.get("coverage", {}).get("checked_units", 0)} checked items',
                      'source and schema validation; read-only LLM audit when requested')
        reviewed.metadata['schema_audit'] = audit
        if reviewed.review_issues:
            reviewed.status = 'needs_review'
            mapped.validation_status.requires_human_review = True
            if mapped.meta['mapping_result'].get('status') == 'success':
                mapped.meta['mapping_result'].update(status='needs_review', requires_review=True)
        mapped.meta['reviewed_sections'] = reviewed.model_dump(mode='json')
        from local_api.services.standardization.export import standardized_export
        mapped.consumer_export = standardized_export(mapped)
        export = mapped.consumer_export
        trace_export_fields(export, mapped)
        from local_api.services.trace_totals import populated_values
        emit('final_export', schema_version=mapped.schema_version,
             requires_human_review=status.requires_human_review,
             populated_values=populated_values(export.get('data', {})),
             preview=json.dumps(export, ensure_ascii=True, indent=2)[:2400]
             if os.getenv('RESUME_LOG_VALUES', '').lower() == 'true' else None)
        stage_summary(7, 'mapped fields and normalization rules',
                      f'JSON schema {mapped.schema_version}; {len(warnings)} validation notices; '
                      f'human review {"required" if status.requires_human_review else "not required"}',
                      'local standardization and JSON export')
        emit('export_result', requires_human_review=status.requires_human_review, validation_notices=len(warnings))
        return mapped
    except ValueError as exc:
        raise mapping_error(exc) from None


@router.post('/standardize')
async def standardize_existing_schema(payload: dict, include_audit: bool = False):
    """Version 2 consumer output; include_audit=true retains source and processing evidence."""
    from local_api.services.standardization.service import standardize_resume_data
    from local_api.services.standardization.export import standardized_export
    data_dict = payload.get('data', payload)
    try:
        std_resume, metadata, status, warnings = standardize_resume_data(data_dict)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, detail='Resume data must have a valid object structure.') from None
    return standardized_export({'data': data_dict, 'standardized_data': std_resume.model_dump(),
        'standardization_metadata': metadata.model_dump(), 'validation_status': status.model_dump(),
        'warnings': [w.model_dump() for w in warnings], 'source': payload.get('source')},
        include_audit=include_audit)
