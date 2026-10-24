"""Compare ten frozen inventories and partial references; do not infer accuracy."""
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent;RUN=ROOT/'reports/end-to-end10-preflight-20261024/execution'
from local_api.schemas.sections import SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.source_accounting import account_source
from local_api.services.subschema_validation import validate_hierarchy,build_field_index

def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def delta(b,a,path=''):
 if type(b)!=type(a):return [{'path':path,'before':b,'after':a}]
 if isinstance(b,dict):return [d for k in sorted(b.keys()|a.keys()) for d in (delta(b[k],a[k],path+'/'+k) if k in b and k in a else [{'path':path+'/'+k,'before':b.get(k),'after':a.get(k)}])]
 if isinstance(b,list):
  if len(b)!=len(a):return [{'path':path,'before':b,'after':a,'note':'Array length changed; subsequent positional evidence/pointers shift.'}]
  return [d for i,(x,y) in enumerate(zip(b,a)) for d in delta(x,y,path+'/'+str(i))]
 return [] if b==a else [{'path':path,'before':b,'after':a}]
def membership(sec):return [(s.category,[(e.entry_id,e.block_indices) for e in s.entries]) for s in sec.sections]
def blocks(sec):return [(s.category,[(b.source_element_index,b.start,b.end,b.text) for b in s.blocks]) for s in sec.sections],[(b.source_element_index,b.start,b.end,b.text) for b in sec.needs_review]
def records(schema):return [(s['category'],[(r['record_id'],r['source_ids']) for r in s['records']]) for s in schema['section_schemas']]
def items(schema):return Counter(json.dumps([s['category'],r['record_id'],a['name'],i],sort_keys=True,ensure_ascii=False) for s in schema['section_schemas'] for r in s['records'] for a in r['attributes'] for i in a['items'])
def residual(schema):return [(s['category'],q['source_id'],q['quote']) for s in schema['section_schemas'] for q in s['residual_blocks']]
def evaluate(ref,schema):
 result=[]
 for f in ref['verified_fields']:
  candidates=[r for s in schema['section_schemas'] if s['category']==f['parent_section'] for r in s['records']];sel=f['record_selector']
  def values(r,name):return [i['value'] for a in r['attributes'] if a['name']==name for i in a['items']]
  if sel['kind']=='record_id':candidates=[r for r in candidates if r['record_id']==sel['value']]
  elif sel['kind']=='attribute':candidates=[r for r in candidates if values(r,sel['attribute'])==[sel['value']]]
  elif sel['kind']!='singleton':raise ValueError('Unknown reference selector')
  actual=values(candidates[0],f['attribute']) if len(candidates)==1 else []
  result.append({'field_id':f['field_id'],'record_selector':sel,'provenance':f['verification_basis'],'expected_values':f['expected_values'],'actual_values':actual,'status':'exact_match' if len(candidates)==1 and actual==f['expected_values'] else 'requires_review'})
 return result

