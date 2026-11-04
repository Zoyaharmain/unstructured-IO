#!/usr/bin/env python3
"""
Validation script for ground_truth/schema_mapping dataset.
Checks file presence, pair completeness, hashes, JSON validity, and manifest consistency.
"""
import os
import sys
import json
import hashlib

REPO_ROOT = "/home/zoyaharmain/unstructured-IO"
MAPPING_DIR = os.path.join(REPO_ROOT, "ground_truth", "schema_mapping")
MANIFEST_PATH = os.path.join(MAPPING_DIR, "manifest.json")
RESUMES_DIR = os.path.join(REPO_ROOT, "resume ground truth", "original resumes")
JSON_DIR = os.path.join(REPO_ROOT, "resume ground truth")

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def validate():
    print(f"Validating manifest: {MANIFEST_PATH}")
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

        print(f"\nChecking [{idx:02d}/12] {resume_id}...")

        # 1. Folder check
        if not os.path.isdir(folder):
            errors.append(f"[{resume_id}] Folder missing: {folder}")
            continue

        folder_files = sorted(os.listdir(folder))
        expected_folder_files = sorted([os.path.basename(orig_file), "expected.json"])
        if folder_files != expected_folder_files:
            errors.append(f"[{resume_id}] Unexpected folder contents: {folder_files} != {expected_folder_files}")

        # 2. Original file check
        if not os.path.isfile(orig_file):
            errors.append(f"[{resume_id}] Original file missing: {orig_file}")
        elif os.path.getsize(orig_file) == 0:
            errors.append(f"[{resume_id}] Original file is empty: {orig_file}")
        else:
            orig_sha = sha256_file(orig_file)
            if orig_sha != item["original_sha256"]:
                errors.append(f"[{resume_id}] Original file sha256 mismatch with manifest")
            # Verify against source file in original resumes
            src_orig = os.path.join(RESUMES_DIR, item["original_filename"])
            if not os.path.isfile(src_orig):
                errors.append(f"[{resume_id}] Source original file missing: {src_orig}")
            elif sha256_file(src_orig) != orig_sha:
                errors.append(f"[{resume_id}] Copied file sha256 does not match source file")

        # 3. Expected JSON check
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

            # Validate JSON parse and schema fields
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
                else:
                    print(f"  OK: Candidate = '{full_name}' | Format = {item['file_type'].upper()}")
            except Exception as e:
                errors.append(f"[{resume_id}] JSON parse error: {e}")

        # 4. Status check
        if item.get("approval_status") != "approved":
            errors.append(f"[{resume_id}] Approval status is not 'approved': {item.get('approval_status')}")

    if errors:
        print("\n--- VALIDATION ERRORS ---")
        for err in errors:
            print(f"ERROR: {err}")
        sys.exit(1)
    else:
        print("\n=======================================================")
        print("ALL 12 PAIRS VALIDATED SUCCESSFULLY WITH ZERO ERRORS!")
        print("=======================================================")

if __name__ == "__main__":
    validate()

