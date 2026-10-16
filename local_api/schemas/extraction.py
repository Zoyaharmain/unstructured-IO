from typing import Any, Literal
from pydantic import BaseModel

Strategy = Literal['auto', 'fast', 'hi_res', 'ocr_only']


class ExtractedElement(BaseModel):
    type: str
    text: str
    page_number: int | None = None
    metadata: dict[str, Any]


class ExtractionMetadata(BaseModel):
    total_elements: int
    page_count: int | None = None
    page_numbers: list[int]


class ExtractionResponse(BaseModel):
    success: bool = True
    filename: str
    file_type: str
    strategy: Strategy
    text: str
    elements: list[ExtractedElement] | None = None
    metadata: ExtractionMetadata
