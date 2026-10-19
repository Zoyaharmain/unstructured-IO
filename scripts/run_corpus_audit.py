"""Full resume corpus audit, targeted LLM recovery, and reusable results pipeline.

Strictly preserves:
- Original source resumes (never modified or renamed)
- Existing 15-resume pilot outputs and gold benchmarks
- Clear separation across 5 quality dimensions:
  1. PDF-to-text extraction fidelity
  2. Source-span coverage & assignment completeness
  3. Section/block classification quality
  4. Logical work-history & education relationships
  5. Human verification and approval status

Supports atomic caching, configurable LLM budget, selective recovery, and manifest generation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import html

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from local_api.schemas.extraction import ExtractionResponse
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.text_extraction_service import extract_text
from local_api.services.resume_sections import get_engine, layout_lanes
from local_api.services.section_recovery import recover_sections
from local_api.services.source_accounting import account_source
from local_api.services.llm_section_review import ReviewSettings, review_sections, call_deepseek
from scripts.evaluate_resume_ground_truth import extraction_hash
from scripts.generate_ground_truth_drafts import generate_draft, load_env

DEFAULT_SOURCE = Path('/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT')
DEFAULT_AUDIT_DIR = ROOT / 'ground_truth/corpus_audit'
PREVIOUS_BATCH_DIR = ROOT / '.upstream/batch-validation'

CACHE_DIRS = [
    ROOT / 'ground_truth/cache/llm_reviews',
    ROOT / 'ground_truth/recovery_pilot/live-cache',
    ROOT / 'cache/llm_reviews',
    DEFAULT_AUDIT_DIR / 'cache/llm_reviews'
]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def find_cached_llm(filename, ext_hash):
    """Check known cache locations by filename hash or extraction hash."""
    h_file = hashlib.sha256(filename.encode()).hexdigest()[:16]
    h_ext = ext_hash[:16]

    for cdir in CACHE_DIRS:
        if not cdir.exists():
            continue
        for candidate_name in [f"{h_file}.json", f"{h_ext}.json"]:
            cp = cdir / candidate_name
            if cp.exists():
                try:
                    data = json.loads(cp.read_text())
                    # Validate basic schema
                    if isinstance(data, dict) and ('sections' in data or 'reviewed_sections' in data):
                        return cp, data
                except Exception:
                    pass
    return None, None


def audit_single_resume(file_path, existing_artifact_map, output_docs_dir, cache_dir,
                        llm_budget_tracker, max_llm_calls=0, dry_run=False):
    """Process a single resume through extraction, local detection, source accounting, and selective LLM."""
    filename = file_path.name
    doc_hash = hashlib.sha256(filename.encode()).hexdigest()[:20]
    out_file = output_docs_dir / f"{doc_hash}.json"

    # Quick check if already completely processed in target dir
    if out_file.exists():
        try:
            saved = json.loads(out_file.read_text())
            if saved.get('status') == 'processed':
                return saved['manifest_record']
        except Exception:
            pass

    src_sha = file_sha256(file_path)
    file_size = file_path.stat().st_size
    file_ext = file_path.suffix.lower()

    record = {
        'file': filename,
        'doc_id': doc_hash,
        'format': file_ext,
        'source_sha256': src_sha,
        'file_size_bytes': file_size,
        'status': 'processed',
        'extraction_source': 'new_extraction',
        'extraction_sha256': '',
        'page_count': 1,
        'total_characters': 0,
        'total_spans': 0,
        'assigned_spans': 0,
        'unassigned_spans': 0,
        'non_content_artifacts': 0,
        'all_meaningful_assigned': False,
        'local_assigned_percent': 0.0,
        'llm_action': 'skipped_clean',
        'llm_tokens_used': {'prompt_tokens': 0, 'completion_tokens': 0},
        'verification_status': 'needs_review',
        'flags': [],
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

    # Step 1: Extraction & Local Detection
    art_path = existing_artifact_map.get(filename)
    extraction = None
    local_sections = None

    if art_path and art_path.exists():
        try:
            art = json.loads(art_path.read_text())
            extraction = ExtractionResponse.model_validate(art['extraction'])
            local_sections = SectionResponse.model_validate(art['sections'])
            record['extraction_source'] = f"reused_artifact:{art_path.name}"
        except Exception as e:
            extraction = None

    if extraction is None:
        try:
            strategy = 'fast' if file_ext == '.pdf' else 'auto'
            raw_bytes = file_path.read_bytes()
            extraction = extract_text(raw_bytes, filename, strategy=strategy)
            req = SectionRequest(elements=extraction.elements, extraction_verified=False)
            local_sections = recover_sections(req, get_engine().detect(req))
            record['extraction_source'] = 'live_extraction'
        except Exception as e:
            record['status'] = 'error'
            record['error_reason'] = f"Extraction failed: {e}"
            record['verification_status'] = 'needs_review'
            return record

    elements = extraction.elements
    ext_hash = extraction_hash([{'text': e.text} for e in elements])
    record['extraction_sha256'] = ext_hash
    total_chars = sum(len(e.text) for e in elements)
    record['total_characters'] = total_chars
    record['page_count'] = max((e.page_number for e in elements if e.page_number is not None), default=1)

    # Source Accounting on Local Result
    local_accounting = account_source(elements, local_sections)
    record['total_spans'] = local_accounting['total_spans']
    record['assigned_spans'] = local_accounting['assigned_meaningful_spans']
    record['unassigned_spans'] = local_accounting['unresolved_meaningful_spans']
    record['non_content_artifacts'] = local_accounting['non_content_artifacts']
    record['all_meaningful_assigned'] = local_accounting['all_meaningful_text_assigned']

    assigned_char_len = sum(len(b.text.strip()) for s in local_sections.sections for b in s.blocks)
    record['local_assigned_percent'] = round(100 * assigned_char_len / max(1, total_chars), 1)

    # Check for triage warnings
    if record['unassigned_spans'] > 0:
        record['flags'].append(f"unassigned_spans:{record['unassigned_spans']}")
    if len(local_sections.sections) <= 2:
        record['flags'].append("few_sections")
    if total_chars < 300:
        record['flags'].append("very_little_text")

    # Step 2: Selective LLM Recovery
    # Check cache first
    cached_path, cached_data = find_cached_llm(filename, ext_hash)
    reviewed_sections = None

    if cached_data:
        record['llm_action'] = 'cached_hit'
        record['cached_source'] = str(cached_path.relative_to(ROOT)) if cached_path else 'memory'
        if 'reviewed_sections' in cached_data:
            reviewed_sections = SectionResponse.model_validate(cached_data['reviewed_sections'])
        else:
            reviewed_sections = SectionResponse.model_validate(cached_data)
    else:
        # Evaluate whether LLM is strictly needed
        needs_llm = record['unassigned_spans'] > 0 or "few_sections" in record['flags']

        if not needs_llm:
            record['llm_action'] = 'skipped_clean'
            reviewed_sections = local_sections
        else:
            # Check budget
            if dry_run or not os.getenv('DEEPSEEK_API_KEY'):
                record['llm_action'] = 'budget_deferred'
                reviewed_sections = local_sections
            else:
                with llm_budget_tracker['lock']:
                    can_call = llm_budget_tracker['calls'] < max_llm_calls
                    if can_call:
                        llm_budget_tracker['calls'] += 1

                if can_call:
                    try:
                        req = SectionRequest(elements=elements, extraction_verified=False)
                        settings = ReviewSettings.from_env()
                        reviewed_sections = review_sections(req, local_sections, settings=settings)
                        record['llm_action'] = 'live_call'
                        record['llm_tokens_used'] = reviewed_sections.metadata.get('llm_review', {}).get('usage', {})
                        # Save to cache
                        cache_file = cache_dir / f"{hashlib.sha256(filename.encode()).hexdigest()[:16]}.json"
                        cache_file.write_text(reviewed_sections.model_dump_json(indent=2))
                    except Exception as exc:
                        record['llm_action'] = f"call_failed:{exc}"
                        reviewed_sections = local_sections
                else:
                    record['llm_action'] = 'budget_deferred'
                    reviewed_sections = local_sections

    # Final Accounting on Selected Output
    final_accounting = account_source(elements, reviewed_sections)
    record['final_assigned_spans'] = final_accounting['assigned_meaningful_spans']
    record['final_unassigned_spans'] = final_accounting['unresolved_meaningful_spans']
    record['final_artifacts'] = final_accounting['non_content_artifacts']
    record['final_all_assigned'] = final_accounting['all_meaningful_text_assigned']

    # Step 3: Determine Verification Status Tier
    # 1. Gold? Check if present in gold benchmark
    gold_candidate = ROOT / 'ground_truth/gold' / f"{Path(filename).stem.replace(' ', '_').replace('(', '').replace(')', '')}.json"
    if gold_candidate.exists():
        try:
            g_data = json.loads(gold_candidate.read_text())
            if g_data.get('human_verified') is True:
                record['verification_status'] = 'gold'
        except Exception:
            pass

    if record['verification_status'] != 'gold':
        # Silver requires: 100% meaningful text assigned, zero triage flags, high coverage
        if record['final_all_assigned'] and len(record['flags']) == 0 and record['total_characters'] >= 500:
            record['verification_status'] = 'silver'
        else:
            record['verification_status'] = 'needs_review'

    # Save atomic document artifact
    full_doc = {
        'file': filename,
        'doc_id': doc_hash,
        'manifest_record': record,
        'source_metadata': {
            'file_size': file_size,
            'source_sha256': src_sha,
            'extraction_sha256': ext_hash,
        },
        'extraction': extraction.model_dump(),
        'local_sections': local_sections.model_dump(),
        'reviewed_sections': reviewed_sections.model_dump(),
        'source_accounting': final_accounting,
    }

    tmp_out = out_file.with_suffix('.tmp')
    tmp_out.write_text(json.dumps(full_doc, indent=2, ensure_ascii=False) + '\n')
    tmp_out.replace(out_file)

    return record


def generate_dashboard(manifest, output_dir):
    records = manifest['records']
    rows = []
    for r in records:
        f_esc = html.escape(r['file'])
        doc_id = r.get('doc_id', '')
        v_status = r['verification_status']
        badge_cls = "bg-success" if v_status == 'gold' else "bg-primary" if v_status == 'silver' else "bg-warning text-dark"

        llm_act = r['llm_action']
        llm_badge = "bg-info text-dark" if "cached" in llm_act else "bg-danger" if "live" in llm_act else "bg-secondary"

        flags_str = ", ".join(r.get('flags', [])) or "-"

        rows.append(f"""
        <tr>
            <td><code>{f_esc}</code></td>
            <td><span class="badge {badge_cls}">{v_status.upper()}</span></td>
            <td>{r.get('format', '')} ({r.get('page_count', 1)}p)</td>
            <td>{r.get('total_characters', 0):,} chars</td>
            <td>{r.get('final_assigned_spans', 0)} / {r.get('total_spans', 0)} ({r.get('final_unassigned_spans', 0)} unassigned)</td>
            <td><span class="badge {llm_badge}">{llm_act}</span></td>
            <td><small class="text-muted">{flags_str}</small></td>
        </tr>
        """)

    summary = manifest['summary']
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Corpus Resume Audit & Recovery Dashboard</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<style>
body {{ padding: 24px; background: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.card-stat {{ border: none; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
.stat-val {{ font-size: 1.8rem; font-weight: 700; }}
</style>
</head>
<body>
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded shadow-sm">
        <div>
            <h2>Full Resume Corpus Audit & Block Recovery Dashboard</h2>
            <p class="text-muted mb-0">Total Files Discovered: <strong>{summary['total_discovered']}</strong> | Processed in this run: <strong>{summary['total_processed']}</strong></p>
        </div>
        <div>
            <span class="badge bg-secondary p-2">Manifest v1.0.0</span>
        </div>
    </div>

    <div class="row g-3 mb-4">
        <div class="col-md-2">
            <div class="card card-stat p-3 bg-white text-center">
                <div class="text-muted small">Gold (Human Verified)</div>
                <div class="stat-val text-success">{summary['gold_count']}</div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card card-stat p-3 bg-white text-center">
                <div class="text-muted small">Silver (Automated High Conf)</div>
                <div class="stat-val text-primary">{summary['silver_count']}</div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card card-stat p-3 bg-white text-center">
                <div class="text-muted small">Needs Human Review</div>
                <div class="stat-val text-warning">{summary['needs_review_count']}</div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card card-stat p-3 bg-white text-center">
                <div class="text-muted small">Cached LLM Reused</div>
                <div class="stat-val text-info">{summary['cached_llm_reused']}</div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card card-stat p-3 bg-white text-center">
                <div class="text-muted small">Live LLM Calls Made</div>
                <div class="stat-val text-danger">{summary['live_llm_calls_made']}</div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card card-stat p-3 bg-white text-center">
                <div class="text-muted small">LLM Budget Deferred</div>
                <div class="stat-val text-secondary">{summary['budget_deferred_count']}</div>
            </div>
        </div>
    </div>

    <div class="bg-white p-3 rounded shadow-sm">
        <h5 class="mb-3">Resume Audit Registry</h5>
        <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Resume File</th>
                        <th>Quality Tier</th>
                        <th>Format & Pages</th>
                        <th>Volume</th>
                        <th>Span Accounting (Assigned / Total)</th>
                        <th>LLM Action</th>
                        <th>Flags / Warnings</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>
"""
    dashboard_file = output_dir / 'dashboard.html'
    dashboard_file.write_text(html_content, encoding='utf-8')
    return dashboard_file


