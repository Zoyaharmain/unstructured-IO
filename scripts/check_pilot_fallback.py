"""Fresh local 15-PDF pilot with optional document-level DeepSeek fallback only.
Never scans the corpus. Exactly the existing selection manifest is eligible.
"""
import argparse,csv,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from collections import Counter
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
DEFAULT_FOLDER=Path('/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT')
def eligible(items):
 if len(items)!=15 or len({s['file'] for s in items})!=15:raise ValueError('Manifest must contain exactly 15 distinct documents')
 if any(Path(s['file']).name!=s['file'] or not s['file'].lower().endswith('.pdf') for s in items):raise ValueError('Only selected PDF basenames allowed')
 return items

def meaningful_pending(response,elements):
 return [b for b in response.needs_review if b.text.strip() and elements[b.source_element_index].type!='PageBreak' and not (elements[b.source_element_index].type=='Footer' and re.fullmatch(r'\s*(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?\s*',b.text,re.I))]
def signature(result):
 return [(b.source_element_index,b.start,b.end,s.category) for s in result.sections for b in s.blocks]+[(b.source_element_index,b.start,b.end,None) for b in result.needs_review]
def save(path,data):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)
from local_api.core.provider_env import load_provider_env
def diagnostics(pdf,extraction):
 els=extraction.elements;duplicate=[]
 for i,e in enumerate(els):
  if len(e.text.split())<25:continue
  for j,v in enumerate(els[:i]):
   if e.text==v.text:duplicate.append({'first_element':j,'repeated_element':i,'page':e.page_number,'words':len(e.text.split()),'status':'candidate_requires_source_review'})
 independent=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,timeout=30)
 text=independent.stdout.decode('utf-8','replace');normalized=lambda s:re.sub(r'\W','',s.casefold())
 joined=normalized('\n'.join(e.text for e in els));terms=Counter(re.findall(r'\w+',text.casefold()))-Counter(re.findall(r'\w+','\n'.join(e.text for e in els).casefold()))
 unmatched={k:v for k,v in terms.items() if normalized(k) not in joined}
 return {'duplicate_candidates':duplicate,'independent_parser_unmatched_tokens':unmatched,'independent_parser_ok':independent.returncode==0,'diagnostics_are_accuracy':False},text

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,default=DEFAULT_FOLDER);p.add_argument('--output',type=Path,required=True);p.add_argument('--use-deepseek',action='store_true');args=p.parse_args()
 selected=eligible(json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text()))
 # Verify entire bounded scope before any extraction or paid call.
 for item in selected:
  pdf=args.folder/item['file']
  if not pdf.is_file() or hashlib.sha256(pdf.read_bytes()).hexdigest()!=item['sha256']:p.error('Missing/changed selected source: '+item['file'])
 if args.output.exists():p.error('Use a new output directory; existing results are never overwritten')
 args.output.mkdir(parents=True,mode=0o700);(args.output/'documents').mkdir();(args.output/'checkpoints').mkdir();(args.output/'provider-decisions').mkdir()
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('HF_HOME',str(ROOT/'.venv/model-cache'));os.environ.setdefault('NUMBA_CACHE_DIR','/tmp/pilot-fallback-numba');os.environ.setdefault('MPLCONFIGDIR','/tmp/pilot-fallback-mpl');os.environ.setdefault('OMP_NUM_THREADS','1')
 from local_api.services.text_extraction_service import extract_text
 from local_api.schemas.sections import SectionRequest
 from local_api.services.resume_sections import get_engine
 from local_api.services.section_recovery import recover_sections
 from local_api.services.source_accounting import account_source
 from local_api.services.llm_section_review import ReviewSettings
 from scripts.llm_verify_resume_batch import review_document,FATAL
 from scripts.batch_check_resumes import validate_result
 if args.use_deepseek:
  load_provider_env(ROOT/'.env')
 settings=replace(ReviewSettings.from_env(),enabled=args.use_deepseek,max_units=1000,max_input_chars=1_000_000,timeout=120,recovery_attempts=1)
 if args.use_deepseek and not settings.api_key:p.error('Set DEEPSEEK_API_KEY in .env or environment')
 settings.validate();save(args.output/'scope.json',[s['file'] for s in selected]);rows=[];fatal=None
 for number,item in enumerate(selected,1):
  started=time.monotonic();file=item['file'];identifier=Path(item['artifact']).stem;pdf=args.folder/file;row={'file':file,'source_sha256':item['sha256'],'llm_called':False,'api_calls':0,'llm_trigger':'none','status':'error','accuracy':'NOT_ESTABLISHED'}
  try:
   extraction=extract_text(pdf.read_bytes(),file,strategy='fast');row['extraction_strategies']=['fast']
   if not extraction.text.strip():
    extraction=extract_text(pdf.read_bytes(),file,strategy='ocr_only');row['extraction_strategies'].append('ocr_only')
   if not extraction.text.strip():raise ValueError('empty_extraction_after_local_retry')
   diagnostic,independent=diagnostics(pdf,extraction);(args.output/'documents'/(identifier+'-independent.txt')).write_text(independent);row['extraction_diagnostics']=diagnostic
   request=SectionRequest(elements=extraction.elements,extraction_verified=False);local=get_engine().detect(request);row['initial_meaningful_unassigned']=len(meaningful_pending(local,request.elements));passes=[]
   for attempt in range(2):
    if not meaningful_pending(local,request.elements):break
    before=signature(local);repaired=recover_sections(request,local);passes.append({'pass':attempt+1,'meaningful_unassigned':len(meaningful_pending(repaired,request.elements)),'changed':signature(repaired)!=before});local=repaired
    if signature(local)==before:break
   row['local_recovery_passes']=passes;row['after_local_meaningful_unassigned']=len(meaningful_pending(local,request.elements));errors=validate_result(request.elements,local)
   save(args.output/'documents'/(identifier+'.json'),{'file':file,'extraction':extraction.model_dump(),'sections':local.model_dump()})
   final=local
   if errors:row.update(status='source_invariant_failure',errors=errors)
   elif row['after_local_meaningful_unassigned'] and args.use_deepseek and not fatal:
    row['llm_trigger']='meaningful_text_still_unassigned_after_local_recovery'
    # Existing reviewer gets whole-document context ONLY for documents failing the local gate.
    live=review_document({'file':file,'extension':'.pdf','artifact':'documents/'+identifier+'.json'},args.output,args.output,pdf.parent,settings)
    row.update(api_calls=live.get('api_calls',0),llm_called=bool(live.get('api_calls')),llm_status=live.get('llm_review',{}),usage=live.get('usage',{}),provider_status=live['status']);row['status']=live['status']
    if live.get('artifact'):
     artifact=json.loads((args.output/live['artifact']).read_text());final=__import__('local_api.schemas.sections',fromlist=['SectionResponse']).SectionResponse.model_validate(artifact['reviewed_sections'])
     # Retain standard local key as well as reviewer artifact fields.
     artifact['sections']=artifact['local_sections'];save(args.output/live['artifact'],artifact)
    error=live.get('error_code') or live.get('llm_review',{}).get('error_code')
    if error in FATAL:fatal=error
   else:
    row['status']='local_all_assigned' if not row['after_local_meaningful_unassigned'] else 'needs_review_llm_disabled' if not args.use_deepseek else 'needs_review_provider_stopped'
   row['after_final_meaningful_unassigned']=len(meaningful_pending(final,request.elements));row['source_accounting']=account_source(request.elements,final);row['final_sections']=[s.category for s in final.sections]
   row['remaining_source_review']=bool(diagnostic['duplicate_candidates'] or diagnostic['independent_parser_unmatched_tokens']);row['record_relationship_accuracy']='NOT_ESTABLISHED'
  except Exception as e:
   row['error_type']=type(e).__name__ # Never print provider messages, keys or resume bodies.
  row['seconds']=round(time.monotonic()-started,2);rows.append(row);save(args.output/'checkpoints'/(identifier+'-run.json'),row)
  print(json.dumps({'completed':number,'total':15,'file':file,'status':row['status'],'api_calls':row['api_calls'],'unassigned':row.get('after_final_meaningful_unassigned')}),flush=True)
  save(args.output/'results.json',rows)
 summary={'scope':15,'completed':len(rows),'new_api_calls':sum(r['api_calls'] for r in rows),'llm_documents':sum(r['llm_called'] for r in rows),'local_only_documents':sum(r['status']=='local_all_assigned' for r in rows),'initial_meaningful_unassigned':sum(r.get('initial_meaningful_unassigned',0) for r in rows),'after_local_meaningful_unassigned':sum(r.get('after_local_meaningful_unassigned',0) for r in rows),'after_final_meaningful_unassigned':sum(r.get('after_final_meaningful_unassigned',0) for r in rows),'errors':sum(r['status']=='error' for r in rows),'provider_stop_reason':fatal,'semantic_accuracy':None,'word_accuracy':None,'human_ground_truth_independently_verified':False,'llm_policy':'only documents with meaningful unassigned spans after local recovery; all spans supplied as context/review','usage':dict(sum((Counter(r.get('usage',{})) for r in rows),Counter()))}
 save(args.output/'summary.json',summary)
 fields=['file','status','initial_meaningful_unassigned','after_local_meaningful_unassigned','after_final_meaningful_unassigned','llm_called','api_calls','llm_trigger','remaining_source_review','accuracy','seconds']
 with (args.output/'per-resume.csv').open('w',newline='') as stream:
  w=csv.DictWriter(stream,fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
 text=['# Fresh 15-resume local-first fallback run','','No human-verified accuracy percentage is available. Zero unassigned measures coverage of extracted text only. Known extraction and record-grouping defects require source review; this runner does not silently fix or hide them.','','```json',json.dumps(summary,indent=2),'```','','| Document | Initial unassigned | After local | Final | DeepSeek calls | Status |','|---|---:|---:|---:|---:|---|']
 for r in rows:text.append(f"| {r['file']} | {r.get('initial_meaningful_unassigned','?')} | {r.get('after_local_meaningful_unassigned','?')} | {r.get('after_final_meaningful_unassigned','?')} | {r['api_calls']} | {r['status']} |")
 text+=['','DeepSeek is skipped when the local stage assigns all meaningful text, even if it assigned something incorrectly. For failed local documents, full resume text is transmitted for relational context and all assignments may be reviewed. Extraction diagnostics do not by themselves trigger an API request. OCR retry occurs only for empty fast extraction; repeated identical local recovery stops immediately. This is bounded recovery, not an endless rerun or a guarantee of correctness.','', 'See results.json for per-document extraction diagnostics, local passes, exact span accounting, provider usage and error status. Original PDFs, annotations, caches and prior reports remain untouched.']
 (args.output/'report.md').write_text('\n'.join(text)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
