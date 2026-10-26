"""Re-run only field mapping on the saved, source-bound section review."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from local_api.core.provider_env import load_provider_env
load_provider_env(ROOT/'.env')
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.llm_section_review import call_deepseek
out=Path(__file__).parent
extraction=json.loads((out/'extraction.json').read_text());sections=json.loads((out/'sections.json').read_text())
req=SchemaMappingRequest(elements=extraction['elements'],sections=sections,source='Abhijit_Dey.docx')
def transport(settings,messages):
 content=call_deepseek(settings,messages)
 (out/'final-field-provider-response.json').write_text(json.dumps({'content':content},indent=2)+'\n')
 return content
mapped=map_with_field_review(req,transport=transport)
(out/'after.schema.json').write_text(json.dumps(mapped.model_dump(),indent=2,ensure_ascii=False)+'\n')
print(mapped.meta.get('field_review'));print('Required missing:',mapped.meta['missing_required_fields'])
print('Jobs:',[(r.company,r.role,r.duration) for r in mapped.data.experience]);print('Skills:',len(mapped.data.skills.all_skills))
