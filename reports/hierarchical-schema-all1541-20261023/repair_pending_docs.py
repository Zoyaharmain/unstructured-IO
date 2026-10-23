"""Retry only failed DOC files after the user installs the required converter."""
import json
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from scripts.map_resume_corpus import fresh_worker
from scripts.batch_check_resumes import offline_environment, initialize_worker

OUT=Path(__file__).parent.resolve()
if not shutil.which('soffice'):
    raise SystemExit('LibreOffice is unavailable. Install libreoffice-writer, then rerun this repair script.')
offline_environment()
manifest=json.loads((OUT/'manifest.json').read_text())
rows=[json.loads(line) for line in (OUT/'results.jsonl').read_text().splitlines() if line.strip()]
pending=[r for r in rows if r['status']=='failed' and r['extension']=='.doc']
repairs=[]
with ProcessPoolExecutor(max_workers=1,initializer=initialize_worker) as pool:
    for row in pending:
        result=pool.submit(fresh_worker,row,str(OUT),manifest['timeout'],manifest['code_sha256']).result()
        result['input_mode']='doc_retry_after_converter_install'
        repairs.append(result)
        (OUT/'doc-repairs.json').write_text(json.dumps(repairs,indent=2,ensure_ascii=False))
        print(json.dumps({'repaired':len(repairs),'total':len(pending),'status':result['status']}),flush=True)
(OUT/'doc-converter.json').write_text(json.dumps({'version':subprocess.run(['soffice','--version'],capture_output=True,text=True).stdout.strip(),'provider_calls':0},indent=2))
