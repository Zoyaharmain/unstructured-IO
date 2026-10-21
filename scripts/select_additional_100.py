"""Select exactly 100 additional unique resumes strictly disjoint from the prior 250-resume LLM batch.

Uses deterministic stratified round-robin sampling (seed 42) based on page count, two-column layout,
and coverage strata. Verifies file existence and SHA-256 hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_pilot_fallback import DEFAULT_FOLDER
from scripts.select_ground_truth_resumes import get_details

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, default=DEFAULT_FOLDER)
    p.add_argument('--prior-manifest', type=Path, default=ROOT / 'reports/pilot250-llm-20261021-004616/manifest.json')
    p.add_argument('--count', type=int, default=100)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--output', type=Path, default=ROOT / 'manifests/selection_pilot100_additional.json')
    args = p.parse_args()

    prior = json.loads(args.prior_manifest.read_text())
    prior_hashes = {r['sha256'] for r in prior['selected']}
    prior_files = {r['file'] for r in prior['selected']}
    print(f"Loaded prior batch: {len(prior_hashes)} distinct hashes, {len(prior_files)} distinct files.")

    rows = json.loads((ROOT / '.upstream/batch-validation/current-results.json').read_text())
    pool = []
    for row in rows:
        if row.get('extension') != '.pdf' or row.get('status') != 'processed':
            continue
        if row.get('sha256') in prior_hashes or row['file'] in prior_files:
            continue
        artifact = ROOT / '.upstream/batch-validation' / row.get('artifact', '')
        if not artifact.is_file():
            continue
        p_file = args.folder / row['file']
        if not p_file.is_file():
            continue
        if sha(p_file) != row.get('sha256'):
            continue
        pool.append(get_details(row, ROOT / '.upstream/batch-validation'))

    print(f"Available verified candidate pool disjoint from prior 250: {len(pool)} PDFs.")

    buckets = {}
    for item in sorted(pool, key=lambda x: x['file']):
        key = (min(item['pages'], 5), item['two_col'], item['coverage'] < 95)
        buckets.setdefault(key, []).append(item)

    rng = random.Random(args.seed)
    for items in buckets.values():
        rng.shuffle(items)

    selected = []
    used_hashes = set()
    used_files = set()

    while len(selected) < args.count:
        progress = False
        for key in sorted(buckets):
            while buckets[key]:
                item = buckets[key].pop()
                if item['sha256'] in used_hashes or item['file'] in used_files:
                    continue
                p_file = args.folder / item['file']
                selected.append({
                    **item,
                    'original_source_path': str(p_file.resolve()),
                    'bytes': p_file.stat().st_size,
                    'selection_rationale': f'Seed{args.seed} round-robin stratum {key}; additional 100 evaluation set disjoint from prior 250',
                })
                used_hashes.add(item['sha256'])
                used_files.add(item['file'])
                progress = True
                break
            if len(selected) == args.count:
                break
        if not progress:
            raise ValueError(f"Insufficient distinct verified PDFs in pool to reach count={args.count}")

    # Validations
    assert len(selected) == args.count, f"Selected {len(selected)} != {args.count}"
    assert len(used_hashes) == args.count, "Duplicate SHA-256 within selected"
    assert len(used_files) == args.count, "Duplicate filenames within selected"
    assert not (used_hashes & prior_hashes), "Selected set intersects prior 250 hashes!"
    assert not (used_files & prior_files), "Selected set intersects prior 250 filenames!"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_data = {
        'count': len(selected),
        'seed': args.seed,
        'selection': f'100 additional unique resumes strictly disjoint from prior 250-resume LLM batch, seed{args.seed} stratified round-robin',
        'prior_batch_manifest': str(args.prior_manifest),
        'disjoint_confirmed': True,
        'selected': selected,
    }
    args.output.write_text(json.dumps(out_data, indent=2, ensure_ascii=False) + '\n')
    print(f"Successfully selected {len(selected)} resumes and saved to {args.output}")

if __name__ == '__main__':
    main()

