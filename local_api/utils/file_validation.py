"""Upload validation without trusting client MIME declarations."""
from pathlib import PurePosixPath

ALLOWED_SUFFIXES = {'.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.csv', '.xlsx', '.pptx', '.png', '.jpg', '.jpeg'}


class ExtractionError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


def safe_filename(filename: str) -> str:
    name = PurePosixPath(filename.replace('\\', '/')).name
    if not name.strip() or name in {'.', '..'}:
        raise ExtractionError(400, 'Missing file or empty filename')
    if PurePosixPath(name).suffix.lower() not in ALLOWED_SUFFIXES:
        raise ExtractionError(415, 'Unsupported document format')
    return name
