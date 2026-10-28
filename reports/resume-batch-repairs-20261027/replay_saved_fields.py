import json
from collections import defaultdict,deque
from pathlib import Path
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy
root=Path('reports/resume-batch-10-llm-20261027');target=Path('reports/resume-batch-repairs-20261027/replay')
for n in [2,9]:
 d=root/f'resume-{n:02d}';queues=defaultdict(deque)
 for p in sorted(d.glob('provider-request-*'),key=lambda p:int(p.stem.split('-')[-1])):
  q=json.loads(p.read_text())
  if not q['messages'][0]['content'].startswith('Map '):continue
  categories=tuple(json.loads(q['messages'][1]['content'])['registry'])
  response=d/p.name.replace('request','response')
  if response.exists():queues[categories].append(json.loads(response.read_text())['content'])
 extraction=json.loads((d/'extraction.json').read_text());sections=json.loads((d/'pass-01/sections.json').read_text())
 req=SchemaMappingRequest(elements=extraction['elements'],sections=sections)
 def transport(settings,messages):
  cats=tuple(json.loads(messages[1]['content'])['registry'])
  if not queues[cats]:raise RuntimeError('No saved response for this batch; network forbidden')
  return queues[cats].popleft()
 out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='offline-replay',recovery_attempts=1),transport=transport)
 revised=SectionResponse.model_validate(out.meta.get('reviewed_sections',sections))
 assert validate_result(req.elements,revised)==[]
 validate_hierarchy(out.section_schemas,revised)
 (target/f'resume-{n:02d}.json').write_text(out.model_dump_json(indent=2))
 print(n,'status',out.meta['field_review']['status'],'fallback',out.meta['field_review'].get('fallback_categories'),'jobs',[(x.company,x.role) for x in out.data.experience])
