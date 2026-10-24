"""Read-only audit preparation and explicit review import. No provider/extraction calls."""
import csv, hashlib, importlib.util, json, sys
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
CORPUS=ROOT/'reports/hierarchical-schema-all1541-20261023'
V4=ROOT/'ground_truth/field_level/v4';V5=ROOT/'ground_truth/field_level/v5'
DECISION=Path('/mnt/c/Users/Gopi Gedar/Downloads/group-02-employment-v4-reviewed-2026-10-24T11-42-09.774Z.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def load(p):return json.loads(p.read_text())
def main():
 if V5.exists() or (OUT/'selection-manifest.json').exists():raise ValueError('Existing reference/output must not be overwritten')
 protected={}
 for folder in [ROOT/'ground_truth',ROOT/'reports',ROOT/'local_api',ROOT/'scripts',ROOT/'tests/fixtures']:
  for p in folder.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and OUT not in p.parents:protected[str(p)]=sha(p)
 protected[str(DECISION)]=sha(DECISION)
 save(OUT/'preservation-before.json',protected)
 refs={p.stem:load(p) for p in V4.glob('*.json')}
 spec=importlib.util.spec_from_file_location('review_import',ROOT/'reports/manual-field-review-group01-import-20261024-v3/import_group.py');imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)
 from local_api.schemas.subschema_spec import SUBSCHEMAS
 from local_api.schemas.sections import SectionResponse
 from local_api.schemas.extraction import ExtractedElement
 from local_api.services.source_validation import validate_result
 from local_api.services.subschema_validation import validate_hierarchy
 group=load(ROOT/'reports/manual-field-review-employment-20261024-v4/group-02.json')['rows']
 payload=load(DECISION)
 if payload['review_group']!='group-02' or payload['review_session']!='manual-field-review-employment-20261024-v4':raise ValueError('Wrong group/session')
 if any(d.get('review_session')!=payload['review_session'] for d in payload['decisions']):raise ValueError('Wrong row session')
 inventories={};bindings={};schemas={}
 for doc,ref in refs.items():
  sec=ROOT/ref['latest_prediction_path'];sec=sec.with_name('sections.json');ext=ROOT/f"reports/hierarchical-deepseek-five-20261023-225341/results/{ref['selection_index']:02d}/extraction.json"
  sections=SectionResponse.model_validate(load(sec));elements=[ExtractedElement.model_validate(e) for e in load(ext)['elements']]
  assert not validate_result(elements,sections)
  inventories[doc]={f'e{b.source_element_index}:{b.start}:{b.end}':b.text for b in [b for s in sections.sections for b in s.blocks]+sections.needs_review}
  pred=ROOT/ref['latest_prediction_path'];schemas[doc]=load(pred);validate_hierarchy(schemas[doc]['section_schemas'],sections)
  bindings[doc]={'extraction':str(ext.relative_to(ROOT)),'extraction_sha256':sha(ext),'sections':str(sec.relative_to(ROOT)),'sections_sha256':sha(sec),'prediction':str(pred.relative_to(ROOT)),'prediction_sha256':sha(pred)}
 # Reuse strict prior validator after independently checking actual group/session above.
 validation_payload=deepcopy(payload);validation_payload['review_group']='group-01'
 accepted,uncertain,pending=imp.validate_payload(validation_payload,group,inventories,SUBSCHEMAS)
 audit=[]
 for d in accepted:
  records=[r for s in schemas[d['document_key']]['section_schemas'] if s['category']==d['expected_parent_section'] for r in s['records'] if r['record_id']==d['expected_record_association']['value']]
  assert len(records)==1 and all(q['source_id'] in records[0]['source_ids'] for q in d['reviewer_source_evidence'])
  actual=[a for a in records[0]['attributes'] if a['name']==d['attribute']];assert len(actual)==1
  assert [i['value'] for i in actual[0]['items']]==d['expected_values']
  audit.append(dict(d,validation_status='accepted',reason='Explicit decision; exact source quote, expected value, field, parent and record-local association validated.'))
 (OUT/'received-group-02.json').write_bytes(DECISION.read_bytes())
 save(OUT/'group02-validation.json',{'reviewer_names':sorted({d['reviewer'] for d in payload['decisions']}),'accepted':audit,'rejected':[],'uncertain':uncertain,'pending':pending,'original_pdf_visually_rechecked':False,'decision_sha256':sha(DECISION),'bindings':bindings})
 V5.mkdir();(V5/'uncertainty').mkdir()
 save(V5/'uncertainty/group02.json',{'decisions':uncertain,'decision_file':str((OUT/'received-group-02.json').relative_to(ROOT)),'sha256':sha(DECISION),'not_accuracy_labels':True})
 for doc,ref in refs.items():
  new=deepcopy(ref);new['reference_version']='v5';new['derived_from']={'path':str((V4/(doc+'.json')).relative_to(ROOT)),'sha256':sha(V4/(doc+'.json'))}
  for d in accepted:
   if d['document_key']!=doc:continue
   assert not any(f.get('decision_row_id')==d['row_id'] for f in new['verified_fields'])
   new['verified_fields'].append({'field_id':d['expected_parent_section']+'.'+d['attribute'],'parent_section':d['expected_parent_section'],'attribute':d['attribute'],'expected_values':d['expected_values'],'record_selector':d['expected_record_association'],'source_evidence':d['reviewer_source_evidence'],'verification_basis':'explicit_saved_group02_reviewer_decision','review_decision':d['review_status'],'reviewer':d['reviewer'],'reviewed_at':d['reviewed_at'],'reviewer_notes':d['reviewer_notes'],'decision_row_id':d['row_id'],'decision_file':str((OUT/'received-group-02.json').relative_to(ROOT)),'decision_file_sha256':sha(DECISION),'source_binding':bindings[doc],'reviewer_identity_status':'self_declared; not independently authenticated','original_pdf_rechecked_by_importer':False})
  new['review_session']={'status':'group02_imported_partial_review','full_document_manual_signoff':False,'pending_rows_unreviewed':218,'ambiguous_rows':1}
  save(V5/(doc+'.json'),new)
 (V5/'README.md').write_text('# Field references v5\n\nGroup 02: five explicit employment header decisions by reviewer `manjunath-muruga` accepted for Aditya (company, role, start_date, end_date, duration). Location A069 remains ambiguous, preserved verbatim under uncertainty/ and excluded from scoring. Earlier 12 labels and provenance remain unchanged: six Group 01 decisions and six prior Manjunath expectations. Total 17 partial expected fields (Aditya 8, Manjunath 9), not whole-resume approval. 218 other worksheet rows remain pending. Quotes checked against frozen blocks and record ownership, not a fresh visual PDF review. Previous versions remain unchanged.\n')
 # Conservatively exclude prior selected documents, including selections never called.
 history=[];excluded_hashes=set();excluded_names=set()
 history_paths=set(ROOT.glob('reports/**/manifest.json'))|set(ROOT.glob('reports/**/selection.json'))|set(ROOT.glob('reports/**/selection-manifest.json'))
 for p in sorted(history_paths):
  if OUT in p.parents:continue
  data=load(p)
  rows=data if isinstance(data,list) else data.get('selected',[]) if isinstance(data,dict) else []
  if not isinstance(rows,list):continue
  entries=[r for r in rows if isinstance(r,dict) and isinstance(r.get('sha256'),str) and len(r['sha256'])==64 and r.get('file')]
  if entries:
   history.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'entries':len(entries),'history_type':'prior_frozen_selection_not_proof_every_call_completed'})
   excluded_hashes.update(r['sha256'] for r in entries);excluded_names.update(r['file'].casefold() for r in entries)
 # Join full350 actual ledger indices to its source manifest; do not conflate local1541 with paid runs.
 fullmanifest=load(ROOT/'reports/deepseek-schema-full350-20261022/manifest.json');ledger=load(ROOT/'reports/deepseek-schema-full350-20261022/call-ledger.json')
 if isinstance(ledger,dict):ledger=ledger.get('calls',[])
 paid_indices={r.get('index') for r in ledger if isinstance(r,dict)}
 paid_full_hashes={r['sha256'] for r in fullmanifest if r['index'] in paid_indices}
 save(OUT/'prior-history.json',{'selection_sources':history,'conservative_excluded_hashes':sorted(excluded_hashes),'conservative_excluded_names':sorted(excluded_names),'full350_ledger':{'path':'reports/deepseek-schema-full350-20261022/call-ledger.json','sha256':sha(ROOT/'reports/deepseek-schema-full350-20261022/call-ledger.json'),'entries':len(ledger),'joined_document_hashes':sorted(paid_full_hashes)},'policy':'Eight generalization resumes excluded by union of prior selection hashes AND case-insensitive filenames, stricter than only confirmed calls. Two reviewed development controls are explicit reuse.'})
 corpus=load(CORPUS/'final-per-resume.json');pool=[];byname={r['file']:r for r in corpus}
 def describe(row,development=False):
  p=Path(row['source']);digest=sha(p)
  if digest!=row['sha256']:raise ValueError('Original hash differs from inventory')
  sp=CORPUS/row['source_artifact'];mp=CORPUS/row['mapping_artifact'];src=load(sp);mapping=load(mp)
  elements=src['extraction']['elements'];pages=sorted({e.get('page_number') or e.get('metadata',{}).get('page_number') for e in elements if e.get('page_number') or e.get('metadata',{}).get('page_number')})
  parents={s['category']:len(s['records']) for s in mapping['section_schemas']}
  text=' '.join(e['text'] for e in elements);normalized=''.join(text.casefold().split())
  geometry=any(e.get('metadata',{}).get('coordinates') for e in elements)
  return {'file':row['file'],'document_id':digest[:20],'sha256':digest,'source_path':str(p),'bytes':p.stat().st_size,'baseline_source':str(sp.relative_to(ROOT)),'baseline_source_sha256':sha(sp),'baseline_mapping':str(mp.relative_to(ROOT)),'baseline_mapping_sha256':sha(mp),'page_numbers':pages,'source_elements':len(elements),'characters':len(text),'saved_coordinate_metadata_present':geometry,'record_counts':parents,'normalized_text_sha256':hashlib.sha256(normalized.encode()).hexdigest(),'unresolved_source_blocks':row.get('unresolved_source_blocks'),'prior_local_mapping':True,'prior_llm_selection_hash_match':digest in excluded_hashes,'prior_llm_selection_name_match':row['file'].casefold() in excluded_names,'prior_full350_ledger_match':digest in paid_full_hashes,'development_control':development,'human_field_reference':'ground_truth/field_level/v5/'+('aditya-vashisth' if 'Aditya vashisth'==p.stem else 'manjunath-murugan')+'.json' if development else None}
 selected=[describe(byname[n],True) for n in ['Aditya vashisth.pdf','_ManjunathMurugan.pdf']]
 for row in corpus:
  if row.get('extension')!='.pdf' or row.get('candidate_resume') is not True or not row.get('source_artifact'):continue
  if row['sha256'] in excluded_hashes or row['file'].casefold() in excluded_names or row['file'].casefold()=='jewel bijoy.pdf':continue
  if not Path(row['source']).is_file():continue
  pool.append(row)
 # Deterministic representative spread using saved output complexity; no new extraction.
 described=[describe(r) for r in pool];used={r['normalized_text_sha256'] for r in selected};usedhash={r['sha256'] for r in selected}
 strategies=[('short resume',lambda r:-abs(len(r['page_numbers'])-1)),('long employment history',lambda r:r['record_counts'].get('experience',0)),('multiple education records',lambda r:r['record_counts'].get('education',0)),('project-rich resume',lambda r:r['record_counts'].get('projects',0)),('certification-rich resume',lambda r:r['record_counts'].get('certifications',0)),('unresolved/fragmented diagnostic case',lambda r:r['unresolved_source_blocks'] or 0),('long document',lambda r:len(r['page_numbers'])),('compact multi-section resume',lambda r:len(r['record_counts'])-abs(len(r['page_numbers'])-2))]
 for reason,key in strategies:
  eligible=[r for r in described if r['sha256'] not in usedhash and r['normalized_text_sha256'] not in used and r['characters']<40000]
  if not eligible:raise ValueError('Insufficient unseen distinct documents')
  row=sorted(eligible,key=lambda r:(-key(r),r['file']))[0];row['selection_rationale']=reason+'; provisional saved-output feature, not an accuracy label';selected.append(row);usedhash.add(row['sha256']);used.add(row['normalized_text_sha256'])
 for i,row in enumerate(selected,1):
  row['index']=i
  if row['development_control']:row['selection_rationale']='Explicitly requested reviewed development control; intentional prior LLM reuse, not generalization evidence'
  protected[row['source_path']]=row['sha256']
 assert len(selected)==10 and len(usedhash)==10 and len(used)==10
 for row in selected[:2]:
  ref=refs['aditya-vashisth' if row['index']==1 else 'manjunath-murugan'];assert ref['source_sha256']==row['sha256']
 from scripts.check_pilot_fallback import load_provider_env
 from local_api.services.llm_section_review import ReviewSettings
 load_provider_env(ROOT/'.env');config=ReviewSettings.from_env();config.validate()
 provider={k:getattr(config,k) for k in ['enabled','model','base_url','thinking','timeout','max_units','max_input_chars','max_tokens']};provider['key_present']=bool(config.api_key);provider['credential_validity']='not tested: no provider request before confirmation'
 code={str(p.relative_to(ROOT)):sha(p) for folder in ['local_api','scripts'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 manifest={'status':'frozen_awaiting_user_confirmation','document_count':10,'selected':selected,'generalization_count':8,'development_control_count':2,'history_sources':history,'provider':provider,'provider_budget':{'recovery_attempts':1,'expected_requests':20,'maximum_requests':40,'maximum_per_document':4,'stages':['section_review_all_spans','schema_audit_advisory'],'field_mapping':'local deterministic mapper; no separate provider field mapping','price':None,'price_reason':'No verified current tariff; no cost estimate invented'},'code_sha256':code,'execution':{'runner':str((OUT/'run_ten.py').relative_to(ROOT)),'results_directory':str((OUT/'execution').relative_to(ROOT)),'strategy':'auto','recovery_attempts':1},'human_reference_version':'v5'}
 save(OUT/'selection-manifest.json',manifest);save(OUT/'preservation-before.json',protected)
 save(OUT/'provider-usage.json',{'phase':'preflight','actual_requests':0,'tokens':0,'latency_seconds':0,'cost':None,'planned_budget':manifest['provider_budget'],'configuration':provider})
 save(OUT/'run-manifest.json',{'status':'awaiting_confirmation_before_provider_execution','production_mapping_modified':False,'document_pipeline_runs':0,'extraction_runs':0,'selection_manifest_sha256':sha(OUT/'selection-manifest.json'),'created_reference':'ground_truth/field_level/v5','api_calls':0})
 print(json.dumps({'selected':[(r['index'],r['file'],r['page_numbers'],r['record_counts']) for r in selected],'provider':provider,'accepted_group02':len(accepted),'uncertain_group02':len(uncertain)},indent=2))
if __name__=='__main__':main()
