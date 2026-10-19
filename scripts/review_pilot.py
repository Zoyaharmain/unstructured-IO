"""Local-only human decision editor. Saves immutable revisions; never promotes gold."""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlparse,parse_qs

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.human_review_validation import sha,validate_bundle,validate_annotation,ATTESTATIONS


def catalog(manifest=None):
    if manifest is not None:
        entries=json.loads(Path(manifest).read_text());result={}
        for row in entries:
            doc={key: (ROOT/Path(row[key])).resolve() for key in ('draft','pdf','artifact')}
            doc['file']=row['file']
            if not all(doc[key].is_file() for key in ('draft','pdf','artifact')):raise ValueError('Review catalog source unavailable')
            identifier=row.get('id') or hashlib.sha256((row['file']+sha(doc['draft'])).encode()).hexdigest()[:20]
            if identifier in result:raise ValueError('Duplicate review catalog ID')
            result[identifier]=doc
        return result
    selected=json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text())
    result={}
    for item in selected:
        name=item['file'];stem=Path(name).stem.replace(' ','_').replace('(','').replace(')','')
        result[hashlib.sha256(name.encode()).hexdigest()[:20]]={'file':name,
            'draft':ROOT/'ground_truth/recovery_pilot/live-review/drafts'/(stem+'.json'),
            'pdf':ROOT/'ground_truth/pilot_resumes'/name,
            'artifact':ROOT/'.upstream/batch-validation'/item['artifact']}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8022);parser.add_argument('--catalog',type=Path);args=parser.parse_args()
    docs=catalog(args.catalog);output=ROOT/'ground_truth/human_review';output.mkdir(exist_ok=True);output.chmod(0o700)
    token=secrets.token_urlsafe(32);lock=threading.RLock()
    def revisions(identifier):return sorted((output/identifier).glob('revision-*.json')) if (output/identifier).exists() else []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,body,status=200,kind='application/json'):
            raw=body.encode() if isinstance(body,str) else body
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            parsed=urlparse(self.path);identifier=parse_qs(parsed.query).get('id',[''])[0]
            if parsed.path=='/':
                page=(ROOT/'scripts/pilot_review.html').read_text().replace('__TOKEN__',token)
                return self.send(page,kind='text/html; charset=utf-8')
            if parsed.path=='/documents':return self.send(json.dumps([{'id':key,'file':value['file'],'saved_revisions':len(revisions(key))} for key,value in docs.items()]))
            if identifier not in docs:return self.send('{}',404)
            doc=docs[identifier]
            if parsed.path=='/pdf':return self.send(doc['pdf'].read_bytes(),kind='application/pdf')
            if parsed.path=='/document':
                history=revisions(identifier);previous=json.loads(history[-1].read_text()) if history else None
                draft=json.loads(doc['draft'].read_text());artifact=json.loads(doc['artifact'].read_text())
                if previous and previous['draft_sha256']!=sha(doc['draft']):return self.send(json.dumps({'error':'Draft changed since saved review. Preserve/rebase decisions before continuing.'}),409)
                data={'id':identifier,'draft_sha256':sha(doc['draft']),'source_pdf_sha256':sha(doc['pdf']),
                      'annotation':previous['annotation'] if previous else draft,
                      'original_prediction':draft,'span_decisions':previous.get('span_decisions',{}) if previous else {},
                      'elements':artifact['extraction']['elements'],'revision':len(history),
                      'reviewer':previous.get('reviewer','') if previous else '',
                      'pdf_issues':previous.get('pdf_issues',[]) if previous else json.loads((output/'audit/content-blockers.json').read_text()).get(doc['file'],[]) if (output/'audit/content-blockers.json').exists() else [],'attestations':ATTESTATIONS,
                      'issues':validate_annotation(previous['annotation'] if previous else draft,artifact['extraction']['elements']),
                      'audit_changes':[r for r in json.loads((output/'audit/section-drift.json').read_text()) if r['file']==doc['file']] if (output/'audit/section-drift.json').exists() else [],
                      'assistant_notes':json.loads((output/'audit/review-notes.json').read_text()).get(doc['file'],[]) if (output/'audit/review-notes.json').exists() else []}
                return self.send(json.dumps(data))
            self.send('{}',404)
        def do_POST(self):
            if self.headers.get('X-Review-Token')!=token:return self.send('{}',403)
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://127.0.0.1:{args.port}',f'http://localhost:{args.port}'}:return self.send('{}',403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=4_000_000:raise ValueError('Invalid review size')
                body=json.loads(self.rfile.read(size));identifier=body['id'];doc=docs[identifier]
                with lock:
                    history=revisions(identifier)
                    if body.get('revision')!=len(history):return self.send(json.dumps({'error':'Review changed in another tab; reload before saving.'}),409)
                    if body.get('draft_sha256')!=sha(doc['draft']) or body.get('source_pdf_sha256')!=sha(doc['pdf']):raise ValueError('Source or draft hash changed; reload')
                    artifact=json.loads(doc['artifact'].read_text());elements=artifact['extraction']['elements']
                    body['annotation']['human_verified']=False
                    body['decision']='approve' if self.path in {'/approve','/validate'} else 'exclude' if self.path=='/exclude' else 'save'
                    body['recorded_at']=datetime.now(timezone.utc).isoformat()
                    body['original_prediction_sha256']=sha(doc['draft'])
                    body['revision']=len(history)+1
                    issues=validate_bundle(body,doc['draft'],doc['pdf'],elements)
                    if self.path=='/exclude':
                        issues=[]
                        from pypdf import PdfReader
                        if not body.get('reviewer','').strip() or not body.get('exclusion_reason','').strip():issues.append('Reviewer and exclusion reason required')
                        if sorted(set(body.get('reviewed_pages',[])))!=list(range(1,len(PdfReader(doc['pdf']).pages)+1)):issues.append('Check all original PDF pages before excluding')
                    if self.path in {'/approve','/exclude'} and issues:return self.send(json.dumps({'errors':issues}),422)
                    if self.path not in {'/save','/approve','/validate','/exclude'}:return self.send('{}',404)
                    if self.path=='/validate':return self.send(json.dumps({'errors':issues}))
                    directory=output/identifier;directory.mkdir(exist_ok=True)
                    with (directory/f"revision-{body['revision']:06d}.json").open('x') as stream:json.dump(body,stream,indent=2,ensure_ascii=False)
                    if self.path=='/approve':
                        with (directory/f"approved-{body['revision']:06d}.json").open('x') as stream:json.dump(body,stream,indent=2,ensure_ascii=False)
                    if self.path=='/exclude':
                        with (directory/f"excluded-{body['revision']:06d}.json").open('x') as stream:json.dump(body,stream,indent=2,ensure_ascii=False)
                    return self.send(json.dumps({'revision':body['revision'],'errors':issues,'approved_review':self.path=='/approve','gold_created':False,'excluded':self.path=='/exclude','review_bundle':str(directory/(f"approved-{body['revision']:06d}.json" if self.path=='/approve' else f"excluded-{body['revision']:06d}.json" if self.path=='/exclude' else f"revision-{body['revision']:06d}.json"))}))
            except (ValueError,KeyError,TypeError) as exc:self.send(json.dumps({'error':str(exc)}),400)
    print(f'Human review: http://127.0.0.1:{args.port} (no external API calls; no gold promotion)',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()


if __name__=='__main__':main()
