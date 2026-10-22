import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent;sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(OUT)]
from schema_gate import validate,repair_confirmed_omissions
OLD=ROOT/'reports/deepseek-schema-pilot5-20261022';rows=[]
for n in range(1,6):
 source=OLD/f'{n:02d}';raw=json.loads((source/'mapping-raw.json').read_text());blocks=json.loads((source/'source-blocks.json').read_text())
 before=validate(raw,blocks);candidate,changes=repair_confirmed_omissions(raw,blocks);after=validate(candidate,blocks)
 target=OUT/'offline'/f'{n:02d}';target.mkdir(parents=True,exist_ok=True,mode=0o700)
 for name,value in [('before-validation',before),('candidate-mapping',candidate),('changes',changes),('after-validation',after)]:
  (target/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 rows.append({'document':n,'before_populated_fields':before['populated_fields'],'before_valid_citation_fields':before['citation_valid_fields'],
  'confirmed_omissions_before':len(before['completeness_findings']),'explicit_repairs':changes,
  'remaining_pattern_detected_omissions':len(after['completeness_findings']),'after_populated_fields':after['populated_fields'],
  'after_valid_citation_fields':after['citation_valid_fields'],'remaining_issue_count':len(after['issues']),
  'uncertainty_flags':len(after['uncertainties']),'accepted':after['accepted'],'paid_calls':0})
summary={'documents':5,'repairs':sum(len(r['explicit_repairs']) for r in rows),'remaining_pattern_detected_omissions':sum(r['remaining_pattern_detected_omissions'] for r in rows),
 'accepted_documents':sum(r['accepted'] for r in rows),'no_citation_inheritance':True,'new_paid_calls':0,'per_document':rows}
assert summary['repairs']==3 and summary['remaining_pattern_detected_omissions']==0
(OUT/'offline-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['local_api','scripts'] for p in (ROOT/base).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(OUT/'production-hashes-before.json').write_text(json.dumps(files,indent=2)+'\n')
print('Offline saved outputs checked; exactly three explicit omission repairs; no paid calls; unrelated failures retained.')
