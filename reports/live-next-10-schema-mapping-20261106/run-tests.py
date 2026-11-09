#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import hashlib
import argparse
from pathlib import Path

ROOT = Path("/home/zoyaharmain/unstructured-IO")
os.chdir(ROOT)
OUT = ROOT / "reports/live-next-10-schema-mapping-20261106"
selection_path = OUT / "selection.json"
selection = json.loads(selection_path.read_text())

parser = argparse.ArgumentParser(description="Run live schema mapping accuracy test")
parser.add_argument("--start", type=int, default=1, help="Start index (1-based)")
parser.add_argument("--end", type=int, default=10, help="End index (1-based, inclusive)")
args = parser.parse_args()

print(f"=== Running Live DeepSeek Test for Resumes {args.start} to {args.end} ===")

env = dict(
    os.environ,
    PYTHONDONTWRITEBYTECODE="1",
    HF_HUB_OFFLINE="1",
    OMP_NUM_THREADS="1",
    OPENBLAS_NUM_THREADS="1"
)

results_file = OUT / "results.json"
if results_file.exists():
    try:
        rows = json.loads(results_file.read_text())
    except Exception:
        rows = []
else:
    rows = []

selected_items = selection["selected"]

for idx in range(args.start, args.end + 1):
    item = next((s for s in selected_items if s["index"] == idx), None)
    if not item:
        print(f"Index {idx} not found in selection.json!")
        continue
    
    file_path = Path(item["local_path"])
    assert file_path.exists(), f"Local PDF missing: {file_path}"
    assert hashlib.sha256(file_path.read_bytes()).hexdigest() == item["sha256"], f"SHA256 mismatch for {item['file']}"
    
    target_dir = OUT / item["folder_name"]
    log_file = OUT / f"{item['folder_name']}.log"
    
    start_time = time.monotonic()
    print(f"\n[{item['folder_name']}] START: {item['file']}", flush=True)
    
    cmd = [
        str(ROOT / ".venv312/bin/python"),
        "-B",
        "scripts/check_single_resume.py",
        "--file", str(file_path),
        "--output", str(target_dir),
        "--llm-review",
        "--recovery-attempts", "1"
    ]
    
    with log_file.open("w") as lf:
        proc = subprocess.run(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT)
    
    elapsed = round(time.monotonic() - start_time, 1)
    
    row = {
        "index": idx,
        "file": item["file"],
        "directory": item["folder_name"],
        "exit_code": proc.returncode,
        "seconds": elapsed
    }
    
    # Update or append
    existing_idx = next((i for i, r in enumerate(rows) if r["directory"] == item["folder_name"]), None)
    if existing_idx is not None:
        rows[existing_idx] = row
    else:
        rows.append(row)
    
    results_file.write_text(json.dumps(rows, indent=2))
    print(f"[{item['folder_name']}] FINISH: exit_code={proc.returncode}, elapsed={elapsed}s", flush=True)
    
    # Check log output for quick inspection
    log_lines = log_file.read_text().splitlines()
    print(f"[{item['folder_name']}] Log summary ({len(log_lines)} lines):")
    for line in log_lines[-10:]:
        print(f"  {line}")

print(f"\nBatch {args.start}-{args.end} complete.")

