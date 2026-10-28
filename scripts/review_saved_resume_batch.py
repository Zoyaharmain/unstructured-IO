"""Explicitly authorized LLM checks for the exact files in a saved offline batch."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-paid',action='store_true',required=True,
                   help='Explicit authorization to send resumes to DeepSeek and incur API usage')
    a=p.parse_args()
    if a.output.exists():p.error('Use a new output directory')
    rows=json.loads((a.source/'results.json').read_text())
    files=[(a.folder/r['file']).resolve() for r in rows]
    if any(not f.is_relative_to(a.folder.resolve()) or not f.is_file() for f in files):
        p.error('Saved batch contains an unavailable or out-of-folder source')
    import hashlib
    if any(hashlib.sha256(f.read_bytes()).hexdigest()!=r['sha256'] for f,r in zip(files,rows)):
        p.error('A source changed since the offline batch; regenerate it first')
    a.output.mkdir(parents=True,mode=0o700)
    results=[]
    for i,(file,row) in enumerate(zip(files,rows),1):
        target=a.output/f'resume-{i:02d}'
        # Existing CLI bounds requests and saves provider requests/responses.
        with (a.output/f'resume-{i:02d}.log').open('w') as log:
            completed=subprocess.run([sys.executable,str(Path(__file__).with_name('check_single_resume.py')),
                '--file',str(file),'--output',str(target),'--strategy','auto','--llm-review'],
                stdout=log,stderr=subprocess.STDOUT)
        record={'file':row['file'],'exit_code':completed.returncode,'accuracy':'not_human_evaluated','artifact':str(target)}
        for name in ('schema','pipeline','provider-calls'):
            path=target/(name+'.json')
            if path.exists():
                data=json.loads(path.read_text())
                if name=='schema':record['mapping_diagnostics']=data.get('meta',{})
                elif name=='provider-calls':record['provider_calls']=len(data)
                else:record['pipeline']=data
        results.append(record)
        (a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(f'{i}/{len(rows)} completed; exit={completed.returncode}',flush=True)
    return int(any(r['exit_code'] for r in results))

if __name__=='__main__':raise SystemExit(main())
