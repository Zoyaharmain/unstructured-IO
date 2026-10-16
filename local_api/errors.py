def error_status(exc: Exception) -> int:
    """Translate documented input/dependency failures; do not hide internal bugs as input errors."""
    dependency_errors = {
        ('pdf2image.exceptions', 'PDFInfoNotInstalledError'),
        ('unstructured_pytesseract.pytesseract', 'TesseractNotFoundError'),
    }
    invalid_errors = {
        ('unstructured.partition.common', 'UnsupportedFileFormatError'),
        ('unstructured.errors', 'UnprocessableEntityError'),
        ('PIL', 'UnidentifiedImageError'),
        ('PIL.UnidentifiedImageError', 'UnidentifiedImageError'),
        ('docx.opc.exceptions', 'PackageNotFoundError'),
        ('lxml.etree', 'XMLSyntaxError'),
        ('pdfminer.pdfdocument', 'PDFPasswordIncorrect'),
        ('pdfminer.pdfdocument', 'PDFEncryptionError'),
        ('pdfminer.pdfparser', 'PDFSyntaxError'),
        ('pypdf.errors', 'PdfReadError'),
        ('unstructured_inference.inference.pdf_image', 'PdfRenderTooLargeError'),
        ('pdf2image.exceptions', 'PDFPageCountError'),
        ('pdf2image.exceptions', 'PDFSyntaxError'),
        ('pypdfium2._helpers.misc', 'PdfiumError'),
    }
    cause = exc
    visited = set()
    while cause is not None and id(cause) not in visited:
        visited.add(id(cause))
        classes = {(c.__module__, c.__name__) for c in type(cause).__mro__}
        if isinstance(cause, ImportError) or classes & dependency_errors:
            return 503
        cause = cause.__cause__
    classes = {(c.__module__, c.__name__) for c in type(exc).__mro__}
    if isinstance(exc, ValueError) or classes & invalid_errors:
        return 422
    return 500


