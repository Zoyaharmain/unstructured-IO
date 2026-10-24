"""Evaluate a completed frozen run, distinguishing partial labels from diagnostics."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def evaluate(manifest,results):
 from local_api.schemas.sections import SectionResponse
 from local_api.schemas.mapping import SchemaMappingResponse
 from local_api.schemas.extraction import ExtractedElement
 from local_api.services.subschema_validation import validate_hierarchy,query_subschemas
 from local_api.services.source_validation import validate_result
 from local_api.services.source_accounting import account_source
 traces=load(results/'stage-traces.json') if (results/'stage-traces.json').exists() else []
 per=[];accounts=[];fields=[];queries=[]
 for selected in manifest['selected']:
  folder=results/f"{selected['index']:02d}";row={'file':selected['file'],'sha256':selected['sha256'],'status':'not_completed'}
  try:
   extraction=load(folder/'extraction.json');raw=load(folder/'sections.json');mapped=load(folder/'schema.json')
   sections=SectionResponse.model_validate(raw);SchemaMappingResponse.model_validate(mapped)
   elements=[ExtractedElement.model_validate(e) for e in extraction['elements']]
   errors=validate_result(elements,sections)
   if errors:raise ValueError('Source interval errors: '+str(errors))
   parsed=validate_hierarchy(mapped['section_schemas'],sections);final=account_source(elements,sections)
   history=load(folder/'pipeline.json');initial=[t for t in traces if t['document_id']==selected['document_id'] and t['stage']=='initial_detection']
   recoveries=[t for t in traces if t['document_id']==selected['document_id'] and t['stage']=='local_recovery_invocation']
   owncalls=[c for c in load(results/'calls.json') if c['document_id']==selected['document_id']]
   accounts.append({'file':selected['file'],'original_extracted_elements':len(elements),'initial_detection':initial[0]['after'] if initial else None,'local_recovery_invocations':recoveries,'feedback_passes':history['passes'],'stop_reason':history['stop_reason'],'final_source_accounting':final,'llm_requests':len(owncalls),'all_span_source_conservation_passed':True,'semantic_reassignment_errors':None,'semantic_reassignment_reason':'No complete human ownership labels; counts alone cannot prove assignment correctness.','counting_policy':'Elements are extraction blocks; assigned/unresolved/reprocessed quantities are source intervals, which may split; retain offsets in trace, never subtract different span inventories as a recovery score.'})
   queries.append({'file':selected['file'],'queries':{q:query_subschemas(parsed,q) for q in ['experience.role','skills.technical_skills','education.degree','certifications.name']},'candidate_search':False,'precision':None,'recall':None})
   row.update(status='validated_output',source_interval_validation='passed',hierarchy_citation_validation='passed',source_accounting=final,stop_reason=history['stop_reason'],semantic_accuracy=None)
   if selected['human_field_reference']:
    ref=load(ROOT/selected['human_field_reference']);allrecords=[(s.category,r) for s in parsed for r in s.records]
    def values(r,name):return [i.value for a in r.attributes if a.name==name for i in a.items]
    def sourcequotes(r):
     inventory={f'e{b.source_element_index}:{b.start}:{b.end}':b.text for s in sections.sections for b in s.blocks}
     return '\n'.join(inventory.get(sid,'') for sid in r.source_ids)
    for f in ref['verified_fields']:
     parent=f['parent_section'];sel=f['record_selector'];candidates=[r for p,r in allrecords if p==parent]
     if sel['kind']=='record_id':candidates=[r for r in candidates if r.record_id==sel['value']]
     elif sel['kind']=='attribute':candidates=[r for r in candidates if values(r,sel['attribute'])==[sel['value']]]
     elif sel['kind']!='singleton':raise ValueError('Unsupported reference selector')
     anchor_fields=[anchor for anchor in ref['verified_fields'] if anchor['parent_section']==parent and anchor['record_selector']==sel and anchor['attribute']=='company'] if parent=='experience' else []
     anchor_mismatch=bool(len(candidates)==1 and anchor_fields and values(candidates[0],'company')!=anchor_fields[0]['expected_values'])
     actual=values(candidates[0],f['attribute']) if len(candidates)==1 else []
     expected=f['expected_values'];status='ambiguous' if len(candidates)>1 else 'exact_match' if len(candidates)==1 and actual==expected else 'missing' if not actual else 'incorrect'
     if anchor_mismatch:status='incorrect_record_association'
     # Record IDs depend on segmentation. A changed record ID is diagnostic, not a silently rematched approval.
     elsewhere=[{'parent':p,'record_id':r.record_id} for p,r in allrecords if r not in candidates and values(r,f['attribute'])==expected]
     if status in {'missing','incorrect'} and elsewhere:status='incorrect_record_association' if any(x['parent']==parent for x in elsewhere) else 'incorrect_parent'
     fields.append({'file':selected['file'],'field_id':f['field_id'],'record_selector':sel,'verification_basis':f['verification_basis'],'expected':expected,'actual':actual,'classification':status,'elsewhere':elsewhere,'scope':'Exact supplied selector/value comparison; record IDs may change on fresh segmentation. Treat changed ownership as manual-review diagnostic, not silently aligned truth.'})
  except Exception as exc:row.update(status='failed_or_incomplete',error_type=type(exc).__name__,error=str(exc))
  per.append(row)
 save(results/'per-resume-results.json',per);save(results/'reprocessing-accounting.json',accounts)
 save(results/'main-section-evaluation.json',{'scorable_documents':0,'precision':None,'recall':None,'f1':None,'reason':'Selected ten have no complete source-bound ownership labels. Separate 15-document labels are not field references or transferable to fresh unbound extractions.'})
 buckets={}
 for basis in sorted({r['verification_basis'] for r in fields}):
  rows=[r for r in fields if r['verification_basis']==basis];n=len(rows);correct=sum(r['classification']=='exact_match' for r in rows)
  buckets[basis]={'reviewed_denominator':n,'exact_matches':correct,'exact_match_rate':correct/n if n else None,'precision':None,'recall':None,'f1':None}
 save(results/'sub-schema-evaluation.json',{'partial_reference_results':fields,'by_provenance':buckets,'precision':None,'recall':None,'f1':None,'reason':'Partial positive expected fields do not enumerate negatives or all missing fields; uncertain A069 and unreviewed fields excluded. No whole-document or population accuracy.','record_association_limits':'Supplied record selectors are compared exactly; changed record IDs require manual adjudication.'})
 save(results/'search-evaluation.json',{'scope':'Existing per-resume field lookup only','candidate_search_implemented':False,'results':queries,'precision':None,'recall':None})
 summary=load(results/'execution-summary.json');save(results/'provider-usage.json',{'actual_requests':summary['provider_requests'],'usage':summary['usage'],'elapsed_run_seconds':summary['seconds'],'calls':load(results/'calls.json'),'cost_usd':None,'reason':'No verified current tariff or billed amount assumed'})
 save(results/'run-manifest.json',{'status':'execution_finished_requires_review','selected':manifest['document_count'],'completed_outputs':sum(r['status']=='validated_output' for r in per),'production_mapping_modified':False})
 (results/'final-readiness-assessment.md').write_text('# Readiness after controlled execution\n\nNO-GO for production scaling on this sample alone. See per-resume validation, partial reference results split by provenance, unresolved recovery traces and provider usage. Cross-candidate search is absent; full semantic section/record labels are missing. Automated validity is not semantic certification. Preserve failures and obtain manual adjudication before expanding.\n')
 save(results/'created-files.json',[str(p.relative_to(results)) for p in results.rglob('*') if p.is_file()])
