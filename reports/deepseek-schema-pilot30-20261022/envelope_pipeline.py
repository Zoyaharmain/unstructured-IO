"""Isolated envelope pipeline: decoupled core extraction and review metadata contracts.

Enforces:
1. Strict JSON parsing with zero automatic repair.
2. Distinct validation for CoreMappingPayload (data + evidence) and ReviewMetadataPayload.
3. Safe assembly guaranteeing target data and citations are immutable and can NEVER be overwritten by metadata.
4. Deterministic offline review metadata generation (Design A).
"""
import copy
import hashlib
import json
import re
from typing import Any, Tuple, Dict, List, Optional
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from local_api.vendor.handoff_schema.models import ResumeSchema


class AssemblySecurityError(ValueError):
    """Raised when metadata attempts to overwrite or mutate core extraction data."""
    pass


def parse_strict_json(content: str, finish_reason: str = "stop") -> Tuple[Optional[dict], Optional[dict]]:
    """Strictly parses model output without guessing, repair, or truncation.
    
    Verifies:
    - String input
    - Valid JSON object
    - No trailing non-whitespace characters
    - Returns (parsed, None) or (None, failure_dict)
    """
    if not isinstance(content, str):
        return None, {
            "error": "invalid_type",
            "message": f"Expected str, got {type(content).__name__}",
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False
        }
    
    trimmed = content.strip()
    if not trimmed:
        return None, {
            "error": "empty_content",
            "message": "Content is empty or whitespace only",
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False
        }

    try:
        decoder = json.JSONDecoder()
        parsed, index = decoder.raw_decode(content)
        # Check for extra trailing non-whitespace characters
        trailing = content[index:].strip()
        if trailing:
            return None, {
                "error": "extra_trailing_data",
                "message": f"Unexpected trailing characters after JSON object at index {index}: {trailing[:50]!r}",
                "finish_reason": finish_reason,
                "automatic_repair_attempted": False,
                "retry_performed": False
            }
    except json.JSONDecodeError as exc:
        return None, {
            "error": "invalid_json",
            "message": exc.msg,
            "line": exc.lineno,
            "column": exc.colno,
            "offset": exc.pos,
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False
        }

    if not isinstance(parsed, dict):
        return None, {
            "error": "not_a_json_object",
            "message": f"Expected JSON object, got {type(parsed).__name__}",
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False
        }

    return parsed, None


def validate_core_payload(payload: dict) -> Tuple[bool, List[str]]:
    """Validates that a payload contains the required core mapping keys ('data', 'evidence')."""
    errors = []
    if not isinstance(payload, dict):
        return False, ["payload_not_a_dict"]
    
    if "data" not in payload:
        errors.append("missing_required_key_data")
    elif not isinstance(payload["data"], dict):
        errors.append("data_not_a_dict")
    else:
        try:
            ResumeSchema.model_validate(payload["data"])
        except Exception as exc:
            errors.append(f"data_fails_schema_validation: {str(exc)[:100]}")

    if "evidence" not in payload:
        errors.append("missing_required_key_evidence")
    elif not isinstance(payload["evidence"], dict):
        errors.append("evidence_not_a_dict")

    return len(errors) == 0, errors


def deduplicate_metadata_items(items: list) -> list:
    """Deterministically deduplicates metadata items preserving insertion order."""
    if not isinstance(items, list):
        return []
    seen = set()
    deduped = []
    for item in items:
        if not isinstance(item, dict):
            continue
        # Key on deterministic tuple
        path = str(item.get("path", ""))
        kind = str(item.get("kind", ""))
        detail = str(item.get("detail", ""))
        source_ids = tuple(sorted(str(s) for s in item.get("source_ids", []))) if isinstance(item.get("source_ids"), list) else ()
        key = (path, kind, detail, source_ids)
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def validate_metadata_payload(payload: dict, core_data: Optional[dict] = None) -> Tuple[bool, List[str]]:
    """Validates review metadata payload.
    
    Ensures:
    - If 'data' or 'evidence' are present, they do not contradict core_data.
    - Metadata lists ('missing_information', 'uncertainties', 'upstream_observations') are well-formed.
    """
    errors = []
    if not isinstance(payload, dict):
        return False, ["metadata_payload_not_a_dict"]

    if core_data is not None:
        if "data" in payload and payload["data"] != core_data:
            errors.append("metadata_attempts_to_mutate_data")

    for key in ["missing_information", "uncertainties", "upstream_observations"]:
        if key in payload and not isinstance(payload[key], list):
            errors.append(f"{key}_must_be_a_list")

    return len(errors) == 0, errors


