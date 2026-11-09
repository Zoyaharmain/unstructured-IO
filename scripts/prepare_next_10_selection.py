#!/usr/bin/env python3
import json
import hashlib
import shutil
from pathlib import Path

FLAT_DIR = Path("/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/Old/resume/RESUMES_FLAT")
OUT_DIR = Path("reports/live-next-10-schema-mapping-20261106")
PDF_DIR = OUT_DIR / "selected-pdfs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

# 12 Ground Truth resumes
GT_DIR = Path("resume ground truth/original resumes")
gt_files = [f.name for f in GT_DIR.iterdir() if f.is_file()]

# 5 Nov 5 resumes
nov5_selection = json.loads(Path("reports/live-five-new-resumes-20261105/selection.json").read_text())
nov5_files = [s["file"] for s in nov5_selection["selected"]]

# Chosen 10 untested resumes
selected_names = [
    "ANURAGVASI.pdf",
    "Aarunis.pdf",
    "AbdulkadarBohari.pdf",
    "AbhinavLahariya.pdf",
    "AjayKumarTiwari.pdf",
    "AkankshaBhand.pdf",
    "Akash Kumar.pdf",
    "Akmal Yezdani.pdf",
    "Akshay Singla.pdf",
    "AkshayGupta.pdf"
]

selected_records = []
for idx, name in enumerate(selected_names, start=1):
    src_path = FLAT_DIR / name
    if not src_path.exists():
        raise FileNotFoundError(f"Missing {src_path}")
    
    assert name.lower() not in [x.lower() for x in gt_files], f"{name} is in GT!"
    assert name.lower() not in [x.lower() for x in nov5_files], f"{name} is in Nov 5!"
    
    content = src_path.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    size = len(content)
    
    dst_path = PDF_DIR / name
    shutil.copy2(src_path, dst_path)
    
    selected_records.append({
        "index": idx,
        "folder_name": f"{idx:02d}",
        "file": name,
        "source_path": str(src_path),
        "local_path": str(dst_path),
        "size_bytes": size,
        "sha256": sha256
    })
    print(f"[{idx:02d}] Verified & Copied: {name} ({size} bytes, sha256: {sha256[:12]}...)")

manifest = {
    "test_run": "live-next-10-schema-mapping-20261106",
    "selection_criteria": {
        "source_pool": str(FLAT_DIR),
        "total_selected": len(selected_records),
        "excluded_ground_truth_count": len(gt_files),
        "excluded_ground_truth": gt_files,
        "excluded_nov5_test_count": len(nov5_files),
        "excluded_nov5_test": nov5_files,
        "untested_verification": "Zero occurrences in previous live tests, pilots, and GT replays."
    },
    "selected": selected_records
}

manifest_path = OUT_DIR / "selection.json"
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"Wrote selection manifest to {manifest_path}")
