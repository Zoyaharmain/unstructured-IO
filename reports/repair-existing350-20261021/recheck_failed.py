"""Offline replay of only the three latest-live failures; never live-provider success."""
import csv,json,socket,sys
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from local_api.schemas.sections import SectionRequest,SectionResponse
from local_api.services.llm_section_review import ReviewSettings,review_sections
from scripts.batch_check_resumes import validate_result

def deny(*a,**kw):raise RuntimeError('Offline replay forbids network')
socket.socket.connect=deny;socket.create_connection=deny
out=Path(__file__).resolve().parent/'failed-provider-rechecks';out.mkdir(exist_ok=False)
with (ROOT/'reports/readiness-300-20261021/inventory/latest-distinct-documents.csv').open() as f:rows=list(csv.DictReader(f))
summary=[]
for row in rows:
 if row['saved_review_status']!='review_failed':continue
 run=ROOT/'reports'/row['run'];review=next(x for x in json.loads((run/'deepseek/current-results.json').read_text()) if x['file']==row['file'])
 art=json.loads((run/'deepseek'/review['artifact']).read_text());req=SectionRequest(elements=art['extraction']['elements']);local=SectionResponse.model_validate(art['local_sections'])
 decs=json.loads((run/'deepseek/provider-decisions'/(review['id']+'.json')).read_text());calls=[]
 def replay(settings,messages):
  idx=len(calls);calls.append(idx)
  if idx>=len(decs):raise ValueError('No further saved response; no provider request sent')
  return decs[idx]['content']
 settings=replace(ReviewSettings(),enabled=True,api_key='offline-replay',max_units=1000,max_input_chars=1000000)
 final=review_sections(req,local,settings=settings,transport=replay)
 state=final.metadata['llm_review'];errs=validate_result(req.elements,final)
 result={'file':row['file'],'execution_mode':'offline_replay','new_api_calls':0,'replayed_response_attempts':len(calls),'provider_state':state,'integrity_errors':errs,'reviewed_sections':final.model_dump()}
 (out/(row['sha256']+'.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 summary.append({k:result[k] for k in ['file','execution_mode','new_api_calls','replayed_response_attempts','integrity_errors']}|{'replayed_status':state['status'],'validation_failures':state.get('validation_failures',[])})
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
