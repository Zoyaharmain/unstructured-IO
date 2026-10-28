"""Source-backed field refinement across record types and ambiguous inputs."""
import pytest
from copy import deepcopy
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, ResumeSection, SectionEntry, SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.record_subfields import refine_record


def request(category, records):
    elements, blocks, entries = [], [], []
    for ri, lines in enumerate(records):
        indices = []
        for text in lines:
            i = len(elements)
            elements.append(ExtractedElement(type='NarrativeText', text=text, page_number=1, metadata={}))
            blocks.append(SectionBlock(source_element_index=i, start=0, end=len(text), text=text,
                page_number=1, lane='source', assignment='semantic', reason='fixture'))
            indices.append(i)
        entries.append(SectionEntry(entry_id=f'{category}-{ri + 1}', block_indices=indices,
            lane='source', boundary_reason='fixture', fields={}))
    return SchemaMappingRequest(elements=elements, sections=SectionResponse(status='provisional',
        sections=[ResumeSection(category=category, label=category, text='\n'.join(b.text for b in blocks),
            blocks=blocks, entries=entries)], needs_review=[], metadata={}, warnings=[]))


def attributes(record):
    return {a.name: [item.value for item in a.items] for a in record.attributes}


@pytest.mark.parametrize('category,lines,expected', [
    ('experience', ['Employer: Acme', 'Job Title: Staff Engineer',
        'Period: 2022-10 \u2013 Present', 'Work Base Location: Paris, France', 'Tech Stack: Python, C++'],
        {'company': ['Acme'], 'role': ['Staff Engineer'], 'start_date': ['2022-10'],
         'end_date': ['Present'], 'location': ['Paris, France'], 'technologies': ['Python', 'C++']}),
    ('projects', ['Project Name: Atlas | Role: Developer',
        'Description: Built a search tool.', 'Tech Stack: Python, PostgreSQL', 'Repository: https://github.com/alex/atlas'],
        {'name': ['Atlas'], 'role': ['Developer'], 'technologies': ['Python', 'PostgreSQL'],
         'url': ['https://github.com/alex/atlas']}),
    ('certifications', ['Certification: Cloud Practitioner | Issuing Organization: AWS | Year: 2024'],
        {'name': ['Cloud Practitioner'], 'issuer': ['AWS'], 'issue_year': ['2024']}),
    ('education', ['Qualification: MBA', 'University: Example University', 'Major: Finance',
        'CGPA: 8.7/10', 'Year of Passing: 2023'],
        {'degree': ['MBA'], 'institution': ['Example University'], 'field_of_study': ['Finance'],
         'grade_or_gpa': ['8.7/10'], 'graduation_year': ['2023']}),
    ('awards', ['Award Name: Best Mentor | Awarded By: Acme | Date: 2024'],
        {'name': ['Best Mentor'], 'issuer': ['Acme'], 'date': ['2024']}),
])
def test_aliases_map_to_correct_subschemas_with_record_local_evidence(category, lines, expected):
    req = request(category, [lines]); before = deepcopy(req.model_dump())
    out = map_schema(req)
    record = out.section_schemas[0].records[0]
    actual = attributes(record)
    for key, value in expected.items():
        assert actual[key] == value
    inventory = {f'e{b.source_element_index}:{b.start}:{b.end}': b.text for b in req.sections.sections[0].blocks}
    for attr in record.attributes:
        for item in attr.items:
            assert any(str(item.value) in quote.quote for quote in item.evidence)
            assert all(quote.quote in inventory[quote.source_id] for quote in item.evidence)
    assert req.model_dump() == before
    if category in {'experience', 'education', 'projects', 'certifications'}:
        legacy = getattr(out.data, category)[0]
        for key, value in expected.items():
            actual = getattr(legacy, key)
            assert actual == (value if isinstance(actual, list) else value[0])


def test_conflicting_labels_do_not_choose_a_company_or_borrow_next_record_fields():
    req = request('experience', [['Employer: Acme', 'Company: Beta', 'Role: Engineer'],
                                 ['Employer: Gamma', 'Location: London']])
    out = map_schema(req)
    first, second = out.section_schemas[0].records
    assert not attributes(first)['company']
    assert attributes(second)['company'] == ['Gamma']
    assert not attributes(first)['location']
    assert not attributes(second)['role']
    assert out.data.experience[0].company == ''
    assert any('Conflicting' in reason for reason in first.review_reasons)
    assert 'experience[0].company' not in out.meta['field_evidence']


@pytest.mark.parametrize('date_range,start,end', [
    ('Jan. 2020 - Sept. 2022', 'Jan. 2020', 'Sept. 2022'),
    ('2020-01 \u2014 2022-09', '2020-01', '2022-09'),
    ('01/2020 to 09/2022', '01/2020', '09/2022'),
    ('2020 - Current', '2020', 'Current'),
])
def test_literal_date_formats(date_range, start, end):
    req = request('experience', [[date_range]])
    values, reasons = refine_record('experience', {'start_date': None, 'end_date': None, 'duration': None}, req.sections.sections[0].blocks)
    assert values == {'start_date': start, 'end_date': end, 'duration': date_range}
    assert not reasons


def test_contact_only_input_does_not_turn_email_or_professional_title_into_name():
    from local_api.vendor.handoff_schema.service import extract_contact_info
    for text in ['alex@example.com', 'Senior Software Engineer\nalex@example.com',
                 'Location: Paris, France\nPhone: +33 612345678']:
        assert extract_contact_info(text, text).full_name == 'Candidate'


@pytest.mark.parametrize('header', ['Senior Analyst | PwC | Jan 2020 - Present',
                                    'PwC | Senior Analyst | Jan 2020 - Present'])
def test_three_part_employment_header_supports_organizations_without_suffixes(header):
    out = map_schema(request('experience', [[header]]))
    assert out.data.experience[0].company == 'PwC'
    assert out.data.experience[0].role == 'Senior Analyst'


def test_date_mentions_in_responsibilities_do_not_replace_employment_dates():
    req = request('experience', [['2020 - Present', 'Migrated systems during 2018 - 2019']])
    values, reasons = refine_record('experience', {'start_date': None, 'end_date': None, 'duration': None}, req.sections.sections[0].blocks)
    assert values['start_date'] == '2020'
    assert values['end_date'] == 'Present'
    assert not reasons


def test_reverse_date_range_is_flagged_for_review():
    req = request('experience', [['2024 - 2020']])
    record = map_schema(req).section_schemas[0].records[0]
    assert any('precedes' in reason for reason in record.review_reasons)
    assert all(i.status == 'needs_review' for a in record.attributes for i in a.items)


@pytest.mark.parametrize('text,company,role',[
    ('SLK Software, Team Leader','SLK Software','Team Leader'),
    ('Impetus Technologies, SRE/Devops Engineer','Impetus Technologies','SRE/Devops Engineer'),
    ('Cavisson Systems, Software Engineer','Cavisson Systems','Software Engineer'),
    ('Acme, Inc., Senior Engineer','Acme, Inc.','Senior Engineer'),
])
def test_comma_employment_headers_preserve_literal_company_and_role(text,company,role):
    from local_api.services.record_subfields import employment_header_fields
    assert employment_header_fields(text)=={'company':company,'role':role}
