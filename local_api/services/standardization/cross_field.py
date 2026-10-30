"""Cross-field consistency validation and sanity checks."""
from __future__ import annotations

from local_api.services.standardization.contracts import (
    StandardizedResumeSchema,
    StandardizationWarning,
    ValidationStatus,
)


def validate_cross_field_consistency(
    resume: StandardizedResumeSchema,
) -> tuple[ValidationStatus, list[StandardizationWarning]]:
    """Validate consistency across resume fields and compute validation status."""
    warnings: list[StandardizationWarning] = []
    requires_review = False

    # 1. Required Contact Check
    if not resume.contact.full_name or not resume.contact.full_name.strip():
        warnings.append(
            StandardizationWarning(
                field="contact.full_name",
                warning_type="missing_required_field",
                severity="review_required",
                original_value=None,
                normalized_value=None,
                message="Candidate full name is missing from contact details."
            )
        )
        requires_review = True

    if not resume.contact.email and not resume.contact.phone:
        warnings.append(
            StandardizationWarning(
                field="contact",
                warning_type="missing_contact_methods",
                severity="warning",
                original_value=None,
                normalized_value=None,
                message="Candidate has neither email nor phone number listed."
            )
        )

    # 2. Total Experience vs Calculated Experience
    stated_exp = resume.total_experience_years
    calc_exp = resume.calculated_experience_years

    if stated_exp is not None and calc_exp is not None:
        discrepancy = abs(stated_exp - calc_exp)
        # Flag if discrepancy is more than 1.5 years
        if discrepancy > 1.5:
            warnings.append(
                StandardizationWarning(
                    field="total_experience_years",
                    warning_type="experience_duration_discrepancy",
                    severity="info",
                    original_value=stated_exp,
                    normalized_value=calc_exp,
                    message=f"Source-stated experience ({stated_exp} years) differs from calculated chronological span ({calc_exp} years). Both values preserved."
                )
            )

    # 3. Duplicate Items in Collections
    # Check duplicate responsibilities within experience records
    for idx, exp in enumerate(resume.experience):
        resp = exp.responsibilities
        if len(resp) != len(set(resp)):
            warnings.append(
                StandardizationWarning(
                    field=f"experience[{idx}].responsibilities",
                    warning_type="duplicate_items_detected",
                    severity="info",
                    original_value=resp,
                    normalized_value=list(dict.fromkeys(resp)),
                    message=f"Duplicate responsibility bullet points detected in experience[{idx}] ({exp.company})."
                )
            )

    # 4. Check for Empty Company or Institution
    for idx, exp in enumerate(resume.experience):
        if not exp.company or not exp.company.strip():
            warnings.append(
                StandardizationWarning(
                    field=f"experience[{idx}].company",
                    warning_type="empty_record_field",
                    severity="warning",
                    original_value=exp.company,
                    normalized_value=None,
                    message=f"Work experience record at index {idx} has an empty company name."
                )
            )

    for idx, edu in enumerate(resume.education):
        if not edu.institution or not edu.institution.strip():
            warnings.append(
                StandardizationWarning(
                    field=f"education[{idx}].institution",
                    warning_type="empty_record_field",
                    severity="warning",
                    original_value=edu.institution,
                    normalized_value=None,
                    message=f"Education record at index {idx} has an empty institution name."
                )
            )

    total_issues = len(warnings)
    status = ValidationStatus(
        is_valid=True,
        usable=not requires_review,
        requires_human_review=requires_review,
        issues_count=total_issues,
    )

    return status, warnings

