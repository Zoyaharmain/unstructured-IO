"""Map source-bound blocks; explicit review_fields enables grounded DeepSeek mapping."""
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from local_api.schemas.mapping import SchemaMappingResponse, ReviewedSubschemaQueryRequest, ReviewedSchemaMappingRequest
from local_api.services.schema_mapping import map_schema
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


@router.get('/definition')
def definition():
    return ResumeSchema.model_json_schema()


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
        mapped.meta['mapping_result'] = mapping_result(mapped)
        from local_api.services.standardization.service import standardize_resume_data
        std_resume, metadata, status, warnings = standardize_resume_data(mapped.data)
        mapped.standardized_data = std_resume
        metadata.source_evidence = mapped.meta.get("field_evidence", {})
        mapped.schema_version = metadata.schema_version
        mapped.standardization_metadata = metadata
        mapped.validation_status = status
        mapped.warnings = warnings
        return mapped
    except ValueError as exc:
        raise mapping_error(exc) from None


@router.post('/standardize')
async def standardize_existing_schema(payload: dict):
    """Directly standardize an existing resume schema or ParseResponse dictionary."""
    from local_api.services.standardization.service import standardize_resume_data
    # Extract data payload if wrapped in ParseResponse or SchemaMappingResponse
    data_dict = payload.get('data', payload)
    std_resume, metadata, status, warnings = standardize_resume_data(data_dict)
    from local_api.services.standardization.export import standardized_export
    canonical = standardized_export({'data':data_dict,'standardized_data':std_resume.model_dump(),
        'standardization_metadata':metadata.model_dump(),'validation_status':status.model_dump(),
        'warnings':[w.model_dump() for w in warnings],'source':payload.get('source')})
    return {
        'export_type':canonical['export_type'],
        'data':canonical['data'],
        'source_evidence':canonical['source_evidence'],
        'schema_version': metadata.schema_version,
        'standardized_data': std_resume.model_dump(),
        'standardization_metadata': canonical['standardization_metadata'],
        'validation_status': status.model_dump(),
        'warnings': [w.model_dump() for w in warnings],
    }
