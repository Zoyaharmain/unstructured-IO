"""Literal opening identities must survive wrapped prose and qualification cards."""
import json
from pathlib import Path
import pytest
from local_api.services.record_subfields import employment_header_fields, refine_record

@pytest.mark.parametrize('institution', ['Example Institute', 'ABC, North Campus'])
def test_institution_preposition_never_becomes_subject(institution):
    from local_api.schemas.sections import SectionBlock
    from local_api.services.education_subfields import refine_education
    text=f'Master of Software Engineering from {institution} passing year December 2015.'
    block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='semantic',reason='test')
    result,_=refine_education({'degree':None,'institution':None,'field_of_study':f'from {institution}'},[block])
    assert result['field_of_study']=='Software Engineering'
    assert result['institution']==institution

@pytest.mark.parametrize('text', ['users with centralized, role-based application experiences.', 'Provided role-based access to services.'])
def test_role_based_duty_is_not_an_employer(text):
    assert employment_header_fields(text) == {}

@pytest.mark.parametrize('company', ['Example Consulting', 'Northstar Ltd'])
def test_opening_pipe_header_overrides_polluted_company_hint(company):
    from local_api.schemas.sections import SectionBlock
    lines=[f'Manager | {company}', 'Developed enterprise services.']
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='main',assignment='semantic',reason='test') for i,t in enumerate(lines)]
    result,_=refine_record('experience', {'company':company+'\nDeveloped enterprise services.', 'role':'Manager'}, blocks, header_fields={'company','role'})
    assert result['company']==company

def test_saved_source_has_seven_jobs_and_two_qualifications():
    from local_api.schemas.sections import SectionRequest
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.resume_sections import detect_sections
    from local_api.services.schema_mapping import map_schema
    document=json.loads(Path('.upstream/batch-validation/documents/79520cb13c8b8bcbbad4.json').read_text())
    elements=document['extraction']['elements']
    result=map_schema(SchemaMappingRequest(elements=elements,sections=detect_sections(SectionRequest(elements=elements))))
    assert [j.company for j in result.data.experience]==['Capgemini','Accenture Solutions','Tata Consultancy Services']+['Wipro Technologies Ltd']*4
    assert len(result.data.education)==2
    assert result.data.education[1].degree=='Master of Software Engineering'
    assert result.data.education[1].institution=='BITS, Pilani'
    assert result.data.education[1].field_of_study=='Software Engineering'
    assert result.data.total_experience_years==11.8
    assert result.data.education[1].graduation_year=='2015'
    assert result.data.education[0].graduation_year=='2011'
