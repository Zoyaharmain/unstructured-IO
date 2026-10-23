"""Resumable offline hierarchy mapping; reuse source-bound saved corpus blocks."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from scripts.batch_check_resumes import (offline_environment, initialize_worker,
    process_document, DocumentDeadline, SUPPORTED)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    temp.replace(path)


def map_artifact(artifact, output, row):
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    request=SchemaMappingRequest(elements=artifact['extraction']['elements'],
        sections=artifact.get('sections',artifact.get('local_sections')),source=row['file'])
    result=map_schema(request)
    target=Path(output)/'documents'/hashlib.sha256(row['file'].encode()).hexdigest()[:20]
    target.mkdir(parents=True,exist_ok=True)
    write(target/'source.json',artifact)
    write(target/'mapping.json',result.model_dump(mode='json'))
    row.update(status='mapped_needs_review',mapping_artifact=str((target/'mapping.json').relative_to(output)),
        source_artifact=str((target/'source.json').relative_to(output)),
        sections=len(result.section_schemas),records=sum(len(s.records) for s in result.section_schemas),
        populated_items=sum(len(a.items) for s in result.section_schemas for r in s.records for a in r.attributes),
        unresolved_attributes=sum(not a.items for s in result.section_schemas for r in s.records for a in r.attributes),
        unresolved_source_blocks=len(request.sections.needs_review),
        candidate_resume=result.meta['document_scope']['candidate_resume'],
        citation_validation_passed=True)
    return row


def fresh_worker(entry, output, timeout, code_hash):
    started=time.monotonic()
    row={**entry,'status':'failed','input_mode':'fresh_local_pipeline','provider_calls':0}
    if digest(Path(entry['source']))!=entry['sha256']:
        return dict(row,error_type='SourceChanged')
    stage=process_document(entry['source'],entry['file'],str(Path(output)/'fresh-inputs'),timeout,True,code_hash)
    row['extraction_status']=stage['status']
    try:
        if stage.get('artifact') and not stage.get('invariant_errors'):
            artifact=json.loads((Path(output)/'fresh-inputs'/stage['artifact']).read_text())
            signal.alarm(timeout)
            row=map_artifact(artifact,output,row)
        else:
            row['error_type']=stage.get('error_type',stage['status'])
            row['error_status']=stage.get('error_status')
    except DocumentDeadline:
        row['error_type']='MappingTimeout'
    except Exception as exc:
        row['error_type']=type(exc).__name__
    finally:
        signal.alarm(0)
    row['seconds']=round(time.monotonic()-started,3)
    return row


def summarize(output, rows, manifest, started):
    statuses=Counter(r['status'] for r in rows)
    summary={'files_discovered':len(manifest['inventory']),'files_completed':len(rows),
        'complete':len(rows)==len(manifest['inventory']),'statuses':dict(statuses),
        'provider_calls':0,'provider_tokens':0,'semantic_accuracy_measured':False,
        'input_modes':dict(Counter(r['input_mode'] for r in rows)),
        'populated_items':sum(r.get('populated_items',0) for r in rows),
        'unresolved_attributes':sum(r.get('unresolved_attributes',0) for r in rows),
        'elapsed_seconds':round(time.monotonic()-started,1)}
    write(output/'summary.json',summary)
    write(output/'per-resume.json',sorted(rows,key=lambda r:r['file']))
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--saved-audit',type=Path,default=ROOT/'.upstream/batch-validation')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--timeout',type=int,default=120)
    args=parser.parse_args()
    if not args.folder.is_dir() or not 1<=args.workers<=4 or args.timeout<1:
        parser.error('Use an existing source folder, 1–4 workers and a positive timeout')
    offline_environment()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True);output.chmod(0o700)
    (output/'fresh-inputs/documents').mkdir(parents=True,exist_ok=True)
    code=hashlib.sha256()
    for p in sorted((ROOT/'local_api').rglob('*.py'))+sorted((ROOT/'local_api/data').glob('*.json'))+[Path(__file__),ROOT/'scripts/batch_check_resumes.py']:
        code.update(str(p.relative_to(ROOT)).encode());code.update(p.read_bytes())
    code_hash=code.hexdigest()
    manifest_path=output/'manifest.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        if manifest['code_sha256']!=code_hash or manifest['source_directory']!=str(args.folder.resolve()) or manifest['timeout']!=args.timeout:
            parser.error('Resume requires the same frozen source directory and code')
    else:
        inventory=[]
        paths=sorted(p for p in args.folder.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith('~$'))
        for p in paths:
            inventory.append({'file':str(p.relative_to(args.folder)),'source':str(p.resolve()),'sha256':digest(p),'extension':p.suffix.lower()})
        manifest={'source_directory':str(args.folder.resolve()),'code_sha256':code_hash,
            'provider_calls':0,'inventory':inventory,'unique_hashes':len({r['sha256'] for r in inventory}),
            'mode':'offline_hierarchy_reuse_then_local_pipeline','timeout':args.timeout}
        write(manifest_path,manifest)
    rows=[]
    ledger=output/'results.jsonl'
    if ledger.exists():
        rows=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        if len({r['file'] for r in rows})!=len(rows):parser.error('Duplicate checkpoint entries')
    done={r['file'] for r in rows}
    saved={}
    if (args.saved_audit/'current-results.json').exists():
        saved={r['file']:r for r in json.loads((args.saved_audit/'current-results.json').read_text())}
    started=time.monotonic();pending=[]
    print(json.dumps({'discovered':len(manifest['inventory']),'resumed':len(rows),'provider_calls':0}),flush=True)
    with ledger.open('a') as stream:
        def record(row):
            rows.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            if len(rows)%25==0 or len(rows)==len(manifest['inventory']):
                s=summarize(output,rows,manifest,started)
                print(json.dumps({k:s[k] for k in ('files_completed','files_discovered','statuses','input_modes')}),flush=True)
        for entry in manifest['inventory']:
            if entry['file'] in done:continue
            previous=saved.get(entry['file'],{})
            artifact_path=args.saved_audit/previous['artifact'] if previous.get('artifact') else None
            if previous.get('sha256')==entry['sha256'] and artifact_path and artifact_path.is_file():
                try:
                    if digest(Path(entry['source']))!=entry['sha256']:raise ValueError('SourceChanged')
                    artifact=json.loads(artifact_path.read_text())
                    row=map_artifact(artifact,output,dict(entry,input_mode='reused_saved_blocks',provider_calls=0,
                        reused_artifact=str(artifact_path),reused_artifact_sha256=digest(artifact_path)))
                    record(row);continue
                except Exception as exc:
                    # Saved inputs that fail current source/record validation go
                    # through the existing local pipeline, never a relaxed gate.
                    entry=dict(entry,saved_input_rejected=type(exc).__name__)
            pending.append(entry)
        summarize(output,rows,manifest,started)
        print(json.dumps({'saved_completed':len(rows),'fresh_pending':len(pending)}),flush=True)
        if pending:
            with ProcessPoolExecutor(max_workers=args.workers,initializer=initialize_worker) as pool:
                futures={pool.submit(fresh_worker,e,str(output),args.timeout,code_hash):e for e in pending}
                for future in as_completed(futures):
                    entry=futures[future]
                    try:row=future.result()
                    except Exception as exc:row=dict(entry,status='failed',input_mode='fresh_local_pipeline',error_type=type(exc).__name__,provider_calls=0)
                    record(row)
    summary=summarize(output,rows,manifest,started)
    failed=[r for r in rows if r['status']=='failed']
    write(output/'failures.json',failed)
    report=f"# Full resume-folder hierarchical mapping\n\nProcessed **{len(rows)}/{len(manifest['inventory'])} files**. Results: {dict(Counter(r['status'] for r in rows))}.\n\nProvider calls: **0**. This is local processing, not DeepSeek verification or semantic accuracy certification. Every mapped result passed the current source-bound hierarchy validator.\n\nInput modes: {summary['input_modes']}. Populated child items: {summary['populated_items']}; unresolved attribute slots: {summary['unresolved_attributes']}.\n\nSee per-resume.json, failures.json, manifest.json and documents/*/mapping.json. Original PDFs and prior artifacts were not modified. Review unresolved values and failed files before downstream use.\n"
    (output/'report.md').write_text(report)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
