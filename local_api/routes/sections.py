from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.resume_sections import detect_sections
from local_api.utils.file_validation import ExtractionError
from local_api.services.section_recovery import recover_sections
from local_api.services.llm_section_review import review_sections, review_status, check_connection
from local_api.services.decision_trace import emit, stage_summary

router = APIRouter()


def report_detection(request, result):
    assigned = sum(len(s.blocks) for s in result.sections)
    stage_summary(2, f'{len(request.elements)} extracted elements',
                  f'{assigned} blocks assigned to {len(result.sections)} sections; {len(result.needs_review)} unresolved',
                  'local headings, layout and context rules plus Sentence-BERT/K-means suggestions')
    stage_summary(3, f'{assigned} assigned blocks',
                  f'{sum(len(s.entries) for s in result.sections)} initial record groups',
                  'local grouping by source boundaries and record context')


def report_ownership(result, before):
    section = result.metadata.get('llm_review', {})
    structure = result.metadata.get('structure_review', {})
    stage_summary(4, f'initial sections and groups; {before} unresolved blocks',
                  f'{len(result.needs_review)} unresolved; section review {section.get("status", "not requested")} '
                  f'({section.get("provider_calls", 0)} calls); record review {structure.get("status", "not requested")} '
                  f'({structure.get("provider_calls", 0)} calls)',
                  'local ownership checks and any requested DeepSeek review')
    emit('stage_summary_result', unresolved=len(result.needs_review))


@router.post('/api/v1/resume/sections', response_model=SectionResponse)
async def resume_sections(request: SectionRequest):
    try:
        local_result = await run_in_threadpool(detect_sections, request)
        report_detection(request, local_result)
        before = len(local_result.needs_review)
        local_result = await run_in_threadpool(recover_sections, request, local_result)
        from local_api.services.contact_sections import recover_contact_sections
        from local_api.services.education_date_recovery import recover_education_dates
        from local_api.services.source_ownership import finalize_ownership
        local_result = recover_contact_sections(recover_education_dates(local_result, request.elements), request.elements)
        local_result = await run_in_threadpool(finalize_ownership, request.elements, local_result)
        reviewed = await run_in_threadpool(review_sections, request, local_result)
        result = await run_in_threadpool(finalize_ownership, request.elements, reviewed, review='ambiguous')
        report_ownership(result, before)
        return result
    except ExtractionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@router.post('/api/v1/resume/sections/local', response_model=SectionResponse)
async def local_resume_sections(request: SectionRequest):
    """Inspect local detection without entering any external review path."""
    try:
        result = await run_in_threadpool(detect_sections, request)
        report_detection(request, result)
        before = len(result.needs_review)
        result = await run_in_threadpool(recover_sections, request, result)
        from local_api.services.contact_sections import recover_contact_sections
        result = recover_contact_sections(result, request.elements)
        from local_api.services.education_date_recovery import recover_education_dates
        result = recover_education_dates(result, request.elements)
        result.metadata['inspection_mode'] = 'local_only'
        result.metadata['llm_review'] = {'status': 'not_requested', 'provider_calls': 0}
        from local_api.services.source_ownership import finalize_ownership
        result = finalize_ownership(request.elements, result)
        report_ownership(result, before)
        return result
    except ExtractionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@router.get('/api/v1/resume/review-status')
def llm_review_status():
    return review_status()


@router.post('/api/v1/resume/review-connection')
def llm_review_connection():
    return check_connection()
