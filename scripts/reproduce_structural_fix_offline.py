"""Replay the 100-document batch offline through the fixed structural grouping pipeline.

Uses the saved DeepSeek responses; makes 0 API requests ($0.00 cost).
Produces a complete run directory with report.md, index.html, report.json, and per-resume.csv.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_api.schemas.extraction import ExtractionResponse
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.llm_section_review import review_sections, ReviewSettings
from local_api.services.resume_sections import build_sections
from scripts.batch_check_resumes import validate_result


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,default=ROOT/'reports/pilot100-fixed-llm-20261021-041000')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();source_run=args.source_run.resolve();target_run=args.output.resolve()
    if target_run.exists():parser.error('Output already exists; use a new directory. Previous results are immutable.')
    if target_run==source_run or source_run in target_run.parents:parser.error('Replay output must be outside the source run')
    protected={str(p):sha(p) for p in source_run.rglob('*') if p.is_file()}
    import socket
    def deny_network(*a,**kw):raise RuntimeError('Offline replay forbids network access')
    socket.socket.connect=deny_network;socket.create_connection=deny_network
    started=datetime.now(timezone.utc).isoformat()
    print(f"Creating structural grouping fix run directory: {target_run}")
    target_run.mkdir(parents=True)

    # 1. Copy manifest and selected PDFs
    manifest=json.loads((source_run/'manifest.json').read_text())
    manifest.update(run_kind='offline_replay',source_run=str(source_run),source_manifest_sha256=sha(source_run/'manifest.json'),replay_started_utc=started,local_processing_mode='saved_extraction_reused',live_api_calls=0,commands=[])
    for key in ('local_completed_utc','review_started_utc','review_completed_utc'):manifest.pop(key,None)
    from scripts.run_pilot50_review import configuration
    manifest['pipeline_source_hashes']=configuration()
    (target_run/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copytree(source_run / 'selected-pdfs', target_run / 'selected-pdfs')
    shutil.copytree(source_run / 'local', target_run / 'local')

    # 2. Setup deepseek directories
    ds_dir = target_run / 'deepseek'
    ds_dir.mkdir()
    (ds_dir / 'checkpoints').mkdir()
    (ds_dir / 'documents').mkdir()
    shutil.copytree(source_run / 'deepseek/provider-requests', ds_dir / 'historical-provider-requests')
    shutil.copytree(source_run / 'deepseek/provider-decisions', ds_dir / 'historical-provider-decisions')

    local_results = json.loads((target_run / 'local/current-results.json').read_text())
    orig_reviews = {r['file']: r for r in json.loads((source_run / 'deepseek/current-results.json').read_text())}

    new_reviews = []
    
    for row in local_results:
        filename = row['file']
        orig = orig_reviews[filename]
        doc_id = orig['id']

        # Load local extraction and sections
        local_art = json.loads((target_run / 'local' / row['artifact']).read_text())
        ext = ExtractionResponse.model_validate(local_art['extraction'])
        local_sec = SectionResponse.model_validate(local_art['sections'])
        
        # Re-build local_sec with new structural grouping
        local_grouped = {s.category: s.blocks for s in local_sec.sections}
        local_sec.sections = build_sections(local_grouped, ext.elements)
        local_art['sections'] = local_sec.model_dump()
        (target_run / 'local' / row['artifact']).write_text(json.dumps(local_art, indent=2, ensure_ascii=False) + '\n')

        req = SectionRequest(elements=ext.elements)

        dec_file = source_run / f'deepseek/provider-decisions/{doc_id}.json'
        if dec_file.exists():
            decs = json.loads(dec_file.read_text())
            call_idx = [0]

            def replay_transport(settings, messages):
                idx = call_idx[0]
                call_idx[0] += 1
                return decs[idx]['content']

            from dataclasses import replace
            settings = replace(
                ReviewSettings.from_env(),
                enabled=True,
                max_units=1000,
                max_input_chars=1_000_000,
                api_key='replay',
                model='deepseek-flash',
                recovery_attempts=len(decs)-1
            )
            reviewed_sec = review_sections(req, local_sec, settings=settings, transport=replay_transport)
        else:
            reviewed_sec = local_sec

        state = reviewed_sec.metadata.get('llm_review', {})
        state['execution_mode']='offline_replay'
        state['replayed_response_count']=call_idx[0] if dec_file.exists() else 0
        state['live_api_calls']=0
        errors = validate_result(req.elements, reviewed_sec)

        # Determine status
        rec_status = 'review_failed'
        if errors:
            rec_status = 'invariant_failure'
        elif state.get('status') == 'complete':
            if state.get('resolution_status') == 'out_of_scope':
                rec_status = 'llm_reviewed_out_of_scope'
            elif not reviewed_sec.sections:
                rec_status = 'llm_reviewed_no_sections'
            elif state.get('remaining_meaningful_review_units', len(reviewed_sec.needs_review)) > 0:
                rec_status = 'llm_reviewed_needs_review'
            else:
                rec_status = 'llm_reviewed_all_assigned'

        # Write reviewed document
        doc_artifact = {
            'file': filename,
            'extraction': ext.model_dump(),
            'local_sections': local_sec.model_dump(),
            'reviewed_sections': reviewed_sec.model_dump()
        }
        (ds_dir / f'documents/{doc_id}.json').write_text(json.dumps(doc_artifact, indent=2, ensure_ascii=False) + '\n')

        record = dict(orig)
        record.update(historical_api_calls=orig.get('api_calls',0),historical_usage=orig.get('usage',{}),api_calls=0,usage={},execution_mode='offline_replay',source_run=str(source_run))
        record.update(
            status=rec_status,
            llm_review=state,
            invariant_errors=errors,
            review_units=len(reviewed_sec.needs_review),
            review_characters=sum(len(b.text.strip()) for b in reviewed_sec.needs_review),
            sections=len(reviewed_sec.sections),
            categories=[s.category for s in reviewed_sec.sections],
            artifact=f'documents/{doc_id}.json'
        )
        (ds_dir / f'checkpoints/{doc_id}.json').write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        new_reviews.append(record)

    # Write deepseek/current-results.json and summary.json
    (ds_dir / 'current-results.json').write_text(json.dumps(sorted(new_reviews, key=lambda r: r['file']), indent=2, ensure_ascii=False) + '\n')

    orig_summary = json.loads((source_run / 'deepseek/summary.json').read_text())
    from collections import Counter
    statuses = Counter(r['status'] for r in new_reviews)
    new_summary = dict(orig_summary)
    new_summary.update(
        statuses=dict(statuses),
        documents_completed=len(new_reviews),
        execution_mode='offline_replay',classification_api_calls=0,usage={},historical_provider_usage=orig_summary.get('usage',{}),historical_classification_api_calls=orig_summary.get('classification_api_calls',0)
    )
    (ds_dir / 'summary.json').write_text(json.dumps(new_summary, indent=2, ensure_ascii=False) + '\n')

    # Write preservation.json
    changed=[path for path,value in protected.items() if not Path(path).is_file() or sha(Path(path))!=value]
    (target_run/'preservation.json').write_text(json.dumps({'checked':len(protected),'changed':changed,'scope':'source run files hashed before and after replay'})+'\n')
    if changed:raise RuntimeError('Source run changed during replay')
    manifest['replay_completed_utc']=datetime.now(timezone.utc).isoformat()
    (target_run/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    print("Replay complete. Generating report via scripts/report_pilot50_review.py...")
    cmd = [sys.executable, '-B', str(ROOT / 'scripts/report_pilot50_review.py'), '--run', str(target_run)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(res.stdout)
    print("Report generated successfully!")


if __name__ == '__main__':
    main()

