import json
from pathlib import Path
from local_api.schemas.sections import SectionResponse
from local_api.services.source_validation import validate_result
from local_api.schemas.sections import SectionRequest
root=Path('reports/live-five-new-resumes-20261105');rows=json.loads((root/'review-summary.json').read_text())
for row in rows:
 d=root/row['directory'];ex=json.loads((d/'extraction.json').read_text());req=SectionRequest(elements=ex['elements']);sections=SectionResponse.model_validate_json((d/'sections.json').read_text())
 errors=validate_result(req.elements,sections);row['final_source_validation_errors']=errors
 audit=json.loads((d/'schema-audit.json').read_text());row['audit_incomplete_reason']=audit.get('reason');row['audit_findings_count']=len(audit.get('findings',[]))
 row['empty_review_count']=sum(not any(c.isalnum() for c in b.text) for b in sections.needs_review)
 row['provider_model']=json.loads((d/'provider-request-1.json').read_text()).get('model')
 print(row['file'],'source validation',errors,'empty review',row['empty_review_count'],'section',row['section_review'].get('status'),'field',row['field_review'].get('status'))
(root/'review-summary.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
