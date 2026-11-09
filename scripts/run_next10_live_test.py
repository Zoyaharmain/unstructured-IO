#!/usr/bin/env python3
"""Runner for live DeepSeek schema mapping test on the 2026-11-09 cohort."""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo))

cohort_dir = repo / "reports/live-next-10-schema-mapping-20261109"
selection_path = cohort_dir / "selection.json"
results_file = cohort_dir / "results.json"


def run_candidate(item):
    idx = item["index"]
    fname = item["filename"]
    out_dir = repo / item["output_directory"]
    pdf_path = repo / item["local_path"]
    if out_dir.exists() and not any(out_dir.iterdir()):
        out_dir.rmdir()

    print(f"\n==========================================")
    print(f"Starting [{idx}] {fname}")
    print(f"Source PDF: {pdf_path}")
    print(f"Output Dir: {out_dir}")
    print(f"==========================================")

    start_time = time.time()
    cmd = [
        str(repo / ".venv312/bin/python"),
        str(repo / "scripts/check_single_resume.py"),
        "--file", str(pdf_path),
        "--output", str(out_dir),
        "--llm-review",
        "--recovery-attempts", "1"
    ]

    proc = subprocess.run(cmd, cwd=repo, text=True)
    duration = time.time() - start_time

    print(f"Finished [{idx}] {fname} in {duration:.1f}s (exit {proc.returncode})")

    # Record timing
    results = []
    if results_file.exists():
        try:
            results = json.loads(results_file.read_text())
        except Exception:
            results = []

    # Update or append
    results = [r for r in results if r.get("index") != idx]
    results.append({
        "index": idx,
        "file": fname,
        "directory": item["output_directory"].split("/")[-1],
        "seconds": round(duration, 1),
        "returncode": proc.returncode
    })
    results.sort(key=lambda r: r["index"])
    results_file.write_text(json.dumps(results, indent=2))
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Live DeepSeek 10-Resume Test Runner")
    parser.add_argument("--indices", nargs="+", help="Specific indices to run, e.g. 01 02")
    parser.add_argument("--stage", type=int, choices=[1, 2], help="Stage 1 (first 2) or Stage 2 (remaining 8)")
    args = parser.parse_args()

    selection = json.loads(selection_path.read_text())

    if args.stage == 1:
        target_items = selection[:2]
    elif args.stage == 2:
        target_items = selection[2:]
    elif args.indices:
        target_items = [s for s in selection if s["index"] in args.indices]
    else:
        target_items = selection

    for item in target_items:
        ret = run_candidate(item)
        if ret != 0:
            print(f"ERROR: Process returned non-zero code {ret} for {item['filename']}")


if __name__ == "__main__":
    main()
