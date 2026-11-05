import os,json,time,subprocess,hashlib
from pathlib import Path
root=Path('/home/zoyaharmain/unstructured-IO');os.chdir(root)
out=root/'reports/live-five-new-resumes-20261105'
selection=json.loads((out/'selection.json').read_text())
selection['status']='approved_running';(out/'selection.json').write_text(json.dumps(selection,indent=2))
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
rows=[]
for i,item in enumerate(selection['selected'],1):
 assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
 target=out/f'{i:02d}';start=time.monotonic();print('START',i,item['file'],flush=True)
 with (out/f'{i:02d}.log').open('w') as log:
  proc=subprocess.run(['/home/zoyaharmain/venv312/bin/python','-B','scripts/check_single_resume.py','--file',item['path'],'--output',str(target),'--llm-review','--recovery-attempts','1'],env=env,stdout=log,stderr=subprocess.STDOUT)
 row={'file':item['file'],'directory':f'{i:02d}','exit_code':proc.returncode,'seconds':round(time.monotonic()-start,1)};rows.append(row)
 (out/'results.json').write_text(json.dumps(rows,indent=2));print('END',json.dumps(row),flush=True)
selection['status']='attempts_finished';(out/'selection.json').write_text(json.dumps(selection,indent=2))
