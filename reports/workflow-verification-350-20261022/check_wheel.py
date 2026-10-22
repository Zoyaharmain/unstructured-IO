import hashlib,json,os,socket,sys,tempfile,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
wheel=next((OUT/'wheels').glob('*.whl'))
request=json.loads((ROOT/'reports/schema-mapping-integration-20261022/example-request.json').read_text())
destination=Path(tempfile.mkdtemp(prefix='resume-audit-wheel-'))
with zipfile.ZipFile(wheel) as archive:archive.extractall(destination)
os.chdir(destination);sys.path.insert(0,str(destination))
os.environ['DEEPSEEK_REVIEW_ENABLED']='false'
os.environ.pop('DEEPSEEK_API_KEY',None)
original=socket.socket.connect

def connect(self,address):
 if isinstance(address,tuple) and address[0] not in {'127.0.0.1','localhost','::1'}:raise RuntimeError('External network disabled')
 return original(self,address)
socket.socket.connect=connect
from fastapi.testclient import TestClient
import local_api.app as api
assert Path(api.__file__).is_relative_to(destination)
client=TestClient(api.app)
results={}
for path in ['/health','/api/v1/resume/schema/definition','/api/v1/resume/schema/mapping']:
 response=client.get(path);assert response.status_code==200;results[path]=response.status_code
response=client.post('/api/v1/resume/schema',json=request)
assert response.status_code==200,response.text
assert response.json()['meta']['provider_calls']==0
assert '/api/v1/resume/sections/local' in client.get('/openapi.json').json()['paths']
result={'wheel':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),
 'imported_app':str(api.__file__),'http_checks':results,'schema_post':response.status_code,
 'schema_provider_calls':0,'local_inspection_route_shipped':True}
(OUT/'wheel-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
