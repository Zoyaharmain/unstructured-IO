"""Headline ownership comes from preamble context, never a fixed title string."""
from copy import deepcopy
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result


def test_sidebar_skills_do_not_hide_headline_or_make_it_a_job():
    texts=['Example Person','SKILLS','Python',
           'PRINCIPAL PLATFORM ENGINEER, DISTRIBUTED SYSTEMS',
           'Experienced platform engineer specializing in distributed systems with a proven track record of delivering reliable services across engineering teams.',
           'EXPERIENCE','Engineer | Example Ltd | Jan 2020 - Dec 2021','Built production services.']
    elements,sections=fixture(texts,{'personal_information':[0],'skills':[1,2], 'experience':[3,4,5,6,7]},[])
    elements[3].type='Title'
    before=deepcopy([e.model_dump() for e in elements])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.professional_title==texts[3]
    assert out.data.summary==texts[4]
    assert len(out.data.experience)==1 and out.data.experience[0].company=='Example Ltd'
    assert texts[3] not in out.data.skills.all_skills
    assert [e.model_dump() for e in elements]==before
    from local_api.schemas.sections import SectionResponse
    assert not validate_result(elements,SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_real_undated_role_inside_history_is_not_removed():
    elements,sections=fixture(['EXPERIENCE','Senior Engineer',
        'Experienced in delivering reliable services with a proven track record of supporting a large engineering team.'],{'experience':[0,1,2]},[])
    elements[1].type='Title'
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.professional_title is None
    assert out.data.experience and out.data.experience[0].role=='Senior Engineer'


def test_title_next_to_employment_dates_is_not_an_introductory_headline():
    elements,sections=fixture(['Senior Engineer','Jan 2020 - Dec 2021',
        'Experienced in building distributed services with a proven track record of delivering reliable software for engineering teams.'],{'experience':[0,1,2]},[])
    elements[0].type='Title'
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.professional_title is None


def test_review_omission_cannot_drop_source_backed_professional_title():
    import json
    from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
    from local_api.services.llm_section_review import ReviewSettings
    texts=['Example Person','PRINCIPAL PLATFORM ENGINEER',
           'Experienced platform engineer specializing in distributed systems with a proven track record of delivering reliable services across engineering teams.',
           'EXPERIENCE','Engineer | Example Ltd | Jan 2020 - Dec 2021']
    elements,sections=fixture(texts,{'personal_information':[0],'experience':[1,2,3,4]},[])
    elements[1].type='Title';req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req)
    payload=local_section_payload(local,{s.category for s in local.section_schemas if s.category!='needs_review'})
    person=next(s for s in payload if s['category']=='personal_information')['records'][0]
    person['fields']['professional_title']=[];person['missing']['professional_title']='not_stated'
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        return json.dumps({'sections':[s for s in payload if s['category'] in categories]})
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert out.meta['field_review']['status']=='complete'
    assert out.data.professional_title==texts[1]
    assert len(out.data.experience)==1
