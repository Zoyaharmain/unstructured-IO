import os
import json
import hashlib
import subprocess
from pathlib import Path

repo = Path('/home/zoyaharmain/unstructured-IO')
flat_dir = Path('/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/Old/resume/RESUMES_FLAT')

# 1. Get all 1082 PDFs
all_pdfs = [f for f in os.listdir(flat_dir) if f.lower().endswith('.pdf')]
print(f"Total PDFs in RESUMES_FLAT: {len(all_pdfs)}")

# 2. Build exclusion set from all known test runs
exclusions = set()

# A. 12 Ground Truth resumes
gt_dir = repo / 'resume ground truth/original resumes'
if gt_dir.exists():
    for f in gt_dir.iterdir():
        exclusions.add(f.name.lower())
        exclusions.add(f.stem.lower())

# B. Nov 5 test resumes
nov5_dir = repo / 'reports/live-five-new-resumes-20261105'
if (nov5_dir / 'selection.json').exists():
    for s in json.loads((nov5_dir / 'selection.json').read_text()).get('selected', []):
        exclusions.add(s['file'].lower())
        exclusions.add(Path(s['file']).stem.lower())

# C. Nov 6 Next-10 test resumes
next10_dir = repo / 'reports/live-next-10-schema-mapping-20261106'
if (next10_dir / 'selection.json').exists():
    n10_data = json.loads((next10_dir / 'selection.json').read_text())
    items = n10_data.get('selected', n10_data) if isinstance(n10_data, dict) else n10_data
    for s in items:
        fn = s.get('filename') or s.get('file') if isinstance(s, dict) else str(s)
        if fn:
            exclusions.add(fn.lower())
            exclusions.add(Path(fn).stem.lower())

# D. Nov 8 five new resumes
nov8_dir = repo / 'reports/live-five-new-resumes-20261108'
if (nov8_dir / 'selection.json').exists():
    for s in json.loads((nov8_dir / 'selection.json').read_text()):
        exclusions.add(s['filename'].lower())
        exclusions.add(Path(s['filename']).stem.lower())

# E. Any file present anywhere under reports/ or ground_truth/
for p in (list((repo / 'reports').rglob('*.pdf')) +
          list((repo / 'ground_truth').rglob('*')) +
          list((repo / 'resume ground truth').rglob('*'))):
    if p.is_file():
        exclusions.add(p.name.lower())
        exclusions.add(p.stem.lower())

# F. Search git commit history and repo text for occurrences
print(f"Exclusions before deep text scan: {len(exclusions)}")

# Create a temporary file with all pdf filenames to check in one grep pass
pdf_list_path = repo / 'reports/all_candidate_names.txt'
with open(pdf_list_path, 'w') as f:
    for name in all_pdfs:
        f.write(name + '\n')

# Check which names appear in git grep or grep in reports/
found_in_reports = set()
res = subprocess.run(
    ["grep", "-rioF", "-f", str(pdf_list_path), "reports", "ground_truth", "resume ground truth", "tests"],
    cwd=repo, capture_output=True, text=True
)
for line in res.stdout.splitlines():
    if ':' in line:
        match = line.split(':', 1)[1].strip().lower()
        found_in_reports.add(match)

print(f"Found {len(found_in_reports)} PDF names referenced across reports/ground_truth/tests.")
exclusions.update(found_in_reports)

# Also check git log
git_log_res = subprocess.run(
    ["git", "log", "--name-only", "--pretty=format:"],
    cwd=repo, capture_output=True, text=True
)
for line in git_log_res.stdout.splitlines():
    name = line.strip().split('/')[-1].lower()
    if name.endswith('.pdf'):
        exclusions.add(name)

print(f"Total excluded tokens: {len(exclusions)}")

# Now filter candidates
eligible = []
for fname in sorted(all_pdfs):
    fname_lower = fname.lower()
    stem_lower = Path(fname).stem.lower()
    clean_stem = stem_lower.split('(')[0].split('[')[0].strip()
    
    if fname_lower in exclusions:
        continue
    if stem_lower in exclusions:
        continue
    if clean_stem in exclusions and len(clean_stem) >= 5:
        continue
    
    full_path = flat_dir / fname
    file_bytes = full_path.read_bytes()
    size = len(file_bytes)
    
    # Must be valid non-trivial PDF: 30KB to 600KB
    if size < 30000 or size > 600000:
        continue
        
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    
    # Check if sha256 appears anywhere in reports/
    sha_check = subprocess.run(
        ["grep", "-r", "-l", sha256, "reports", "ground_truth", "resume ground truth"],
        cwd=repo, capture_output=True, text=True
    )
    if sha_check.stdout.strip():
        continue
        
    eligible.append({
        'filename': fname,
        'path': str(full_path),
        'size': size,
        'sha256': sha256
    })

print(f"\n==========================================")
print(f"ELIGIBLE COMPLETELY UNTESTED CANDIDATES: {len(eligible)}")
print(f"==========================================")
for i, c in enumerate(eligible[:25], 1):
    print(f"{i:02d}. {c['filename']} ({c['size']} bytes, {c['sha256']})")

with open(repo / 'reports/eligible_untested_pool.json', 'w') as f:
    json.dump(eligible, f, indent=2)
