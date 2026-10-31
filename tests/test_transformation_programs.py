"""Business programs belong to project records, including dates outside title order."""
import json
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.standardization.service import standardize_resume_data


def program_fixture():
    texts=['Analyst | Example Ltd | Jan 2010 - Dec 2024','Managed core operations.',
           'SELECTED TRANSFORMATION PROGRAMS',
           'Mortgage Re-Migration Program Oct 2013 – Oct 2014','Led migration with minimal service impact.',
           'Loan Automation Program Sep 2020 – Feb 2021','Directed automation reducing turnaround from 5 days to 1 day.',
           'EDUCATION','Degree: BSc | University: Example University']
    elements,sections=fixture(texts,{'experience':list(range(7)),'education':[7,8]},[])
    return elements,sections


def test_programs_are_projects_with_dates_descriptions_and_no_duplicate_job_duties():
    elements,sections=program_fixture()
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(out.data.experience)==1 and len(out.data.projects)==2
    assert out.data.projects[0].name=='Mortgage Re-Migration Program'
    assert out.data.projects[0].start_date=='Oct 2013'
    assert out.data.projects[0].description==elements[4].text
    assert out.data.projects[1].name=='Loan Automation Program'
    assert out.data.projects[1].description not in out.data.experience[0].responsibilities
    std,*_=standardize_resume_data(out.data)
    assert std.projects[1].start_date=='2020-09' and std.projects[1].end_date=='2021-02'
    assert out.data.education


def test_date_row_before_title_does_not_become_project_name_or_hide_title():
    elements,sections=fixture(['PROJECTS','Oct 2013 – Oct 2014','Migration Program','Led migration safely.'],{'projects':[0,1,2,3]},[])
    # A source-backed supplied record demonstrates date-first text order.
    section=sections.sections[0]
    section.entries=[section.entries[0].model_copy(update={'block_indices':[1,2,3],'fields':{}})]
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.projects[0].name=='Migration Program'
    assert out.data.projects[0].start_date=='Oct 2013'
    assert out.data.projects[0].description=='Led migration safely.'


def test_review_cannot_merge_separately_dated_source_programs_into_one_record():
    elements,sections=program_fixture();req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req)
    # Request the repaired source-section inventory that the review mapper uses.
    from local_api.schemas.sections import SectionResponse
    req=req.model_copy(update={'sections':SectionResponse.model_validate(local.meta['reviewed_sections'])})
    payload=local_section_payload(local,{s.category for s in local.section_schemas if s.category!='needs_review'})
    projects=next(s for s in payload if s['category']=='projects')
    first,second=projects['records'];first['source_ids'].extend(second['source_ids']);projects['records']=[first]
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        return json.dumps({'sections':[s for s in payload if s['category'] in categories]})
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert out.meta['field_review']['status']=='complete'
    assert len(out.data.projects)==2
    assert [p.name for p in out.data.projects]==['Mortgage Re-Migration Program','Loan Automation Program']
