"""Main standardization service orchestrating normalization, metadata accounting, and validation."""
from __future__ import annotations

from datetime import datetime, timezone
from collections import Counter
from local_api.services.standardization.contracts import (
    StandardizationWarning,
    StandardizationMetadata,
    ValidationStatus,
    StandardizedResumeSchema,
    StandardizedWorkExperience,
    StandardizedEducation,
    StandardizedProject,
    StandardizedCertification,
)
from local_api.services.standardization.contacts import standardize_contact
from local_api.services.standardization.skills import standardize_skills_categorized
from local_api.services.standardization.dates import (
    parse_date_string,
    calculated_duration,
    calculate_non_overlapping_experience,
)
from local_api.services.standardization.spelling import correct_ocr_or_spelling
from local_api.services.standardization.cross_field import validate_cross_field_consistency
from local_api.vendor.handoff_schema.models import ResumeSchema


def standardize_resume_data(
    data: ResumeSchema | dict,
    *, reference_date: datetime | None = None,
) -> tuple[StandardizedResumeSchema, StandardizationMetadata, ValidationStatus, list[StandardizationWarning]]:
    """Standardize resume data deterministically without altering ground-truth facts.

    Returns:
        (standardized_schema, metadata, validation_status, all_warnings)
    """
    reference_date = reference_date or datetime.now(timezone.utc)
    applied_at = datetime.now(timezone.utc).isoformat()
    all_warnings: list[StandardizationWarning] = []

    if isinstance(data, dict):
        raw_dict = data
    else:
        raw_dict = data.model_dump()

    # 1. Contact standardization
    std_contact, contact_warns = standardize_contact(raw_dict.get("contact", {}))
    all_warnings.extend(contact_warns)

    # 2. Professional title and summary
    raw_title = raw_dict.get("professional_title")
    clean_title = raw_title.strip() if raw_title else None

    raw_summary = raw_dict.get("summary")
    clean_summary = raw_summary.strip() if raw_summary else None

    # 3. Skills standardization & canonicalization
    std_skills, skill_warns = standardize_skills_categorized(raw_dict.get("skills", {}))
    all_warnings.extend(skill_warns)

    # 4. Experience records standardization
    std_experience: list[StandardizedWorkExperience] = []
    exp_calc_inputs: list[dict] = []

    for idx, exp in enumerate(raw_dict.get("experience", [])):
        company = exp.get("company", "").strip()
        role = exp.get("role", "").strip()
        raw_start = exp.get("start_date")
        raw_end = exp.get("end_date")
        duration = exp.get("duration")
        loc = exp.get("location")

        # Parse start and end dates
        start_iso, start_prec, _, start_warns = parse_date_string(raw_start, f"experience[{idx}].start_date", reference_date=reference_date)
        end_iso, end_prec, is_curr_from_end, end_warns = parse_date_string(raw_end, f"experience[{idx}].end_date", reference_date=reference_date)

        all_warnings.extend(start_warns)
        all_warnings.extend(end_warns)

        # Check if duration mentions 'Present' or 'Current'
        from local_api.services.standardization.dates import CURRENT_PATTERNS
        is_current = is_curr_from_end
        if not raw_end and duration and CURRENT_PATTERNS.search(duration.split(' – ')[-1].strip()):
            is_current = True
        duration_text, duration_months, duration_status = calculated_duration(
            start_iso,end_iso,start_prec,end_prec,is_current,reference_date)
        if duration_status == 'calculated':
            all_warnings.append(StandardizationWarning(field=f'experience[{idx}].duration',
                warning_type='duration_calculated',severity='info',original_value=duration,
                normalized_value=duration_text,applied=True,
                basis=f'Month precision: inclusive calendar-month coverage. Day precision: completed calendar units. As of {reference_date.date().isoformat()}.',
                message='Derived duration, approximate calendar-month coverage; original date range retained.'))
        if duration_status != 'calculated':
            all_warnings.append(StandardizationWarning(field=f'experience[{idx}].duration',
                warning_type=duration_status,severity='warning',original_value=duration,
                basis='Requires unambiguous start/end months, or an explicit current indicator.',
                message='Duration was not calculated because dates are insufficient, invalid, or in the future.'))


        # Responsibilities
        clean_resp = [r.strip() for r in exp.get("responsibilities", []) if r and r.strip()]

        # Technologies
        clean_tech = [t.strip() for t in exp.get("technologies", []) if t and t.strip()]

        std_rec = StandardizedWorkExperience(
            company=company,
            role=role,
            start_date=start_iso or raw_start,
            end_date=end_iso or (None if is_current else raw_end),
            duration=duration_text,
            raw_duration=duration,
            duration_months=duration_months,
            duration_status=duration_status,
            duration_is_approximate=not (start_prec == "day" and (is_current or end_prec == "day")),
            duration_as_of=reference_date.date().isoformat() if is_current else None,
            location=loc.strip() if loc else None,
            responsibilities=clean_resp,
            technologies=clean_tech,
            raw_start_date=raw_start,
            raw_end_date=raw_end,
            start_date_iso=start_iso,
            end_date_iso=end_iso,
            start_date_precision=start_prec,
            end_date_precision=end_prec,
            is_current=is_current,
        )
        std_experience.append(std_rec)
        exp_calc_inputs.append({
            "raw_start_date": raw_start,
            "raw_end_date": raw_end,
            "start_date_iso": start_iso,
            "end_date_iso": end_iso,
            "start_date_precision": start_prec,
            "end_date_precision": end_prec,
            "is_current": is_current,
        })

    # 5. Non-overlapping experience calculation
    calc_years, overlap_detected, calc_warns = calculate_non_overlapping_experience(exp_calc_inputs, reference_date=reference_date)
    all_warnings.extend(calc_warns)

    # 6. Education standardization
    std_education: list[StandardizedEducation] = []
    for idx, edu in enumerate(raw_dict.get("education", [])):
        institution = edu.get("institution", "").strip()
        degree = edu.get("degree", "").strip()
        fos = edu.get("field_of_study")
        raw_start_yr = edu.get("start_year")
        raw_grad_yr = edu.get("graduation_year")
        grade = edu.get("grade_or_gpa")

        start_yr_iso, _, _, start_yr_warns = parse_date_string(raw_start_yr, f"education[{idx}].start_year", reference_date=reference_date)
        grad_yr_iso, _, _, grad_yr_warns = parse_date_string(raw_grad_yr, f"education[{idx}].graduation_year", reference_date=reference_date)
        all_warnings.extend(start_yr_warns)
        all_warnings.extend(grad_yr_warns)

        std_edu = StandardizedEducation(
            institution=institution,
            degree=degree,
            field_of_study=fos.strip() if fos else None,
            start_year=start_yr_iso or raw_start_yr,
            graduation_year=grad_yr_iso or raw_grad_yr,
            grade_or_gpa=grade.strip() if grade else None,
            raw_start_year=raw_start_yr,
            raw_graduation_year=raw_grad_yr,
            start_year_iso=start_yr_iso,
            graduation_year_iso=grad_yr_iso,
        )
        std_education.append(std_edu)

    # 7. Certifications standardization
    std_certifications: list[StandardizedCertification] = []
    for idx, cert in enumerate(raw_dict.get("certifications", [])):
        name = cert.get("name", "").strip()
        issuer = cert.get("issuer")
        raw_yr = cert.get("issue_year")

        yr_iso, _, _, yr_warns = parse_date_string(raw_yr, f"certifications[{idx}].issue_year", reference_date=reference_date)
        all_warnings.extend(yr_warns)

        std_cert = StandardizedCertification(
            name=name,
            issuer=issuer.strip() if issuer else None,
            issue_year=yr_iso or raw_yr,
            raw_issue_year=raw_yr,
            issue_year_iso=yr_iso,
        )
        std_certifications.append(std_cert)

    # 8. Projects standardization
    std_projects: list[StandardizedProject] = []
    for idx, proj in enumerate(raw_dict.get("projects", [])):
        p_name = proj.get("name", "").strip()
        p_desc = proj.get("description")
        p_role = proj.get("role")
        p_url = proj.get("url")
        p_tech = [t.strip() for t in proj.get("technologies", []) if t and t.strip()]

        clean_url = p_url.strip() if p_url else None
        if clean_url and not clean_url.startswith(("http://", "https://")) and "." in clean_url:
            clean_url = f"https://{clean_url}"

        std_proj = StandardizedProject(
            name=p_name,
            description=p_desc.strip() if p_desc else None,
            role=p_role.strip() if p_role else None,
            technologies=p_tech,
            url=clean_url,
            raw_url=p_url,
        )
        std_projects.append(std_proj)

    # 9. Languages
    clean_languages = [l.strip() for l in raw_dict.get("languages", []) if l and l.strip()]

    # Assemble StandardizedResumeSchema
    stated_total = raw_dict.get("total_experience_years")
    if stated_total is not None:
        try:
            stated_total = float(stated_total)
        except (ValueError, TypeError):
            stated_total = None

    std_resume = StandardizedResumeSchema(
        contact=std_contact,
        professional_title=clean_title,
        summary=clean_summary,
        total_experience_years=stated_total,
        calculated_experience_years=calc_years,
        calculated_experience_complete=bool(std_experience) and all(e.duration_status == "calculated" for e in std_experience),
        experience_overlap_detected=overlap_detected,
        skills=std_skills,
        experience=std_experience,
        education=std_education,
        certifications=std_certifications,
        projects=std_projects,
        languages=clean_languages,
    )

    # 10. Cross-field consistency validation
    status, cross_warns = validate_cross_field_consistency(std_resume)
    all_warnings.extend(cross_warns)

    # Suggestions are advisory; source names, locations and prose stay unchanged.
    from local_api.services.standardization.suggestions import spelling_suggestions
    all_warnings.extend(spelling_suggestions(raw_dict))
    status.issues_count = len(all_warnings)
    status.requires_human_review = status.requires_human_review or any(w.severity in {'warning','review_required'} for w in all_warnings)
    applied_types = {'duration_calculated','skill_canonicalization','phone_e164_normalized',
                     'email_whitespace_trimmed','url_scheme_canonicalized','name_whitespace_trimmed',
                     'bare_profile_label_rejected'}
    for warning in all_warnings:
        if warning.warning_type in applied_types:
            warning.applied = True
            warning.basis = warning.basis or 'Deterministic local formatting/alias rule; not external factual verification.'
    # Build Metadata
    type_counts = Counter(w.warning_type for w in all_warnings)
    metadata = StandardizationMetadata(
        schema_version="1.1.0",
        as_of_date=reference_date.date().isoformat(),
        field_verification={
            'source_values':'preserved; normalized values are derived and do not replace source citations',
            'locations':'not_externally_verified',
            'spelling_suggestions':'dictionary_candidates_only; not proof of correctness',
            'experience.duration':'derived_from_dates; inclusive calendar months; approximate',
        },
        applied_at=applied_at,
        total_normalizations=sum(w.applied for w in all_warnings),
        corrections_by_type=dict(type_counts),
        cross_field_notes=[w.message for w in all_warnings if w.warning_type in {
            "experience_duration_discrepancy", "experience_overlap_resolved", "invalid_date_order"
        }],
    )

    return std_resume, metadata, status, all_warnings

