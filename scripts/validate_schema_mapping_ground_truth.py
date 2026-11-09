#!/usr/bin/env python3
"""
Strengthened validation script for ground_truth/schema_mapping dataset.

1. Checks file presence, pair completeness, hashes, JSON validity, and manifest consistency.
2. Performs offline semantic replay validation comparing every expected employment and education record
   against actual mapped output:
   - Employer, role, dates, institution, degree, and critical field values.
   - Detects missing, extra, duplicate, merged, and split records.
   - Validates candidate names against contamination.
   - Verifies calculated experience against source-backed employment periods.
   - Strictly reports each resume as PASS, FAIL, or INCOMPLETE (missing expected records never receive PASS).
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = "/home/zoyaharmain/unstructured-IO"
MAPPING_DIR = os.path.join(REPO_ROOT, "ground_truth", "schema_mapping")
MANIFEST_PATH = os.path.join(MAPPING_DIR, "manifest.json")
RESUMES_DIR = os.path.join(REPO_ROOT, "resume ground truth", "original resumes")
JSON_DIR = os.path.join(REPO_ROOT, "resume ground truth")

# Ensure repository root is on sys.path
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.ground_truth_eval import (
    load_ground_truth_inputs, evaluate_resume_mapping,
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest_and_files():
    print(f"=== STEP 1: Validating Manifest and Files ({MANIFEST_PATH}) ===")
    if not os.path.isfile(MANIFEST_PATH):
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    resumes = manifest.get("resumes", [])
    summary = manifest.get("summary", {})

    assert len(resumes) == 12, f"Expected 12 resumes, found {len(resumes)}"
    assert summary.get("total_resumes") == 12, f"Summary total_resumes mismatch: {summary.get('total_resumes')}"
    assert summary.get("approved_count") == 12, f"Summary approved_count mismatch: {summary.get('approved_count')}"
    assert summary.get("file_types", {}).get("pdf") == 8, f"Expected 8 PDFs, found {summary.get('file_types', {}).get('pdf')}"
    assert summary.get("file_types", {}).get("docx") == 4, f"Expected 4 DOCX, found {summary.get('file_types', {}).get('docx')}"

    print(f"Total entries in manifest: {len(resumes)}")
    errors = []

    for idx, item in enumerate(resumes, start=1):
        resume_id = item["resume_id"]
        folder = os.path.join(REPO_ROOT, item["folder"])
        orig_file = os.path.join(REPO_ROOT, item["original_file"])
        exp_file = os.path.join(REPO_ROOT, item["expected_json"])

        if not os.path.isdir(folder):
            errors.append(f"[{resume_id}] Folder missing: {folder}")
            continue

        folder_files = sorted(os.listdir(folder))
        expected_folder_files = sorted([os.path.basename(orig_file), "expected.json"])
        if folder_files != expected_folder_files:
            errors.append(f"[{resume_id}] Unexpected folder contents: {folder_files} != {expected_folder_files}")

        if not os.path.isfile(orig_file):
            errors.append(f"[{resume_id}] Original file missing: {orig_file}")
        elif os.path.getsize(orig_file) == 0:
            errors.append(f"[{resume_id}] Original file is empty: {orig_file}")
        else:
            orig_sha = sha256_file(orig_file)
            if orig_sha != item["original_sha256"]:
                errors.append(f"[{resume_id}] Original file sha256 mismatch with manifest")
            src_orig = os.path.join(RESUMES_DIR, item["original_filename"])
            if not os.path.isfile(src_orig):
                errors.append(f"[{resume_id}] Source original file missing: {src_orig}")
            elif sha256_file(src_orig) != orig_sha:
                errors.append(f"[{resume_id}] Copied file sha256 does not match source file")

        if not os.path.isfile(exp_file):
            errors.append(f"[{resume_id}] Expected JSON missing: {exp_file}")
        elif os.path.getsize(exp_file) == 0:
            errors.append(f"[{resume_id}] Expected JSON is empty: {exp_file}")
        else:
            exp_sha = sha256_file(exp_file)
            if exp_sha != item["expected_sha256"]:
                errors.append(f"[{resume_id}] Expected JSON sha256 mismatch with manifest")
            src_json = os.path.join(JSON_DIR, item["json_filename"])
            if not os.path.isfile(src_json):
                errors.append(f"[{resume_id}] Source JSON file missing: {src_json}")
            elif sha256_file(src_json) != exp_sha:
                errors.append(f"[{resume_id}] Copied JSON sha256 does not match source JSON")

            try:
                with open(exp_file, "r", encoding="utf-8") as fp:
                    jdata = json.load(fp)
                required_keys = ["source", "data", "schema_version", "export_type"]
                for k in required_keys:
                    if k not in jdata:
                        errors.append(f"[{resume_id}] JSON missing key: {k}")
                data_obj = jdata.get("data", {})
                contact = data_obj.get("contact", {})
                full_name = contact.get("full_name")
                if not full_name:
                    errors.append(f"[{resume_id}] JSON contact full_name is missing or empty")
            except Exception as e:
                errors.append(f"[{resume_id}] JSON parse error: {e}")

        if item.get("approval_status") != "approved":
            errors.append(f"[{resume_id}] Approval status is not 'approved': {item.get('approval_status')}")

    if errors:
        print("\n--- MANIFEST VALIDATION ERRORS ---")
        for err in errors:
            print(f"ERROR: {err}")
        return False
    else:
        print("Manifest and files integrity check: 12/12 verified OK.\n")
        return True


def run_semantic_evaluation():
    print("=== STEP 2: Running Strengthened Semantic Ground-Truth Evaluation ===")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    resumes = manifest.get("resumes", [])
    eval_results = []

    print(f"{'Resume ID':<25} | {'Candidate Name':<28} | {'Jobs (Act/Exp)':<14} | {'Edu (Act/Exp)':<13} | {'Exp (Act/Exp)':<13} | {'Status'}")
    print("-" * 110)

    for item in resumes:
        rid = item["resume_id"]
        fname = item["original_filename"]
        exp_path = os.path.join(REPO_ROOT, item["expected_json"])

        with open(exp_path, "r", encoding="utf-8") as fp:
            exp_data = json.load(fp)["data"]

        elements, sections = load_ground_truth_inputs(rid, fname)
        mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=fname))
        std, meta, status, warns = standardize_resume_data(mapped.data.model_dump())

        audit = evaluate_resume_mapping(rid, std, exp_data)
        eval_results.append(audit)

        cand_str = audit['candidate_actual'][:26]
        jobs_str = f"{audit['jobs_actual']}/{audit['jobs_expected']}"
        edu_str = f"{audit['edu_actual']}/{audit['edu_expected']}"
        exp_act = f"{audit['exp_years_actual']}" if audit['exp_years_actual'] is not None else "None"
        exp_exp = f"{audit['exp_years_expected']}" if audit['exp_years_expected'] is not None else "None"
        exp_str = f"{exp_act}/{exp_exp}"
        print(f"{rid:<25} | {cand_str:<28} | {jobs_str:<14} | {edu_str:<13} | {exp_str:<13} | {audit['status']}")

    print("\n" + "=" * 110)
    print("DETAILED DEFECT & INCOMPLETENESS AUDIT:")
    print("=" * 110)

    status_counts = {"PASS": 0, "FAIL": 0, "INCOMPLETE": 0}
    for audit in eval_results:
        status_counts[audit["status"]] += 1
        if audit["status"] != "PASS":
            print(f"\n[RESUME] {audit['resume_id']} -> STATUS: {audit['status']}")
            print(f"  Candidate: Actual={audit['candidate_actual']!r} | Expected={audit['candidate_expected']!r} (Name Status: {audit['name_status']})")
            print(f"  Experience: Actual Jobs={audit['jobs_actual']} | Expected Jobs={audit['jobs_expected']}")
            if audit["missing_jobs"]:
                print(f"  Missing Expected Jobs ({len(audit['missing_jobs'])}):")
                for mj in audit["missing_jobs"]:
                    print(f"    - Index {mj['index']}: {mj['company']} | {mj['role']} ({mj['dates']})")
            if audit["split_jobs"]:
                print(f"  Split / Fragmented Jobs ({len(audit['split_jobs'])}):")
                for sj in audit["split_jobs"]:
                    print(f"    - Act Index {sj['act_idx']}: {sj['company']} | {sj['role']} (split from Exp Index {sj['split_from_exp_idx']})")
            if audit["extra_jobs"]:
                print(f"  Extra Jobs ({len(audit['extra_jobs'])}):")
                for ej in audit["extra_jobs"]:
                    print(f"    - Act Index {ej['act_idx']}: {ej['company']} | {ej['role']} ({ej['dates']})")
            if audit["missing_edu"]:
                print(f"  Missing Education ({len(audit['missing_edu'])}):")
                for me in audit["missing_edu"]:
                    print(f"    - Index {me['index']}: {me['institution']} | {me['degree']}")
            if audit["extra_edu"]:
                print(f"  Extra Education ({len(audit['extra_edu'])}):")
                for ee in audit["extra_edu"]:
                    print(f"    - Act Index {ee['act_idx']}: {ee['institution']} | {ee['degree']}")
            if audit["failures"]:
                print("  Failures & Discrepancies:")
                for f in audit["failures"]:
                    print(f"    - {f}")

    print("\n" + "=" * 110)
    print(f"SUMMARY: Total Resumes: {len(eval_results)} | PASS: {status_counts['PASS']} | FAIL: {status_counts['FAIL']} | INCOMPLETE: {status_counts['INCOMPLETE']}")
    print("=" * 110)

    return eval_results


def main():
    parser = argparse.ArgumentParser(description="Validate schema mapping ground truth.")
    parser.add_argument("--manifest-only", action="store_true", help="Only validate manifest and file integrity.")
    parser.add_argument("--semantic", action="store_true", help="Run semantic evaluation.")
    args = parser.parse_args()

    manifest_ok = validate_manifest_and_files()
    if not manifest_ok:
        sys.exit(1)

    if not args.manifest_only:
        eval_results = run_semantic_evaluation()


if __name__ == "__main__":
    main()
