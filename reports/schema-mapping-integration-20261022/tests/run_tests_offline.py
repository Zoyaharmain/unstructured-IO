import os,sys,socket
from pathlib import Path
out=Path(__file__).resolve().parent
os.environ.pop('DEEPSEEK_API_KEY',None);os.environ.pop('OPENAI_API_KEY',None)
os.environ.update(DEEPSEEK_REVIEW_ENABLED='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(Path.cwd()/'.venv/model-cache'),NUMBA_CACHE_DIR=str(out/'numba-cache'),MPLCONFIGDIR=str(out/'mpl-cache'),OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
original=socket.socket.connect;blocked=[]
def connect(self,address):
 if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
  blocked.append(str(address));raise RuntimeError('External network disabled by validation audit')
 return original(self,address)
socket.socket.connect=connect
sys.path.insert(0,str(Path.cwd()))
import pytest
code=pytest.main(['tests','-q','-p','no:cacheprovider','--junitxml='+str(out/'tests.xml')])
(out/'network-guard.txt').write_text('External socket connections blocked: '+str(blocked)+'\n')
sys.exit(code)
