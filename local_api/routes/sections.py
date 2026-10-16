from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.resume_sections import detect_sections
from local_api.utils.file_validation import ExtractionError

router = APIRouter()


@router.post('/api/v1/resume/sections', response_model=SectionResponse)
async def resume_sections(request: SectionRequest):
    try:
        return await run_in_threadpool(detect_sections, request)
    except ExtractionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc
