"""Replay failed existing tests with HEAD implementations in memory; no checkout mutation."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path.cwd()))
root=Path('reports/source-ownership-20261112/isolated-all-tests')
nodes=[]
for row in json.loads((root/'results.json').read_text()):
    if row.get('failures'):
        for case in ET.parse(root/(Path(row['module']).stem+'.xml')).getroot().findall('.//testcase'):
            if case.find('failure') is not None:
                nodes.append(row['module']+'::'+case.get('name'))
for name in ('record_subfields','resume_structure','resume_sections','record_relationships','source_validation','subschema_validation','section_subschemas','schema_mapping'):
    path=f'local_api/services/{name}.py'
    module=importlib.import_module(f'local_api.services.{name}')
    original=subprocess.check_output(['git','show',f'HEAD:{path}'],text=True)
    exec(compile(original,path,'exec'),module.__dict__)
import pytest
sys.exit(pytest.main(['-q','--tb=short','--junitxml=reports/source-ownership-20261112/baseline-comparison.xml',*nodes]))
