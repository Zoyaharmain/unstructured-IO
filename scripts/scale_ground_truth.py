"""Scale ground-truth candidate generation across the full resume collection.

Distinguishes strictly between:
- gold: human-verified annotations (never modified by this script)
- silver: automatically generated annotations with full coverage & high confidence
- needs_review: suspicious, low-coverage, or unresolved annotations

Supports resumable processing, atomic caching, parallel execution, and manifest generation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from local_api.services.llm_section_review import ReviewSettings
from scripts.evaluate_resume_ground_truth import extraction_hash
from scripts.generate_ground_truth_drafts import generate_draft, load_env

DEFAULT_SOURCE = Path('/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT')


def process_single_resume(record, source_results_dir, output_dir, cache_dir, use_deepseek=True):
    filename = record['file']
    art_path = source_results_dir / record['artifact']
    if not art_path.exists():
        return {
            'file': filename,
            'status': 'error',
            'reason': 'artifact_not_found',
            'verification_status': 'needs_review'
        }

    try:
        # Generate candidate draft
        candidate = generate_draft(filename, art_path, cache_dir=cache_dir, use_deepseek=use_deepseek)

        # Evaluate quality for silver vs needs_review
        uncertain_cnt = candidate['uncertainty_summary']['uncertain_spans']
        meaningful=[s for s in candidate['spans'] if s['category']!='ignore']
        denominator=sum(len(s['text'].strip()) for s in meaningful)
        cov=100*sum(len(s['text'].strip()) for s in meaningful if s['category']!='needs_review')/max(1,denominator)
        active_flags=[f for f in record.get('flags',[]) if f!='unassigned_text']
        if candidate['uncertainty_summary'].get('unassigned_spans'):active_flags.append('unassigned_text')
        has_triage_flags=bool(active_flags)
        llm_status = candidate.get('llm_review_status', 'complete')

        safe_stem = Path(filename).stem.replace(' ', '_').replace('(', '').replace(')', '')

        if uncertain_cnt == 0 and cov >= 95.0 and llm_status in {'complete', 'cached'} and not has_triage_flags:
            verif_status = 'silver'
            candidate['status'] = 'silver_automated'
            target_dir = output_dir / 'silver'
        else:
            verif_status = 'needs_review'
            candidate['status'] = 'needs_review'
            target_dir = output_dir / 'needs_review'

        target_dir.mkdir(parents=True, exist_ok=True)
        out_file = target_dir / f"{safe_stem}.json"
        if out_file.exists() and json.loads(out_file.read_text()).get('file')!=filename:raise ValueError('Candidate filename collision; no existing file overwritten')
        out_file.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + '\n')

        return {
            'file': filename,
            'source_sha256': record.get('sha256'),
            'extraction_sha256': candidate['extraction_sha256'],
            'verification_status': verif_status,
            'annotation_path': str(out_file.relative_to(ROOT)),
            'coverage_percent': cov,
            'pages': len(record.get('pages', [1])),
            'uncertain_spans': uncertain_cnt,
            'local_flags':record.get('flags',[]),
            'flags': active_flags + ([f"uncertain_spans_{uncertain_cnt}"] if uncertain_cnt else []),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            'file': filename,
            'status': 'error',
            'reason': str(e),
            'verification_status': 'needs_review'
        }


def scale_corpus(source_results_dir, output_dir, limit=None, workers=4, use_deepseek=True, approved_gold_dir=None, pilot_review_dir=None, dry_run=False, review_catalog=None):
    from scripts.pilot_review_gate import check_pilot_ready
    if approved_gold_dir is None or pilot_review_dir is None:raise ValueError('Explicit pilot review and approved gold directories are required before scaling')
    gate=check_pilot_ready(pilot_review_dir,approved_gold_dir,review_catalog)
    print(json.dumps({k:v for k,v in gate.items() if k!='decisions'},indent=2))
    if not gate['ready']:
        if dry_run:return gate
        raise ValueError('Pilot human-review gate is not complete; no bulk requests started')
    if dry_run:return gate
    load_env()
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / 'cache/llm_reviews'
    cache_dir.mkdir(parents=True, exist_ok=True)

    with open(source_results_dir / 'results.jsonl') as f:
        latest={}
        for line in f:
            if line.strip():
                record=json.loads(line);latest[record['file']]=record
        records=list(latest.values())

    # Filter to valid PDFs with artifacts
    pdf_records = [r for r in records if r.get('extension', '').lower() == '.pdf' and r.get('artifact')]
    print(f"Total discovered valid PDF resumes: {len(pdf_records)}")

    # Load existing manifest if present for resumability
    manifest_path = output_dir / 'manifest.json'
    existing_manifest = {}
    if manifest_path.exists():
        try:
            m_data = json.loads(manifest_path.read_text())
            existing_manifest = {item['file']: item for item in m_data.get('records', [])}
        except Exception:
            existing_manifest = {}

    # Only explicit approved review exports are protected as gold. Legacy
    # auto-promoted files are preserved but not silently trusted as approvals.
    existing_manifest={key:value for key,value in existing_manifest.items() if value.get('verification_status') not in {'gold','excluded_by_human'}}
    for filename,decision in gate['decisions'].items():
        existing_manifest[filename]={'file':filename,'verification_status':decision['status'],**decision}
    source_by_name={record['file']:record for record in pdf_records}
    for filename,decision in gate['decisions'].items():
        if filename not in source_by_name:continue
        record=source_by_name[filename]
        if record.get('sha256')!=decision['pdf_sha256']:raise ValueError('Approved PDF hash differs from bulk source: '+filename)
        if decision['status']=='gold':
            artifact=json.loads((source_results_dir/record['artifact']).read_text())
            if extraction_hash(artifact['extraction']['elements'])!=decision['extraction_sha256']:
                raise ValueError('Approved source inventory differs; explicit correction rebase required: '+filename)

    to_process = []
    for r in pdf_records:
        if r['file'] in existing_manifest and existing_manifest[r['file']].get('verification_status') in {'gold','excluded_by_human'}:
            continue
        to_process.append(r)

    if limit:
        to_process = to_process[:limit]

    print(f"Resumes to process in this run: {len(to_process)} (workers={workers})")

    results = []
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_single_resume, r, source_results_dir, output_dir, cache_dir, use_deepseek): r for r in to_process}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 10 == 0 or completed == len(to_process):
                print(f"[{completed:4d}/{len(to_process)}] Completed: {res.get('file')} -> {res.get('verification_status')}")

    # Build final consolidated manifest
    all_records = {**existing_manifest, **{r['file']: r for r in results if 'file' in r}}

    gold_cnt = sum(1 for r in all_records.values() if r.get('verification_status') == 'gold')
    silver_cnt = sum(1 for r in all_records.values() if r.get('verification_status') == 'silver')
    needs_review_cnt = sum(1 for r in all_records.values() if r.get('verification_status') == 'needs_review')

    manifest = {
        'collection_summary': {
            'total_resumes_discovered': len(pdf_records),
            'total_processed_in_manifest': len(all_records),
            'gold_human_verified_count': gold_cnt,
            'silver_automated_high_confidence_count': silver_cnt,
            'needs_review_count': needs_review_cnt,
            'manifest_version': '1.0.0',
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'model_configuration': {'local':'sentence-bert+seeded-kmeans','review_model':ReviewSettings.from_env().model if use_deepseek else None},
            'approved_corrections_directory':str(approved_gold_dir),
            'pilot_human_review_gate_passed':True
        },
        'records': sorted(all_records.values(), key=lambda x: x.get('file', ''))
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f"\nManifest successfully updated at {manifest_path}:")
    print(f" - Gold (Human Verified): {gold_cnt}")
    print(f" - Silver (Automated High Confidence): {silver_cnt}")
    print(f" - Needs Review (Suspicious / Unresolved): {needs_review_cnt}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-results-dir', type=Path, default=ROOT / '.upstream/batch-validation')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'ground_truth')
    parser.add_argument('--limit', type=int, default=None, help="Limit number of resumes to process")
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--review-catalog',type=Path)
    parser.add_argument('--approved-gold-dir',type=Path,required=True)
    parser.add_argument('--pilot-review-dir',type=Path,required=True)
    parser.add_argument('--dry-run',action='store_true',help='Check pilot approvals only; no candidate generation or API calls')
    parser.add_argument('--skip-deepseek', action='store_true')
    args = parser.parse_args()

    result=scale_corpus(args.source_results_dir, args.output_dir, limit=args.limit, workers=args.workers, use_deepseek=not args.skip_deepseek,approved_gold_dir=args.approved_gold_dir,pilot_review_dir=args.pilot_review_dir,dry_run=args.dry_run,review_catalog=args.review_catalog)
    if args.dry_run and not result['ready']:raise SystemExit(2)


if __name__ == '__main__':
    main()
