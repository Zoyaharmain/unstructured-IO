"""Fresh offline evaluation of a frozen selection. Never creates accuracy labels."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selection',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--truth',type=Path)
    p.add_argument('--split-manifest',type=Path, help='Frozen development/validation/held-out JSONL manifest')
    p.add_argument('--evaluate-held-out',action='store_true', help='Require independent, adjudicated labels before opening held-out documents')
    a=p.parse_args()
    if a.output.exists():p.error('Output must be new')
    split_rows = [json.loads(line) for line in a.split_manifest.read_text().splitlines() if line.strip()] if a.split_manifest else []
    if not a.selection and not a.split_manifest:
        p.error('Supply --selection for diagnostics or --split-manifest for a frozen dataset')
    manifest = json.loads(a.selection.read_text()) if a.selection else {'selected':[
        {'file':row['names'][0], 'sha256':row['sha256'], 'original_source_path':row['paths'][0]} for row in split_rows]}
    if not manifest['selected']:
        p.error('Dataset split has no documents; reserve genuinely new resumes rather than reusing development data')
    split_by_hash = {row['sha256']:row for row in split_rows}
    if a.truth and not a.split_manifest:
        p.error('Scored evaluations require --split-manifest; historical diagnostics cannot claim held-out accuracy')
    from scripts.batch_check_resumes import initialize_worker, process_document
    from local_api.schemas.sections import SectionResponse
    from local_api.schemas.extraction import ExtractedElement
    from local_api.services.source_ownership import finalize_ownership,snapshot
    from local_api.services.ownership_evaluation import evaluate_ownership
    initialize_worker()
    a.output.mkdir(parents=True,mode=0o700)
    (a.output/'documents').mkdir(mode=0o700)
    truth=json.loads(a.truth.read_text()) if a.truth else {}
    rows=[]
    for item in manifest['selected']:
        reserved = split_by_hash.get(item['sha256'])
        if a.split_manifest and reserved is None:
            raise ValueError('Selection is outside the frozen split manifest')
        if reserved and reserved['split'] == 'held_out_test':
            if not a.evaluate_held_out or reserved.get('historical_evidence') or item['sha256'] not in truth:
                raise ValueError('Held-out documents remain sealed until explicit evaluation with independent labels')
            from local_api.services.evaluation_datasets import validate_annotation, audit_usage
            annotation = truth[item['sha256']]
            validate_annotation(annotation, annotation.get('source_digest'), held_out=True)
            if annotation.get('source_sha256') != item['sha256']:
                raise ValueError('Held-out annotation is not bound to the original document hash')
            audit = json.loads((a.split_manifest.parent/'audit-summary.json').read_text())
            if audit_usage([reserved], [Path(path) for path in audit['history_roots']])[0]['historical_evidence']:
                raise ValueError('Held-out document acquired development exposure after reservation')
        path=Path(item['original_source_path'])
        from hashlib import sha256
        if sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Selection source changed')
        row=process_document(path,item['file'],a.output,120,True,'ownership_heldout')
        if row['status']=='processed':
            artifact=json.loads((a.output/row['artifact']).read_text())
            elements=[ExtractedElement.model_validate(e) for e in artifact['extraction']['elements']]
            result=finalize_ownership(elements,SectionResponse.model_validate(artifact['sections']))
            state=snapshot(elements,result)
            row['metrics']=evaluate_ownership(elements,state,truth.get(item['sha256']))
            artifact['sections']=result.model_dump()
            (a.output/row['artifact']).write_text(json.dumps(artifact,ensure_ascii=False))
        rows.append(row)
        print(json.dumps({'completed':len(rows),'status':row['status']}),flush=True)
    metrics=[r['metrics'] for r in rows if 'metrics' in r]
    labeled=[m for m in metrics if m['accuracy_status']=='independently_labeled']
    total=sum(m['meaningful_spans'] for m in metrics)
    summary={'selected_documents':len(rows),'processed_documents':len(metrics),'independently_labeled_documents':len(labeled),
             'source_processing_success_rate':len(metrics)/len(rows) if rows else None,
             'failed_documents':len(rows)-len(metrics),
             'selection_disjoint_from_saved_batches':manifest.get('disjoint_confirmed',False),
             'dataset_splits':sorted({row['split'] for row in split_rows}),
             'true_unseen_status':'Not established: selector excludes saved batch manifests, not all historical artifacts.',
             'unresolved_span_rate':sum(m['unresolved_spans'] for m in metrics)/total if total else None,
             'provider_calls':0,'production_quality_established':False}
    if split_rows and {row['split'] for row in split_rows} == {'held_out_test'} and len(labeled) == len(rows):
        summary['true_unseen_status'] = 'Independently reviewed held-out evaluation with tracked-exposure checks; external training provenance remains unknown.'
    for key in ('section_f1','record_boundary_f1','responsibility_ownership_accuracy','cross_record_leakage'):
        values=[m[key] for m in labeled if m[key] is not None]
        summary[key]=sum(values)/len(values) if values else None
    (a.output/'results.json').write_text(json.dumps(rows,indent=2))
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
