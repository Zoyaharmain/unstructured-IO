"""Ten saved-input, mocked-provider replay. Never extract/detect/embed/call network."""
import hashlib,json,os,socket,sys
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent
RUN=ROOT/'reports/end-to-end10-preflight-20261024/execution';BASE=ROOT/'reports/ten-resume-phase1-20261024/after'
def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def prohibited(*a,**k):raise AssertionError('Forbidden network/extraction/detection/embedding in replay')
for k in ['DEEPSEEK_API_KEY','OPENAI_API_KEY']:os.environ.pop(k,None)
os.environ['DEEPSEEK_REVIEW_ENABLED']='false';socket.socket.connect=prohibited;socket.create_connection=prohibited
from local_api.services import llm_section_review as llm
from local_api.services import resume_sections as detector
from local_api.services import text_extraction_service as extractor
llm.provider_json=prohibited;llm.call_deepseek=prohibited;detector.detect_sections=prohibited;detector.get_engine=prohibited;extractor.extract_text=prohibited
from local_api.schemas.sections import SectionRequest,SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.review_chunking import RequestBudget,run_schema_audit,binding
from local_api.services.source_validation import validate_result
from local_api.services.source_accounting import account_source
from local_api.services.subschema_validation import validate_hierarchy

def main():
 name=os.environ.get('PHASE2_REPLAY_NAME','replay')
 dest=OUT/name
 if dest.exists():raise ValueError('Preserve existing replay')
 dest.mkdir();rows=[];usage=[];budget=RequestBudget(max_total=128,max_document=32,max_pass=16)
 for item in load(RUN.parent/'selection-manifest.json')['selected']:
  i=item['index'];d=dest/f'{i:02d}';d.mkdir()
  elements=[ExtractedElement.model_validate(e) for e in load(RUN/f'{i:02d}/extraction.json')['elements']]
  request=SectionRequest(elements=elements);before=SectionResponse.model_validate(load(BASE/f'{i:02d}/sections.json'));baseline=load(BASE/f'{i:02d}/schema.json')
  config=llm.ReviewSettings(enabled=True,api_key='mock-only',model='mock-only',recovery_attempts=0)
  own=[]
  def section_transport(cfg,messages):
   payload=json.loads(messages[1]['content']);targets=payload.get('targets',payload.get('spans'))
   own.append({'stage':'section_review','owned':len(targets)})
   # Confirm frozen placements. This is synthetic structural verification, not LLM accuracy.
   return json.dumps({'assignments':[[t['id'],t['current_category']] for t in targets]})
  def audit_transport(cfg,messages):
   payload=json.loads(messages[1]['content']);own.append({'stage':'schema_audit','owned':len(payload['targets'])})
   return json.dumps({'checked_ids':[t['id'] for t in payload['targets']],'findings':[]})
  after=llm.review_sections(request,before,settings=config,transport=section_transport,_budget=budget,document_sha256=item['sha256'])
  assert not validate_result(elements,after)
  mapped=map_schema(SchemaMappingRequest(elements=elements,sections=after,source=item['file'])).model_dump(mode='json')
  validate_hierarchy(mapped['section_schemas'],after)
  audit=run_schema_audit(elements,after,mapped,config,audit_transport,budget=budget,document_sha256=item['sha256'])
  ba=account_source(elements,before);aa=account_source(elements,after)
  def membership(s):return [(p.category,[(e.entry_id,e.block_indices) for e in p.entries]) for p in s.sections]
  changed=[k for k in mapped if mapped[k]!=baseline.get(k)]
  save(d/'sections.json',after.model_dump(mode='json'));save(d/'schema.json',mapped);save(d/'audit.json',audit)
  state=after.metadata['llm_review']
  row={'file':item['file'],'section_review':state['status'],'section_chunks':len(state.get('chunking',{}).get('chunks',[])),'section_calls':state['provider_calls'],'schema_audit':audit['status'],'audit_chunks':len(audit['coverage']['chunks']),'audit_calls':audit['provider_calls'],'blocked_audit_units':len(audit['coverage']['blocked']),'changed_schema_keys':changed,'legacy_data_unchanged':mapped['data']==baseline['data'],'nested_hierarchy_unchanged':mapped['section_schemas']==baseline['section_schemas'],'record_membership_unchanged':membership(before)==membership(after),'source_outcomes_unchanged':ba['outcomes']==aa['outcomes'],'source_assignment_outcomes_unchanged':[{k:v for k,v in o.items() if k!='reason'} for o in ba['outcomes']]==[{k:v for k,v in o.items() if k!='reason'} for o in aa['outcomes']],'source_coverage_before':{k:v for k,v in ba.items() if k!='outcomes'},'source_coverage_after':{k:v for k,v in aa.items() if k!='outcomes'},'audit_checked_ids':audit['checked_ids'],'section_inventory_sha256':binding(elements,item['sha256']),'mock_requests':own,'meaning':'Confirm-only section mock and acknowledgement-only audit mock. Empty mock findings are not semantic validation.'}
  rows.append(row);usage+=own
  save(dest/'results.json',rows)
 save(OUT/('before-after-comparison'+('-'+name.removeprefix('replay-') if name!='replay' else '')+'.json'),{'baseline':'Phase1 after/ on unchanged frozen extraction/sections, original artifacts preserved','documents':rows,'semantic_accuracy':None,'live_api_calls':0})
 save(OUT/('source-coverage-ledger'+('-'+name.removeprefix('replay-') if name!='replay' else '')+'.json'),{'documents':rows,'request_budget_events':budget.events,'mock_requests':budget.total,'budget':{'global':128,'per_document':32,'per_pass':16},'live_api_calls':0})
 print(json.dumps([{k:r[k] for k in ['file','section_review','section_calls','schema_audit','audit_calls','changed_schema_keys','record_membership_unchanged']} for r in rows],indent=2))
if __name__=='__main__':main()
