"""Schema mapping consumes existing blocks, without triggering provider requests."""
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from local_api.schemas.mapping import SchemaMappingRequest, SchemaMappingResponse
from local_api.services.schema_mapping import map_schema
from local_api.vendor.handoff_schema.models import ResumeSchema
from local_api.vendor.handoff_schema.schema_spec import get_full_schema_mapping

router=APIRouter(prefix='/api/v1/resume/schema',tags=['Resume schema mapping'])


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
    return spec


@router.post('',response_model=SchemaMappingResponse)
async def map_existing_sections(request: SchemaMappingRequest):
    try:
        return await run_in_threadpool(map_schema,request)
    except ValueError as exc:
        raise HTTPException(422,'Invalid or stale source/section binding') from exc