def assemble_envelope(core: dict, metadata: Optional[dict] = None) -> dict:
    """Safely assembles the complete 5-key envelope from core mapping and review metadata.
    
    Security & Integrity Guarantees:
    1. core['data'] is preserved exactly: assembled['data'] == core['data'].
    2. core['evidence'] is preserved exactly: assembled['evidence'] == core['evidence'].
    3. Metadata can NEVER mutate, overwrite, or delete core data.
    4. All 5 required envelope keys are guaranteed to be present:
       ('data', 'evidence', 'missing_information', 'uncertainties', 'upstream_observations').
    5. Duplicate metadata items are deduplicated deterministically.
    """
    valid_core, core_errors = validate_core_payload(core)
    if not valid_core:
        raise ValueError(f"Cannot assemble envelope: invalid core payload: {core_errors}")

    meta = metadata or {}
    if not isinstance(meta, dict):
        raise ValueError(f"Metadata must be a dict, got {type(meta).__name__}")

    # Integrity guard: check that metadata does not attempt to overwrite core data or evidence
    if "data" in meta and meta["data"] != core["data"]:
        raise AssemblySecurityError("Security Violation: Review metadata attempted to overwrite core data!")
    if "evidence" in meta and meta["evidence"] != core["evidence"]:
        raise AssemblySecurityError("Security Violation: Review metadata attempted to overwrite core evidence!")

    assembled = {
        "data": copy.deepcopy(core["data"]),
        "evidence": copy.deepcopy(core["evidence"]),
        "missing_information": deduplicate_metadata_items(meta.get("missing_information", [])),
        "uncertainties": deduplicate_metadata_items(meta.get("uncertainties", [])),
        "upstream_observations": deduplicate_metadata_items(meta.get("upstream_observations", []))
    }

    # Strict immutability post-condition check
    assert assembled["data"] == core["data"], "Post-condition failed: core data was mutated during envelope assembly!"
    assert assembled["evidence"] == core["evidence"], "Post-condition failed: core evidence was mutated during envelope assembly!"

    return assembled


def generate_deterministic_review_metadata(core_data: dict, evidence: dict, blocks: list, validation_result: Optional[dict] = None) -> dict:
    """Generates objective, deterministic review metadata offline without requiring an LLM call (Design A).
    
    1. missing_information: identifies unpopulated schema sections or unassigned blocks.
    2. uncertainties: identifies explicit tenure qualifiers ('+', 'around'), current role indicators ('Present'), or ambiguous dates.
    3. upstream_observations: identifies local category classification vs target schema placement.
    """
    missing_info = []
    uncertainties = []
    observations = []

    blocks_by_id = {b["source_id"]: b for b in blocks}

    # 1. Uncertainties from explicit text qualifiers in evidence
    for path, refs in evidence.items():
        if not isinstance(refs, list):
            continue
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            quote = ref.get("quote", "")
            sid = ref.get("source_id", "")
            block_text = blocks_by_id.get(sid, {}).get("text", "")

            # Approximate or plus qualifiers on experience
            if "total_experience" in path and ("+" in quote or "+" in block_text):
                uncertainties.append({
                    "path": path,
                    "kind": "approximate_value",
                    "detail": f"Source contains plus qualifier '+' in experience statement: {quote!r}",
                    "source_ids": [sid]
                })

            # Present date in current role
            if "end_date" in path and re.search(r'\bpresent\b', quote, re.I):
                uncertainties.append({
                    "path": path,
                    "kind": "date_qualifier",
                    "detail": "End date contains 'Present', indicating an ongoing position.",
                    "source_ids": [sid]
                })

    # 2. Missing information for empty high-level schema collections
    for collection in ["experience", "education", "certifications", "projects"]:
        val = core_data.get(collection)
        if val is None or (isinstance(val, list) and len(val) == 0):
            # Check if source blocks had material with that local category
            matching_blocks = [b["source_id"] for b in blocks if b.get("local_category") == collection]
            if matching_blocks:
                missing_info.append({
                    "path": f"/{collection}",
                    "reason": "upstream_defect",
                    "detail": f"Source blocks contained category {collection!r} but mapped collection is empty.",
                    "source_ids": matching_blocks[:5]
                })

    # 3. Upstream observations: category migrations
    local_cats_mapped = {}
    for path, refs in evidence.items():
        top_section = path.strip("/").split("/")[0]
        if isinstance(refs, list):
            for ref in refs:
                sid = ref.get("source_id") if isinstance(ref, dict) else None
                if sid and sid in blocks_by_id:
                    loc_cat = blocks_by_id[sid].get("local_category")
                    if loc_cat and loc_cat != top_section and loc_cat not in ("needs_review", "personal_information"):
                        local_cats_mapped.setdefault((loc_cat, top_section), []).append(sid)

    for (loc_cat, top_section), sids in local_cats_mapped.items():
        observations.append({
            "path": f"/{top_section}",
            "kind": "mislabeling",
            "detail": f"Source blocks locally classified as {loc_cat!r} were mapped into schema section {top_section!r}.",
            "source_ids": sids[:5]
        })

    return {
        "missing_information": deduplicate_metadata_items(missing_info),
        "uncertainties": deduplicate_metadata_items(uncertainties),
        "upstream_observations": deduplicate_metadata_items(observations)
    }

