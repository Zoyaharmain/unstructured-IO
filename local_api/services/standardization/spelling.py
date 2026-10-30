"""Conservative spelling and OCR correction using explicit dictionaries and source validation."""
from __future__ import annotations

import re
from local_api.services.standardization.contracts import StandardizationWarning
from local_api.services.standardization.dictionaries import OCR_AND_SPELLING_CORRECTIONS


def correct_ocr_or_spelling(
    text: str | None,
    field_context: str = "text",
    is_protected: bool = False,
) -> tuple[str | None, list[StandardizationWarning]]:
    """Conservatively correct whitelisted OCR errors and typos.

    Protected fields (personal names, companies, URLs, emails, unknown acronyms) are
    strictly preserved and never modified.
    """
    warnings: list[StandardizationWarning] = []
    if not text:
        return text, warnings

    if is_protected:
        return text, warnings

    cleaned = text.strip()
    if not cleaned:
        return text, warnings

    # Exact string match against dictionary
    folded = cleaned.lower()
    if folded in OCR_AND_SPELLING_CORRECTIONS:
        corrected = OCR_AND_SPELLING_CORRECTIONS[folded]
        if corrected != cleaned:
            warnings.append(
                StandardizationWarning(
                    field=field_context,
                    warning_type="ocr_spelling_correction",
                    severity="info",
                    original_value=text,
                    normalized_value=corrected,
                    message=f"Corrected OCR/spelling '{cleaned}' to '{corrected}' using verified dictionary."
                )
            )
            return corrected, warnings

    # Word-boundary replacements for known typographical artifacts in multi-word sentences
    modified_text = cleaned
    for mistake, fix in OCR_AND_SPELLING_CORRECTIONS.items():
        if " " in mistake or len(mistake) >= 5:
            pattern = re.compile(rf"\b{re.escape(mistake)}\b", re.I)
            if pattern.search(modified_text):
                modified_text = pattern.sub(fix, modified_text)

    if modified_text != cleaned:
        warnings.append(
            StandardizationWarning(
                field=field_context,
                warning_type="ocr_spelling_correction",
                severity="info",
                original_value=cleaned,
                normalized_value=modified_text,
                message=f"Applied conservative spelling/OCR correction to '{field_context}'."
            )
        )
        return modified_text, warnings

    return cleaned, warnings

