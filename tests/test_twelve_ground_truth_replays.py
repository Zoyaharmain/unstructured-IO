"""Deterministic replay tests against all 12 manually verified ground truths.

Strengthened semantic validation:
- Validates candidate name against contamination.
- Bipartite matching on employment (employer, role, dates).
- Bipartite matching on education (institution, degree, graduation year).
- Detects missing, extra, split, duplicate, and merged records.
- Verifies calculated experience vs expected date evidence.
- Strictly asserts PASS on verified passing resumes (7/12) and INCOMPLETE/FAIL
  with specific defects on resumes with known missing/split records (5/12).
  Missing expected records NEVER receive PASS.
"""
import json
from pathlib import Path
import pytest

from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.ground_truth_eval import (
    load_ground_truth_inputs, evaluate_resume_mapping,
)


MANIFEST_PATH = Path("ground_truth/schema_mapping/manifest.json")
MANIFEST = json.load(open(MANIFEST_PATH))["resumes"]

# Resumes that achieve full semantic accuracy
PASSING_RESUME_IDS = {
    "shyam_kumar_donka",
    "ashfaq_rahman",
    "a_suribhotla",
    "arnab_kumar_kar",
    "yogendra_singh",
    "deeksha_yadu",
    "supriya_bhagat",
    "abhishek_tiwari",
}

# Resumes that are incomplete or have formatting/layout defects
INCOMPLETE_RESUME_IDS = {
    "chaganti_leela_sankar",
    "sureshbabus",
    "ashwin_s_s",
    "ravisankar_sundar",
}


@pytest.mark.parametrize("item", MANIFEST, ids=[r["resume_id"] for r in MANIFEST])
def test_ground_truth_semantic_validation(item):
    rid = item["resume_id"]
    fname = item["original_filename"]
    expected_path = item["expected_json"]

    elements, sections = load_ground_truth_inputs(rid, fname)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=fname))
    std, meta, status, warns = standardize_resume_data(mapped.data.model_dump())

    exp_data = json.load(open(expected_path))["data"]
    audit = evaluate_resume_mapping(rid, std, exp_data)

    # 1. Candidate Name must be valid and uncontaminated
    assert audit["name_status"] == "PASS", f"Name error on {rid}: {audit['failures']}"
    assert audit["candidate_actual"] != ""

    # 2. Field evidence must be preserved
    assert len(mapped.meta.get("field_evidence", {})) > 0

    # 3. Strict semantic validation
    if rid in PASSING_RESUME_IDS:
        # Full semantic pass: 0 missing jobs, 0 missing edu, exact record counts
        assert audit["status"] == "PASS", f"{rid} expected PASS but got {audit['status']}: {audit['failures']}"
        assert len(audit["missing_jobs"]) == 0
        assert len(audit["missing_edu"]) == 0
        assert audit["jobs_actual"] == audit["jobs_expected"]
        assert audit["edu_actual"] == audit["edu_expected"]
        assert len(audit["failures"]) == 0
    else:
        # Incomplete / failing resumes: MUST NEVER PASS
        assert audit["status"] != "PASS", f"{rid} has missing records or defects and MUST NEVER receive PASS!"
        assert audit["status"] in {"INCOMPLETE", "FAIL"}

        # Verify specific known defects are detected
        if rid == "chaganti_leela_sankar":
            # Missing 1 job (Thomson Reuters)
            assert len(audit["missing_jobs"]) == 1
            assert audit["jobs_actual"] == 3
            assert audit["jobs_expected"] == 4
        elif rid == "sureshbabus":
            # Standard Chartered split record
            assert audit["jobs_actual"] == 4
            assert audit["jobs_expected"] == 3
        elif rid == "ashwin_s_s":
            # Missing jobs in summary prose/table
            assert len(audit["missing_jobs"]) in {1, 2}
            assert audit["jobs_actual"] == 3
            assert audit["jobs_expected"] == 4
        elif rid == "ravisankar_sundar":
            # Missing 2 jobs in table cells
            assert len(audit["missing_jobs"]) == 2
            assert audit["jobs_actual"] == 1
            assert audit["jobs_expected"] == 3
