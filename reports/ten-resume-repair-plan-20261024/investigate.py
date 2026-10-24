"""Offline saved-artifact investigation. Never extracts, maps, or calls a provider."""
import ast,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=Path(__file__).parent;RUN=ROOT/'reports/end-to-end10-preflight-20261024/execution'
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 from local_api.schemas.sections import SectionResponse
 from local_api.schemas.extraction import ExtractedElement
 from local_api.services.llm_section_review import make_messages,source_ledger
 from local_api.services.resume_sections import ANCHORS
 from local_api.services.source_validation import validate_result
 from local_api.services.source_accounting import account_source
 from local_api.services.subschema_validation import validate_hierarchy
 if (OUT/'investigation.json').exists():raise ValueError('Refuse to overwrite report')
 protected={}
 for folder in [ROOT/'ground_truth',ROOT/'reports',ROOT/'local_api',ROOT/'scripts',ROOT/'tests/fixtures']:
  for p in folder.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and OUT not in p.parents:protected[str(p)]=sha(p)
 selection=load(RUN.parent/'selection-manifest.json')
 for row in selection['selected']:protected[row['source_path']]=sha(Path(row['source_path']))
 save(OUT/'preservation-before.json',protected)
 system=next(n.value for n in ast.walk(ast.parse((ROOT/'scripts/check_single_resume.py').read_text())) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('Audit resume schema against source text.'))
 limits=selection['provider'];stats=[];evidence={};checks=[]
 for row in selection['selected']:
  d=RUN/f"{row['index']:02d}";raw=load(d/'extraction.json');els=[ExtractedElement.model_validate(e) for e in raw['elements']]
  local=SectionResponse.model_validate(load(d/'local-sections.json'));ledger=source_ledger(local)
  messages=make_messages(ledger,{k:v['label'] for k,v in ANCHORS.items()},els,local.sections)
  schema=load(d/'schema.json');final=SectionResponse.model_validate(load(d/'sections.json'));pipe=load(d/'pipeline.json')
  inventory={f'e{b.source_element_index}:{b.start}:{b.end}':b.text for s in final.sections for b in s.blocks};inventory.update({f'e{b.source_element_index}:{b.start}:{b.end}':b.text for b in final.needs_review})
  audit_messages=[{'role':'system','content':system},{'role':'user','content':json.dumps({'source':inventory,'schema':schema},ensure_ascii=False)}]
  stats.append({'file':row['file'],'initial_review_units':len(ledger),'max_units':limits['max_units'],'section_prompt_characters':sum(len(m['content']) for m in messages),'max_prompt_characters':limits['max_input_chars'],'final_audit_prompt_characters':sum(len(m['content']) for m in audit_messages),'final_section_review':final.metadata.get('llm_review'),'final_schema_audit':load(d/'schema-audit.json').get('status'),'audit_reason':load(d/'schema-audit.json').get('reason'),'schema_serialized_characters':len(json.dumps(schema,ensure_ascii=False)),'original_text_characters':sum(len(e.text) for e in els),'interpretation':'Locally reconstructed exact current message serialization; whole-envelope/context limits, not provider HTTP/model errors.'})
  passchecks=[]
  for folder in sorted(d.glob('pass-*')):
   sec=SectionResponse.model_validate(load(folder/'sections.json'));sch=load(folder/'schema.json');errs=validate_result(els,sec);account=account_source(els,sec);validate_hierarchy(sch['section_schemas'],sec)
   assert not errs
   passchecks.append({'pass':folder.name,'interval_validation':'passed','hierarchy_validation':'passed','source_accounting':{k:v for k,v in account.items() if k!='outcomes'}})
  checks.append({'file':row['file'],'feedback_pass_count':len(pipe['passes']),'stop_reason':pipe['stop_reason'],'within_two_pass_limit':len(pipe['passes'])<=2,'passes':passchecks})
  if row['index'] in [1,2]:
   relevant=[s for s in final.sections if s.category==('education' if row['index']==1 else 'experience')]
   evidence[row['file']]={'source_sha256':row['sha256'],'sections':[s.model_dump(mode='json') for s in relevant],'mapped_records':[s for s in schema['section_schemas'] if s['category']==('education' if row['index']==1 else 'experience')],'original_elements':[{'index':i,**e.model_dump(mode='json')} for i,e in enumerate(els) if i in ([12,20] if row['index']==1 else list(range(13,32)))],'advisory_findings':load(d/'schema-audit.json')['findings']}
 save(OUT/'investigation.json',{'limits':stats,'recovery_validation':checks,'api_calls':0,'extraction_runs':0,'mapping_replays':0});save(OUT/'source-evidence.json',evidence)
 save(OUT/'original-run-bindings.json',{'selection_sha256':sha(RUN.parent/'selection-manifest.json'),'execution_summary_sha256':sha(RUN/'execution-summary.json'),'provider_usage_sha256':sha(RUN/'provider-usage.json'),'historical_tests_sha256':sha(RUN.parent/'regression-tests.txt'),'production_source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'local_api').rglob('*.py')}})
 for s in stats:print(s['file'],s['initial_review_units'],s['section_prompt_characters'],s['final_audit_prompt_characters'])
if __name__=='__main__':main()