def main():
 docs=[];refs=[]
 for row in load(RUN.parent/'selection-manifest.json')['selected']:
  i=row['index'];b=load(OUT/f'before/{i:02d}/schema.json');a=load(OUT/f'after/{i:02d}/schema.json');frozen=load(RUN/f'{i:02d}/schema.json')
  assert b==frozen,'Pre-fix replay drifted from frozen baseline'
  bs=SectionResponse.model_validate(load(OUT/f'before/{i:02d}/sections.json'));as_=SectionResponse.model_validate(load(OUT/f'after/{i:02d}/sections.json'));fs=SectionResponse.model_validate(load(RUN/f'{i:02d}/sections.json'))
  elements=[ExtractedElement.model_validate(e) for e in load(RUN/f'{i:02d}/extraction.json')['elements']]
  assert membership(bs)==membership(as_)==membership(fs)
  assert records(b)==records(a)
  assert blocks(bs)==blocks(as_)==blocks(fs)
  ba=account_source(elements,bs);aa=account_source(elements,as_);assert ba==aa
  parsed=validate_hierarchy(a['section_schemas'],as_);assert a['field_index']==build_field_index(parsed)
  added=list((items(a)-items(b)).elements());removed=list((items(b)-items(a)).elements());rdremoved=[r for r in residual(b) if r not in residual(a)];rdadded=[r for r in residual(a) if r not in residual(b)]
  allchanges=delta(b,a)
  if allchanges:
   assert i==2 and not removed and len(added)==1 and not rdadded and len(rdremoved)==1
   new=json.loads(added[0]);assert new[:3]==['experience','experience-2','responsibilities']
   assert new[3]['value']=='delivering high-integrity data feeds to downstream Fund accounting systems.'
   assert new[3]['evidence']==[{'source_id':'e24:0:75','quote':new[3]['value']}]
   assert rdremoved[0][1]=='e24:0:75'
  docs.append({'index':i,'file':row['file'],'pre_fix_replay_equals_frozen_baseline':b==frozen,'schema_changed':bool(allchanges),'legacy_data_differences':delta(b['data'],a['data']),'all_schema_differences':allchanges,'populated_nested_items_before':sum(items(b).values()),'populated_nested_items_after':sum(items(a).values()),'nested_items_added':[json.loads(x) for x in added],'nested_items_removed':[json.loads(x) for x in removed],'residual_blocks_before':len(residual(b)),'residual_blocks_after':len(residual(a)),'residual_removed':rdremoved,'residual_added':rdadded,'section_entry_field_evidence_changes':delta(bs.model_dump(mode='json'),as_.model_dump(mode='json')),'record_membership_unchanged':True,'parent_sections_and_source_intervals_unchanged':True,'legacy_and_nested_responsibility_change_agree':not allchanges or a['data']['experience'][1]['responsibilities']==[i['value'] for s in a['section_schemas'] if s['category']=='experience' for r in s['records'] if r['record_id']=='experience-2' for attr in r['attributes'] if attr['name']=='responsibilities' for i in attr['items']],'field_index_equals_canonical_hierarchy':True,'source_accounting_before':{k:v for k,v in ba.items() if k!='outcomes'},'source_accounting_after':{k:v for k,v in aa.items() if k!='outcomes'},'explanation':'D1 moves e24 from generic employer evidence to responsibilities inside the same BNP record. One literal item is added in both legacy and nested output with its own quote; its residual is consumed, and subsequent list evidence and JSON pointers shift by one. No employer, role, date or record boundary changes.' if allchanges else 'No schema-output change. D3 affects feedback progress detection, not these fixed-inventory mapper outputs.'})
  if i in [1,2]:
   ref=load(ROOT/'ground_truth/field_level/v5'/('aditya-vashisth.json' if i==1 else 'manjunath-murugan.json'))
   br=evaluate(ref,b);ar=evaluate(ref,a);assert br==ar and all(r['status']=='exact_match' for r in ar)
   refs.append({'file':row['file'],'before':br,'after':ar})
 byprov={}
 for r in refs:
  for field in r['after']:
   c=byprov.setdefault(field['provenance'],{'denominator':0,'exact_before':0,'exact_after':0});c['denominator']+=1;c['exact_before']+=1;c['exact_after']+=1
 result={'scope':'Pure field annotation plus mapping replay on deep copies of ten frozen final extraction/section inventories. No extraction/detection/embeddings/provider execution. Existing record membership is never rebuilt.','documents':docs,'partial_references':refs,'reference_matches_by_provenance':byprov,'precision':None,'recall':None,'f1':None,'overall_semantic_accuracy':None,'scope_limits':'17 partial expected tuples only, including six prior expectations with narrower provenance. Pending rows and ambiguous A069 are excluded. No new human labels. Source coverage/citation validity alone is not accuracy.','changed_documents':sum(d['schema_changed'] for d in docs),'unchanged_documents':sum(not d['schema_changed'] for d in docs),'provider_calls':0,'production_changes':['local_api/services/record_relationships.py','scripts/single_resume_pipeline.py']}
 save(OUT/'before-after-comparison.json',result)
 print(json.dumps({'changed':result['changed_documents'],'unchanged':result['unchanged_documents'],'references':byprov},indent=2))
if __name__=='__main__':main()
