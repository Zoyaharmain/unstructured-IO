import os,socket,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
os.environ.pop('DEEPSEEK_API_KEY',None);os.environ.pop('OPENAI_API_KEY',None)
os.environ.update(DEEPSEEK_REVIEW_ENABLED='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1')
def deny(*a,**k):raise AssertionError('Network access prohibited during manual-review preparation tests')
socket.socket.connect=deny
socket.socket.connect_ex=deny
socket.create_connection=deny
import pytest
OUT=Path(__file__).resolve().parent
sys.exit(pytest.main([str(OUT/'test_review_session.py'),'tests/test_ground_truth_workflow.py','tests/test_resume_ground_truth.py','tests/test_record_subfields.py','tests/test_saved_hierarchical_defects.py','-q','-p','no:cacheprovider','--junitxml='+str(OUT/'results.xml')]))
