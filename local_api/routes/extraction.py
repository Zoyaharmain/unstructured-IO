from typing import Annotated
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool
from local_api.core.config import Settings
from local_api.schemas.extraction import ExtractionResponse, Strategy
from local_api.services.text_extraction_service import extract_text
from local_api.utils.file_validation import ExtractionError, safe_filename

router = APIRouter()


@router.post('/api/v1/extract/text', response_model=ExtractionResponse)
async def extract_document(
    file: Annotated[UploadFile | None, File()] = None,
    strategy: Annotated[Strategy, Form()] = 'auto',
    include_elements: Annotated[bool, Form()] = True,
):
    if file is None:
        raise HTTPException(400, 'Missing file or empty filename')
    try:
        name = safe_filename(file.filename or '')
        settings = Settings.from_env()
        payload = bytearray()
        while chunk := await file.read(min(1024 * 1024, settings.max_upload_bytes + 1)):
            payload.extend(chunk)
            if len(payload) > settings.max_upload_bytes:
                raise ExtractionError(413, 'Uploaded file exceeds configured size limit')
        return await run_in_threadpool(extract_text, bytes(payload), name, strategy, include_elements, settings)
    except ExtractionError as exc:
        raise HTTPException(exc.status, str(exc)) from exc
    finally:
        await file.close()
