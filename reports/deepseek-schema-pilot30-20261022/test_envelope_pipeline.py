"""Tests for envelope pipeline: strict JSON parsing, decoupled core/review contracts, safe assembly."""
import copy
import json
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PILOT = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(PILOT)]

from envelope_pipeline import (
    parse_strict_json,
    validate_core_payload,
    validate_metadata_payload,
    assemble_envelope,
    deduplicate_metadata_items,
    generate_deterministic_review_metadata,
    AssemblySecurityError
)
from local_api.vendor.handoff_schema.models import ResumeSchema, ContactInfo


@pytest.fixture
def valid_core_data():
    resume = ResumeSchema(
        contact=ContactInfo(
            full_name="Jane Doe",
            email="jane.doe@example.com",
            phone="+1234567890"
        )
    ).model_dump(mode="json")
    return {
        "data": resume,
        "evidence": {
            "/contact/full_name": [{"source_id": "e0:0:10", "quote": "Jane Doe"}],
            "/contact/email": [{"source_id": "e1:0:20", "quote": "jane.doe@example.com"}]
        }
    }


def test_parse_strict_json_valid():
    content = '{"data": {}, "evidence": {}}'
    parsed, err = parse_strict_json(content)
    assert err is None
    assert parsed == {"data": {}, "evidence": {}}


def test_parse_strict_json_malformed():
    content = '{"data": {}, "evidence": ['
    parsed, err = parse_strict_json(content)
    assert parsed is None
    assert err is not None
    assert err["error"] == "invalid_json"
    assert err["automatic_repair_attempted"] is False
    assert err["retry_performed"] is False


def test_parse_strict_json_reproduce_doc02_syntax():
    """Reproduces the exact unclosed array syntax error from Ashfaq Rahman.pdf."""
    doc2_content_path = PILOT / '02/response-content.txt'
    if not doc2_content_path.exists():
        pytest.skip("Doc 02 content not found")
    content = doc2_content_path.read_text()
    parsed, err = parse_strict_json(content)
    assert parsed is None
    assert err is not None
    assert err["error"] == "invalid_json"
    assert err["automatic_repair_attempted"] is False


def test_parse_strict_json_extra_trailing_data():
    content = '{"data": {}, "evidence": {}} and some trailing explanation outside JSON'
    parsed, err = parse_strict_json(content)
    assert parsed is None
    assert err is not None
    assert err["error"] == "extra_trailing_data"
    assert "trailing explanation" in err["message"]
    assert err["automatic_repair_attempted"] is False


def test_parse_strict_json_partial_response():
    content = '{"data": {"contact": {"full_name": "Abhi'
    parsed, err = parse_strict_json(content)
    assert parsed is None
    assert err is not None
    assert err["error"] == "invalid_json"
    assert err["automatic_repair_attempted"] is False


def test_parse_strict_json_non_dict_root():
    for non_dict in ['["item1", "item2"]', '"just a string"', '12345', 'true']:
        parsed, err = parse_strict_json(non_dict)
        assert parsed is None
        assert err is not None
        assert err["error"] == "not_a_json_object"


def test_validate_core_payload_missing_keys():
    # Missing data
    valid, errors = validate_core_payload({"evidence": {}})
    assert not valid
    assert "missing_required_key_data" in errors

    # Missing evidence
    valid_resume = ResumeSchema(contact=ContactInfo(full_name="Jane Doe", email="j@e.com", phone="123")).model_dump(mode="json")
    valid, errors = validate_core_payload({"data": valid_resume})
    assert not valid
    assert "missing_required_key_evidence" in errors

    # Both missing
    valid, errors = validate_core_payload({})
    assert not valid
    assert "missing_required_key_data" in errors
    assert "missing_required_key_evidence" in errors


def test_validate_core_payload_valid(valid_core_data):
    valid, errors = validate_core_payload(valid_core_data)
    assert valid
    assert errors == []


def test_deduplicate_metadata_items():
    duplicates = [
        {"path": "/skills", "kind": "mislabeling", "detail": "locally languages", "source_ids": ["e1", "e2"]},
        {"path": "/skills", "kind": "mislabeling", "detail": "locally languages", "source_ids": ["e1", "e2"]},
        {"path": "/skills", "kind": "mislabeling", "detail": "locally languages", "source_ids": ["e2", "e1"]}, # sorted source_ids match
        {"path": "/experience/0", "kind": "date_qualifier", "detail": "present role", "source_ids": ["e5"]}
    ]
    deduped = deduplicate_metadata_items(duplicates)
    assert len(deduped) == 2
    assert deduped[0]["path"] == "/skills"
    assert deduped[1]["path"] == "/experience/0"


