"""Local Unstructured adapter, callable without HTTP or application state."""
from io import BytesIO
from importlib.util import find_spec
import logging
import os
import shutil
from zipfile import BadZipFile

from unstructured.file_utils.filetype import detect_filetype
from unstructured.file_utils.model import FileType
from unstructured.partition.auto import partition

from local_api.core.config import Settings
from local_api.errors import error_status
from local_api.schemas.extraction import ExtractionResponse, ExtractionMetadata, ExtractedElement, Strategy
from local_api.utils.file_validation import ExtractionError, safe_filename

logger = logging.getLogger(__name__)
ALLOWED_TYPES = {getattr(FileType, name) for name in
                 ('PDF', 'DOC', 'DOCX', 'TXT', 'MD', 'HTML', 'CSV', 'XLSX', 'PPTX', 'PNG', 'JPG')}


def extract_text(payload: bytes, filename: str, strategy: Strategy = 'auto',
                 include_elements: bool = True, settings: Settings | None = None) -> ExtractionResponse:
    settings = settings or Settings.from_env()
    filename = safe_filename(filename)
    if not payload:
        raise ExtractionError(422, 'Uploaded document is empty')
    if len(payload) > settings.max_upload_bytes:
        raise ExtractionError(413, 'Uploaded file exceeds configured size limit')
    if strategy not in {'auto', 'fast', 'hi_res', 'ocr_only'}:
        raise ExtractionError(422, 'Invalid extraction strategy')
    try:
        stream = BytesIO(payload)
        # Inspect content before using a filename hint for ambiguous textual formats.
        detected = detect_filetype(file=stream)
        stream.seek(0)
        if detected not in ALLOWED_TYPES:
            raise ExtractionError(415, 'Unsupported document content')
        if detected == FileType.TXT:
            detected = detect_filetype(file=stream, metadata_file_path=filename)
            stream.seek(0)
        if detected not in ALLOWED_TYPES:
            raise ExtractionError(415, 'Unsupported document content')
        if detected == FileType.PDF:
            # Upstream fast may suppress parser errors and return an empty list.
            # Validate readability separately; extraction remains entirely upstream.
            from pypdf import PdfReader
            reader = PdfReader(stream)
            if reader.is_encrypted:
                raise ExtractionError(422, 'Encrypted PDFs are unsupported by this endpoint')
            len(reader.pages)
            stream.seek(0)
        image = detected in {FileType.PNG, FileType.JPG}
        if (image and strategy == 'fast') or (detected != FileType.PDF and not image and strategy != 'auto'):
            raise ExtractionError(422, 'Requested strategy is unsupported for this document format')
        local_ocr_agent = 'unstructured.partition.utils.ocr_models.tesseract_ocr.OCRAgentTesseract'
        if (detected == FileType.PDF or image) and os.getenv('OCR_AGENT', local_ocr_agent) not in {local_ocr_agent, 'tesseract'}:
            raise ExtractionError(503, 'This local extraction service requires the Tesseract OCR agent')
        if detected == FileType.DOC and not shutil.which('soffice'):
            raise ExtractionError(503, 'Legacy Word extraction requires LibreOffice (soffice)')
        if strategy == 'ocr_only' and (not shutil.which('tesseract') or find_spec('unstructured_pytesseract') is None):
            raise ExtractionError(503, 'OCR extraction requires Tesseract and unstructured-pytesseract')
        if strategy == 'hi_res' and find_spec('unstructured_inference') is None:
            raise ExtractionError(503, 'High-resolution extraction requires unstructured-inference')
        elements = partition(file=stream, content_type=detected.mime_type,
                             metadata_filename=filename, strategy=strategy, languages=['eng'])
        serialized = [e.to_dict() for e in elements]
        # Uploads carry no local filesystem identity. Never expose parser paths.
        for element in serialized:
            metadata = element.setdefault('metadata', {})
            metadata.pop('file_directory', None)
            metadata['filename'] = filename
        pages = sorted({e['metadata']['page_number'] for e in serialized
                        if isinstance(e['metadata'].get('page_number'), int)})
        return ExtractionResponse(
            filename=filename, file_type=detected.mime_type, strategy=strategy,
            text='\n\n'.join(e.get('text', '') for e in serialized),
            elements=[ExtractedElement(type=e.get('type', 'UncategorizedText'), text=e.get('text', ''),
                                      page_number=e['metadata'].get('page_number'), metadata=e['metadata'])
                      for e in serialized] if include_elements else None,
            # Element page numbers do not establish the number of blank/trailing pages.
            metadata=ExtractionMetadata(total_elements=len(serialized), page_count=None, page_numbers=pages))
    except ExtractionError:
        raise
    except Exception as exc:
        # Log only exception class, never document content, exception text or parser paths.
        logger.error('Extraction failed: %s', type(exc).__name__)
        status = 422 if isinstance(exc, (BadZipFile, SyntaxError)) else error_status(exc)
        message = {422: 'Corrupted or invalid document', 503: 'Required extraction dependency unavailable',
                   500: 'Unexpected internal processing failure'}[status]
        raise ExtractionError(status, message) from exc
