"""Offline saved-source replay; mocked field omissions, no provider calls."""
import json
from pathlib import Path
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.services.schema_mapping import map_schema
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.subschema_validation import validate_hierarchy
from local_api.services.source_validation import validate_result

root=Path(__file__).parent
req=SchemaMappingRequest(elements=json.loads((root/'after/extraction.json').read_text())['elements'],
    sections=json.loads((root/'after/sections.json').read_text()))
local=map_schema(req)
if local.meta.get('reviewed_sections'):
    req=req.model_copy(update={'sections':SectionResponse.model_validate(local.meta['reviewed_sections'])})
(root/'final-local.schema.json').write_text(local.model_dump_json(indent=2))
rows=[]
for section in local.section_schemas:
    if section.category=='needs_review':continue
    records=[]
    for record in section.records:
        fields={a.name:[v.model_dump() for v in a.items] for a in record.attributes}
        if section.category=='experience':
            fields['company']=[];fields['role']=[]
        records.append(dict(record_id=record.record_id,source_ids=record.source_ids,fields=fields,
                            missing={k:'not_stated' for k,v in fields.items() if not v}))
    rows.append(dict(category=section.category,records=records))
def transport(settings,prompt):
    categories={s['category'] for s in json.loads(prompt[1]['content'])['sections']}
    return json.dumps({'sections':[r for r in rows if r['category'] in categories]})
out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock-only',recovery_attempts=0),transport=transport)
expected=[('SLK Software','Team Leader'),('Impetus Technologies','SRE/Devops Engineer'),('Cavisson Systems','Software Engineer')]
actual=[(r.company,r.role) for r in out.data.experience]
assert actual==expected
assert out.meta['field_review']['status']=='complete'
revised=SectionResponse.model_validate(out.meta['reviewed_sections'])
assert validate_result(req.elements,revised)==[]
validate_hierarchy(out.section_schemas,revised)
assert local.data.contact.phone and local.data.contact.email
assert [(e.start_year,e.graduation_year) for e in local.data.education]==[('2014','2018')]
summary={'paid_calls':0,'field_omission_replay':'controlled mock using actual saved extraction',
 'field_review_status':out.meta['field_review']['status'],'jobs':[{'company':c,'role':r} for c,r in actual],
 'email_present':bool(local.data.contact.email),'phone_present':bool(local.data.contact.phone),
 'education_years':[{'start':e.start_year,'graduation':e.graduation_year} for e in local.data.education],
 'identity_fields_recovered':len([r for r in out.meta['field_review']['evidence_repairs'] if r.get('field') in {'company','role'}])}
(root/'verified-reviewed.schema.json').write_text(out.model_dump_json(indent=2))
(root/'verification.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
