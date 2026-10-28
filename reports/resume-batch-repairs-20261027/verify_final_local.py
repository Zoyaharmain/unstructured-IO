"""Rebuild the same ten source-bound inventories offline with the repaired mapper."""
import json
from pathlib import Path
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy
from scripts.report_llm_resume_batch import employer_matches
root=Path('reports/resume-batch-repairs-20261027')
source=root/'final-current';target=root/'final-schemas';target.mkdir(exist_ok=True,mode=0o700)
expected=json.loads(Path('reports/resume-batch-10-llm-20261027/source-employer-checks.json').read_text())['expected']
rows=[]
for n,row in enumerate(json.loads((source/'results.json').read_text()),1):
    artifact=json.loads((source/row['artifact']).read_text())
    req=SchemaMappingRequest(elements=artifact['extraction']['elements'],sections=artifact['sections'])
    req.sections.sections=build_sections({s.category:s.blocks for s in req.sections.sections},req.elements)
    assert validate_result(req.elements,req.sections)==[]
    mapped=map_schema(req)
    from local_api.schemas.sections import SectionResponse
    revised=SectionResponse.model_validate(mapped.meta.get('reviewed_sections',req.sections.model_dump()))
    validate_hierarchy(mapped.section_schemas,revised)
    assert validate_result(req.elements,revised)==[]
    (target/f'{n:02d}.json').write_text(mapped.model_dump_json(indent=2))
    rows.append({'file':row['file'],'source_schema_checks':'pass','expected_employers':len(expected[row['file']]),
        'recovered_employers':employer_matches(expected[row['file']],mapped.data.model_dump()['experience']),
        'experience_records':len(mapped.data.experience),'project_records':len(mapped.data.projects)})
summary={'provider_calls':0,'documents':len(rows),'checks_passed':len(rows),
    'employers_expected':sum(r['expected_employers'] for r in rows),
    'employers_recovered':sum(r['recovered_employers'] for r in rows),'rows':rows}
(root/'local-final-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
