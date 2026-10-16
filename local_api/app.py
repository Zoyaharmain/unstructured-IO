"""Local upload API; extraction is delegated unchanged to Unstructured auto.partition."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, Response
from starlette.concurrency import run_in_threadpool
from unstructured.partition.auto import partition

from local_api.errors import error_status
from local_api.routes.extraction import router
from local_api.routes.comparison import router as comparison_router
from local_api.routes.sections import router as sections_router

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
app = FastAPI(title='Local Unstructured Extraction API', version='1.0.0')


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    if any(e.get('loc', ())[-1:] == ('file',) for e in exc.errors()):
        return JSONResponse(status_code=400, content={'detail': 'Missing file or empty filename'})
    return JSONResponse(status_code=422, content={'detail': 'Invalid request parameters'})


app.include_router(router)
app.include_router(comparison_router)
app.include_router(sections_router)
STATIC_DIR = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


@app.middleware('http')
async def frontend_cache_control(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == '/' or request.url.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/', include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / 'index.html')


@app.get('/favicon.ico', include_in_schema=False, status_code=204)
async def favicon():
    return Response(status_code=204)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.error('Unexpected API failure: %s', type(exc).__name__)
    return JSONResponse(status_code=500, content={'detail': 'Unexpected internal processing failure'})


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/v1/partition')
async def partition_document(
    file: Annotated[UploadFile | None, File()] = None,
    strategy: Annotated[Literal['auto', 'fast', 'hi_res', 'ocr_only'], Form()] = 'auto',
    languages: Annotated[list[str] | None, Form()] = None,
    hi_res_model_name: Annotated[str | None, Form()] = None,
    infer_table_structure: Annotated[bool, Form()] = False,
    include_page_breaks: Annotated[bool, Form()] = False,
    starting_page_number: Annotated[int, Form(ge=1)] = 1,
    pdf_image_dpi: Annotated[int, Form(ge=1, le=600)] = 200,
    metadata_last_modified: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
):
    if file is None:
        raise HTTPException(400, 'Missing file or empty filename')
    try:
        if not file.filename or not file.filename.strip():
            raise HTTPException(400, 'Missing file or empty filename')
        size = 0
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(413, 'Uploaded file exceeds 25 MiB')
        if not size:
            raise HTTPException(422, 'Uploaded document is empty')
        await file.seek(0)
        # Let the original file detector choose the correct document partitioner.
        # No content-type override forces non-PDF documents down the PDF path.
        settings = dict(
            metadata_filename=file.filename, strategy=strategy, languages=languages or ['eng'],
            hi_res_model_name=hi_res_model_name, infer_table_structure=infer_table_structure,
            include_page_breaks=include_page_breaks, starting_page_number=starting_page_number,
            pdf_image_dpi=pdf_image_dpi, metadata_last_modified=metadata_last_modified,
            password=password,
        )
        def extract():
            return [element.to_dict() for element in partition(file=file.file, **settings)]
        try:
            elements = await run_in_threadpool(extract)
        except Exception as exc:
            status = error_status(exc)
            logger.error('Document partition failed (HTTP %s): %s', status, type(exc).__name__)
            message = {422: 'Unsupported or invalid document input',
                       503: 'Required extraction dependency unavailable',
                       500: 'Unexpected internal processing failure'}[status]
            raise HTTPException(status, message) from exc
        return {
            'filename': file.filename,
            'requested_strategy': strategy,
            'element_count': len(elements),
            'page_numbers': sorted({e['metadata']['page_number'] for e in elements
                                    if e.get('metadata', {}).get('page_number') is not None}),
            'text': '\n\n'.join(e.get('text', '') for e in elements),
            'elements': elements,
        }
    finally:
        await file.close()
