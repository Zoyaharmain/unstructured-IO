"""Versioned canonical contracts for resume JSON standardization and validation."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from local_api.vendor.handoff_schema.models import (
    ContactInfo,
    WorkExperience,
    Education,
    CategorizedSkills,
    Project,
    Certification,
)


class StandardizationWarning(BaseModel):
    model_config = ConfigDict(extra="ignore")
    field: str = Field(description="Target field or path affected by the warning")
    warning_type: str = Field(description="Classification of normalization or issue (e.g. ocr_correction, date_standardization, alias_canonicalization)")
    severity: Literal["info", "warning", "review_required"] = Field(default="info", description="Severity level")
    original_value: Any = Field(default=None, description="Original source-extracted value before modification")
    normalized_value: Any = Field(default=None, description="Standardized or canonical value")
    suggested_value: Any = None
    basis: str | None = None
    applied: bool = False
    verification_status: str = 'rule_based_not_independently_verified'
    message: str = Field(description="Human-readable explanation of why this was changed or flagged")


class StandardizationMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    applied_at: str = Field(description="ISO-8601 UTC timestamp of normalization")
    total_normalizations: int = Field(default=0, description="Count of applied normalization log entries; not distinct fields")
    corrections_by_type: dict[str, int] = Field(default_factory=dict, description="Summary counts per warning/normalization type")
    corrections: list[StandardizationWarning] = Field(default_factory=list, description="Applied system changes with original values, resulting values and reasons")
    source_evidence: dict[str, list[str]] = Field(default_factory=dict)
    as_of_date: str | None = None
    duration_policy: str = 'Year precision: annual-resolution estimates from year-label differences, including current reference year for current roles; months are estimated years times 12, not known elapsed months. Year-label unions use common annual boundaries only for computation; no employment month is inferred. Month precision: elapsed calendar months (approximate). Day precision: completed calendar units. Aggregate unions use first-of-month boundaries for month-only dates; residual days use 365.2425/12 days per month, rounded to one decimal year.'
    field_verification: dict[str, str] = Field(default_factory=dict)
    cross_field_notes: list[str] = Field(default_factory=list, description="Cross-field relationship and consistency observations")
    experience_summary: dict[str, Any] = Field(default_factory=dict)
    experience_calculations: list[dict[str, Any]] = Field(default_factory=list)


class ValidationStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    is_valid: bool = Field(default=True, description="Whether schema passes validation constraints")
    usable: bool = Field(default=True, description="Whether data is ready for downstream consumption")
    requires_human_review: bool = Field(default=False, description="Whether flagged inconsistencies require human verification")
    issues_count: int = Field(default=0, description="Total number of warnings and flags")


class StandardizedContactInfo(ContactInfo):
    model_config = ConfigDict(extra="ignore")
    raw_phone: str | None = Field(default=None, description="Raw source phone string")
    phone_e164: str | None = Field(default=None, description="E.164 canonical phone number if country code known")
    raw_email: str | None = Field(default=None, description="Raw source email string")
    phone_extension: str | None = None


class StandardizedWorkExperience(WorkExperience):
    model_config = ConfigDict(extra="ignore")
    raw_duration: str | None = None
    duration_months: int | None = None
    duration_is_approximate: bool = True
    duration_as_of: str | None = None
    duration_status: Literal['calculated', 'estimated_year_precision', 'insufficient_dates', 'invalid_dates'] = 'insufficient_dates'
    raw_start_date: str | None = Field(default=None, description="Original source start date")
    raw_end_date: str | None = Field(default=None, description="Original source end date")
    start_date_iso: str | None = Field(default=None, description="ISO-8601 start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    end_date_iso: str | None = Field(default=None, description="ISO-8601 end date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    start_date_precision: Literal["year", "month_year", "day"] | None = Field(default=None, description="Granularity of source start date")
    end_date_precision: Literal["year", "month_year", "day"] | None = Field(default=None, description="Granularity of source end date")
    is_current: bool = Field(default=False, description="True if position is currently active (e.g. 'Present')")


class StandardizedEducation(Education):
    model_config = ConfigDict(extra="ignore")
    raw_graduation_year: str | None = Field(default=None, description="Raw source graduation year text")
    graduation_year_iso: str | None = Field(default=None, description="ISO-8601 4-digit graduation year")
    raw_start_year: str | None = Field(default=None, description="Raw source start year text")
    start_year_iso: str | None = Field(default=None, description="ISO-8601 4-digit start year")


class StandardizedProject(Project):
    model_config = ConfigDict(extra="ignore")
    raw_url: str | None = Field(default=None, description="Raw source URL string")


class StandardizedCertification(Certification):
    model_config = ConfigDict(extra="ignore")
    raw_issue_year: str | None = Field(default=None, description="Raw source issue year text")
    issue_year_iso: str | None = Field(default=None, description="ISO-8601 4-digit certification issue year")


class SupplementalRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str | None = None
    description: str | None = None
    organization: str | None = None
    date: str | None = Field(default=None, pattern=r'^\d{4}(?:-\d{2}(?:-\d{2})?)?$')
    start_date: str | None = Field(default=None, pattern=r'^\d{4}(?:-\d{2}(?:-\d{2})?)?$')
    end_date: str | None = Field(default=None, pattern=r'^\d{4}(?:-\d{2}(?:-\d{2})?)?$')
    url: str | None = None
    outcomes: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class StandardizedResumeSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    contact: StandardizedContactInfo
    professional_title: str | None = None
    summary: str | None = None
    total_experience_years: float | None = Field(default=None, description="Non-overlapping experience at source precision, including labelled year-only estimates; null when records cannot be dated")
    stated_total_experience_years: float | None = Field(default=None, description="Original source-stated numeric experience; qualifiers remain in original summary/evidence")
    calculated_experience_years: float | None = Field(default=None, description="Calculated non-overlapping chronological experience in years")
    calculated_experience_complete: bool = Field(default=False, description="All employment records included at supplied precision; does not establish exact months")
    calculated_experience_is_approximate: bool = False
    experience_overlap_detected: bool = Field(default=False, description="Whether overlapping employment spans were detected")
    skills: CategorizedSkills = Field(default_factory=CategorizedSkills)
    experience: list[StandardizedWorkExperience] = Field(default_factory=list)
    education: list[StandardizedEducation] = Field(default_factory=list)
    certifications: list[StandardizedCertification] = Field(default_factory=list)
    projects: list[StandardizedProject] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    awards: list[SupplementalRecord] = Field(default_factory=list)
    achievements: list[SupplementalRecord] = Field(default_factory=list)
    publications: list[SupplementalRecord] = Field(default_factory=list)
    volunteering: list[SupplementalRecord] = Field(default_factory=list)
    interests: list[SupplementalRecord] = Field(default_factory=list)
    references: list[SupplementalRecord] = Field(default_factory=list)
    additional_sections: list[dict[str, Any] | str] = Field(default_factory=list)

