"""Safe contact information normalization and validation."""
from __future__ import annotations

import re
from urllib.parse import urlsplit
from local_api.services.standardization.contracts import (
    StandardizedContactInfo,
    StandardizationWarning,
)
from local_api.vendor.handoff_schema.models import ContactInfo

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")
BARE_PROFILE_LABELS = {"linkedin", "linked in", "github", "git hub", "portfolio", "website", "profile"}


PHONE_EXTENSION = re.compile(r"\s*(?:ext(?:ension)?\.?|x|#)\s*[:.]?\s*(\d+)\s*$", re.I)
PREFERENCE = re.compile(r"\b(?:open to|preferred?|willing to relocate|relocation|seeking|target role)\b", re.I)


def split_phone_extension(value):
    match = PHONE_EXTENSION.search(value)
    return (value[:match.start()].strip(), match[1]) if match else (value, None)


def normalize_phone(raw_phone):
    if not raw_phone:
        return None, None, []
    cleaned = raw_phone.strip()
    base, extension = split_phone_extension(cleaned)
    warnings = []
    international = base.startswith(('+', '00'))
    digits = re.sub(r"[ ()\-.]", "", base[1:] if base.startswith('+') else base[2:] if base.startswith('00') else base)
    if international and re.fullmatch(r'[1-9][0-9]{6,14}', digits):
        normalized = '+' + digits
        if normalized != raw_phone or extension:
            warnings.append(StandardizationWarning(field='contact.phone', warning_type='phone_e164_normalized',
                original_value=raw_phone, normalized_value=normalized, applied=True,
                message='Formatted explicit international number; extension stored separately. Number ownership and dialability are not verified.'))
        return normalized, normalized, warnings
    if not re.fullmatch(r'[0-9]{7,15}', digits) or international:
        warnings.append(StandardizationWarning(field='contact.phone', warning_type='invalid_phone_syntax',
            severity='review_required', original_value=raw_phone, normalized_value=base,
            message='Phone syntax is invalid or ambiguous; no country code or digits inferred.'))
    else:
        warnings.append(StandardizationWarning(field='contact.phone', warning_type='phone_lacks_country_code',
            original_value=raw_phone, normalized_value=base,
            message='Country code is not explicit; domestic format retained.'))
    return base or None, None, warnings


def normalize_email(
    raw_email: str | None,
) -> tuple[str | None, list[StandardizationWarning]]:
    """Trim and validate email address."""
    warnings: list[StandardizationWarning] = []
    if not raw_email:
        return None, warnings

    cleaned = raw_email.strip()
    if not cleaned:
        return None, warnings

    # Check for internal spaces or invalid characters
    if not EMAIL_REGEX.match(cleaned):
        warnings.append(
            StandardizationWarning(
                field="contact.email",
                warning_type="invalid_email_syntax",
                severity="warning",
                original_value=raw_email,
                normalized_value=cleaned,
                message=f"Email address '{cleaned}' does not match standard RFC syntax; left un-altered."
            )
        )
        return cleaned, warnings

    if cleaned != raw_email:
        warnings.append(
            StandardizationWarning(
                field="contact.email",
                warning_type="email_whitespace_trimmed",
                severity="info",
                original_value=raw_email,
                normalized_value=cleaned,
                message=f"Trimmed whitespace from email '{raw_email}'."
            )
        )

    return cleaned, warnings


