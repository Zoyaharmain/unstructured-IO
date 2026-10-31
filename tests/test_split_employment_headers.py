"""Employment header association uses source position, not a company catalog."""
import json
from copy import deepcopy
import pytest
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.source_fragments import citations
from local_api.services.dated_record_headers import split_employment_headers

@pytest.mark.parametrize('employer,city,reverse,joined',[
    ('Concentrix','Visakhapatnam',False,False),
    ('Example Analytics','Wellington',True,False),
    ('Sample Research','Reykjavik',False,True),
])
def test_adjacent_role_employer_client_dates_form_one_job(employer,city,reverse,joined):
    header=['Data Analyst',f'{employer} – {city}']
    if reverse:header.reverse()
    rows=header+['Client: Unrelated Customer','Apr 2017 – Nov 2017']
    texts=['EXPERIENCE']+(['\n'.join(rows)] if joined else rows)+['Built reliable dashboards.']
    elements,sections=fixture(texts,{'experience':list(range(len(texts)))},[])
    before=deepcopy([e.model_dump() for e in elements]);req=SchemaMappingRequest(elements=elements,sections=sections)
    out=map_schema(req)
    assert len(out.data.experience)==1
    job=out.data.experience[0]
    assert (job.company,job.role,job.location)==(employer,'Data Analyst',city)
    assert job.start_date=='Apr 2017' and job.end_date=='Nov 2017'
    std,*_=standardize_resume_data(out.data)
    assert std.experience[0].duration_months==7
    assert [e.model_dump() for e in elements]==before
    repaired=SectionResponse.model_validate(out.meta.get('reviewed_sections',sections.model_dump()))
    assert not validate_result(elements,repaired)
    again=map_schema(req.model_copy(update={'sections':repaired}))
    assert len(again.data.experience)==1 and again.data.experience[0].company==employer


def test_two_jobs_do_not_exchange_clients_dates_or_responsibilities():
    texts=['EXPERIENCE','Data Analyst','Example Research – Wellington','Client: Customer A',
           'Apr 2017 – Nov 2017','Built dashboards.',
           'Software Engineer','Other Systems – Dublin','Client: Customer B','Jan 2018 – Dec 2019','Developed services.']
    elements,sections=fixture(texts,{'experience':list(range(len(texts)))},[])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [(j.company,j.role,j.location) for j in out.data.experience]==[
        ('Example Research','Data Analyst','Wellington'),('Other Systems','Software Engineer','Dublin')]
    assert out.data.experience[0].responsibilities==['Built dashboards.']
    assert out.data.experience[1].responsibilities==['Developed services.']


def test_missing_employer_is_not_replaced_with_client():
    elements,sections=fixture(['Data Analyst','Client: Customer A','Apr 2017 – Nov 2017'],{'experience':[0,1,2]},[])
    assert not split_employment_headers(sections.sections[0].blocks)
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert all(not j.company for j in out.data.experience)

@pytest.mark.parametrize('employer',['Example – Platform Engineering','Built dashboards for customers'])
def test_department_or_duty_is_not_recast_as_employer_location(employer):
    elements,sections=fixture(['Data Analyst',employer,'Apr 2017 – Nov 2017'],{'experience':[0,1,2]},[])
    assert not split_employment_headers(sections.sections[0].blocks)


def test_separate_columns_are_not_joined():
    elements,sections=fixture(['Data Analyst','Example – Wellington','Apr 2017 – Nov 2017'],{'experience':[0,1,2]},[],['left','right','left'])
    assert not split_employment_headers(sections.sections[0].blocks)


def test_reviewed_missing_employer_uses_source_header_not_client():
    texts=['Data Analyst','Example Analytics – Wellington','Client: Customer A','Apr 2017 – Nov 2017']
    elements,sections=fixture(texts,{'experience':[0,1,2,3]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections);local=map_schema(req)
    payload=local_section_payload(local,{'experience'});record=payload[0]['records'][0]
    record['fields']['company']=[];record['missing']['company']='unmapped'
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert out.meta['field_review']['status']=='complete'
    assert len(out.data.experience)==1 and out.data.experience[0].company=='Example Analytics'
    assert out.data.experience[0].location=='Wellington'
