import pytest
from local_api.services.record_subfields import employment_header_fields, RANGE
from local_api.services.resume_structure import employment_start


@pytest.mark.parametrize('quote',["'", '’', '‘'])
def test_quoted_short_year_job_header(quote):
    text = f'Oct{quote}21 – Jan{quote}24: Example Systems, as Global Delivery Head – Contact Center Technologies'
    assert RANGE.match(text)
    assert employment_start(text)
    assert employment_header_fields(text) == {'company':'Example Systems','role':'Global Delivery Head – Contact Center Technologies'}


def test_formerly_known_as_is_not_role_delimiter():
    text = 'May’07 – Mar’10: Example Bank (Formerly known as Example Services) as Assistant Manager - Technology'
    assert employment_header_fields(text) == {'company':'Example Bank (Formerly known as Example Services)', 'role':'Assistant Manager - Technology'}


def test_dated_summary_and_client_statement_are_not_employer_identity():
    assert not employment_header_fields('Jan’20 – Jan’24: Delivered projects for clients.')
    assert not employment_header_fields('Client: Example Bank, as Manager')


@pytest.mark.parametrize('body,expected',[
    ('Oct’21 – Jan’24: Example Systems, as Global Delivery Head','experience'),
    ('Experienced professional with expertise in service delivery and stakeholder management.','summary')])
def test_highlights_heading_uses_job_content(body,expected):
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionRequest
    from local_api.services.resume_sections import get_engine
    from local_api.services.source_validation import validate_result
    texts=['Professional Highlights',body,'Education','Bachelor of Science']
    request=SectionRequest(elements=[ExtractedElement(type='Title' if i in {0,2} else 'NarrativeText',text=t,page_number=1,metadata={}) for i,t in enumerate(texts)])
    result=get_engine().detect(request)
    assert any(b.source_element_index==0 for s in result.sections if s.category==expected for b in s.blocks)
    assert not validate_result(request.elements,result)
