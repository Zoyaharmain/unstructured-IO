import csv,html,json,os
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'repaired-350';rows=json.loads((out/'current-results.json').read_text());review=[];cards=[]
for row in rows:
 a=json.loads(Path(row['artifact']).read_text());res=a['repaired_sections'];meta=res['metadata'];q=meta['quality_assessment'];scope=q['document_scope'];relations=q['relationship_correctness']['sections']
 pending=meta['source_accounting']['unresolved_meaningful_spans'];unlinked=sum(len(v['unlinked_block_indices']) for v in relations.values());entryflags=sum(len(v['entries_needing_review']) for v in relations.values());fidelity=q['source_fidelity']
 review.append({'file':row['file'],'sha256':row['sha256'],'repair_status':row['repair_status'],'candidate_resume':scope['candidate_resume'],'meaningful_unknown_spans':pending,'unlinked_record_blocks':unlinked,'records_with_warnings':entryflags,'ocr_reference_needed':fidelity['ocr_reference_needed'],'damaged_glyph_elements':fidelity['damaged_glyph_elements'],'human_verified':False})
 groups=[]
 for section in res['sections']:
  if section['category'] not in {'experience','education'}:continue
  for entry in section['entries']:
   blocks=[section['blocks'][i] for i in entry['block_indices']]
   groups.append({'category':section['category'],'record':entry['entry_id'],'warnings':entry['review_reasons'],'members':[{'source_id':f"e{b['source_element_index']}:{b['start']}:{b['end']}",'page':b['page_number'],'text':b['text']} for b in blocks]})
 source=Path(meta.get('record_repair',{}).get('source_artifact',''))
 # Source PDF paths are recoverable from the prior live inventory's run column.
 cards.append('<details><summary>'+html.escape(row['file'])+' · '+html.escape(row['repair_status'])+'</summary><p><a href="'+html.escape(os.path.relpath(row['artifact'],p),quote=True)+'">Repaired artifact with extraction/source evidence</a></p><pre>'+html.escape(json.dumps({'source_issues':fidelity,'scope':scope,'pending_text':res['needs_review'],'records':groups},indent=2,ensure_ascii=False))+'</pre></details>')
with (p/'remaining-review-queue.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(review[0]));w.writeheader();w.writerows(review)
summary={'documents':len(review),'candidate_meaningful_unknown_spans':sum(r['meaningful_unknown_spans'] for r in review if r['candidate_resume'] is not False),'non_resume_meaningful_unknown_spans':sum(r['meaningful_unknown_spans'] for r in review if r['candidate_resume'] is False),'documents_requiring_ocr_reference':sum(r['ocr_reference_needed'] for r in review),'documents_with_damaged_glyphs':sum(bool(r['damaged_glyph_elements']) for r in review),'documents_with_unlinked_record_blocks':sum(bool(r['unlinked_record_blocks']) for r in review),'documents_with_record_warnings':sum(bool(r['records_with_warnings']) for r in review),'human_verified_documents':0}
(p/'remaining-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(p/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Existing 350 repair results</title><style>body{font:16px/1.6 system-ui;max-width:1200px;margin:auto;padding:24px}details{border:1px solid #ccc;padding:12px;margin:10px 0}summary{cursor:pointer;font-weight:bold}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Existing 350 repair results</h1><p>Source-supported automated proposals. No human approvals; no new resume batch. <a href="report.md">Repair report</a> · <a href="remaining-review-queue.csv">Remaining review queue</a></p>'+''.join(cards))
print(json.dumps(summary,indent=2))
