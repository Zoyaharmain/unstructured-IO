import os
import json
import hashlib
from pathlib import Path

repo = Path('.')
resumes_flat = Path('/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/Old/resume/RESUMES_FLAT')

search_dirs = [
    'reports/live-deepseek-test-5-resumes-20261105',
    'reports/live-five-new-resumes-20261105',
    'reports/live-next-10-schema-mapping-20261106',
    'reports/live-five-new-resumes-20261108',
    'reports/deepseek-schema-full350-20261022',
    'reports/deepseek-schema-pilot10-20261022',
    'reports/deepseek-schema-pilot30-20261022',
    'reports/deepseek-schema-pilot5-20261022',
    'reports/deepseek-schema-pilot5-v2-20261022',
    'reports/pilot100-additional-llm-20261021-025143',
    'reports/pilot100-fixed-llm-20261021-041000',
    'reports/pilot250-llm-20261021-004616',
    'reports/pilot-full-review-20261020-075828',
    'reports/batch-next-20261021-064222',
    'reports/structural-grouping-fix-20261021-051500',
    'reports/resume-batch-10-llm-20261027',
    'reports/single-jayesh-feedback-live-20261022',
    'reports/llm-schema-five-preflight-20261023-224040',
    'reports/hierarchical-deepseek-five-20261023-225341',
    'reports/frontend-deepseek-review-20261026',
    'ground_truth',
    'resume ground truth',
    'tests/fixtures'
]

seen_tokens = set()
seen_hashes = set()

for sd in search_dirs:
    p = repo / sd
    if not p.exists():
        continue
    for f in p.glob('**/*'):
        if f.is_file():
            seen_tokens.add(f.name.lower())
            seen_tokens.add(f.stem.lower())
            clean = f.stem.lower().split('(')[0].split('[')[0].strip()
            seen_tokens.add(clean)
            if f.suffix in ('.json', '.csv', '.md', '.txt', '.log'):
                try:
                    for line in f.read_text(errors='ignore').lower().splitlines():
                        for w in line.split():
                            tok = w.strip('\"\'`:,;()[]{}<>')
                            if len(tok) >= 5:
                                seen_tokens.add(tok)
                                if len(tok) == 64 and all(c in '0123456789abcdef' for c in tok):
                                    seen_hashes.add(tok)
                except Exception:
                    pass

print(f'Indexed {len(seen_tokens)} tokens and {len(seen_hashes)} hashes.')

candidates = []
for entry in sorted(os.scandir(resumes_flat), key=lambda e: e.name):
    if not entry.is_file() or not entry.name.lower().endswith('.pdf'):
        continue
    fname = entry.name
    fname_lower = fname.lower()
    stem = Path(fname).stem.lower()
    clean = stem.split('(')[0].split('[')[0].strip()
    if len(clean) < 6:
        continue
    if fname_lower in seen_tokens or stem in seen_tokens or clean in seen_tokens:
        continue
    
    data = Path(entry.path).read_bytes()
    if len(data) < 30000 or len(data) > 600000:
        continue
    sha256 = hashlib.sha256(data).hexdigest().lower()
    if sha256 in seen_hashes or sha256 in seen_tokens:
        continue
    candidates.append({
        'filename': fname,
        'path': entry.path,
        'size': len(data),
        'sha256': sha256
    })

print(f'Eligible candidates count: {len(candidates)}')
for i, c in enumerate(candidates[:20], 1):
    print(f'{i:02d}. {c["filename"]} ({c["size"]} B, {c["sha256"][:16]}...)')

with open('reports/clean_candidates_pool.json', 'w') as f:
    json.dump(candidates, f, indent=2)
