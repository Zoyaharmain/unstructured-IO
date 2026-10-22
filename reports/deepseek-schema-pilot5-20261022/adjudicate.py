"""AI analyst source-block adjudication; no provider calls or PDF examination."""
import csv,json,re,sys
from collections import Counter
from pathlib import Path
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT))
from evaluate import norm,leaves,source_support

def tokens(v):return [w for w in re.findall(r'\w+',norm(v)) if w!='in']
def contains(expected,actual):
 a=tokens(expected);b=tokens(actual)
 return any(b[i:i+len(a)]==a for i in range(len(b)-len(a)+1))
def get(data,field):
 for key in field.split('.'):
  if not isinstance(data,dict):return None
  data=data.get(key)
 return data

def fact_check(fact,data):
 collection=fact['collection'];field=fact['field'];expected=fact['expected']
 if collection=='root':value=get(data,field);path='/'+field.replace('.','/');record=data
 else:
  candidates=[]
  for i,record in enumerate(data[collection]):
   yes=True
   for key,selector in fact['selector'].items():
    candidate=record.get(key,'') or ''
    if key=='degree':candidate += ' '+(record.get('field_of_study') or '')
    if not contains(selector,candidate):yes=False
   if yes:candidates.append((i,record))
  if len(candidates)!=1:return {'status':'missing_assignment' if not candidates else 'ambiguous','actual':None,'path':None,'reason':'No uniquely matching record'}
  i,record=candidates[0];value=record.get(field);path=f'/{collection}/{i}/{field}'
 if fact['document']==1 and collection=='experience' and fact['selector']['company']=='Godavari Cuts' and field in {'start_date','end_date'}:
  return {'status':'ambiguous','actual':value,'path':path,'reason':'Date range is attached to previous employer block. Association is not independently established from the block inventory; retained in conservative denominator.'}
 if value is None or value=='':return {'status':'missing_assignment','actual':value,'path':path,'reason':'Source-supported reference opportunity unassigned'}
 if field=='degree':value_to_compare=value+' '+(record.get('field_of_study') or '')
 else:value_to_compare=value
 if isinstance(expected,(float,int)):correct=isinstance(value,(float,int)) and float(expected)==float(value)
 elif field in {'start_year','graduation_year'}:correct=str(expected) in re.findall(r'\b(?:19|20)\d{2}\b',str(value))
 else:correct=contains(expected,value_to_compare)
 return {'status':'correct_mapping' if correct else 'incorrect_mapping','actual':value,'path':path,
  'reason':'Normalized source-fact agreement; degree/major splits, original month-year strings, label prefixes and enclosing organization context accepted' if correct else 'Value differs from selected source-supported fact'}


def reviewer_evidence(value,blocks):
 # Independent local lookup against immutable blocks; do not attribute it to LLM.
 if isinstance(value,(float,int)):
  candidates=[b for b in blocks if source_support(value,b['text']) and re.search(r'experience|years',b['text'],re.I)]
  return [{'source_id':b['source_id'],'quote':b['text']} for b in candidates[:1]]
 value_norm=norm(value);canonical='';positions=[]
 for b in blocks:
  t=norm(b['text'])
  if not t:continue
  if canonical:canonical+=' '
  start=len(canonical);canonical+=t;positions.append((start,len(canonical),b))
 start=canonical.find(value_norm)
 if start>=0:
  end=start+len(value_norm)
  return [{'source_id':b['source_id'],'quote':b['text']} for a,z,b in positions if z>start and a<end]
 # A source date is interleaved inside the thesis sentence; explicit exact segments.
 if isinstance(value,str) and value.startswith('Master’s Thesis: “Appearance based terrain learning'):
  return [{'source_id':'e34:58:163','quote':'Master’s Thesis: “Appearance based terrain learning and classification for'},
          {'source_id':'e34:58:163','quote':'autonomous'},
          {'source_id':'e35:0:76','quote':'mobile robot navigation”, advised by Prof Prabhakar Mishra.'}]
 return []

