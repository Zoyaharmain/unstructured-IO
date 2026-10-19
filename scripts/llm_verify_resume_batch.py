"""Review the saved corpus with DeepSeek: all assigned + unassigned spans together.

Paid calls are checkpointed per document. No automatic transport retries. API keys
come from the process environment only. Resume bodies and filenames stay private.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import replace
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from local_api.schemas.extraction import ExtractionResponse
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.llm_section_review import (ReviewSettings, ReviewError,
    provider_json, review_sections, check_connection)
from scripts.batch_check_resumes import validate_result

FATAL = {'authentication_failed','insufficient_balance','provider_forbidden','model_unavailable','invalid_configuration'}


def write_json(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    tmp.replace(path)


def summarize(output,inventory,rows,stop_reason=None):
    statuses=Counter(row['status'] for row in rows.values())
    calls=sum(row.get('api_calls',0) for row in rows.values())
    usage=Counter()
    for row in rows.values():
        for key,value in row.get('usage',{}).items():
            if isinstance(value,int):usage[key]+=value
    summary={'scope_documents':len(inventory),'documents_completed':len(rows),
             'not_attempted':len(inventory)-len(rows),'all_documents_attempted':len(rows)==len(inventory),
             'statuses':dict(statuses),'provider':'DeepSeek','classification_api_calls':calls,
             'usage':dict(usage),'stop_reason':stop_reason,
             'llm_review_is_ground_truth':False,'original_word_accuracy_measured':False}
    write_json(output/'summary.json',summary)
    write_json(output/'current-results.json',sorted(rows.values(),key=lambda r:r['file']))
    return summary


def review_document(row,source,output,folder,settings):
    started=time.monotonic();identifier=hashlib.sha256(row['file'].encode()).hexdigest()[:20]
    record={'file':row['file'],'id':identifier,'extension':row['extension'],'status':'review_failed',
            'api_calls':0,'usage':{},'source_reextracted':False,'local_before':{},'provider':'DeepSeek','model':settings.model}
    usage=Counter();responses=[]
    try:
        if row.get('artifact'):
            artifact=json.loads((source/row['artifact']).read_text())
            extraction=ExtractionResponse.model_validate(artifact['extraction'])
            local=SectionResponse.model_validate(artifact['sections'])
        else:
            # Only the six original batch failures are retried, within this scope.
            from local_api.services.text_extraction_service import extract_text
            from local_api.services.resume_sections import get_engine
            from local_api.services.section_recovery import recover_sections
            path=folder/row['file']
            extraction=extract_text(path.read_bytes(),path.name,strategy='fast' if path.suffix.lower()=='.pdf' else 'auto')
            request=SectionRequest(elements=extraction.elements,extraction_verified=False)
            local=recover_sections(request,get_engine().detect(request))
            record['source_reextracted']=True
        request=SectionRequest(elements=extraction.elements,extraction_verified=False)
        record['local_before']={'sections':len(local.sections),'review_units':len(local.needs_review),
                                'categories':[s.category for s in local.sections]}
        def transport(config,messages):
            record['api_calls']+=1
            envelope=provider_json(config,'/chat/completions',{
                'model':config.model,'messages':messages,'stream':False,
                'response_format':{'type':'json_object'},'thinking':{'type':config.thinking},'max_tokens':config.max_tokens})
            for key,value in envelope.get('usage',{}).items():
                if isinstance(value,int):usage[key]+=value
            try:
                choice=envelope['choices'][0]
                responses.append({'finish_reason':choice.get('finish_reason'),'content':choice['message'].get('content')})
                if choice.get('finish_reason')!='stop':raise ReviewError('incomplete_response')
                return choice['message']['content']
            except (KeyError,IndexError,TypeError):raise ReviewError('invalid_response') from None
        final=review_sections(request,local,settings=settings,transport=transport)
        state=final.metadata.get('llm_review',{})
        errors=validate_result(request.elements,final)
        record.update(llm_review=state,invariant_errors=errors,review_units=len(final.needs_review),
                      review_characters=sum(len(b.text.strip()) for b in final.needs_review),
                      sections=len(final.sections),categories=[s.category for s in final.sections])
        if errors:record['status']='invariant_failure'
        elif state.get('status')!='complete':
            record.update(status='review_failed',error_code=state.get('error_code',state.get('status','unknown')))
        elif not final.sections:record['status']='llm_reviewed_no_sections'
        elif final.needs_review:record['status']='llm_reviewed_needs_review'
        else:record['status']='llm_reviewed_all_assigned'
        artifact={'file':row['file'],'extraction':extraction.model_dump(),'local_sections':local.model_dump(),
                  'reviewed_sections':final.model_dump()}
        write_json(output/'documents'/(identifier+'.json'),artifact)
        record['artifact']='documents/'+identifier+'.json'
    except Exception as exc:
        record.update(status='extraction_failed' if not record['api_calls'] else 'review_failed',error_type=type(exc).__name__)
        if hasattr(exc,'status'):record['error_status']=exc.status
        if isinstance(exc,ReviewError):record['error_code']=str(exc)
    finally:
        record['usage']=dict(usage)
        record['seconds']=round(time.monotonic()-started,2)
        if responses:write_json(output/'provider-decisions'/(identifier+'.json'),responses)
        # Per-document atomic checkpoint prevents a second paid call on resume.
        write_json(output/'checkpoints'/(identifier+'.json'),record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=8)
    parser.add_argument('--limit',type=int,help='Limit NEW attempts, retaining the full saved scope in reports')
    parser.add_argument('--retry-failed',action='store_true')
    args=parser.parse_args()
    if not 1<=args.workers<=16:parser.error('Workers must be between 1 and 16')
    settings=replace(ReviewSettings.from_env(),enabled=True,max_units=1000,max_input_chars=1_000_000,timeout=120)
    settings.validate()
    if not settings.api_key:parser.error('DEEPSEEK_API_KEY must be set privately in the process environment')
    logging.basicConfig(level=logging.ERROR)
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
    output=args.output;output.mkdir(parents=True,exist_ok=True);output.chmod(0o700)
    for name in ('documents','provider-decisions','checkpoints'):(output/name).mkdir(exist_ok=True)
    inventory=json.loads((args.source/'current-results.json').read_text())
    # Freeze source selection: no other resumes or previously untested files enter.
    scope=output/'scope.json'
    selected=[row['file'] for row in inventory]
    if scope.exists() and json.loads(scope.read_text())!=selected:parser.error('Saved LLM scope differs from source; use a new output directory')
    write_json(scope,selected)
    records={}
    for path in (output/'checkpoints').glob('*.json'):
        record=json.loads(path.read_text())
        if record.get('file') in selected:records[record['file']]=record
    pending=[row for row in inventory if row['file'] not in records or (args.retry_failed and records[row['file']]['status'] in {'review_failed','extraction_failed','invariant_failure'})]
    if args.limit is not None:pending=pending[:args.limit]
    connection=check_connection()
    if connection['status']!='ready':
        summary=summarize(output,inventory,records,connection.get('error_code','connection_not_ready'))
        print(json.dumps({'connection':connection,'summary':summary}),flush=True);return
    print(json.dumps({'scope':len(inventory),'cached':len(records),'new_attempts':len(pending),'workers':args.workers,'model':settings.model,'connection':'ready'}),flush=True)
    iterator=iter(pending);stop_reason=None;failure_streak=0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        active={}
        def submit():
            try:row=next(iterator)
            except StopIteration:return False
            active[pool.submit(review_document,row,args.source,output,args.folder,settings)]=row['file'];return True
        for _ in range(args.workers):
            if not submit():break
        while active:
            finished,_=wait(active,return_when=FIRST_COMPLETED)
            for future in finished:
                active.pop(future)
                record=future.result();records[record['file']]=record
                code=record.get('error_code') or record.get('llm_review',{}).get('recovery_error_code')
                if code in FATAL:stop_reason=code
                if code in {'provider_unavailable','rate_limited'}:failure_streak+=1
                elif record['status'].startswith('llm_reviewed'):failure_streak=0
                if failure_streak>=5:stop_reason='repeated_provider_failures'
                summary=summarize(output,inventory,records,stop_reason)
                print(json.dumps({'completed':len(records),'scope':len(inventory),'statuses':summary['statuses'],'api_calls':summary['classification_api_calls'],'stop_reason':stop_reason}),flush=True)
                if not stop_reason:submit()
    print(json.dumps(summarize(output,inventory,records,stop_reason),indent=2),flush=True)


if __name__=='__main__':main()
