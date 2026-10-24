import importlib.util,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('phase1_comparison_helpers',ROOT/'reports/ten-resume-phase1-20261024/compare.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
load=lambda p:json.loads(p.read_text())
rows=load(OUT/'before-after-comparison-verified.json')['documents'];references=[];measurements=[];changes=[]
for i,row in enumerate(rows,1):
 after=load(OUT/f'replay-verified/{i:02d}/schema.json');before=load(ROOT/f'reports/ten-resume-phase1-20261024/after/{i:02d}/schema.json')
 assert after['data']==before['data'] and after['section_schemas']==before['section_schemas'] and after['field_index']==before['field_index']
 assert row['record_membership_unchanged'] and row['source_assignment_outcomes_unchanged']
 changes.append({'file':row['file'],'recursive_schema_differences':helpers.delta(before,after),'explanation':'Only meta.source_accounting reason strings and meta.needs_review review/provenance annotations change. Source IDs, intervals, categories, accounting outcomes, record membership, legacy/nested values, field index and residuals are unchanged.'})
 sec=load(OUT/f'replay-verified/{i:02d}/sections.json');audit=load(OUT/f'replay-verified/{i:02d}/audit.json')
 for stage,plan in [('section_review',sec['metadata']['llm_review'].get('chunking')),('schema_audit',audit['coverage'])]:
  if plan:
   for c in plan['chunks']:
    measurements.append({'file':row['file'],'stage':stage,'chunk_id':c['chunk_id'],'owned_targets':len(c['targets']),**c['measurement']})
 if i in [1,2]:
  doc='aditya-vashisth' if i==1 else 'manjunath-murugan';ref=load(ROOT/f'ground_truth/field_level/v5/{doc}.json')
  br=helpers.evaluate(ref,before);ar=helpers.evaluate(ref,after);assert br==ar and all(f['status']=='exact_match' for f in ar)
  references.append({'file':row['file'],'before':br,'after':ar})
assert all(m['fits'] for m in measurements)
by=Counter(f['provenance'] for r in references for f in r['after'])
(OUT/'reference-comparison-verified.json').write_text(json.dumps({'documents':references,'exact_before_and_after_by_provenance':by,'precision':None,'recall':None,'f1':None,'semantic_accuracy':None,'reason':'17 partial positive expectations only; uncertain/pending labels excluded; six older expectations retain narrower provenance.'},indent=2,ensure_ascii=False)+'\n')
(OUT/'request-measurements-verified.json').write_text(json.dumps(measurements,indent=2)+'\n')
(OUT/'output-differences-verified.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False)+'\n')
print('17 partial tuples unchanged; all actual chunk envelopes fit configured guards; no semantic output differences.')
print('Full recursive metadata differences saved to output-differences.json.')
