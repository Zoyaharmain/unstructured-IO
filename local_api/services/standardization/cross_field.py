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
    stated_exp = resume.stated_total_experience_years
    calc_exp = resume.calculated_experience_years

    if stated_exp is not None and calc_exp is not None:
        discrepancy = abs(stated_exp - calc_exp)
        # Allow only the rounding tolerance of the calculated one-decimal value.
        if discrepancy > 0.100000001:
            warnings.append(
                StandardizationWarning(
                    field="total_experience_years",
                    warning_type="experience_duration_discrepancy",
                    severity="review_required",
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

    for category, records, required in (
        ('experience', resume.experience, 'role'),
        ('education', resume.education, 'degree'),
        ('certifications', resume.certifications, 'name'),
        ('projects', resume.projects, 'name'),
    ):
        for i, record in enumerate(records):
            if not getattr(record, required).strip():
                warnings.append(StandardizationWarning(field=f'{category}[{i}].{required}',
                    warning_type='empty_record_field', severity='review_required',
                    message='Required record identity is not established; source review required.'))
    if resume.additional_sections:
        warnings.append(StandardizationWarning(field='additional_sections', warning_type='unresolved_source_content',
            severity='review_required', message='Additional source content is retained and requires association review.'))

    # Compare source-stated elapsed durations only, never a literal date range.
    import re
    for i, job in enumerate(resume.experience):
        raw = job.raw_duration
        if not raw or job.duration_months is None:
            continue
        # A source date range may carry its explicit elapsed claim in parentheses.
        parenthetical = re.search(r'\(([^()]*)\)\s*$', raw)
        elapsed_claim = parenthetical[1] if parenthetical else raw
        match = re.fullmatch(r'\s*(?:(\d+)\s*(?:years?|yrs?)\s*(?:and\s*)?)?(?:(\d+)\s*(?:months?|mos?)\s*)?', elapsed_claim, re.I)
        if match and any(match.groups()):
            months = int(match[1] or 0) * 12 + int(match[2] or 0)
            if months != job.duration_months:
                warnings.append(StandardizationWarning(field=f'experience[{i}].duration',
                    warning_type='stated_duration_discrepancy', severity='review_required',
                    original_value=raw, normalized_value=job.duration, applied=True,
                    basis='Elapsed calendar duration calculated from employment start/end dates; current roles use the metadata as-of date.',
                    message='System corrected the source-stated duration using employment dates; original duration retained.'))
    for category, records, start_key, end_key in (
        ('education', resume.education, 'start_year', 'graduation_year'),
        ('certifications', resume.certifications, 'issue_year', 'expiry_date'),
        ('projects', resume.projects, 'start_date', 'end_date'),
        ('awards', resume.awards, 'start_date', 'end_date'),
        ('achievements', resume.achievements, 'start_date', 'end_date'),
        ('publications', resume.publications, 'start_date', 'end_date'),
        ('volunteering', resume.volunteering, 'start_date', 'end_date'),
    ):
        for i, record in enumerate(records):
            start, end = getattr(record, start_key), getattr(record, end_key)
            # Only compare the precision both values establish.
            if start and end and start[:min(len(start), len(end))] > end[:min(len(start), len(end))]:
                warnings.append(StandardizationWarning(field=f'{category}[{i}]', warning_type='invalid_date_order',
                    severity='review_required', original_value={start_key: start, end_key: end},
                    message='Start/issue date is after end/expiry date. Source values require review.'))
    from local_api.services.standardization.validation import finalize_status
    return finalize_status(warnings), warnings
