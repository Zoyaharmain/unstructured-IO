"""Safe contact information normalization and validation."""
from __future__ import annotations

import re
from local_api.services.standardization.contracts import (
    StandardizedContactInfo,
    StandardizationWarning,
)
from local_api.vendor.handoff_schema.models import ContactInfo

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")
BARE_PROFILE_LABELS = {"linkedin", "linked in", "github", "git hub", "portfolio", "website", "profile"}


def normalize_phone(
    raw_phone: str | None,
) -> tuple[str | None, str | None, list[StandardizationWarning]]:
    """Normalize phone number to E.164 if country code is present.

    Returns:
        (canonical_phone, phone_e164, warnings)
    """
    warnings: list[StandardizationWarning] = []
    if not raw_phone:
        return None, None, warnings

    cleaned = raw_phone.strip()
    if not cleaned:
        return None, None, warnings

    # Check for explicit '+' prefix
    if cleaned.startswith("+"):
        # Strip internal spaces, hyphens, periods, parentheses
        digits_only = re.sub(r"[^\d]", "", cleaned[1:])
        if 7 <= len(digits_only) <= 15:
            e164 = f"+{digits_only}"
            if e164 != cleaned:
                warnings.append(
                    StandardizationWarning(
                        field="contact.phone",
                        warning_type="phone_e164_normalized",
                        severity="info",
                        original_value=raw_phone,
                        normalized_value=e164,
                        message=f"Normalized phone number '{raw_phone}' to E.164 format '{e164}'."
                    )
                )
            return e164, e164, warnings

    # Check for '00' international prefix
    if cleaned.startswith("00"):
        digits_only = re.sub(r"[^\d]", "", cleaned[2:])
        if 7 <= len(digits_only) <= 15:
            e164 = f"+{digits_only}"
            warnings.append(
                StandardizationWarning(
                    field="contact.phone",
                    warning_type="phone_e164_normalized",
                    severity="info",
                    original_value=raw_phone,
                    normalized_value=e164,
                    message=f"Converted '00' prefix in '{raw_phone}' to E.164 '{e164}'."
                )
            )
            return e164, e164, warnings

    # Domestic number without explicit country code - DO NOT INVENT country code
    digits_only = re.sub(r"[^\d]", "", cleaned)
    if digits_only:
        warnings.append(
            StandardizationWarning(
                field="contact.phone",
                warning_type="phone_lacks_country_code",
                severity="info",
                original_value=raw_phone,
                normalized_value=cleaned,
                message=f"Phone number '{raw_phone}' lacks an explicit international country code; preserved without guessing."
            )
        )
    return cleaned, None, warnings


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


def normalize_url(
    raw_url: str | None,
    field_name: str,
) -> tuple[str | None, list[StandardizationWarning]]:
    """Clean and canonicalize profile URLs, rejecting bare text labels."""
    warnings: list[StandardizationWarning] = []
    if not raw_url:
        return None, warnings

    cleaned = raw_url.strip()
    if not cleaned:
        return None, warnings

    # Detect bare labels like "LinkedIn", "GitHub"
    if cleaned.lower() in BARE_PROFILE_LABELS:
        warnings.append(
            StandardizationWarning(
                field=f"contact.{field_name}",
                warning_type="bare_profile_label_rejected",
                severity="warning",
                original_value=raw_url,
                normalized_value=None,
                message=f"Discarded bare label '{raw_url}' for {field_name} as it does not contain a profile handle or URL."
            )
        )
        return None, warnings

    # Add https:// scheme if missing
    if not re.match(r"^https?:\/\/", cleaned, re.I):
        if "." in cleaned and "/" in cleaned:
            canonical_url = f"https://{cleaned}"
            warnings.append(
                StandardizationWarning(
                    field=f"contact.{field_name}",
                    warning_type="url_scheme_canonicalized",
                    severity="info",
                    original_value=raw_url,
                    normalized_value=canonical_url,
                    message=f"Added https:// scheme to {field_name} '{raw_url}'."
                )
            )
            return canonical_url, warnings

    return cleaned, warnings


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
    elif isinstance(raw_contact, dict):
        name = raw_contact.get("full_name", "")
        email = raw_contact.get("email", "")
        phone = raw_contact.get("phone", "")
        location = raw_contact.get("location")
        linkedin = raw_contact.get("linkedin_url")
        github = raw_contact.get("github_url")
        portfolio = raw_contact.get("portfolio_url")
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
        location=clean_location,
        linkedin_url=norm_linkedin,
        github_url=norm_github,
        portfolio_url=norm_portfolio,
    )

    return standardized, warnings

