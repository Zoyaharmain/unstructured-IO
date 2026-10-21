"""Orchestrate the existing local and DeepSeek batch CLIs for a bounded number of PDFs (50 by default).
No extraction, detection or provider algorithms are implemented here.
"""
import argparse,hashlib,json,os,random,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.check_pilot_fallback import DEFAULT_FOLDER,load_provider_env
from scripts.select_ground_truth_resumes import get_details

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def configuration():
 paths=sorted((ROOT/'local_api').rglob('*.py'))+sorted((ROOT/'local_api/data').glob('*.json'))+[ROOT/'scripts/batch_check_resumes.py',ROOT/'scripts/llm_verify_resume_batch.py',Path(__file__)]
 return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def select(folder, count=50):
 original=json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text());rows=json.loads((ROOT/'.upstream/batch-validation/current-results.json').read_text());selected=[];used=set();names=set()
 def add(item,rationale):
  p=folder/item['file']
  if not p.is_file() or sha(p)!=item['sha256']:raise ValueError('Missing/changed source: '+item['file'])
  if item['sha256'] in used or item['file'] in names:raise ValueError('Duplicate selected document')
  selected.append({**item,'original_source_path':str(p),'bytes':p.stat().st_size,'selection_rationale':rationale});used.add(item['sha256']);names.add(item['file'])
 for item in original:add(item,'Preserved original 15-member pilot; known Java requirements template retained for explicit scope tracking')
 pool=[]
 for row in rows:
  if row.get('extension')!='.pdf' or row.get('status')!='processed' or row['file'] in names or row.get('sha256') in used:continue
  artifact=ROOT/'.upstream/batch-validation'/row.get('artifact','')
  if not artifact.is_file():continue
  p=folder/row['file']
  if not p.is_file() or sha(p)!=row.get('sha256'):continue
  pool.append(get_details(row,ROOT/'.upstream/batch-validation'))
 # Same seed and page/layout/coverage stratification features as original selection.
 buckets={}
 for item in sorted(pool,key=lambda x:x['file']):
  key=(min(item['pages'],5),item['two_col'],item['coverage']<95)
  buckets.setdefault(key,[]).append(item)
 rng=random.Random(42)
 for items in buckets.values():rng.shuffle(items)
 while len(selected)<count:
  progress=False
  for key in sorted(buckets):
   while buckets[key]:
    item=buckets[key].pop()
    if item['sha256'] in used or item['file'] in names:continue
    add(item,f'Seed42 round-robin page/layout/coverage stratum {key}; extension of existing pilot mechanism');progress=True;break
   if len(selected)==count:break
  if not progress:raise ValueError(f'Insufficient distinct hash-verified PDFs for {count}')
 return selected

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,default=DEFAULT_FOLDER);p.add_argument('--output',type=Path,required=True);p.add_argument('--selection-manifest',type=Path,help='Reuse an exact prior selected source hash set, with fresh processing');p.add_argument('--count',type=int,default=50,help='Exact document scope, including the original 15; minimum 15');p.add_argument('--resume',action='store_true');p.add_argument('--local-only',action='store_true');args=p.parse_args();out=args.output.resolve()
 if args.count<15:p.error('--count must be at least 15')
 load_provider_env(ROOT/'.env')
 if not args.local_only and not os.getenv('DEEPSEEK_API_KEY','').strip():p.error('Private API key unavailable')
 config=configuration()
 if out.exists():
  if not args.resume:p.error('Existing output requires explicit --resume')
  manifest=json.loads((out/'manifest.json').read_text());selected=manifest['selected']
  if manifest['scope']!=args.count:p.error('--count differs from the frozen run scope')
  if manifest['pipeline_source_hashes']!=config:p.error('Pipeline changed since run creation; stop rather than mix outputs')
  for item in selected:
   if sha(args.folder/item['file'])!=item['sha256'] or sha(out/'selected-pdfs'/item['file'])!=item['sha256']:p.error('Source hash mismatch on resume')
  if manifest.get('provider_model')!=os.getenv('DEEPSEEK_MODEL','deepseek-flash') or manifest.get('provider_base')!=os.getenv('DEEPSEEK_BASE_URL','https://api.deepseek.com'):p.error('Provider configuration changed')
 else:
  if args.selection_manifest:
   manifest_data=json.loads(args.selection_manifest.read_text())
   frozen=manifest_data['selected'];selected=[]
   for item in frozen:
    source=args.folder/item['file']
    if not source.is_file() or sha(source)!=item['sha256']:raise ValueError('Frozen selection source hash mismatch: '+item['file'])
    selected.append({**item,'original_source_path':str(source.resolve()),'bytes':source.stat().st_size,'selection_rationale':'Exact prior manifest hash-bound selection; fresh pipeline and provider review'})
   selection_desc=manifest_data.get('selection',f'Selection manifest: {args.selection_manifest.name}')
  else:
   selected=select(args.folder,args.count)
   selection_desc=f'original15 +{args.count-15} seeded stratified distinct PDF hashes from existing processed pool'
  if len(selected)!=args.count or len({s['sha256'] for s in selected})!=args.count:raise ValueError('Scope must contain the requested number of unique hashes')
  out.mkdir(parents=True,mode=0o700);(out/'selected-pdfs').mkdir()
  protected={str(f.resolve()):sha(f) for folder in [ROOT/'ground_truth',ROOT/'reports'] for f in folder.rglob('*') if f.is_file() and out not in f.resolve().parents}
  protected.update({s['original_source_path']:s['sha256'] for s in selected});write(out/'protected-before.json',protected)
  for item in selected:shutil.copy2(args.folder/item['file'],out/'selected-pdfs'/item['file'])
  manifest={'created_utc':now(),'seed':42,'scope':args.count,'selection':selection_desc,'source_directory':str(args.folder),'selected':selected,'pipeline_source_hashes':config,'provider_model':os.getenv('DEEPSEEK_MODEL','deepseek-flash'),'provider_base':os.getenv('DEEPSEEK_BASE_URL','https://api.deepseek.com'),'status':'selected','selection_manifest':str(args.selection_manifest) if args.selection_manifest else None,'commands':[]}
  write(out/'manifest.json',manifest)
 env=dict(os.environ,DEEPSEEK_REVIEW_ENABLED='true',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(ROOT/'.venv/model-cache'),NUMBA_CACHE_DIR='/tmp/pilot50-numba',MPLCONFIGDIR='/tmp/pilot50-mpl',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',UNSTRUCTURED_DISABLE_NOTICE='1')
 def run(script,arguments,log):
  command=[sys.executable,'-B',str(ROOT/'scripts'/script),*map(str,arguments)];manifest['commands'].append({'started_utc':now(),'argv':command,'log':log});write(out/'manifest.json',manifest)
  with (out/log).open('a') as stream:subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
  manifest['commands'][-1]['finished_utc']=now();write(out/'manifest.json',manifest)
 if manifest['status']=='selected':
  manifest['local_started_utc']=now();write(out/'manifest.json',manifest)
  run('batch_check_resumes.py',[out/'selected-pdfs','--output',out/'local','--workers','2','--timeout','120'],'local.log')
  local=json.loads((out/'local/current-results.json').read_text())
  if len(local)!=args.count or any(r['status']!='processed' for r in local):
   manifest['status']='blocked_local_stage';write(out/'manifest.json',manifest);raise SystemExit('Blocking local failure: provider not started. Inspect local log; no pipeline changes made')
  manifest['local_completed_utc']=now();manifest['status']='local_complete';write(out/'manifest.json',manifest)
 if manifest['status']=='blocked_local_stage':raise SystemExit('Local blocking issue must be investigated before continuing')
 if args.local_only:print(f'All {args.count} local stages complete; no provider calls made');return
 if manifest['status'] not in {'local_complete','review_started','review_complete'}:raise SystemExit('Invalid phase')
 if manifest['status']!='review_complete':
  # Only this run's source-bound checkpoints are eligible, after source/config checks.
  existing=out/'deepseek/current-results.json'
  if existing.exists():
   local_rows={r['file']:r for r in json.loads((out/'local/current-results.json').read_text())}
   for r in json.loads(existing.read_text()):
    if r['file'] not in local_rows:raise SystemExit('Checkpoint outside scope')
    artifact=r.get('artifact')
    if artifact:
     a=json.loads((out/'deepseek'/artifact).read_text());b=json.loads((out/'local'/local_rows[r['file']]['artifact']).read_text())
     if a['extraction']!=b['extraction'] or a['local_sections']!=b['sections']:raise SystemExit('Stale checkpoint source mismatch')
  manifest.setdefault('review_started_utc',now());manifest['status']='review_started';write(out/'manifest.json',manifest)
  run('llm_verify_resume_batch.py',['--source',out/'local','--output',out/'deepseek','--folder',out/'selected-pdfs','--workers','2'],'deepseek.log')
  manifest['review_completed_utc']=now();manifest['status']='review_complete';write(out/'manifest.json',manifest)
 protected=json.loads((out/'protected-before.json').read_text());write(out/'preservation.json',{'checked':len(protected),'changed':[f for f,h in protected.items() if not Path(f).is_file() or sha(Path(f))!=h]});print((out/'deepseek/summary.json').read_text(),flush=True)
if __name__=='__main__':main()