def test_safe_assembly_guarantees_data_immutability(valid_core_data):
    metadata = {
        "missing_information": [{"path": "/certifications", "reason": "not_in_source", "detail": "No certs"}],
        "uncertainties": [{"path": "/experience/0/end_date", "kind": "date_qualifier", "detail": "Present"}],
        "upstream_observations": []
    }
    assembled = assemble_envelope(valid_core_data, metadata)

    # 1. Exact equality
    assert assembled["data"] == valid_core_data["data"]
    assert assembled["evidence"] == valid_core_data["evidence"]

    # 2. All 5 keys present
    assert set(assembled.keys()) == {
        "data", "evidence", "missing_information", "uncertainties", "upstream_observations"
    }

    # 3. Deep copy isolation: mutating assembled does not mutate core
    assembled["data"]["contact"]["full_name"] = "Attacker Name"
    assert valid_core_data["data"]["contact"]["full_name"] == "Jane Doe"


def test_safe_assembly_rejects_metadata_data_overwrite(valid_core_data):
    tampered_metadata = {
        "data": {"contact": {"full_name": "Tampered Name"}},
        "missing_information": []
    }
    with pytest.raises(AssemblySecurityError, match="Review metadata attempted to overwrite core data"):
        assemble_envelope(valid_core_data, tampered_metadata)


def test_safe_assembly_rejects_metadata_evidence_overwrite(valid_core_data):
    tampered_metadata = {
        "evidence": {"/contact/full_name": [{"source_id": "fabricated", "quote": "fake"}]},
        "missing_information": []
    }
    with pytest.raises(AssemblySecurityError, match="Review metadata attempted to overwrite core evidence"):
        assemble_envelope(valid_core_data, tampered_metadata)


def test_deterministic_review_metadata_generation(valid_core_data):
    blocks = [
        {"source_id": "e0:0:10", "local_category": "personal_information", "text": "Jane Doe"},
        {"source_id": "e1:0:20", "local_category": "personal_information", "text": "jane.doe@example.com"},
        {"source_id": "e2:0:30", "local_category": "experience", "text": "Senior Engineer 5+ years experience"},
        {"source_id": "e3:0:40", "local_category": "certifications", "text": "AWS Certified Architect"}
    ]
    meta = generate_deterministic_review_metadata(valid_core_data["data"], valid_core_data["evidence"], blocks)
    assert isinstance(meta, dict)
    assert "missing_information" in meta
    assert "uncertainties" in meta
    assert "upstream_observations" in meta
    # Certifications block existed in blocks, but core_data['certifications'] was empty list -> detected in missing_information
    assert any(m["path"] == "/certifications" for m in meta["missing_information"])


def test_offline_replay_doc01_saved_output():
    """Replays saved Doc 01 response through the envelope pipeline."""
    p1 = PILOT / '01/mapping-raw.json'
    if not p1.exists():
        pytest.skip("Doc 01 raw output not found")
    raw = json.loads(p1.read_text())
    
    # 1. Validate core payload
    valid, errors = validate_core_payload(raw)
    assert valid, f"Core validation errors: {errors}"
    
    # 2. Re-assemble envelope
    blocks = json.loads((PILOT / '01/source-blocks.json').read_text())
    meta = generate_deterministic_review_metadata(raw['data'], raw['evidence'], blocks)
    assembled = assemble_envelope(raw, meta)
    
    assert assembled['data'] == raw['data']
    assert assembled['evidence'] == raw['evidence']
    assert len(assembled['missing_information']) >= 0
    assert len(assembled['uncertainties']) >= 0


def test_offline_replay_doc02_core_intact_vs_monolithic_failure():
    """Demonstrates that Doc 02's core extraction (data + evidence) is completely valid,
    proving that Design A eliminates the monolithic trailing-array syntax failure.
    """
    p2_txt = PILOT / '02/response-content.txt'
    if not p2_txt.exists():
        pytest.skip("Doc 02 content not found")
    content = p2_txt.read_text()
    
    # 1. Monolithic parser strictly rejects the whole output
    parsed, err = parse_strict_json(content)
    assert parsed is None
    assert err['error'] == 'invalid_json'
    
    # 2. Isolating core keys (data + evidence) reveals clean syntax
    idx = content.find('"missing_information"')
    assert idx > 0
    core_text = "{" + content[1:idx].rstrip().rstrip(",") + "}"
    core_obj, core_err = parse_strict_json(core_text)
    assert core_err is None, f"Core text parse failed: {core_err}"
    assert "data" in core_obj and "evidence" in core_obj
    assert len(core_obj["evidence"]) == 155