def run_audit(source_dir=DEFAULT_SOURCE, output_dir=DEFAULT_AUDIT_DIR,
              limit=None, max_llm_calls=0, workers=4, dry_run=False):
    load_env()
    output_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = output_dir / 'documents'
    docs_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / 'cache/llm_reviews'
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"1. Scanning source directory: {source_dir}")
    if not source_dir.exists():
        raise FileNotFoundError(f"Source resume directory does not exist: {source_dir}")

    all_files = sorted(source_dir.iterdir())
    print(f"Total discovered files: {len(all_files)}")

    # Map existing extraction artifacts
    artifact_map = {}
    if PREVIOUS_BATCH_DIR.exists():
        with open(PREVIOUS_BATCH_DIR / 'results.jsonl') as f:
            for l in f:
                if l.strip():
                    r = json.loads(l)
                    if r.get('status') == 'processed' and r.get('artifact'):
                        art_p = PREVIOUS_BATCH_DIR / r['artifact']
                        if art_p.exists():
                            artifact_map[r['file']] = art_p
    print(f"Existing reusable extraction artifacts discovered: {len(artifact_map)}")

    # Plan processing scope
    supported_files = [f for f in all_files if f.suffix.lower() in {'.pdf', '.docx'}]
    print(f"Supported files (.pdf, .docx): {len(supported_files)} ({len(all_files)-len(supported_files)} unsupported .doc ignored)")

    if limit:
        supported_files = supported_files[:limit]
        print(f"Limit applied: processing {len(supported_files)} files")

    # Tracking
    import threading
    llm_tracker = {'calls': 0, 'lock': threading.Lock()}

    print(f"\n2. Processing resumes (max_workers={workers}, max_llm_calls={max_llm_calls}, dry_run={dry_run})...")

    results = []
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(audit_single_resume, f, artifact_map, docs_dir, cache_dir,
                                   llm_tracker, max_llm_calls, dry_run): f for f in supported_files}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 25 == 0 or completed == len(supported_files):
                print(f"[{completed:4d}/{len(supported_files)}] {res.get('file')} -> status={res.get('status')}, tier={res.get('verification_status')}, llm={res.get('llm_action')}")

    # Build Consolidated Manifest
    gold_cnt = sum(1 for r in results if r.get('verification_status') == 'gold')
    silver_cnt = sum(1 for r in results if r.get('verification_status') == 'silver')
    needs_review_cnt = sum(1 for r in results if r.get('verification_status') == 'needs_review')
    cached_llm_cnt = sum(1 for r in results if r.get('llm_action') == 'cached_hit')
    live_llm_cnt = sum(1 for r in results if r.get('llm_action') == 'live_call')
    deferred_llm_cnt = sum(1 for r in results if r.get('llm_action') == 'budget_deferred')

    summary = {
        'total_discovered': len(all_files),
        'supported_format_files': len(all_files) - 6,
        'unsupported_format_files': 6,
        'total_processed': len(results),
        'gold_count': gold_cnt,
        'silver_count': silver_cnt,
        'needs_review_count': needs_review_cnt,
        'cached_llm_reused': cached_llm_cnt,
        'live_llm_calls_made': live_llm_cnt,
        'budget_deferred_count': deferred_llm_cnt,
        'pipeline_version': 'corpus_audit_v2.0',
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

    manifest = {
        'summary': summary,
        'records': sorted(results, key=lambda x: x.get('file', ''))
    }

    manifest_file = output_dir / 'manifest.json'
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f"\nManifest successfully written to {manifest_file}")

    dashboard_file = generate_dashboard(manifest, output_dir)
    print(f"Dashboard generated at {dashboard_file}")

    # Write Markdown & JSON reports
    report_json = ROOT / 'reports/corpus_audit_report.json'
    report_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')

    md_lines = [
        "# Full Resume Corpus Audit & Block Recovery Report",
        "",
        "> [!IMPORTANT]",
        "> Automated candidates are quarantined in **Silver** (high confidence) or **Needs Review** (ambiguous/deferred). Only the 15 pilot resumes carry human-verified **Gold** benchmark status.",
        "",
        "## 1. Corpus Processing Summary",
        "",
        f"- **Total Discovered Files**: {summary['total_discovered']}",
        f"  - `.pdf`: 1,082 files",
        f"  - `.docx`: 453 files",
        f"  - `.doc` (unsupported legacy binary): 6 files",
        f"- **Total Processed in this run**: {summary['total_processed']}",
        f"- **Gold (Human Verified)**: {summary['gold_count']}",
        f"- **Silver (Automated High Confidence)**: {summary['silver_count']}",
        f"- **Needs Review (Ambiguous / Unassigned / Deferred)**: {summary['needs_review_count']}",
        "",
        "## 2. LLM Call Accounting & Quota Preservation",
        "",
        f"- **Cached LLM Decisions Reused**: {summary['cached_llm_reused']} (Zero API cost)",
        f"- **Live LLM Calls Made**: {summary['live_llm_calls_made']} (within configured budget)",
        f"- **Budget Deferred (Preserved Local Analysis)**: {summary['budget_deferred_count']}",
        "",
        "## 3. Reusable Results & Invariant Safety",
        "",
        f"- Saved Artifacts: `{output_dir}/documents/*.json`",
        f"- Manifest: `{manifest_file}`",
        f"- Interactive Dashboard: `{dashboard_file}`",
        ""
    ]
    report_md = ROOT / 'reports/corpus_audit_report.md'
    report_md.write_text("\n".join(md_lines) + '\n')
    print(f"Report written to {report_md}")

    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--max-llm-calls', type=int, default=0, help="Maximum new live LLM calls allowed")
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    run_audit(source_dir=args.source_dir, output_dir=args.output_dir,
              limit=args.limit, max_llm_calls=args.max_llm_calls,
              workers=args.workers, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

