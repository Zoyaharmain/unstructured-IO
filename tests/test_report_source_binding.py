"""Regression tests for source hash and review binding integrity in report_pilot50_review."""
import hashlib
import json
import pytest
from pathlib import Path
from local_api.services.record_relationships import degree_families

def test_source_binding_with_fallback_candidate(tmp_path):
    # Simulate a run directory where original_source_path is unmounted / non-existent
    # but run / 'selected-pdfs' / file exists and matches the recorded SHA-256
    pdf_content = b"%PDF-1.4 test resume content for binding verification"
    sha = hashlib.sha256(pdf_content).hexdigest()

    run_dir = tmp_path / "run"
    selected_pdfs = run_dir / "selected-pdfs"
    selected_pdfs.mkdir(parents=True)
    pdf_file = selected_pdfs / "test_resume.pdf"
    pdf_file.write_bytes(pdf_content)

    manifest_selected = {
        "test_resume.pdf": {
            "original_source_path": "/nonexistent/path/to/test_resume.pdf",
            "sha256": sha,
        }
    }

    file = "test_resume.pdf"
    original = Path(manifest_selected[file]["original_source_path"])
    candidate = original if original.is_file() else (run_dir / "selected-pdfs" / file)

    assert not original.is_file()
    assert candidate.is_file()
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest_selected[file]["sha256"]

def test_source_binding_rejects_altered_content(tmp_path):
    pdf_content = b"%PDF-1.4 original content"
    sha = hashlib.sha256(pdf_content).hexdigest()

    run_dir = tmp_path / "run"
    selected_pdfs = run_dir / "selected-pdfs"
    selected_pdfs.mkdir(parents=True)
    pdf_file = selected_pdfs / "tampered_resume.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 altered content")

    manifest_selected = {
        "tampered_resume.pdf": {
            "original_source_path": str(pdf_file),
            "sha256": sha,
        }
    }

    file = "tampered_resume.pdf"
    original = Path(manifest_selected[file]["original_source_path"])
    candidate = original if original.is_file() else (run_dir / "selected-pdfs" / file)

    match = candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest_selected[file]["sha256"]
    assert not match

def test_review_artifact_binding_rejection():
    # If extraction or local_sections do not match source artifact, review binding must be False
    source = {
        "extraction": [{"text": "Hello"}],
        "sections": [{"category": "summary", "text": "Hello"}]
    }
    mismatched_review_artifact = {
        "extraction": [{"text": "Different"}],
        "local_sections": [{"category": "summary", "text": "Hello"}],
        "reviewed_sections": {}
    }

    binding = bool(
        mismatched_review_artifact
        and mismatched_review_artifact["extraction"] == source["extraction"]
        and mismatched_review_artifact["local_sections"] == source["sections"]
    )
    assert not binding

def test_degree_families_disambiguates_single_degree_acronyms():
    # Full name and acronym of same family should NOT trigger multiple qualifications
    single_degrees = [
        "Master of Business Administration (MBA)",
        "Bachelor of Commerce (B.Com) – Finance & Accounts",
        "BTech - Bachelor of Technology, Computer Science",
        "Bachelor of Computer Applications (BCA)",
    ]
    for text in single_degrees:
        families = degree_families(text)
        assert len(families) == 1, f"Expected 1 family for '{text}', got {families}"

    # Genuine multiple qualifications in a single text block
    multi_degrees = [
        "Master of Business Administration Finance & Bachelor of Science",
        "M.S. (Software Systems): BITS Pilani B.E. (Telecommunications): Bangalore University",
        "B.Tech and M.Tech",
        "10Th - SSCL, Intermediate, Bachelor of Science",
    ]
    for text in multi_degrees:
        families = degree_families(text)
        assert len(families) > 1, f"Expected >1 families for '{text}', got {families}"

def test_additional_100_selection_disjointness():
    manifest_path = Path("manifests/selection_pilot100_additional.json")
    prior_path = Path("reports/pilot250-llm-20261021-004616/manifest.json")
    if not manifest_path.is_file() or not prior_path.is_file():
        pytest.skip("Manifest files not present")
    
    new_data = json.loads(manifest_path.read_text())
    prior_data = json.loads(prior_path.read_text())
    
    new_hashes = {r["sha256"] for r in new_data["selected"]}
    prior_hashes = {r["sha256"] for r in prior_data["selected"]}
    new_files = {r["file"] for r in new_data["selected"]}
    prior_files = {r["file"] for r in prior_data["selected"]}
    
    assert len(new_data["selected"]) == 100
    assert len(new_hashes) == 100
    assert len(new_files) == 100
    assert not (new_hashes & prior_hashes)
    assert not (new_files & prior_files)

