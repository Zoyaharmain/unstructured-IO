import pytest
from local_api.schemas.sections import SectionBlock
from local_api.services.contact_sections import profile_values
from local_api.services.list_fields import skill_candidates


def block(text,index=0):
    return SectionBlock(source_element_index=index,start=0,end=len(text),text=text,page_number=1,lane='left',assignment='heading_context',reason='test')


@pytest.mark.parametrize('username',['skills-engineer','projects-expert','education-tools'])
def test_github_username_is_never_truncated_as_a_section_heading(username):
    value='https://github.com/'+username
    assert profile_values([block('GitHub: '+value)])['github_url']=={value}


def test_repository_url_is_not_mistaken_for_candidate_profile():
    assert not profile_values([block('https://github.com/person/project')])['github_url']


def test_long_literal_core_competency_is_not_dropped_by_eight_word_limit():
    value='End to End Client Management and Service Delivery across Global Accounts'
    assert value in skill_candidates([block('➥ '+value)])


def test_role_records_at_same_employer_stay_separate_without_inheriting_duties():
    from local_api.services.resume_structure import entry_groups
    from local_api.schemas.extraction import ExtractedElement
    texts=['Jan’19 – Jan’21: Example Ltd., as Engineer',
           'Managed production support.',
           'Feb’21 – Jan’24: Example Ltd., as Senior Engineer']
    elements=[ExtractedElement(type='NarrativeText',text=t,page_number=1,metadata={}) for t in texts]
    groups=entry_groups([block(t,i) for i,t in enumerate(texts)],'experience',elements)
    assert len(groups)==2
    assert groups[0]['block_indices']==[0,1]
    assert groups[1]['block_indices']==[2]


def test_mapping_keeps_full_github_username_with_exact_evidence():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionResponse, ResumeSection
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    texts=['Jane Doe','GitHub: https://github.com/skills-engineer']
    elements=[ExtractedElement(type='NarrativeText',text=t,page_number=1,metadata={}) for t in texts]
    sections=SectionResponse(status='provisional',warnings=[],metadata={},needs_review=[],sections=[
        ResumeSection(category='personal_information',label='Personal information',text='\n'.join(texts),blocks=[block(t,i) for i,t in enumerate(texts)])])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert mapped.data.contact.github_url=='https://github.com/skills-engineer'
    field=next(a for a in mapped.section_schemas[0].records[0].attributes if a.name=='github_url')
    assert field.items[0].evidence[0].quote=='https://github.com/skills-engineer'


@pytest.mark.parametrize('heading',['Business Analysis Competencies','Core Competences','Leadership Competencies'])
def test_competency_headings_route_to_skills_without_domain_name_rules(heading):
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.resume_sections import ALIASES
    assert heading_boundary(heading,ALIASES)==('skills',None)
