"""Offline baseline diagnostics only; no new extraction/detection/mapping/provider."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent
from local_api.schemas.sections import SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.source_validation import validate_result
from local_api.services.source_accounting import account_source
from local_api.services.subschema_validation import validate_hierarchy,query_subschemas
m=json.loads((OUT/'selection-manifest.json').read_text());rows=[]
for row in m['selected']:
 source=json.loads((ROOT/row['baseline_source']).read_text());mapped=json.loads((ROOT/row['baseline_mapping']).read_text())
 sections=SectionResponse.model_validate(source['sections']);elements=[ExtractedElement.model_validate(e) for e in source['extraction']['elements']]
 record={'file':row['file'],'baseline_source':row['baseline_source'],'fresh_run':False,'semantic_accuracy':None}
 try:
  errors=validate_result(elements,sections);record['source_validation_errors']=errors
  if errors:raise ValueError('Invalid extracted-source intervals')
  parsed=validate_hierarchy(mapped['section_schemas'],sections);record['hierarchy_and_citation_validation']='passed'
  record['source_accounting']=account_source(elements,sections)
  record['lookup_examples']={p:query_subschemas(parsed,p) for p in ['experience.role','skills.technical_skills','education.degree','certifications.name']}
  experiences=[r for s in parsed if s.category=='experience' for r in s.records]
  if experiences:
   rid=experiences[0].record_id;filtered=query_subschemas(parsed,'experience.role',rid);assert all(r['record_id']==rid for r in filtered);record['record_filter_check']='passed'
  record['populated_items']=sum(len(a.items) for s in parsed for r in s.records for a in r.attributes)
 except Exception as exc:record.update(validation_status='failed',error_type=type(exc).__name__,error=str(exc))
 rows.append(record)
(OUT/'saved-baseline-diagnostics.json').write_text(json.dumps({'scope':'Existing saved bulk outputs only, not fresh end-to-end results or ground truth','documents':rows},indent=2,ensure_ascii=False)+'\n')
print(json.dumps([{'file':r['file'],'validation':r.get('hierarchy_and_citation_validation',r.get('error')),'populated_items':r.get('populated_items')} for r in rows],indent=2))
