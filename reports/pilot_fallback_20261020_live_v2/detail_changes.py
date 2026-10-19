import json,csv,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent;rows=json.loads((out/'results.json').read_text());changes=[];pending=[];assigned=total=0
for r in rows:
 id=hashlib.sha256(r['file'].encode()).hexdigest()[:20];a=json.loads((out/'documents'/(id+'.json')).read_text());els=a['extraction']['elements'];local=a.get('local_sections',a['sections']);final=a.get('reviewed_sections',local)
 def spans(response):return [(b,s['category']) for s in response['sections'] for b in s['blocks']]+[(b,'needs_review') for b in response['needs_review']]
 def maps(response):
  m=[[None]*len(e['text']) for e in els]
  for b,c in spans(response):m[b['source_element_index']][b['start']:b['end']]=[c]*(b['end']-b['start'])
  return m
 before,after=maps(local),maps(final)
 for i,e in enumerate(els):
  start=0
  while start<len(e['text']):
   end=start+1
   while end<len(e['text']) and (before[i][start],after[i][start])==(before[i][end],after[i][end]):end+=1
   t=e['text'][start:end]
   if t.strip() and before[i][start]!=after[i][start]:changes.append({'file':r['file'],'page':e.get('page_number'),'element':i,'start':start,'end':end,'local_section':before[i][start],'final_section':after[i][start],'text':t})
   start=end
 for outcome in r['source_accounting']['outcomes']:
  if outcome['outcome']=='non_content_artifact':continue
  text=els[outcome['source_element_index']]['text'][outcome['start']:outcome['end']];n=sum(not c.isspace() for c in text);total+=n;assigned+=n if outcome['outcome']=='assigned' else 0
 for b in final['needs_review']:
  if b['text'].strip():pending.append({'file':r['file'],'page':b.get('page_number'),'element':b['source_element_index'],'start':b['start'],'end':b['end'],'text':b['text']})
for name,data in [('llm-assignment-changes.csv',changes),('remaining-unassigned.csv',pending)]:
 with (out/name).open('w',newline='') as f:
  if data:w=csv.DictWriter(f,list(data[0]));w.writeheader();w.writerows(data)
summary=json.loads((out/'summary.json').read_text());summary['meaningful_extracted_character_assignment_coverage']=assigned/total;summary['assigned_meaningful_nonspace_characters']=assigned;summary['total_meaningful_nonspace_characters']=total;summary['documents_all_meaningful_text_assigned']=sum(r.get('after_final_meaningful_unassigned')==0 for r in rows);summary['coverage_is_semantic_accuracy']=False;(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
p=out/'report.md';p.write_text(p.read_text()+f'\n## Additional measured coverage\n\n{assigned:,}/{total:,} meaningful extracted non-whitespace characters assigned: **{assigned/total:.2%} coverage**, not word or section accuracy. {summary["documents_all_meaningful_text_assigned"]}/15 documents have all meaningful extracted text assigned. See llm-assignment-changes.csv for {len(changes)} changed intervals (a change is not automatically correct), and remaining-unassigned.csv for {len(pending)} remaining nonempty spans. Provider input cache hits are provider billing metadata; all 15 classification requests were live, not reuse of a saved local LLM response.\n\nEight offline checks passed for bounded scope, meaningful fallback gating and private configuration loading. The first live startup stopped before any API calls due to missing python-dotenv; the runner now reads simple DEEPSEEK_ configuration without that dependency or shell execution. No application endpoint behavior was changed; this policy is implemented by scripts/check_pilot_fallback.py.\n')
print(json.dumps(summary,indent=2))
