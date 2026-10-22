"""Field-level source checks. Does not call a provider or read/reparse PDFs."""
import csv,json,re,sys,unicodedata,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
OUT=Path(__file__).parent

def norm(v):
 return ' '.join(unicodedata.normalize('NFKC',str(v)).replace('•',' ').replace('●',' ').replace('▪',' ').casefold().split())
def leaves(value,path=''):
 if isinstance(value,dict):
  for key,v in value.items():yield from leaves(v,path+'/'+str(key).replace('~','~0').replace('/','~1'))
 elif isinstance(value,list):
  if not value:yield path,value
  else:
   for i,v in enumerate(value):yield from leaves(v,path+'/'+str(i))
 else:yield path,value

def source_support(value,text):
 if isinstance(value,(int,float)) and not isinstance(value,bool):
  return any(float(m.group())==float(value) for m in re.finditer(r'\d+(?:\.\d+)?',text))
 return bool(norm(value) and norm(value) in norm(text))

def evaluate_document(number):
 d=OUT/f'{number:02d}';raw=json.loads((d/'mapping-raw.json').read_text());data=json.loads((d/'mapping.json').read_text())
 blocks=json.loads((d/'source-blocks.json').read_text());sources={b['source_id']:b for b in blocks}
 alltext=' '.join(b['text'] for b in blocks);rows=[]
 for path,value in leaves(data):
  populated=value is not None and value!='' and value!=[]
  refs=raw.get('evidence',{}).get(path,[])
  errors=[];quotes=[]
  if populated and not refs:errors.append('missing_field_citation')
  if not isinstance(refs,list):errors.append('invalid_evidence_shape');refs=[]
  for ref in refs:
   if not isinstance(ref,dict):errors.append('invalid_reference_shape');continue
   source=ref.get('source_id');quote=ref.get('quote')
   if source not in sources:errors.append('unknown_source_id');continue
   if not isinstance(quote,str) or not quote or quote not in sources[source]['text']:
    errors.append('quote_not_exact_substring');continue
   quotes.append(quote)
  supported=populated and bool(quotes) and source_support(value,' '.join(quotes))
  global_support=populated and source_support(value,alltext)
  status='not_populated' if not populated else 'citation_supported' if supported and not errors else 'citation_error' if global_support else 'not_literal_in_source'
  rows.append({'path':path,'value':value,'populated':populated,'support_status':status,
   'evidence_errors':sorted(set(errors)),'value_supported_by_valid_cited_quotes':supported,
   'value_literal_somewhere_in_source':global_support,'evidence':refs,
   'source_text':[sources[r['source_id']]['text'] for r in refs if isinstance(r,dict) and r.get('source_id') in sources]})
 (d/'field-evaluation-automatic.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 return rows

if __name__=='__main__':
 for selection in json.loads((OUT/'selection.json').read_text()):
  number=selection['number'];d=OUT/f'{number:02d}'
  if not (d/'mapping.json').exists():continue
  rows=evaluate_document(number)
  print(number,'fields',sum(r['populated'] for r in rows),'citation supported',sum(r['support_status']=='citation_supported' for r in rows))
  for r in rows:
   if r['populated'] and r['support_status']!='citation_supported':print('CHECK',number,r['path'],str(r['value'])[:130],r['support_status'],r['evidence_errors'])
  a=json.loads((ROOT/selection['source_artifact']).read_text())
  local=map_schema(SchemaMappingRequest(elements=a['extraction']['elements'],sections=a['local_sections'],source=selection['file']))
  (d/'local-mapping-baseline.json').write_text(local.model_dump_json(indent=2)+'\n')