def normalize_url(raw_url, field_name):
    if not raw_url:
        return None, []
    cleaned = raw_url.strip()
    path = field_name if '.' in field_name or '[' in field_name else 'contact.' + field_name
    if cleaned.lower() in BARE_PROFILE_LABELS:
        return None, [StandardizationWarning(field=path, warning_type='bare_profile_label_rejected',
            severity='warning', original_value=raw_url, normalized_value=None, applied=True,
            message='Bare profile label is not a URL; original retained in source evidence.')]
    from local_api.services.profile_url_recovery import repair_url_whitespace
    repaired = repair_url_whitespace(cleaned)
    candidate = repaired
    explicit_scheme = bool(re.match(r'^[a-z][a-z0-9+.-]*:', repaired, re.I))
    if not explicit_scheme:
        candidate = 'https:' + repaired if repaired.startswith('//') else 'https://' + repaired
    try:
        parts = urlsplit(candidate)
        valid = (parts.scheme.lower() in {'http', 'https'} and parts.hostname
                 and '.' in parts.hostname and not parts.username and not parts.password
                 and not re.search(r'\s|[<>\\]', candidate))
        parts.port  # Reject invalid port syntax.
    except ValueError:
        valid = False
    if not valid:
        return None, [StandardizationWarning(field=path, warning_type='invalid_url',
            severity='review_required', original_value=raw_url, normalized_value=None,
            message='URL could not be validated as an HTTP(S) destination; retained in source evidence without inventing a link.')]
    warnings = []
    if repaired != cleaned:
        warnings.append(StandardizationWarning(field=path,warning_type='url_whitespace_repaired',
            original_value=raw_url,normalized_value=candidate,applied=True,
            basis='Only whitespace at URI separators, wrapped path continuations or a split TLD before a slash was removed; no URL letters or path were inferred.',
            message='System repaired source URL whitespace/wrapping; original preserved. Destination existence and ownership are not verified.'))
    if candidate != raw_url and repaired == cleaned:
        warnings.append(StandardizationWarning(field=path, warning_type='url_scheme_canonicalized',
            original_value=raw_url, normalized_value=candidate, applied=True,
            message='Trimmed URL or added HTTPS to an explicit hostname; path/query/fragment preserved.'))
    return candidate, warnings


def standardize_contact(
    raw_contact: ContactInfo | dict,
) -> tuple[StandardizedContactInfo, list[StandardizationWarning]]:
    """Standardize contact information safely."""
    warnings: list[StandardizationWarning] = []

    if isinstance(raw_contact, ContactInfo):
        name = raw_contact.full_name
        email = raw_contact.email
        phone = raw_contact.phone
        location = raw_contact.location
        linkedin = raw_contact.linkedin_url
        github = raw_contact.github_url
        portfolio = raw_contact.portfolio_url
        preferences = raw_contact.work_preferences
        target_role = raw_contact.target_role
    elif isinstance(raw_contact, dict):
        name = raw_contact.get("full_name", "")
        email = raw_contact.get("email", "")
        phone = raw_contact.get("phone", "")
        location = raw_contact.get("location")
        linkedin = raw_contact.get("linkedin_url")
        github = raw_contact.get("github_url")
        portfolio = raw_contact.get("portfolio_url")
        preferences = raw_contact.get("work_preferences")
        target_role = raw_contact.get("target_role")
    else:
        return StandardizedContactInfo(full_name="", email="", phone=""), warnings

    # Name: trim whitespace, never spell-check
    clean_name = name.strip() if name else ""
    if clean_name != name:
        warnings.append(
            StandardizationWarning(
                field="contact.full_name",
                warning_type="name_whitespace_trimmed",
                severity="info",
                original_value=name,
                normalized_value=clean_name,
                message="Trimmed extraneous whitespace from candidate name."
            )
        )

    norm_phone, phone_e164, phone_warns = normalize_phone(phone)
    warnings.extend(phone_warns)

    norm_email, email_warns = normalize_email(email)
    warnings.extend(email_warns)

    clean_location = location.strip() if location else None
    if clean_location and PREFERENCE.search(clean_location):
        if not preferences:
            preferences = clean_location
        warnings.append(StandardizationWarning(field='contact.location', warning_type='work_preference_not_residence',
            severity='review_required', original_value=location, normalized_value=None, applied=True,
            message='Preference wording is not evidence of residence; retained as work preferences or original evidence.'))
        clean_location = None

    norm_linkedin, li_warns = normalize_url(linkedin, "linkedin_url")
    warnings.extend(li_warns)

    norm_github, gh_warns = normalize_url(github, "github_url")
    warnings.extend(gh_warns)

    norm_portfolio, pf_warns = normalize_url(portfolio, "portfolio_url")
    warnings.extend(pf_warns)

    standardized = StandardizedContactInfo(
        full_name=clean_name,
        email=norm_email or "",
        phone=norm_phone or "",
        raw_email=email,
        raw_phone=phone,
        phone_e164=phone_e164,
        phone_extension=split_phone_extension(phone.strip())[1] if phone else None,
        work_preferences=preferences.strip() if preferences else None,
        target_role=target_role.strip() if target_role else None,
        location=clean_location,
        linkedin_url=norm_linkedin,
        github_url=norm_github,
        portfolio_url=norm_portfolio,
    )

    return standardized, warnings

