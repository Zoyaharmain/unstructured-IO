"""Read-only, no-provider verification of available batch and schema evidence."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import socket
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
OUT = Path(__file__).resolve().parent

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, obj): (OUT/name).write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')
def deny(*args, **kwargs): raise RuntimeError('Verification audit forbids provider/network access')
socket.socket.connect = deny
socket.create_connection = deny
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.source_validation import validate_result
from local_api.services.schema_mapping import map_schema
from local_api.services.source_accounting import account_source
from local_api.services.quality_assessment import assess_quality
from local_api.services.llm_section_review import parse_decisions, ReviewError
from local_api.vendor.handoff_schema.models import ParseResponse

runs = ['pilot250-llm-20261021-004616','pilot100-additional-llm-20261021-025143',
        'pilot100-fixed-llm-20261021-041000','structural-grouping-fix-20261021-051500',
        'batch-next-20261021-064222']
replays = set(runs[2:4])
latest = {}; run_rows = []; tracked = {}; observed = set()
def track(path):
    if path.is_file(): tracked[str(path.relative_to(ROOT))] = sha(path)
for run in runs:
    directory=ROOT/'reports'/run; manifest=read(directory/'manifest.json')
    selected={x['file']:x for x in manifest['selected']}
    rows=read(directory/'deepseek/current-results.json')
    summary=read(directory/'deepseek/summary.json')
    digests={x['sha256'] for x in selected.values()}
    stamp=manifest.get('review_completed_utc',manifest['created_utc'])
    run_rows.append({'run':run,'execution':'offline_replay' if run in replays else 'historical_live',
        'selected':len(selected),'distinct_hashes':len(digests),'new_hashes_in_chronological_scope':len(digests-observed),
        'reported_requests':sum(x.get('api_calls',0) for x in rows),
        'requests_attributed_to_this_run':0 if run in replays else sum(x.get('api_calls',0) for x in rows),
        'statuses':dict(Counter(x['status'] for x in rows)),
        'available_request_files':len(list((directory/'deepseek/provider-requests').glob('*.json'))),
        'local_before_review':manifest.get('local_completed_utc','z') <= manifest.get('review_started_utc',''),
        'source_code_files_changed_since_run':sum(not (ROOT/k).is_file() or sha(ROOT/k)!=v for k,v in manifest.get('pipeline_source_hashes',{}).items()),
        'recorded_source_code_files':len(manifest.get('pipeline_source_hashes',{})),
        'token_usage':summary.get('provider_usage',summary.get('usage'))})
    if run not in replays:
        observed.update(digests)
        localrows={x['file']:x for x in read(directory/'local/current-results.json')}
        for row in rows:
            info=selected[row['file']]; digest=info['sha256']
            if row.get('artifact') and (digest not in latest or stamp>latest[digest]['stamp']):
                latest[digest]={'stamp':stamp,'directory':directory,'row':row,'source':info,'localrow':localrows[row['file']]}
    for p in [directory/'manifest.json',directory/'deepseek/current-results.json',directory/'local/current-results.json']:
        track(p)
assert len(latest)==350, len(latest)
rows=[]; fingerprints=[]
old_index={x['sha256']:x for x in read(ROOT/'reports/schema-mapping-integration-20261022/validation-source-index.json')}
for digest, item in sorted(latest.items(), key=lambda pair:pair[1]['source']['file'].casefold()):
    d=item['directory']; row=item['row']; info=item['source']; lr=item['localrow']
    artifact_path=d/'deepseek'/row['artifact']; localpath=d/'local'/lr['artifact']
    track(artifact_path);track(localpath)
    artifact=read(artifact_path); local=read(localpath)
    elements=SectionRequest(elements=artifact['extraction']['elements']).elements
    sections=SectionResponse.model_validate(artifact['reviewed_sections'])
    before=SectionResponse.model_validate(artifact['local_sections'])
    errors=validate_result(elements,sections); accounting=account_source(elements,sections)
    quality=assess_quality(elements,sections)
    original=Path(info['original_source_path'])
    if not original.is_file():original=d/'selected-pdfs'/info['file']
    pdf_hash_match=original.is_file() and sha(original)==digest
    req=SchemaMappingRequest(elements=elements,sections=sections,source=info['file'])
    snapshot=req.model_dump_json(); mapped=map_schema(req); ParseResponse.model_validate(mapped.model_dump())
    assert req.model_dump_json()==snapshot
    ids={f'e{b.source_element_index}:{b.start}:{b.end}' for s in sections.sections for b in s.blocks}
    ids.update(f'e{b.source_element_index}:{b.start}:{b.end}' for b in sections.needs_review)
    evidence_valid=all(ref in ids for refs in mapped.meta['field_evidence'].values() for ref in refs)
    rel=quality['relationship_correctness']['sections']
    relation_flags={k:{'entries_needing_review':len(v['entries_needing_review']),
        'unlinked_blocks':len(v['unlinked_block_indices']),'proposed_entries':v['proposed_entries']} for k,v in rel.items()}
    # Recheck source text against a second parser, without calling it ground truth.
    independent={'status':'source_unavailable','unmatched_terms':0,'empty':False}
    if original.is_file():
        result=subprocess.run(['pdftotext','-layout',str(original),'-'],capture_output=True,timeout=45)
        text=result.stdout.decode('utf-8','replace'); extracted='\n'.join(e.text for e in elements)
        difference=Counter(re.findall(r'\w+',text.casefold()))-Counter(re.findall(r'\w+',extracted.casefold()))
        normalized=re.sub(r'\W','',extracted.casefold())
        unmatched={k:v for k,v in difference.items() if re.sub(r'\W','',k) not in normalized}
        independent={'status':'complete' if result.returncode==0 else 'failed',
                     'unmatched_terms':sum(unmatched.values()),'empty':not text.strip()}
    # Validate available recorded request/response pairs with today's strict contract.
    decisionpath=d/'deepseek/provider-decisions'/(row['id']+'.json');track(decisionpath)
    decisions=read(decisionpath) if decisionpath.exists() else []
    validation=[]; requests=0; request_source_mismatch=0
    for number, response in enumerate(decisions,1):
        requestpath=d/'deepseek/provider-requests'/(row['id']+f'-{number}.json')
        if not requestpath.exists():continue
        track(requestpath); requests+=1
        request=read(requestpath)
        try:
            payload=json.loads(request['messages'][1]['content']); spans=payload['spans']
            for span in spans:
                i=span.get('source_element'); start=span.get('source_start'); end=span.get('source_end')
                if i is not None and start is not None and end is not None:
                    if not 0<=i<len(elements) or elements[i].text[start:end]!=span['text']: request_source_mismatch+=1
            lengths={x['id']:x.get('length',len(x['text'])) for x in spans}
            texts={x['id']:x['text'] for x in spans}
            cuts={x['id']:set(x['allowed_split_offsets']) for x in spans} if all('allowed_split_offsets' in x for x in spans) else None
            parse_decisions(response['content'],len(spans),payload['categories'],lengths,texts,cuts)
            validation.append({'attempt':number,'status':'valid_current_contract'})
        except ReviewError as exc:
            validation.append({'attempt':number,'status':'invalid_current_contract','error':str(exc),
                               'kinds':sorted({x.get('kind','unknown') for x in getattr(exc,'details',[])})})
        except (KeyError, ValueError, TypeError) as exc:
            validation.append({'attempt':number,'status':'unverifiable_pair_format','error':type(exc).__name__})
    scope=mapped.meta['document_scope']; outscope=scope['candidate_resume'] is False
    missing=mapped.meta['missing_required_fields']
    duplicate_candidates=sum(e.text==v.text and len(e.text.split())>=25 for i,e in enumerate(elements) for v in elements[:i])
    flags=[]
    if row['llm_review'].get('status')!='complete':flags.append('provider_review_not_complete')
    if outscope:flags.append('non_resume')
    if accounting['unresolved_meaningful_spans'] and not outscope:flags.append('meaningful_candidate_text_unassigned')
    if missing and not outscope:flags.append('schema_required_fields_incomplete')
    if any(v['entries_needing_review'] or v['unlinked_blocks'] for v in relation_flags.values()) and not outscope:flags.append('relationship_diagnostics')
    if independent['unmatched_terms'] or independent['empty']:flags.append('independent_pdf_text_check_required')
    if duplicate_candidates:flags.append('repeated_passage_source_check_required')
    fidelity=quality['source_fidelity']
    if fidelity['ocr_reference_needed'] or fidelity['damaged_glyph_elements']:flags.append('ocr_or_glyph_source_review_required')
    record_counts={c:len(getattr(mapped.data,c)) for c in ('experience','education','projects','certifications')}
    oldschema=ROOT/'reports/schema-mapping-integration-20261022/mapped-documents-final'/(digest+'.json')
    olddata_matches=oldschema.exists() and read(oldschema)['data']==mapped.model_dump(mode='json')['data']
    rows.append({'file':info['file'],'sha256':digest,'selected_live_run':d.name,
        'artifact':str(artifact_path.relative_to(ROOT)),'original_pdf_hash_match':pdf_hash_match,
        'local_source_hash_matches_manifest':lr['sha256']==digest,
        'local_review_binding':artifact['extraction']==local['extraction'] and artifact['local_sections']==local['sections'],
        'prior_schema_index_artifact_hash_matches':sha(artifact_path)==old_index[digest]['artifact_sha256'],
        'interval_errors':errors,'all_extracted_source_preserved':accounting['all_source_text_preserved'],
        'historical_status':row['status'],'provider_state':row['llm_review'].get('status'),
        'provider_error':row['llm_review'].get('error_code'),'recorded_calls':row['api_calls'],
        'recorded_tokens':row.get('usage',{}),'saved_response_attempts':len(decisions),
        'available_request_pairs':requests,'request_source_mismatches':request_source_mismatch,
        'pair_validation':validation,'schema_valid':True,'schema_data_matches_previous_check':olddata_matches,
        'schema_field_evidence_ids_valid':evidence_valid,'schema_provider_calls':mapped.meta['provider_calls'],
        'missing_required_fields':missing,'document_scope':scope,'record_counts':record_counts,
        'relationship_diagnostics':relation_flags,'meaningful_unassigned':accounting['unresolved_meaningful_spans'],
        'local_meaningful_unassigned':account_source(elements,before)['unresolved_meaningful_spans'],
        'raw_unassigned':len(sections.needs_review),'unmapped_blocks':len(mapped.meta['unmapped_blocks']),
        'independent_pdf_text':independent,'duplicate_passage_candidates':duplicate_candidates,
        'source_fidelity':fidelity,'flags':flags,'semantic_accuracy_verified':False})
    fingerprints.append({'sha256':digest,'file':info['file'],'artifact_sha256':sha(artifact_path)})

save('per-resume.json',rows);save('batch-provenance.json',run_rows);save('source-index.json',fingerprints)
summary={'unique_pdf_hashes':len(rows),'original_pdf_hash_matches':sum(r['original_pdf_hash_match'] for r in rows),
 'local_review_bindings':sum(r['local_review_binding'] for r in rows),
 'interval_checks_passed':sum(not r['interval_errors'] for r in rows),
 'schema_contract_passed':sum(r['schema_valid'] for r in rows),
 'schema_evidence_id_checks_passed':sum(r['schema_field_evidence_ids_valid'] for r in rows),
 'prior_schema_data_matches':sum(r['schema_data_matches_previous_check'] for r in rows),
 'latest_live_statuses':dict(Counter(r['historical_status'] for r in rows)),
 'latest_live_provider_states':dict(Counter(r['provider_state'] for r in rows)),
 'scope_kinds':dict(Counter(r['document_scope']['kind'] for r in rows)),
 'candidate_or_unknown_documents':sum(r['document_scope']['candidate_resume'] is not False for r in rows),
 'documents_with_missing_fields_all':sum(bool(r['missing_required_fields']) for r in rows),
 'candidate_documents_missing_fields':sum(bool(r['missing_required_fields']) and r['document_scope']['candidate_resume'] is not False for r in rows),
 'missing_required_field_instances':sum(len(r['missing_required_fields']) for r in rows),
 'meaningful_unassigned_all':sum(r['meaningful_unassigned'] for r in rows),
 'candidate_meaningful_unassigned':sum(r['meaningful_unassigned'] for r in rows if r['document_scope']['candidate_resume'] is not False),
 'local_meaningful_unassigned':sum(r['local_meaningful_unassigned'] for r in rows),
 'flags':dict(Counter(f for r in rows for f in r['flags'])),
 'saved_response_attempts_latest_scope':sum(r['saved_response_attempts'] for r in rows),
 'available_request_pairs_latest_scope':sum(r['available_request_pairs'] for r in rows),
 'pair_validation':dict(Counter(v['status'] for r in rows for v in r['pair_validation'])),
 'recorded_calls_latest_scope':sum(r['recorded_calls'] for r in rows),
 'new_llm_calls':0,'source_or_pipeline_reexecuted':False,'semantic_accuracy_established':False}
summary['recorded_tokens_latest_scope']={k:sum(r['recorded_tokens'].get(k,0) for r in rows) for k in ('prompt_tokens','completion_tokens','total_tokens')}
summary['relationships']={cat:{'documents_with_review_entries':sum(r['relationship_diagnostics'].get(cat,{}).get('entries_needing_review',0)>0 for r in rows if r['document_scope']['candidate_resume'] is not False),
 'documents_with_unlinked_blocks':sum(r['relationship_diagnostics'].get(cat,{}).get('unlinked_blocks',0)>0 for r in rows if r['document_scope']['candidate_resume'] is not False),
 'unlinked_blocks':sum(r['relationship_diagnostics'].get(cat,{}).get('unlinked_blocks',0) for r in rows if r['document_scope']['candidate_resume'] is not False)} for cat in ('experience','education')}
save('summary.json',summary)
changed=[p for p,h in tracked.items() if sha(ROOT/p)!=h]
save('preservation.json',{'files_checked':len(tracked),'changed':changed,'hashes':tracked})
with (OUT/'per-resume.csv').open('w',newline='') as stream:
 fields=['file','sha256','selected_live_run','historical_status','provider_state','original_pdf_hash_match','local_review_binding','schema_valid','meaningful_unassigned','missing_required_fields','flags']
 writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
 for row in rows: writer.writerow({k:json.dumps(row[k]) if isinstance(row[k],list) else row[k] for k in fields})
print(json.dumps(summary,indent=2))
