"""Prepare read-only acceptance evidence; never approve, relabel or call a provider."""
import csv,hashlib,html,json,os,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.review_pilot import catalog
from scripts.human_review_validation import validate_annotation,sha
OUT=Path(__file__).resolve().parent
AUDIT=ROOT/'reports/project-readiness-audit-20261021'
def write(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def link(path):return html.escape(os.path.relpath(path,OUT),quote=True)
def main():
 before={str(path):sha(path) for d in catalog().values() for path in (d['pdf'],d['draft'],d['artifact'])}
 issues=json.loads((ROOT/'ground_truth/human_review/audit/content-blockers.json').read_text())
 pilots=[]
 for ident,doc in catalog().items():
  draft=json.loads(doc['draft'].read_text());artifact=json.loads(doc['artifact'].read_text())
  elements=artifact['extraction']['elements'];errors=validate_annotation(draft,elements)
  pilots.append({'id':ident,'file':doc['file'],'pdf_sha256':sha(doc['pdf']),'draft_sha256':sha(doc['draft']),
    'pages':sorted({e['page_number'] for e in elements if e.get('page_number') is not None}),
    'span_count':len(draft['spans']),'annotation_issues':errors,'known_pdf_issues':issues.get(doc['file'],[]),
    'human_approved':False,'pdf':str(doc['pdf']),'draft':str(doc['draft'])})
 write('pilot-preflight.json',pilots)
 audit=json.loads((AUDIT/'inventory-v2/audit.json').read_text())
 index={(d['sha256'],d['run']):d for d in audit['documents']}
 with (AUDIT/'inventory-v2/latest-distinct-documents.csv').open() as f:latest=list(csv.DictReader(f))
 queue=[]
 for row in latest:
  d=index[(row['sha256'],row['run'])];q=d['quality_assessment'];reasons=[]
  if not d['artifact_binding'] or d['integrity_errors']:reasons.append('source_or_interval_integrity')
  if d['saved_review_status']=='review_failed':reasons.append('historical_provider_failure')
  if d['current_scope']['candidate_resume'] is False:reasons.append('document_scope_decision')
  if q['source_fidelity']['ocr_reference_needed'] or q['source_fidelity']['damaged_glyph_elements']:reasons.append('pdf_text_or_ocr_check')
  if d['candidate_meaningful_unassigned']:reasons.append('meaningful_unknown_text')
  relationships=q['relationship_correctness']['sections']
  for category,details in relationships.items():
   if details['entries_needing_review'] or details['unlinked_block_indices']:reasons.append(category+'_association_review')
  priority=0 if 'source_or_interval_integrity' in reasons else 1 if any(r in reasons for r in ['historical_provider_failure','document_scope_decision','pdf_text_or_ocr_check']) else 2 if reasons else 3
  queue.append({**d,'priority':priority,'review_reasons':reasons or ['independent_semantic_sample_required']})
 queue.sort(key=lambda d:(d['priority'],d['file']))
 write('all-350-review-queue.json',queue)
 with (OUT/'all-350-review-queue.csv').open('x',newline='') as f:
  fields=['priority','file','sha256','run','saved_review_status','candidate_meaningful_unassigned','review_reasons'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for d in queue:w.writerow({k:'; '.join(d[k]) if k=='review_reasons' else d[k] for k in fields})
 # Use current replay source accounting to separate artifacts from meaningful unknowns.
 run=AUDIT/'offline-100';pending=[]
 for row in json.loads((run/'deepseek/current-results.json').read_text()):
  a=json.loads((run/'deepseek'/row['artifact']).read_text());res=a['reviewed_sections']
  meaningful={o['source_id'] for o in res['metadata']['source_accounting']['outcomes'] if o['outcome']=='human_review'}
  for b in res['needs_review']:
   sid=f"e{b['source_element_index']}:{b['start']}:{b['end']}"
   if sid in meaningful:pending.append({'file':row['file'],'source_id':sid,'page':b.get('page_number'),'text':b['text'],'decision':'unverified_policy_or_section_review_required'})
 write('latest-100-meaningful-spans.json',pending)
 cards=[]
 for d in pilots:
  cards.append('<article><h3>'+html.escape(d['file'])+'</h3><a href="'+link(Path(d['pdf']))+'">Original PDF</a><p>'+str(d['span_count'])+' spans; '+str(len(d['annotation_issues']))+' structural/field issues; '+str(len(d['known_pdf_issues']))+' known PDF issues.</p><details><summary>Issues to check before approval</summary><pre>'+html.escape(json.dumps({'annotation':d['annotation_issues'],'pdf':d['known_pdf_issues']},indent=2))+'</pre></details></article>')
 for d in queue:
  pdf=ROOT/'reports'/d['run']/'selected-pdfs'/d['file']
  cards.append('<details><summary>Priority '+str(d['priority'])+' · '+html.escape(d['file'])+'</summary><a href="'+link(pdf)+'">Original copied PDF</a><p>'+html.escape('; '.join(d['review_reasons']))+'</p><p>Historical live status: '+html.escape(d['saved_review_status'])+'. This queue is not an approval.</p><pre>'+html.escape(json.dumps({'scope':d['current_scope'],'relationships':d['quality_assessment']['relationship_correctness'],'source_fidelity':d['quality_assessment']['source_fidelity'],'unknown_source_text_including_retained_artifacts':d['remaining_source_text']},indent=2,ensure_ascii=False))+'</pre></details>')
 (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Acceptance review queue</title><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:auto;padding:24px}article,details{padding:12px;border:1px solid #ddd;margin:12px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}</style><h1>Acceptance review: scaling is on hold</h1><p>Start with the 15 pilot documents below. <a href="http://127.0.0.1:8022">Open the human decision editor</a>. No approval is recorded by opening this page. All 350 distinct documents follow, prioritized using saved evidence.</p>'+''.join(cards))
 preservation={'checked':len(before),'changed':[name for name,h in before.items() if sha(Path(name))!=h]};write('pilot-preservation.json',preservation)
 summary={'distinct_documents':len(queue),'priority_counts':dict(Counter(d['priority'] for d in queue)),'pilot_documents':len(pilots),'pilot_structural_issues':sum(len(d['annotation_issues']) for d in pilots),'pilot_documents_with_known_pdf_issues':sum(bool(d['known_pdf_issues']) for d in pilots),'latest_100_meaningful_spans':len(pending),'new_api_calls':0,'human_approvals_created':0,'ready_to_scale':False,'pilot_preservation':preservation}
 write('summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
