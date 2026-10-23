"""Offline integration smoke check using saved extraction/section artifacts."""
import json
from pathlib import Path
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
root = Path('reports/single-jayesh-feedback-local-20261022')
outdir = Path('reports/nested-schema-implementation-20261023')
extraction = json.loads((root/'extraction.json').read_text())
sections = json.loads((root/'pass-01/sections.json').read_text())
request = SchemaMappingRequest(elements=extraction['elements'], sections=sections, source='saved-jayesh-blocks')
result = map_schema(request).model_dump(mode='json')
(outdir/'saved-jayesh-nested.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
source = {f'e{b.source_element_index}:{b.start}:{b.end}': b.text for s in request.sections.sections for b in s.blocks}
count = 0
for section in result['section_schemas']:
    for record in section['records']:
        for field in record['attributes']:
            for item in field['items']:
                assert item['evidence']
                for ref in item['evidence']:
                    assert ref['quote'] in source[ref['source_id']]
                count += 1
summary = {'source_directory': str(root), 'sections': len(result['section_schemas']),
           'records': sum(len(s['records']) for s in result['section_schemas']),
           'populated_attribute_items': count, 'exact_quote_checks_passed': True,
           'provider_calls': 0, 'extraction_runs': 0, 'block_detection_runs': 0,
           'human_verified': False}
(outdir/'saved-check.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary))
