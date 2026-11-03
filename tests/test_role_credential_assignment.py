import pytest
from local_api.schemas.sections import SectionBlock
from local_api.services.record_subfields import employment_header_fields
from local_api.services.education_subfields import refine_education
from local_api.services.certification_integrity import detail_row, inline_credential_cuts, credential_values


def block(text,index=0):
    return SectionBlock(source_element_index=index,start=0,end=len(text),text=text,page_number=1,lane='left',assignment='semantic',reason='fixture')


def test_role_pipe_organization_compound_is_not_discarded_or_guessed_apart():
    assert employment_header_fields('Business Analyst | Example Consulting — Client Bank')=={'company':'Example Consulting — Client Bank','role':'Business Analyst'}
    assert not employment_header_fields('Client: Client Bank')


@pytest.mark.parametrize('text,degree',[('MBA – Master of Business Administration','MBA'),('B.Tech – Bachelor of Technology','B.Tech')])
def test_acronym_and_expanded_degree_are_one_qualification(text,degree):
    values,reasons=refine_education({'degree':None,'field_of_study':None,'institution':None},[block(text)])
    assert values['degree']==degree
    assert not reasons


def test_institution_with_abbreviation_and_city_is_retained_literally():
    institution='Example Institute of Management (EIM) North Campus'
    values,reasons=refine_education({'degree':'MBA','field_of_study':None,'institution':None},[block('MBA',0),block(institution,1)])
    assert values['institution']==institution


def test_active_is_status_not_a_certificate_and_issuer_is_not_another_title():
    assert detail_row('Active')
    text='Advanced Program | Example Academy Certified in collaboration with Research Institute'
    assert inline_credential_cuts(text)==[]
    values,reasons=credential_values([block(text)])
    assert values['name']=='Advanced Program'
    assert values['issuer']=='Example Academy Certified in collaboration with Research Institute'


def test_spaced_additional_information_is_context_not_a_degree():
    from local_api.services.resume_sections import ALIASES
    from local_api.services.resume_structure import heading_boundary
    assert heading_boundary('A D D I T I O N A L I N F O R M A T I O N',ALIASES)==('personal_information',None)


def test_repeated_status_word_uses_its_own_source_box_and_never_another_page():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.services.certification_integrity import aligned_credential_detail
    title='Advanced Analysis | Example Institute'
    left=block(title,0);right=block('Active',1)
    elements=[ExtractedElement(type='NarrativeText',text=title,page_number=1,metadata={'pdf_source_lines':[{'start':0,'end':len(title),'bbox':[.1,.2,.6,.21]}]}),
              ExtractedElement(type='Title',text='Active',page_number=1,metadata={'coordinates':{'points':[[80,20],[90,20],[90,21],[80,21]],'layout_width':100,'layout_height':100}})]
    assert aligned_credential_detail(left,right,elements)
    right.page_number=2
    assert not aligned_credential_detail(left,right,elements)


def test_credential_year_is_not_dropped_from_separate_source_row():
    values,reasons=credential_values([block('Advanced Program',0),block('2025',1)])
    assert values['issue_year']=='2025'
