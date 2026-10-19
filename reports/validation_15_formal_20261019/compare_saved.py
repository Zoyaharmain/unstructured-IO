"""Compare existing predictions only. Does not import production models or API clients."""
import json,csv,re,hashlib
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=Path.cwd()
rows=json.loads((OUT/'artifact-inventory.json').read_text());details=[];deltas=[];bindings=[];splits=[]
def hash_elements(els):return hashlib.sha256(json.dumps([e['text'] for e in els],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def blocks(response):
 return [(b,s['category']) for s in response['sections'] for b in s['blocks']]+[(b,'needs_review') for b in response['needs_review']]
def label_map(response,els):
 labels=[[None]*len(e['text']) for e in els]
 for b,c in blocks(response):
  i,a,z=b['source_element_index'],b['start'],b['end'];assert b['text']==els[i]['text'][a:z]
  for j in range(a,z):assert labels[i][j] is None;labels[i][j]=c
 assert all(all(v is not None for v in l) for l in labels)
 return labels
for r in rows:
 local=json.loads((ROOT/r['local_path']).read_text());live=json.loads((ROOT/r['recovered_path']).read_text());els=local['extraction']['elements'];a=label_map(local['sections'],els);b=label_map(live['reviewed_sections'],els)
 changed=recovered=0
 for i,e in enumerate(els):
  start=0
  while start<len(e['text']):
   end=start+1
   while end<len(e['text']) and (a[i][end],b[i][end])==(a[i][start],b[i][start]):end+=1
   t=e['text'][start:end]
   if t.strip() and a[i][start]!=b[i][start]:
    deltas.append({'file':r['file'],'element':i,'page':e.get('page_number'),'start':start,'end':end,'local':a[i][start],'recovered':b[i][start],'text':t});changed+=sum(not c.isspace() for c in t)
    if a[i][start]=='needs_review':recovered+=sum(not c.isspace() for c in t)
   start=end
 for stage,response in [('local',local['sections']),('recovered',live['reviewed_sections'])]:
  for i,e in enumerate(els):
   for match in re.finditer('PostgreSQL|PGSQL',e['text'],re.I):
    touching=[(v,c) for v,c in blocks(response) if v['source_element_index']==i and v['start']<match.end() and v['end']>match.start()]
    if len(touching)>1:splits.append({'file':r['file'],'stage':stage,'element':i,'page':e.get('page_number'),'word':match.group(),'start':match.start(),'end':match.end(),'pieces':[{'text':v['text'],'start':v['start'],'end':v['end'],'category':c} for v,c in touching]})
 stem=Path(r['file']).stem.replace(' ','_').replace('(','').replace(')','');eh=hash_elements(els)
 for folder in ['ground_truth/drafts','ground_truth/gold','ground_truth/recovery_pilot/live-review/drafts']:
  p=ROOT/folder/(stem+'.json');ann=json.loads(p.read_text()) if p.exists() else {}
  bindings.append({'file':r['file'],'path':str(p.relative_to(ROOT)),'exists':p.exists(),'extraction_hash_matches':ann.get('extraction_sha256')==eh,'source_pdf_hash_recorded':ann.get('source_sha256') or ann.get('source_pdf_sha256'),'human_verified_claim':ann.get('human_verified'),'approved_bundle_sha256':ann.get('approved_bundle_sha256')})
 meaningful=lambda v:bool(v['text'].strip()) and els[v['source_element_index']].get('type')!='PageBreak' and not (els[v['source_element_index']].get('type')=='Footer' and re.fullmatch(r'\s*(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?\s*',v['text'],re.I))
 r.update(local_meaningful_unassigned=sum(meaningful(v) for v in local['sections']['needs_review']),recovered_meaningful_unassigned=sum(meaningful(v) for v in live['reviewed_sections']['needs_review']),changed_nonspace_characters=changed,recovered_nonspace_characters=recovered,exact_source_span_accounting=True,extraction_sha256=eh)
 # Expand each saved relationship group to its exact members for inspection.
 with (OUT/r['id']/'relationships.txt').open('w') as stream:
  for stage,response in [('local',local['sections']),('recovered',live['reviewed_sections'])]:
   for sec in response['sections']:
    if sec['category'] not in ['experience','education','projects']:continue
    for entry in sec['entries']:
     stream.write(f"\n{stage} {entry['entry_id']} lane={entry.get('lane')}\n")
     for index in entry['block_indices']:
      v=sec['blocks'][index];stream.write(f"block={index} e={v['source_element_index']} [{v['start']}:{v['end']}] p={v.get('page_number')} {v['text']}\n")
 details.append(r)
for name,value in [('comparison.json',details),('local-recovered-deltas.json',deltas),('annotation-bindings.json',bindings),('skill-splits.json',splits)]: (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False))
print('MEANINGFUL UNASSIGNED',sum(r['local_meaningful_unassigned'] for r in rows),'->',sum(r['recovered_meaningful_unassigned'] for r in rows));print('RAW',sum(r['local_unassigned'] for r in rows));print('SPLITS',json.dumps(splits,ensure_ascii=False));print('ANNOTATION_HASH_MISMATCHES',[v for v in bindings if not v['extraction_hash_matches']])
