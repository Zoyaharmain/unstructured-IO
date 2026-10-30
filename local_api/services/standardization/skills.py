"""Skills and technology canonicalization using version-controlled alias dictionaries."""
from __future__ import annotations

from local_api.services.standardization.contracts import StandardizationWarning
from local_api.services.standardization.dictionaries import TECH_ALIASES, TECH_CATEGORIES
from local_api.vendor.handoff_schema.models import CategorizedSkills


def canonicalize_skill_name(
    raw_skill: str,
    field_context: str = "skills",
) -> tuple[str, StandardizationWarning | None]:
    """Standardize a skill name using the canonical technology dictionary.

    Returns:
        (canonical_name, warning_if_modified)
    """
    clean_skill = raw_skill.strip()
    if not clean_skill:
        return raw_skill, None

    folded = clean_skill.lower()
    if folded == 'alm':
        return clean_skill, StandardizationWarning(field=field_context,warning_type='ambiguous_skill_alias',
            severity='review_required',original_value=raw_skill,normalized_value=clean_skill,
            suggested_value=None,applied=False,
            basis='ALM is an ambiguous acronym; source does not establish a specific vendor/product.',
            message='Preserved ALM without expanding it to HP ALM. A specific product requires source evidence.')
    canonical = TECH_ALIASES.get(folded)

    if canonical and canonical != clean_skill:
        warning = StandardizationWarning(
            field=field_context,
            warning_type="skill_canonicalization",
            severity="info",
            original_value=raw_skill,
            normalized_value=canonical,
            message=f"Canonicalized skill '{raw_skill}' using the local alias rule '{canonical}'."
        )
        return canonical, warning

    return clean_skill, None


def standardize_skills_categorized(
    raw_skills: CategorizedSkills | dict,
) -> tuple[CategorizedSkills, list[StandardizationWarning]]:
    """Standardize, deduplicate, and preserve categorization of resume skills.

    Distinct technologies are NEVER merged; categories are preserved.
    """
    warnings: list[StandardizationWarning] = []

    if isinstance(raw_skills, CategorizedSkills):
        technical = list(raw_skills.technical_skills)
        tools = list(raw_skills.tools_and_platforms)
        domain = list(raw_skills.domain_and_functional)
        soft = list(raw_skills.soft_skills)
        all_s = list(raw_skills.all_skills)
    elif isinstance(raw_skills, dict):
        technical = list(raw_skills.get("technical_skills", []))
        tools = list(raw_skills.get("tools_and_platforms", []))
        domain = list(raw_skills.get("domain_and_functional", []))
        soft = list(raw_skills.get("soft_skills", []))
        all_s = list(raw_skills.get("all_skills", []))
    else:
        return CategorizedSkills(), warnings

    def process_list(skill_list: list[str], category_name: str) -> list[str]:
        seen_casefolded: set[str] = set()
        standardized_items: list[str] = []
        for s in skill_list:
            if not s or not s.strip():
                continue
            canonical_name, warning = canonicalize_skill_name(s, f"skills.{category_name}")
            if warning:
                warnings.append(warning)
            key = canonical_name.casefold()
            if key not in seen_casefolded:
                seen_casefolded.add(key)
                standardized_items.append(canonical_name)
        return standardized_items

    norm_technical = process_list(technical, "technical_skills")
    norm_tools = process_list(tools, "tools_and_platforms")
    norm_domain = process_list(domain, "domain_and_functional")
    norm_soft = process_list(soft, "soft_skills")

    # Combine for all_skills deduplicated in order of appearance
    combined_seen: set[str] = set()
    norm_all: list[str] = []
    for item in norm_technical + norm_tools + norm_domain + norm_soft + process_list(all_s, "all_skills"):
        key = item.casefold()
        if key not in combined_seen:
            combined_seen.add(key)
            norm_all.append(item)

    standardized = CategorizedSkills(
        technical_skills=norm_technical,
        tools_and_platforms=norm_tools,
        domain_and_functional=norm_domain,
        soft_skills=norm_soft,
        all_skills=norm_all,
    )

    return standardized, warnings