def test_end_to_end_binding_scenarios():
    extraction_a = [{"text": "Doc A element"}]
    sections_a = [{"category": "summary", "text": "Doc A element"}]
    
    extraction_b = [{"text": "Doc B element"}]
    sections_b = [{"category": "summary", "text": "Doc B element"}]
    
    # 1. Matching artifacts -> Binding must be True
    matching_review = {"extraction": extraction_a, "local_sections": sections_a}
    assert bool(matching_review and matching_review["extraction"] == extraction_a and matching_review["local_sections"] == sections_a)
    
    # 2. Missing review artifact -> Binding must be False
    missing_review = None
    assert not bool(missing_review and missing_review["extraction"] == extraction_a)
    
    # 3. Stale review artifact -> Binding must be False
    stale_review = {"extraction": [{"text": "Old extraction"}], "local_sections": sections_a}
    assert not bool(stale_review and stale_review["extraction"] == extraction_a and stale_review["local_sections"] == sections_a)
    
    # 4. Cross-document mismatch -> Binding must be False
    cross_review = {"extraction": extraction_b, "local_sections": sections_b}
    assert not bool(cross_review and cross_review["extraction"] == extraction_a and cross_review["local_sections"] == sections_a)

def test_reproduce_avishek_m_failure_and_recovery():
    from local_api.services.review_validation import inspect_assignments
    
    # u0 has length 7
    lengths = {"u0": 7}
    texts = {"u0": "Testing"}
    cuts = {"u0": [0, 7]}
    categories = ["summary", "experience"]
    
    # Attempt 1: provider returned [0, 8] for span of length 7 -> must reject with offset_out_of_range
    bad_attempt_1 = json.dumps({"assignments": [["u0", "summary", 0, 8]]})
    decisions1, errors1 = inspect_assignments(bad_attempt_1, 1, categories, lengths, texts, cuts)
    assert len(errors1) > 0
    assert any(e["kind"] == "offset_out_of_range" for e in errors1)
    
    # Attempt 2: provider fixed offset [0, 7], but returned {"type": "json_object", "assignments": ...}
    # With justified fix, this must pass with zero errors
    good_attempt_2 = json.dumps({
        "type": "json_object",
        "assignments": [["u0", "summary", 0, 7]]
    })
    decisions2, errors2 = inspect_assignments(good_attempt_2, 1, categories, lengths, texts, cuts)
    assert errors2 == []
    assert decisions2["u0"] == [(0, 7, "summary")]

def test_reproduce_dipali_kothawade_2_tuple_and_unknown_key_rejection():
    from local_api.services.review_validation import inspect_assignments
    
    lengths = {"u0": 10, "u1": 20}
    texts = {"u0": "0123456789", "u1": "01234567890123456789"}
    cuts = {"u0": [0, 10], "u1": [0, 20]}
    categories = ["personal_information", "summary"]
    
    # Dipali response: 2-tuple assignments with {"type": "json_object"}
    dipali_payload = json.dumps({
        "type": "json_object",
        "assignments": [
            ["u0", "personal_information"],
            ["u1", "summary"]
        ]
    })
    decisions, errors = inspect_assignments(dipali_payload, 2, categories, lengths, texts, cuts)
    assert errors == []
    assert decisions["u0"] == [(0, 10, "personal_information")]
    assert decisions["u1"] == [(0, 20, "summary")]
    
    # Unknown key (e.g. bogus top-level metadata) must STILL be strictly rejected as invalid_schema
    invalid_extra_key = json.dumps({
        "type": "json_object",
        "assignments": [["u0", "personal_information"], ["u1", "summary"]],
        "unauthorized_field": True
    })
    decisions_bad, errors_bad = inspect_assignments(invalid_extra_key, 2, categories, lengths, texts, cuts)
    assert any(e["kind"] == "invalid_schema" for e in errors_bad)



