"""Measure parent-array evidence separately; preserve strict raw leaf results."""
import json,sys
from pathlib import Path
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT))
from evaluate import source_support
summary=[]
for i in range(1,6):
 d=OUT/f'{i:02d}';raw=json.loads((d/'mapping-raw.json').read_text());blocks={x['source_id']:x['text'] for x in json.loads((d/'source-blocks.json').read_text())};rows=json.loads((d/'field-evaluation.json').read_text());supported_count=0;parent_count=0
 for row in rows:
  if not row['populated']:continue
  refs=row['evidence'];origin=row['path']
  if not refs:
   while '/' in origin[1:]:
    origin=origin.rsplit('/',1)[0];refs=raw['evidence'].get(origin,[])
    if refs:break
  quotes=[r['quote'] for r in refs if r.get('source_id') in blocks and isinstance(r.get('quote'),str) and r['quote'] in blocks[r['source_id']]]
  supported=bool(refs) and len(quotes)==len(refs) and source_support(row['value'],' '.join(quotes))
  supported_count+=supported;parent_count+=bool(supported and origin!=row['path'])
  row['inherited_provider_citation_supported']=bool(supported);row['provider_evidence_pointer_used_for_inheritance']=origin if refs else None
 (d/'field-evaluation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 summary.append({'document':i,'direct_or_parent_citation_supported':supported_count,'parent_inherited_supported_fields':parent_count})
(OUT/'inherited-citation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
