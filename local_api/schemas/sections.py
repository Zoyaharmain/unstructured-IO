from typing import Annotated, Literal
from pydantic import BaseModel, Field, model_validator
from local_api.schemas.extraction import ExtractedElement


class SectionRequest(BaseModel):
    elements: Annotated[list[ExtractedElement], Field(min_length=1, max_length=1000)]
    extraction_verified: Literal[True]

    @model_validator(mode='after')
    def validate_text_size(self):
        if sum(len(element.text) for element in self.elements) > 100_000:
            raise ValueError('Section detection supports up to 100,000 characters')
        if not any(element.text.strip() for element in self.elements):
            raise ValueError('No extracted text to group')
        return self


class SectionBlock(BaseModel):
    source_element_index: int
    start: int
    end: int
    text: str
    page_number: int | None
    cluster_id: int | None = None
    candidate_section: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    cluster_space: Literal['heading', 'content'] = 'content'
    context_source_element_index: int | None = None
    assignment: str
    similarity: float | None = None
    margin: float | None = None
    lane: str
    reason: str


class SectionEntry(BaseModel):
    entry_id: str
    block_indices: list[int]
    lane: str
    boundary_reason: str


class ReadableGroup(BaseModel):
    kind: str
    title: str
    block_indices: list[int]
    children: list['ReadableGroup'] = Field(default_factory=list)


class ResumeSection(BaseModel):
    category: str
    label: str
    blocks: list[SectionBlock]
    entries: list[SectionEntry] = Field(default_factory=list)
    source_heading: str | None = None
    readable_blocks: list[ReadableGroup] = Field(default_factory=list)


class SectionResponse(BaseModel):
    status: Literal['provisional', 'needs_review']
    extraction_verified: bool = True
    sections: list[ResumeSection]
    needs_review: list[SectionBlock]
    metadata: dict
    warnings: list[str]
