import importlib.util,sys,os,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent
for key in ('DEEPSEEK_API_KEY','OPENAI_API_KEY'):os.environ.pop(key,None)
os.environ['DEEPSEEK_REVIEW_ENABLED']='false'
def deny(*a,**k):raise AssertionError('No network')
socket.socket.connect=deny
import pytest
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
old_relationship=module('old_relationship',OUT/'record_relationships_before.py');old_pipeline=module('old_pipeline',OUT/'single_resume_pipeline_before.py')
class Baseline:
 def pytest_collection_modifyitems(self,items):
  for item in items:
   if item.module.__name__.endswith('test_phase1_repairs'):
    item.module.field_kinds=old_relationship.field_kinds;item.module.fingerprint=old_pipeline.fingerprint
# Exclude only the integration test whose inline function import intentionally uses installed current code.
sys.exit(pytest.main(['tests/test_phase1_repairs.py','-q','-k','not continuation_keeps_its_existing_record', '-p','no:cacheprovider'],plugins=[Baseline()]))
