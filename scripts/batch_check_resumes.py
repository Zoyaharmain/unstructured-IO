"""Offline corpus audit: direct extraction + BERT/K-means + local recovery, no APIs.

Per-file details stay in the private output directory. Resume with the same output
and configuration; changed files/code are reprocessed. This is an invariant and
triage audit, not labeled semantic accuracy measurement.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SUPPORTED = {'.pdf', '.docx', '.doc'}


def forbid_network(*args, **kwargs):
    raise RuntimeError('Network access is forbidden by the offline corpus audit')


def offline_environment():
    os.environ.update(DEEPSEEK_REVIEW_ENABLED='false', HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', DO_NOT_TRACK='true',
                      UNSTRUCTURED_DISABLE_NOTICE='1', OMP_NUM_THREADS='1',
                      TOKENIZERS_PARALLELISM='false')
    os.environ.pop('DEEPSEEK_API_KEY', None)
    os.environ.setdefault('HF_HOME', str(ROOT / '.venv/model-cache'))
    os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/resume-audit-numba')
    os.environ.setdefault('MPLCONFIGDIR', '/tmp/resume-audit-mpl')
    # Guard outbound Python sockets as well as disabling known provider paths.
    socket.socket.connect = forbid_network
    socket.socket.connect_ex = forbid_network
    socket.create_connection = forbid_network


class DocumentDeadline(BaseException):
    """Do not let parser catch-all Exception handlers swallow the audit timer."""


def timeout_handler(*args):
    raise DocumentDeadline('Per-document deadline exceeded')


def initialize_worker():
    offline_environment()
    import logging
    logging.disable(logging.CRITICAL)
    from local_api.services.resume_sections import get_engine
    get_engine()  # One cached model per process, never one model load per resume.
    signal.signal(signal.SIGALRM, timeout_handler)


def tokens(text):
    return Counter(re.findall(r'\w+', text.casefold()))


from local_api.services.source_validation import validate_result


def process_document(path, relative, output, timeout, ocr_fallback, fingerprint):
    started = time.monotonic()
    row = {'file': relative, 'extension': Path(path).suffix.lower(), 'fingerprint': fingerprint,
           'status': 'error', 'flags': [], 'api_used': False}
    signal.alarm(timeout)
    try:
        from local_api.services.text_extraction_service import extract_text
        from local_api.schemas.sections import SectionRequest
        from local_api.services.resume_sections import get_engine
        from local_api.services.section_recovery import recover_sections
        payload = Path(path).read_bytes()
        row['sha256'] = hashlib.sha256(payload).hexdigest()
        row['bytes'] = len(payload)
        strategy = 'fast' if row['extension'] == '.pdf' else 'auto'
        extraction = extract_text(payload, Path(path).name, strategy=strategy)
        if not extraction.text.strip() and row['extension'] == '.pdf' and ocr_fallback:
            strategy = 'ocr_only'
            extraction = extract_text(payload, Path(path).name, strategy=strategy)
        row.update(strategy=strategy, characters=len(extraction.text), words=len(extraction.text.split()),
                   elements=len(extraction.elements or []), pages=extraction.metadata.page_numbers)
        if not extraction.text.strip():
            row.update(status='empty', flags=['no_extracted_text'])
        else:
            request = SectionRequest(elements=extraction.elements, extraction_verified=False)
            result = recover_sections(request, get_engine().detect(request))
            errors = validate_result(request.elements, result)
            row.update(status='invariant_failure' if errors else 'processed', invariant_errors=errors,
                       categories=[s.category for s in result.sections],
                       review_units=len(result.needs_review),
                       assigned_text_percent=result.metadata.get('assigned_text_percent'),
                       units=result.metadata.get('total_units'),
                       recovery=result.metadata.get('recovery'),
                       highlights=sum(len(s.highlights) for s in result.sections))
            if result.needs_review: row['flags'].append('unassigned_text')
            if row['characters'] < 150: row['flags'].append('very_little_text')
            if len(result.sections) < 3: row['flags'].append('few_sections')
            # An independent parser comparison is a diagnostic, not ground truth.
            if row['extension'] == '.pdf':
                from pypdf import PdfReader
                from io import BytesIO
                reference = tokens('\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(payload)).pages))
                actual = tokens(extraction.text)
                recall = sum((reference & actual).values()) / max(1, sum(reference.values()))
                row.update(reference_parser_tokens=sum(reference.values()), reference_parser_token_recall=round(recall, 4))
                if reference and recall < .90: row['flags'].append('parser_token_disagreement')
            target = Path(output) / 'documents' / (hashlib.sha256(relative.encode()).hexdigest()[:20] + '.json')
            target.write_text(json.dumps({'file':relative, 'extraction':extraction.model_dump(),
                                         'sections':result.model_dump()}, ensure_ascii=False))
            row['artifact'] = str(target.relative_to(output))
    except DocumentDeadline:
        row.update(status='timeout', error_type='TimeoutError')
    except Exception as exc:
        # Do not copy document text or arbitrary exception messages into summaries.
        row.update(error_type=type(exc).__name__)
        if hasattr(exc, 'status'): row['error_status'] = exc.status
    finally:
        signal.alarm(0)
    row['seconds'] = round(time.monotonic()-started, 3)
    return row


def write_summary(output, rows, inventory, elapsed):
    summary = {'files_discovered': len(inventory), 'files_completed':len(rows),
               'complete':len(rows)==len(inventory), 'api_calls':0, 'llm_review_exercised':False,
               'semantic_accuracy_measured':False, 'original_word_accuracy_measured':False,
               'statuses':dict(Counter(r['status'] for r in rows)),
               'formats':dict(Counter(r['extension'] for r in rows)),
               'flags':dict(Counter(f for r in rows for f in r['flags'])),
               'error_types':dict(Counter(r.get('error_type') for r in rows if r.get('error_type'))),
               'documents_with_unassigned_text':sum(bool(r.get('review_units')) for r in rows),
               'all_assigned_documents':sum(r['status']=='processed' and not r.get('review_units') for r in rows),
               'invariant_failure_documents':sum(r['status']=='invariant_failure' for r in rows),
               'retained_from_prior_revision':sum(bool(r.get('retained_from_prior_revision')) for r in rows),
               'elapsed_seconds_this_run':round(elapsed,1)}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'.upstream/batch-validation')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--limit',type=int)
    parser.add_argument('--no-ocr-fallback',action='store_true')
    parser.add_argument('--retry-failed',action='store_true',help='Recheck failed files; retain prior processed results even after code changes (not a fresh full-corpus rerun)')
    args=parser.parse_args()
    if not args.folder.is_dir():parser.error('Resume folder is unavailable')
    if not 1<=args.workers<=8 or args.timeout<1:parser.error('Use 1–8 workers and a positive timeout')
    offline_environment()
    output=args.output.resolve();(output/'documents').mkdir(parents=True,exist_ok=True)
    output.chmod(0o700)
    inventory=sorted(p for p in args.folder.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith('~$'))
    if args.limit:inventory=inventory[:args.limit]
    code=hashlib.sha256()
    for p in sorted((ROOT/'local_api').rglob('*.py'))+[Path(__file__)]+sorted((ROOT/'local_api/data').glob('*.json')):
        code.update(p.read_bytes())
    config=code.hexdigest()+str(not args.no_ocr_fallback)+str(args.timeout)
    ledger=output/'results.jsonl';old={}
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            try:r=json.loads(line);old[r['file']]=r
            except (ValueError,KeyError):pass
    rows=[];pending=[];started=time.monotonic()
    for path in inventory:
        relative=str(path.relative_to(args.folder));stat=path.stat()
        fp=hashlib.sha256(f'{config}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()
        previous = old.get(relative)
        cached = previous and previous.get('fingerprint') == fp
        if previous and args.retry_failed:
            cached = previous['status'] == 'processed'
        if cached:
            retained = dict(previous)
            if previous.get('fingerprint') != fp:
                retained['retained_from_prior_revision'] = True
            rows.append(retained)
        else:
            pending.append((path,relative,fp))
    print(json.dumps({'discovered':len(inventory),'cached':len(rows),'pending':len(pending),'api_calls':0}),flush=True)
    with ProcessPoolExecutor(max_workers=args.workers,initializer=initialize_worker) as pool, ledger.open('a') as stream:
        futures={pool.submit(process_document,str(p),rel,str(output),args.timeout,not args.no_ocr_fallback,fp):rel for p,rel,fp in pending}
        for future in as_completed(futures):
            row=future.result();rows.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            if len(rows)%25==0 or len(rows)==len(inventory):
                summary=write_summary(output,rows,inventory,time.monotonic()-started)
                print(json.dumps({'completed':len(rows),'total':len(inventory),'statuses':summary['statuses']}),flush=True)
    summary=write_summary(output,rows,inventory,time.monotonic()-started)
    (output/'current-results.json').write_text(json.dumps(sorted(rows,key=lambda r:r['file']),indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
