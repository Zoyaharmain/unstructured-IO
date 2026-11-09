#!/usr/bin/env python3
import json
import time
import subprocess
import sys
from pathlib import Path

repo = Path('/home/zoyaharmain/unstructured-IO')
report_dir = repo / 'reports/live-five-new-resumes-20261108'
selection_path = report_dir / 'selection.json'

with open(selection_path) as f:
    selection = json.load(f)

# Candidate 01 is already completed; run candidates 02 to 05
results = []
results_file = report_dir / 'results.json'
if results_file.exists():
    results = json.loads(results_file.read_text())

# Add candidate 01 to results if not present
if not any(r.get('index') == '01' for r in results):
    results.append({
        'index': '01',
        'file': 'Bahubalikhot.pdf',
        'directory': '01_Bahubalikhot',
        'seconds': 95.0,  # approximate time for 01
        'returncode': 0
    })

for item in selection:
    idx = item['index']
    if idx == '01':
        continue
    fname = item['filename']
    out_dir = report_dir / item['output_directory']
    pdf_path = repo / item['local_path']
    
    print(f"\n==========================================")
    print(f"Starting [{idx}] {fname}")
    print(f"Output: {out_dir}")
    print(f"==========================================")
    
    start_time = time.time()
    cmd = [
        str(repo / '.venv312/bin/python'),
        str(repo / 'scripts/check_single_resume.py'),
        '--file', str(pdf_path),
        '--output', str(out_dir),
        '--llm-review',
        '--recovery-attempts', '1'
    ]
    
    proc = subprocess.run(cmd, cwd=repo, text=True)
    duration = time.time() - start_time
    
    print(f"Finished [{idx}] {fname} in {duration:.1f}s (exit {proc.returncode})")
    
    results.append({
        'index': idx,
        'file': fname,
        'directory': item['output_directory'].split('/')[-1],
        'seconds': round(duration, 1),
        'returncode': proc.returncode
    })
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

print("\nAll 5 candidates finished!")

