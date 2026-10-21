"""Run exact selected 15 locally first, then review all 15 with DeepSeek.
This command incurs API usage. No API requests occur on --help.
"""
import argparse,csv,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.check_pilot_fallback import DEFAULT_FOLDER,eligible,load_provider_env

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,default=DEFAULT_FOLDER);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 selected=eligible(json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text()))
 for s in selected:
  source=args.folder/s['file']
  if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=s['sha256']:p.error('Missing/changed selected PDF: '+s['file'])
 if args.output.exists():p.error('Use a fresh output directory to preserve earlier results')
 load_provider_env(ROOT/'.env')
 if not os.getenv('DEEPSEEK_API_KEY','').strip():p.error('Set DEEPSEEK_API_KEY in .env before running')
 out=args.output.resolve();out.mkdir(parents=True,mode=0o700);inputs=out/'selected-pdfs';inputs.mkdir()
 for s in selected:shutil.copy2(args.folder/s['file'],inputs/s['file'])
 (out/'selection.json').write_text(json.dumps(selected,indent=2)+'\n')
 env=dict(os.environ,DEEPSEEK_REVIEW_ENABLED='true',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(ROOT/'.venv/model-cache'),NUMBA_CACHE_DIR='/tmp/pilot-full-review-numba',MPLCONFIGDIR='/tmp/pilot-full-review-mpl',OMP_NUM_THREADS='1',UNSTRUCTURED_DISABLE_NOTICE='1')
 def run(script,arguments,log):
  print('Running '+script+'; log: '+str(out/log),flush=True)
  with (out/log).open('w') as stream:subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/script),*map(str,arguments)],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
 run('batch_check_resumes.py',[inputs,'--output',out/'local','--workers','2','--timeout','120'],'local.log')
 local=json.loads((out/'local/current-results.json').read_text())
 if len(local)!=15 or any(r['status']!='processed' for r in local):
  (out/'report.md').write_text('# Pilot stopped before DeepSeek\n\nLocal extraction/detection did not successfully finish for exactly 15 documents. Inspect local.log and local/current-results.json. No DeepSeek review started.\n');raise SystemExit('Local stage incomplete; no DeepSeek review started')
 # Source directory contains only the exact hash-verified 15 copies, never the corpus.
 run('llm_verify_resume_batch.py',['--source',out/'local','--output',out/'deepseek','--folder',inputs,'--workers','1'],'deepseek.log')
 summary=json.loads((out/'deepseek/summary.json').read_text());reviewed={r['file']:r for r in json.loads((out/'deepseek/current-results.json').read_text())};rows=[]
 for r in local:
  final=reviewed.get(r['file'],{});rows.append({'file':r['file'],'source_sha256':r['sha256'],'local_status':r['status'],'local_raw_unassigned':r.get('review_units'),'llm_status':final.get('status','not_attempted'),'api_calls':final.get('api_calls',0),'final_raw_unassigned':final.get('review_units'),'extracted_source_invariants': 'PASS' if final and final.get('invariant_errors')==[] else 'NOT_CONFIRMED','semantic_accuracy':'NOT_ESTABLISHED','relationship_accuracy':'NOT_ESTABLISHED'})
 with (out/'per-resume.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,list(rows[0]));writer.writeheader();writer.writerows(rows)
 text=['# Exact 15-resume local pipeline + full DeepSeek verification','','All 15 finish local extraction, BERT/K-means detection and local recovery before any DeepSeek review begins. DeepSeek receives all extracted spans for assigned-block review and unresolved-span placement. Model review remains a prediction, not independently verified truth.','','| File | Local unassigned (raw) | Final unassigned (raw) | API calls | Review status |','|---|---:|---:|---:|---|']
 for r in rows:text.append(f"| {r['file']} | {r['local_raw_unassigned']} | {r['final_raw_unassigned']} | {r['api_calls']} | {r['llm_status']} |")
 text+=['','## Provider usage and completeness','','```json',json.dumps(summary,indent=2),'```','','## Limits','','Counts above include raw needs_review blocks, potentially whitespace. Exact source invariants check preservation of extracted text, not every original PDF word. Missing PDF text, duplication, semantic section correctness and employer/title/date or degree/institution/year relationships need independent source-backed approval. No numeric semantic/word accuracy is claimed. Failed/skipped provider reviews are reported explicitly; they do not count as verified.','','Local artifacts: local/documents/. Full-context reviewed artifacts: deepseek/documents/. Actual provider responses and call/token records: deepseek/provider-decisions/ and deepseek/checkpoints/. Original PDFs, previous annotations and reports were not modified.']
 (out/'report.md').write_text('\n'.join(text)+'\n');print('Report: '+str(out/'report.md'),flush=True);print('Per-resume CSV: '+str(out/'per-resume.csv'),flush=True)
 if summary.get('documents_completed')!=15 or any(not r['llm_status'].startswith('llm_reviewed') for r in rows):raise SystemExit('Some reviews incomplete; inspect the report before accepting results')
if __name__=='__main__':main()