ambiguous={1:{'/experience/1/end_date','/experience/1/duration'},2:{'/professional_title'},3:set(),4:set(),5:{'/contact/email','/education/0/graduation_year','/education/1/graduation_year','/experience/4/start_date','/experience/4/end_date','/experience/4/duration','/experience/4/location'}}
missing_findings={5:[{'path':'/education/0/field_of_study','status':'missing_assignment','expected':'Intelligent Systems','source_ids':['e8:38:82'],'reason':'Explicit specialization in degree; schema has a separate field, but mapper leaves it null.'},
 {'path':'/education/1/field_of_study','status':'missing_assignment','expected':'Electronics and Communication','source_ids':['e8:120:176'],'reason':'Explicit specialization in degree; kept in degree text but not assigned to available specialization field.'}]}
reference=json.loads((OUT/'reference-facts.json').read_text())['facts'];summary=[];allfields=[];allfacts=[]
for doc in json.loads((OUT/'selection.json').read_text()):
 n=doc['number'];p=OUT/f'{n:02d}';data=json.loads((p/'mapping.json').read_text());blocks=json.loads((p/'source-blocks.json').read_text());byid={b['source_id']:b['text'] for b in blocks}
 auto=json.loads((p/'field-evaluation-automatic.json').read_text());raw=json.loads((p/'mapping-raw.json').read_text())
 for row in auto:
  row['document']=n;row['analyst_evidence']=reviewer_evidence(row['value'],blocks) if row['populated'] else []
  if row['populated'] and not row['analyst_evidence'] and row['support_status']=='citation_supported':
   row['analyst_evidence'] = row['evidence']  # Exact quotes already checked independently against saved blocks.
  row['evidence_origin']='analyst-derived from saved blocks; raw LLM evidence preserved separately'
  row['analyst_notes']=[]
  row['provider_missing_information']=[m for m in raw.get('missing_information',[]) if row['path'] in m.get('path','') or m.get('path')==row['path']]
  path=row['path'];value=row['value']
  if not row['populated']:row['mapping_status']='not_populated'
  elif not row['analyst_evidence']:row['mapping_status']='unsupported_value'
  elif path in ambiguous[n] or n==3 and path.startswith('/experience/1/') or n==5 and path.startswith('/experience/1/'):
   row['mapping_status']='ambiguous'
   row['analyst_notes'].append('Source text is present, but role/record classification, primary contact choice or detached-date association remains uncertain; not counted as confirmed correct.')
  else:row['mapping_status']='correct_mapping'
  if '/education/' in path and path.endswith(('/start_year','/graduation_year')) and value and not re.fullmatch(r'\d{4}',str(value)):
   row['analyst_notes'].append('Noncanonical year formatting: original month-year string is source-supported and schema accepts string; normalize to year only if field policy requires it. Not an invented date.')
  if row['populated'] and row['support_status']!='citation_supported':
   row['analyst_notes'].append('Raw provider citation contract fails; analyst traceability does not repair the original provider response.')
  if n==5 and path=='/experience/1/responsibilities/0':
   row['analyst_notes'].append('Sentence reconstructable by excluding embedded date from e34; provider incorrectly cites autonomous as part of e35. Value content supported, quote attribution incorrect.')
  for ref in row['analyst_evidence']:assert ref['source_id'] in byid and ref['quote'] in byid[ref['source_id']],ref
 if n==4:
  auto.append({'document':n,'path':'/experience/3/responsibilities/-','value':None,'populated':False,
   'mapping_status':'missing_assignment','support_status':'not_emitted','evidence_errors':[],
   'value_supported_by_valid_cited_quotes':False,'value_literal_somewhere_in_source':False,
   'evidence':[],'source_text':[],'analyst_evidence':[{'source_id':'e61:0:56','quote':byid['e61:0:56']}],
   'evidence_origin':'analyst-derived source opportunity, not an emitted model leaf',
   'missing_opportunity':True,'expected':byid['e61:0:56'],
   'analyst_notes':['Source Tag Mapping / IMPS work item is absent from the mapped NPCI responsibilities and project names/descriptions. The append-marker path is an expected missing array item, not a real emitted JSON field.'],
   'provider_missing_information':[]})
 for finding in missing_findings.get(n,[]):
  row=next(r for r in auto if r['path']==finding['path']);row['mapping_status']='missing_assignment';row['analyst_notes'].append(finding['reason']);row['expected']=finding['expected'];row['analyst_evidence']=[{'source_id':sid,'quote':byid[sid]} for sid in finding['source_ids']]
 facts=[]
 for f in reference:
  if f['document']!=n:continue
  facts.append({**f,**fact_check(f,data)})
 baseline=json.loads((p/'local-mapping-baseline.json').read_text())['data']
 baselinefacts=[{**f,**fact_check(f,baseline)} for f in reference if f['document']==n]
 (p/'field-evaluation.json').write_text(json.dumps(auto,ensure_ascii=False,indent=2)+'\n')
 (p/'critical-fact-evaluation.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
 (p/'baseline-critical-fact-evaluation.json').write_text(json.dumps(baselinefacts,ensure_ascii=False,indent=2)+'\n')
 numerator=sum(f['status']=='correct_mapping' for f in facts);denominator=len(facts)
 counts=Counter(r['mapping_status'] for r in auto)
 result={'document':n,'file':doc['file'],'populated_scalar_fields':sum(r['populated'] for r in auto),
  'raw_citation_supported':sum(r['support_status']=='citation_supported' for r in auto),
  'analyst_mapping_status_counts':dict(counts),'critical_facts_correct':numerator,'critical_fact_denominator':denominator,
  'critical_agreement_percent':round(100*numerator/denominator,2),'critical_fact_statuses':dict(Counter(f['status'] for f in facts)),
  'baseline_critical_correct':sum(f['status']=='correct_mapping' for f in baselinefacts),
  'raw_evidence_missing_fields':sum('missing_field_citation' in r['evidence_errors'] for r in auto),
  'raw_quote_errors':sum('quote_not_exact_substring' in r['evidence_errors'] for r in auto),
  'human_or_pdf_verified':False}
 summary.append(result);allfields+=auto;allfacts+=facts
 (p/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 print(n,result)
ledger=json.loads((OUT/'call-ledger.json').read_text())
overall={'documents':5,'mapping_calls':len(ledger),'valid_schema_outputs':sum(c['status']=='mapped_schema_valid' for c in ledger),
 'populated_scalar_fields':sum(r['populated_scalar_fields'] for r in summary),
 'raw_citation_supported':sum(r['raw_citation_supported'] for r in summary),
 'critical_facts_correct':sum(r['critical_facts_correct'] for r in summary),
 'critical_fact_denominator':len(reference),'baseline_critical_correct':sum(r['baseline_critical_correct'] for r in summary),
 'analyst_mapping_status_counts':dict(Counter(r['mapping_status'] for r in allfields)),
 'usage':{k:sum(c['usage'].get(k,0) for c in ledger) for k in ['prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens']},
 'human_verified_accuracy':None,'original_pdf_accuracy':None,'extra_mapping_calls_authorized':False}
overall['critical_agreement_percent']=round(100*overall['critical_facts_correct']/len(reference),2)
overall['raw_citation_support_percent']=round(100*overall['raw_citation_supported']/overall['populated_scalar_fields'],2)
(OUT/'summary.json').write_text(json.dumps({'overall':overall,'per_resume':summary},indent=2)+'\n')
with (OUT/'field-evaluation.csv').open('w',newline='') as f:
 keys=['document','path','value','populated','mapping_status','support_status','evidence_errors','analyst_notes','analyst_evidence']
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
 for row in allfields:w.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row[k],(list,dict)) else row[k] for k in keys})
(OUT/'critical-fact-evaluation.json').write_text(json.dumps(allfacts,ensure_ascii=False,indent=2)+'\n')
print('OVERALL',overall)
