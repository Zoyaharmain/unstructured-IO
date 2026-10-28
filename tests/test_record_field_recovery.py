"""An LLM omission must not discard explicit, record-local source fields."""
import json
from copy import deepcopy
import pytest
from test_llm_schema_mapping import fixture,configured
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.subschema_validation import validate_hierarchy
from local_api.schemas.sections import SectionResponse


@pytest.mark.parametrize('status',['not_stated','unmapped'])
def test_missing_company_and_role_are_recovered_from_each_own_job(status):
    req,payload=fixture();before=deepcopy(req.model_dump())
    for record in payload['sections'][0]['records']:
        for field in ['company','role']:
            record['fields'][field]=[];record['missing'][field]=status
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status']=='complete'
    assert [(r.company,r.role) for r in out.data.experience]==[('Acme Ltd','Engineer'),('Beta Ltd','Analyst')]
    assert req.model_dump()==before
    assert len([r for r in out.meta['field_review']['evidence_repairs'] if r['field'] in {'company','role'}])==4
    validate_hierarchy(out.section_schemas,SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_explicitly_ambiguous_company_is_not_overridden():
    req,payload=fixture();record=payload['sections'][0]['records'][0]
    record['fields']['company']=[];record['missing']['company']='ambiguous'
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.data.experience[0].company==''
    assert out.meta['mapping_result']['requires_review'] is True


def test_missing_company_does_not_borrow_another_jobs_company():
    req,payload=fixture();record=payload['sections'][0]['records'][0]
    # Remove employer from this job's source; leave a clear employer in job 2.
    old=req.sections.sections[0].blocks[0]
    text='Engineer | 2020 - Present'
    req.elements[0]=req.elements[0].model_copy(update={'text':text})
    section=req.sections.sections[0]
    section.blocks[0]=old.model_copy(update={'text':text,'end':len(text)})
    section.text='\n'.join(b.text for b in section.blocks)
    sid=f'e0:0:{len(text)}';record['source_ids']=[sid]
    for values in record['fields'].values():
        for item in values:item['evidence'][0]['source_id']=sid
    record['fields']['company']=[];record['missing']['company']='not_stated'
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status']=='complete'
    assert out.data.experience[0].company==''
    assert out.data.experience[1].company=='Beta Ltd'
    assert 'experience[0].company' in out.meta['missing_required_fields']
