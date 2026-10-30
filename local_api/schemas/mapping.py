"""Map an existing, source-bound section response into the handoff contract."""
from pydantic import ConfigDict, Field, computed_field
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.vendor.handoff_schema.models import ParseResponse
from local_api.schemas.subschemas import SectionSchema
from local_api.services.standardization.contracts import (
    StandardizedResumeSchema,
    StandardizationMetadata,
    ValidationStatus,
    StandardizationWarning,
)


class SchemaMappingRequest(SectionRequest):
    model_config = ConfigDict(extra='forbid')
    sections: SectionResponse
    source: str = Field(default='existing-section-blocks', min_length=1, max_length=256)


class SchemaMappingResponse(ParseResponse):
    section_schemas: list[SectionSchema] = Field(default_factory=list)
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    standardized_data: StandardizedResumeSchema | None = Field(default=None, description="Standardized canonical resume payload")
    standardization_metadata: StandardizationMetadata | None = Field(default=None, description="Audit metadata of all applied normalizations")
    validation_status: ValidationStatus | None = Field(default=None, description="Schema and cross-field validation status")
    warnings: list[StandardizationWarning] = Field(default_factory=list, description="Structured warnings for all corrections and normalizations")

    @computed_field
    @property
    def subschema_definitions(self) -> dict:
        from copy import deepcopy
        from local_api.schemas.subschema_spec import hierarchy_definition
        return deepcopy(hierarchy_definition())

    @computed_field
    @property
    def field_index(self) -> dict:
        from local_api.services.subschema_validation import build_field_index
        return build_field_index(self.section_schemas)


class SubschemaQueryRequest(SchemaMappingRequest):
    query_path: str = Field(min_length=3, max_length=128)
    record_id: str | None = Field(default=None, max_length=256)


class ReviewedSchemaMappingRequest(SchemaMappingRequest):
    review_fields: bool = False


class ReviewedSubschemaQueryRequest(SubschemaQueryRequest):
    review_fields: bool = False
