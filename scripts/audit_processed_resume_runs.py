"""Read-only provenance/integrity/readiness audit of saved resume batches.

No extraction model or provider calls. Deduplicates documents by PDF SHA256,
never adds counts from overlapping runs, never modifies the inspected runs.
"""
import argparse,csv,hashlib,json,socket,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_api.schemas.sections import SectionResponse,SectionRequest
from local_api.services.llm_section_review import source_ledger,assert_coverage
from local_api.services.source_accounting import account_source
from local_api.services.review_resolution import document_scope
from local_api.services.record_relationships import annotate_relationships
from local_api.services.quality_assessment import assess_quality
from scripts.batch_check_resumes import validate_result

# Historical forensics: these two creator scripts were inspected and found to
# copy live counts, timestamps and manifests. This registry labels old artifacts;
# it is never used by extraction/classification or candidate selection.
LEGACY_REPLAYS={
 'pilot100-fixed-llm-20261021-041000':'pilot100-additional-llm-20261021-025143',
 'structural-grouping-fix-20261021-051500':'pilot100-fixed-llm-20261021-041000',
}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reports',type=Path,default=ROOT/'reports');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Use a new output directory')
    a.output.mkdir(parents=True)
    def deny(*args,**kwargs):raise RuntimeError('Saved-artifact audit forbids network calls')
    socket.socket.connect=deny;socket.create_connection=deny
    runs=[];documents=[];latest={}
    for run in sorted(a.reports.iterdir()):
        manifest_path=run/'manifest.json';results_path=run/'deepseek/current-results.json'
        if not manifest_path.is_file() or not results_path.is_file():continue
        manifest=json.loads(manifest_path.read_text());selected=manifest.get('selected',[])
        if len(selected)<50:continue
        summary=json.loads((run/'deepseek/summary.json').read_text());reviews=json.loads(results_path.read_text())
        replay=manifest.get('run_kind')=='offline_replay' or run.name in LEGACY_REPLAYS or summary.get('execution_mode')=='offline_replay'
        rows={r['file']:r for r in reviews};bindings=0;valid=0;errors=[];scope_counts=Counter();rel_counts=Counter()
        for source in selected:
            name=source['file'];row=rows.get(name)
            pdf=run/'selected-pdfs'/name
            copied_hash=pdf.is_file() and sha(pdf)==source['sha256']
            primary=Path(source.get('original_source_path','/nonexistent'));original_hash=primary.is_file() and sha(primary)==source['sha256']
            artifact_path=run/'deepseek'/row['artifact'] if row and row.get('artifact') else None
            if artifact_path is None or not artifact_path.is_file():errors.append({'file':name,'error':'missing_review_artifact'});continue
            artifact=json.loads(artifact_path.read_text());req=SectionRequest(elements=artifact['extraction']['elements']);res=SectionResponse.model_validate(artifact['reviewed_sections'])
            local_rows=json.loads((run/'local/current-results.json').read_text());local_row=next((r for r in local_rows if r['file']==name),None)
            local_art=json.loads((run/'local'/local_row['artifact']).read_text()) if local_row and local_row.get('artifact') else None
            bound=bool(copied_hash and local_row and local_row.get('sha256')==source['sha256'] and local_art and artifact['extraction']==local_art['extraction'] and artifact['local_sections']==local_art['sections'])
            bindings+=bound
            try:
                assert_coverage(req.elements,source_ledger(res));invariants=validate_result(req.elements,res);account=account_source(req.elements,res)
            except Exception as exc:
                errors.append({'file':name,'error':type(exc).__name__});continue
            valid+=not invariants
            for sec in res.sections:annotate_relationships(sec)
            quality=assess_quality(req.elements,res);scope=document_scope(req.elements);scope_counts[scope['kind']]+=1
            for category,info in quality['relationship_correctness']['sections'].items():
                if info['unlinked_block_indices'] or info['entries_needing_review']:rel_counts[category]+=1
            unresolved=[{'source_id':f'e{b.source_element_index}:{b.start}:{b.end}','page':b.page_number,'text':b.text} for b in res.needs_review if b.text.strip()]
            item={'file':name,'sha256':source['sha256'],'run':run.name,'execution_mode':'offline_replay' if replay else 'recorded_live_batch',
                  'saved_review_status':row['status'],'copied_source_hash_match':copied_hash,'original_source_hash_match':original_hash,'artifact_binding':bound,
                  'integrity_errors':invariants,'current_scope':scope,'meaningful_unassigned':account['unresolved_meaningful_spans'],
                  'candidate_meaningful_unassigned':account['unresolved_meaningful_spans'] if scope['candidate_resume'] is not False else None,
                  'quality_assessment':quality,'remaining_source_text':unresolved,'human_approval_established':False}
            documents.append(item)
            if not replay:
                stamp=manifest.get('review_completed_utc',manifest.get('created_utc',''))
                if source['sha256'] not in latest or stamp>latest[source['sha256']][0]:latest[source['sha256']]=(stamp,item)
        recorded={str(ROOT/k):h for k,h in manifest.get('pipeline_source_hashes',{}).items()}
        changed=[str(Path(k).relative_to(ROOT)) for k,h in recorded.items() if Path(k).is_file() and sha(Path(k))!=h]
        runs.append({'run':run.name,'execution_mode':'offline_replay' if replay else 'recorded_live_batch','documents':len(selected),'distinct_hashes':len({r['sha256'] for r in selected}),
                     'reported_classification_requests':summary.get('classification_api_calls',0),'new_live_calls_attributed_to_run':0 if replay else summary.get('classification_api_calls',0),
                     'reported_statuses':summary.get('statuses',{}),'scope_counts_current_rules':dict(scope_counts),'record_association_flags_current_rules':dict(rel_counts),
                     'source_artifact_bindings_passed':bindings,'interval_and_entry_integrity_passed':valid,'errors':errors,'source_files_changed_since_run':changed,
                     'live_evidence_files':{'local_log':(run/'local.log').is_file(),'provider_log':(run/'deepseek.log').is_file(),'requests':len(list((run/'deepseek/provider-requests').glob('*.json')))},
                     'replay_source':manifest.get('source_run',LEGACY_REPLAYS.get(run.name))})
    unique=[v[1] for v in latest.values()];statuses=Counter(r['saved_review_status'] for r in unique);scopes=Counter(r['current_scope']['kind'] for r in unique)
    result={'runs':runs,'distinct_documents_with_recorded_live_runs':len(unique),'latest_live_outcomes':dict(statuses),'scope_current_rules':dict(scopes),
            'meaningful_unassigned_all_scopes':sum(r['meaningful_unassigned'] for r in unique),
            'candidate_meaningful_unassigned':sum(r['candidate_meaningful_unassigned'] or 0 for r in unique),
            'new_api_calls_by_this_audit':0,'independent_human_approval_established':0,'ready_for_production_acceptance':False,'documents':documents}
    (a.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    columns=['file','sha256','run','saved_review_status','copied_source_hash_match','original_source_hash_match','artifact_binding','meaningful_unassigned','candidate_meaningful_unassigned','human_approval_established']
    with (a.output/'latest-distinct-documents.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows({k:r[k] for k in columns} for r in sorted(unique,key=lambda r:r['file']))
    (a.output/'runs.json').write_text(json.dumps(runs,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'documents','runs'}},indent=2))
if __name__=='__main__':main()
