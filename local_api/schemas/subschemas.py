"""Strict, additive section/record/attribute contract; legacy data stays compatible."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from local_api.schemas.subschema_spec import SUBSCHEMAS, valid_field_shape


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class SourceQuote(StrictModel):
    source_id: str = Field(min_length=1)
    quote: str


class AttributeValue(StrictModel):
    value: str | float
    evidence: list[SourceQuote] = Field(min_length=1)
    status: Literal['source_supported', 'needs_review'] = 'source_supported'

    @model_validator(mode='after')
    def nonempty_support(self):
        if any(not ref.quote.strip() for ref in self.evidence):
            raise ValueError('Populated attributes require nonempty evidence quotes')
        return self


class Attribute(StrictModel):
    name: str
    items: list[AttributeValue] = Field(default_factory=list)
    status: Literal['mapped', 'unresolved', 'not_stated', 'ambiguous', 'unmapped'] = 'unresolved'

    @model_validator(mode='after')
    def consistent_status(self):
        if (self.status == 'mapped') != bool(self.items):
            raise ValueError('Attribute status must agree with its items')
        return self


class SubschemaRecord(StrictModel):
    record_id: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)
    attributes: list[Attribute]
    review_reasons: list[str] = Field(default_factory=list)


class SectionSchema(StrictModel):
    category: str
    label: str
    records: list[SubschemaRecord]
    residual_blocks: list[SourceQuote] = Field(default_factory=list)

    @model_validator(mode='after')
    def defined_hierarchy(self):
        if self.category not in SUBSCHEMAS:
            raise ValueError('Unknown parent schema')
        specification = SUBSCHEMAS[self.category]
        if len({r.record_id for r in self.records}) != len(self.records):
            raise ValueError('Duplicate record ID')
        for record in self.records:
            names = [a.name for a in record.attributes]
            if len(set(names)) != len(names) or set(names) != set(specification):
                raise ValueError('Unknown, duplicate or missing child schema')
            for attribute in record.attributes:
                rule = specification[attribute.name]
                if not rule['multiple'] and len(attribute.items) > 1:
                    raise ValueError('Scalar child has multiple values')
                for item in attribute.items:
                    if not valid_field_shape(self.category, attribute.name, item.value):
                        raise ValueError('Value violates the child field shape policy')
                    if rule['type'] == 'string' and not isinstance(item.value, str):
                        raise ValueError('String child requires a string')
                    if rule['type'] == 'number' and (isinstance(item.value, bool) or not isinstance(item.value, (float, int))):
                        raise ValueError('Numeric child requires a number')
        return self
