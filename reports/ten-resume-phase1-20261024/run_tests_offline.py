"""Offline regression harness: no provider credentials or external connections."""
import os,socket,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];LABEL=os.environ.get('AUDIT_TEST_LABEL','')
for key in ('DEEPSEEK_API_KEY','OPENAI_API_KEY'):os.environ.pop(key,None)
os.environ.update(DEEPSEEK_REVIEW_ENABLED='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(ROOT/'.venv/model-cache'),NUMBA_CACHE_DIR=str(OUT/'numba-cache'),MPLCONFIGDIR=str(OUT/'mpl-cache'),OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
original=socket.socket.connect;blocked=[]
def connect(self,address):
 if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
  blocked.append(str(address));raise RuntimeError('External network prohibited during offline tests')
 return original(self,address)
socket.socket.connect=connect
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
import pytest
args=sys.argv[1:] or ['tests']
code=pytest.main([*args,'-q','-p','no:cacheprovider','--junitxml='+str(OUT/(LABEL+'regression-tests.xml'))])
(OUT/(LABEL+'network-guard.txt')).write_text('External socket attempts blocked: '+str(blocked)+'\n')
sys.exit(code)
