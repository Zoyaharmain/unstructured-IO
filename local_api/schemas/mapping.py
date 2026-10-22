"""Map an existing, source-bound section response into the handoff contract."""
from pydantic import ConfigDict, Field
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.vendor.handoff_schema.models import ParseResponse


class SchemaMappingRequest(SectionRequest):
    model_config = ConfigDict(extra='forbid')
    sections: SectionResponse
    source: str = Field(default='existing-section-blocks', min_length=1, max_length=256)


SchemaMappingResponse = ParseResponse
