#!/usr/bin/env python3
"""
Setup and validate ground_truth/schema_mapping/ dataset.
Copies 12 manually verified resume/JSON pairs, generates folder hierarchy and manifest.json.
"""
import os
import sys
import shutil
import json
import hashlib

REPO_ROOT = "/home/zoyaharmain/unstructured-IO"
RESUMES_DIR = os.path.join(REPO_ROOT, "resume ground truth", "original resumes")
JSON_DIR = os.path.join(REPO_ROOT, "resume ground truth")
TARGET_BASE_DIR = os.path.join(REPO_ROOT, "ground_truth", "schema_mapping")

PAIRS = [
    {
        "id": "shyam_kumar_donka",
        "original_file": "ShyamKumarDonka.pdf",
        "json_file": "ShyamKumarDonka.standardized.json",
    },
    {
        "id": "ashfaq_rahman",
        "original_file": "Ashfaq Rahman.pdf",
        "json_file": "Ashfaq Rahman.standardized.json",
    },
    {
        "id": "chaganti_leela_sankar",
        "original_file": "Chaganti Leela Sankar.docx",
        "json_file": "Chaganti Leela Sankar.standardized.json",
    },
    {
        "id": "sureshbabus",
        "original_file": "_SURESHBABUS.pdf",
        "json_file": "_SURESHBABUS.standardized.json",
    },
    {
        "id": "a_suribhotla",
        "original_file": "A Suribhotla.pdf",
        "json_file": "A Suribhotla.standardized.json",
    },
    {
        "id": "abhishek_tiwari",
        "original_file": "AbhishekTiwari.pdf",
        "json_file": "AbhishekTiwari.standardized.json",
    },
    {
        "id": "ashwin_s_s",
        "original_file": "Ashwin S S.docx",
        "json_file": "Ashwin S S.standardized.json",
    },
    {
        "id": "arnab_kumar_kar",
        "original_file": "Arnab_Kumar Kar.pdf",
        "json_file": "Arnab_Kumar Kar.standardized.json",
    },
    {
        "id": "yogendra_singh",
        "original_file": "Yogendra Singh.pdf",
        "json_file": "Yogendra Singh.standardized 1.json",
    },
    {
        "id": "deeksha_yadu",
        "original_file": "DeekshaYadu.pdf",
        "json_file": "DeekshaYadu.standardized (1).json",
    },
    {
        "id": "supriya_bhagat",
        "original_file": "Supriya Bhagat_1.docx",
        "json_file": "Supriya Bhagat.standardized.json",
    },
    {
        "id": "ravisankar_sundar",
        "original_file": "Ravisankar Sundar.docx",
        "json_file": "Ravisankar Sundar.standardized.json",
    },
]

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(TARGET_BASE_DIR, exist_ok=True)
    manifest_entries = []

    print(f"Creating ground truth pairs in: {TARGET_BASE_DIR}")

    for idx, p in enumerate(PAIRS, start=1):
        resume_id = p["id"]
        r_src = os.path.join(RESUMES_DIR, p["original_file"])
        j_src = os.path.join(JSON_DIR, p["json_file"])

        if not os.path.exists(r_src):
            raise FileNotFoundError(f"Original resume not found: {r_src}")
        if not os.path.exists(j_src):
            raise FileNotFoundError(f"Verified JSON not found: {j_src}")

        folder = os.path.join(TARGET_BASE_DIR, resume_id)
        os.makedirs(folder, exist_ok=True)

        ext = os.path.splitext(p["original_file"])[1].lower()
        if ext not in [".pdf", ".docx"]:
            raise ValueError(f"Unsupported file format: {ext}")

        r_dest_name = f"original{ext}"
        r_dest = os.path.join(folder, r_dest_name)
        j_dest = os.path.join(folder, "expected.json")

        shutil.copy2(r_src, r_dest)
        shutil.copy2(j_src, j_dest)

        r_sha = sha256_file(r_dest)
        j_sha = sha256_file(j_dest)

        with open(j_dest, "r", encoding="utf-8") as fp:
            j_data = json.load(fp)

        candidate_name = j_data.get("data", {}).get("contact", {}).get("full_name")
        source_in_json = j_data.get("source")

        entry = {
            "resume_id": resume_id,
            "folder": f"ground_truth/schema_mapping/{resume_id}",
            "original_filename": p["original_file"],
            "original_file": f"ground_truth/schema_mapping/{resume_id}/{r_dest_name}",
            "json_filename": p["json_file"],
            "expected_json": f"ground_truth/schema_mapping/{resume_id}/expected.json",
            "file_type": ext.lstrip("."),
            "candidate_name": candidate_name,
            "source_recorded_in_json": source_in_json,
            "approval_status": "approved",
            "verified_manually": True,
            "original_sha256": r_sha,
            "expected_sha256": j_sha,
        }
        manifest_entries.append(entry)
        print(f"[{idx:02d}/12] {resume_id}: {r_dest_name} + expected.json (Candidate: {candidate_name})")

    manifest = {
        "summary": {
            "description": "Ground truth schema mapping dataset with manually verified expected JSON outputs",
            "total_resumes": len(manifest_entries),
            "approved_count": sum(1 for m in manifest_entries if m["approval_status"] == "approved"),
            "file_types": {
                "pdf": sum(1 for m in manifest_entries if m["file_type"] == "pdf"),
                "docx": sum(1 for m in manifest_entries if m["file_type"] == "docx"),
            },
        },
        "resumes": manifest_entries,
    }

    manifest_path = os.path.join(TARGET_BASE_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2, ensure_ascii=False)

    print(f"\nManifest successfully written to: {manifest_path}")

if __name__ == "__main__":
    main()

