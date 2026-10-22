from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.resume_sections import detect_sections
from local_api.utils.file_validation import ExtractionError
from local_api.services.section_recovery import recover_sections
from local_api.services.llm_section_review import review_sections, review_status, check_connection

router = APIRouter()


@router.post('/api/v1/resume/sections', response_model=SectionResponse)
async def resume_sections(request: SectionRequest):
    try:
        local_result = await run_in_threadpool(detect_sections, request)
        local_result = await run_in_threadpool(recover_sections, request, local_result)
        return await run_in_threadpool(review_sections, request, local_result)
    except ExtractionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@router.post('/api/v1/resume/sections/local', response_model=SectionResponse)
async def local_resume_sections(request: SectionRequest):
    """Inspect local detection without entering any external review path."""
    try:
        result = await run_in_threadpool(detect_sections, request)
        result = await run_in_threadpool(recover_sections, request, result)
        result.metadata['inspection_mode'] = 'local_only'
        result.metadata['llm_review'] = {'status': 'not_requested', 'provider_calls': 0}
        return result
    except ExtractionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@router.get('/api/v1/resume/review-status')
def llm_review_status():
    return review_status()


@router.post('/api/v1/resume/review-connection')
def llm_review_connection():
    return check_connection()
