"""Exercise real local extraction -> embeddings/blocks -> schema HTTP contracts."""
import os,socket,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
os.environ.pop('DEEPSEEK_API_KEY',None);os.environ.pop('OPENAI_API_KEY',None)
os.environ.update(DEEPSEEK_REVIEW_ENABLED='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(ROOT/'.venv/model-cache'),OMP_NUM_THREADS='1')
original=socket.socket.connect
blocked=[]
def connect(self,address):
 if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
  blocked.append(str(address));raise RuntimeError('Offline smoke check forbids external connections')
 return original(self,address)
socket.socket.connect=connect
from fastapi.testclient import TestClient
from local_api.app import app
p=Path(__file__).resolve().parent;pdf=ROOT/'tests/fixtures/Jayesh Yadav-CV.pdf'
with TestClient(app) as client:
 extraction=client.post('/api/v1/extract/text',files={'file':(pdf.name,pdf.read_bytes(),'application/pdf')},data={'strategy':'fast'})
 assert extraction.status_code==200,extraction.text
 elements=extraction.json()['elements']
 sections=client.post('/api/v1/resume/sections',json={'elements':elements})
 assert sections.status_code==200,sections.text
 mapped=client.post('/api/v1/resume/schema',json={'elements':elements,'sections':sections.json(),'source':pdf.name})
 assert mapped.status_code==200,mapped.text
 data=mapped.json();assert data['meta']['provider_calls']==0
 (p/'http-pipeline-response.json').write_text(json.dumps(data,indent=2)+'\n')
 result={'extraction_http':extraction.status_code,'sections_http':sections.status_code,'schema_http':mapped.status_code,'source_elements':len(elements),'section_count':len(sections.json()['sections']),'schema_mode':data['extraction_mode'],'schema_provider_calls':0,'section_provider_status':sections.json()['metadata'].get('llm_review',{}).get('status'),'blocked_external_socket_attempts':blocked}
 (p/'http-pipeline-smoke.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
