"""Fresh local+live rerun ONLY of up to three flagged members of an existing pilot."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.check_pilot_fallback import DEFAULT_FOLDER,load_provider_env

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--previous',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--files',nargs='+',required=True);p.add_argument('--folder',type=Path,default=DEFAULT_FOLDER);args=p.parse_args()
 old=json.loads((args.previous/'deepseek/current-results.json').read_text());flagged={r['file'] for r in old if r['status']=='llm_reviewed_needs_review'};selection={r['file']:r for r in json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text())}
 if not 1<=len(args.files)<=3 or len(set(args.files))!=len(args.files) or any(f not in flagged or f not in selection for f in args.files):p.error('Only up to three distinct flagged pilot members may be rerun')
 for f in args.files:
  source=args.folder/f
  if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=selection[f]['sha256']:p.error('Source missing/changed: '+f)
 load_provider_env(ROOT/'.env')
 if not os.getenv('DEEPSEEK_API_KEY','').strip():p.error('Private DeepSeek key unavailable; set .env or export it')
 out=args.output.resolve()
 if out.exists():p.error('New output directory required')
 out.mkdir(parents=True,mode=0o700);inputs=out/'selected-pdfs';inputs.mkdir()
 protected={str(f.resolve()):hashlib.sha256(f.read_bytes()).hexdigest() for folder in [args.previous,ROOT/'ground_truth'] for f in folder.rglob('*') if f.is_file()}
 protected.update({str((args.folder/f).resolve()):hashlib.sha256((args.folder/f).read_bytes()).hexdigest() for f in args.files})
 (out/'protected-before.json').write_text(json.dumps(protected,indent=2))
 for f in args.files:shutil.copy2(args.folder/f,inputs/f)
 (out/'selection.json').write_text(json.dumps([selection[f] for f in args.files],indent=2))
 env=dict(os.environ,DEEPSEEK_REVIEW_ENABLED='true',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(ROOT/'.venv/model-cache'),NUMBA_CACHE_DIR='/tmp/flagged-three-numba',MPLCONFIGDIR='/tmp/flagged-three-mpl',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',UNSTRUCTURED_DISABLE_NOTICE='1')
 def run(script,arguments,log):
  with (out/log).open('w') as stream:subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/script),*map(str,arguments)],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
 run('batch_check_resumes.py',[inputs,'--output',out/'local','--workers','1','--timeout','120'],'local.log')
 rows=json.loads((out/'local/current-results.json').read_text())
 if len(rows)!=len(args.files) or any(r['status']!='processed' for r in rows):raise SystemExit('Local stage incomplete; provider not started')
 run('llm_verify_resume_batch.py',['--source',out/'local','--output',out/'deepseek','--folder',inputs,'--workers','1'],'deepseek.log')
 after={'checked':len(protected),'changed':[name for name,h in protected.items() if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest()!=h]};(out/'preservation.json').write_text(json.dumps(after,indent=2));print((out/'deepseek/summary.json').read_text(),flush=True)
if __name__=='__main__':main()
