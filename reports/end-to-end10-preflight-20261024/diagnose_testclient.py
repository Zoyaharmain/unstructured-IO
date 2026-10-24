import faulthandler,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
os.environ['DEEPSEEK_REVIEW_ENABLED']='false';os.environ.pop('DEEPSEEK_API_KEY',None)
faulthandler.dump_traceback_later(20,repeat=False)
from fastapi.testclient import TestClient
from local_api.app import app
print('Calling local /health through TestClient; no provider access.',flush=True)
print(TestClient(app).get('/health').status_code,flush=True)
