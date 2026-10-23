"""Regressions from inspected source; no provider and no accuracy certification."""
import json
from pathlib import Path
import pytest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema


FIXTURES = Path(__file__).parent / 'fixtures' / 'hierarchical_defects'


def replay(index):
    obj = json.loads((FIXTURES / f'{index:02d}.json').read_text())
    elements = [ExtractedElement.model_validate(e) for e in obj['elements']]
    saved = SectionResponse.model_validate(obj['sections'])
    sections = saved.model_copy(deep=True)
    sections.sections = build_sections({s.category: s.blocks for s in sections.sections}, elements)
    return map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=obj['file']))


@pytest.fixture(autouse=True)
def prohibit_network(monkeypatch):
    import socket
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Offline regression attempted network'))


def test_levi_email_token_is_not_overridden_by_phone():
    out = replay(4)
    assert out.data.contact.email == 'arbole60@gmail.com'
    assert out.data.contact.phone == '9823506339'


def test_manjunath_four_part_headers_keep_role_employer_and_location():
    jobs = replay(2).data.experience
    assert (jobs[0].company, jobs[0].role, jobs[0].location) == ('PwC', 'Senior Business Analyst', 'Chennai')
    assert jobs[2].company == 'Barclays Shared Services'
    assert (jobs[3].company, jobs[3].role) == ('BNP Paribas GSO', 'Senior Associate Intraday Pricing')


def test_rachana_header_and_full_title():
    out = replay(5)
    assert out.data.experience[0].company == 'Tieto HealthCare'
    assert out.data.experience[0].role == 'Senior Business Analyst / Scrum Master'
    assert out.data.experience[0].location == 'Bangalore, India'
    assert out.data.professional_title == 'Senior Business Analyst | Scrum Master | US Healthcare'


def test_split_month_and_year_are_one_source_backed_date():
    assert replay(2).data.experience[2].start_date == 'October 2015'


def test_aditya_geometry_recovers_separate_degrees_and_clean_contact_tokens():
    out = replay(3)
    assert len(out.data.education) == 2
    assert any('Master' in e.degree for e in out.data.education)
    assert all(e.institution == 'Guru Gobind Singh Indraprastha University' for e in out.data.education)
    assert out.data.contact.full_name == 'Aditya Vashisth'
    assert out.data.contact.email == 'avmsv1996@gmail.com'
    assert out.data.contact.github_url == 'github.com/av525'
    assert out.data.contact.linkedin_url == 'linkedin.com/in/aditya-vashisth'


def test_aashish_postgraduate_certificate_stays_in_education():
    out = replay(1)
    assert len(out.data.education) == 3
    certificate = next(e for e in out.data.education if 'Certificate' in e.degree)
    assert certificate.graduation_year == '2008'
    assert certificate.institution == 'Pune University'


def test_combined_education_lines_recover_institutions():
    assert [e.institution for e in replay(2).data.education] == ['SRM University', 'Madras University']
    assert replay(5).data.education[0].institution == 'NMAMIT / Nitte University'


def test_responsibility_blocks_do_not_contaminate_titles_or_disappear():
    out = replay(1)
    assert out.data.experience[2].role == 'Senior Business Analyst'
    assert out.data.experience[4].role == 'Underwriter'
    duties = replay(5).data.experience[0].responsibilities
    assert duties
    assert any('workshops' in value.lower() for value in duties)


def test_spoken_language_list_inside_personal_details_is_routed_and_bullets_removed():
    out = replay(4)
    parent = next(p for p in out.section_schemas if p.category == 'languages')
    languages = [i.value for r in parent.records for a in r.attributes if a.name == 'language' for i in a.items]
    assert languages == ['English', 'Hindi']
    assert out.data.languages == ['English', 'Hindi']
    assert all(any(c.isalpha() for c in value) for value in replay(2).data.languages)


def test_skill_fragments_and_case_duplicates_are_filtered():
    for index in (1, 2, 3, 4, 5):
        values = replay(index).data.skills.all_skills
        assert len(values) == len({v.casefold() for v in values})
        assert not {'including', 'data mapping and', 'validation.', 'us healthcare domain expertise'} & {v.casefold() for v in values}


def test_legacy_and_hierarchy_agree_for_shared_record_fields_with_exact_evidence():
    from local_api.services.subschema_validation import validate_hierarchy
    for index in range(1, 6):
        out = replay(index)
        for parent in out.section_schemas:
            if parent.category not in {'experience', 'education'}:continue
            legacy = getattr(out.data, parent.category)
            assert len(legacy) == len(parent.records)
            for old, record in zip(legacy, parent.records):
                for attr in record.attributes:
                    value = getattr(old, attr.name)
                    expected = value if isinstance(value, list) else [value] if value else []
                    assert [i.value for i in attr.items] == expected
                    assert all(i.evidence for i in attr.items)



def test_ambiguous_header_does_not_choose_between_two_organizations():
    from local_api.services.record_subfields import employment_header_fields
    assert employment_header_fields('Senior Analyst | Alpha | Beta | Jan 2020 - Present') == {}


def test_contiguous_field_quotes_cannot_join_foreign_or_gapped_sources():
    from local_api.services.source_fragments import contiguous_support
    from local_api.schemas.subschemas import SourceQuote
    good = [SourceQuote(source_id='e0:0:7', quote='October'), SourceQuote(source_id='e0:7:12', quote=' 2015')]
    inventory = {'e0:0:7': 'October', 'e0:7:12': ' 2015'}
    assert contiguous_support('October 2015', good, inventory)
    bad = [good[0], SourceQuote(source_id='e1:7:12', quote=' 2015')]
    assert not contiguous_support('October 2015', bad, inventory | {'e1:7:12': ' 2015'})


def test_unstated_language_proficiency_and_unknown_employer_remain_unresolved():
    out = replay(4)
    parent = next(p for p in out.section_schemas if p.category == 'languages')
    assert all(not a.items for r in parent.records for a in r.attributes if a.name == 'proficiency')



def test_certificate_cards_do_not_disappear_when_legacy_values_are_validated():
    for index in (1,3):
        out = replay(index)
        assert out.data.certifications
        assert all(c.name for c in out.data.certifications)
        parent=next(p for p in out.section_schemas if p.category=='certifications')
        assert [c.name for c in out.data.certifications] == [next(a.items[0].value for a in r.attributes if a.name=='name') for r in parent.records]


def test_abbreviated_education_year_does_not_become_a_false_graduation_year():
    out=replay(3)
    assert out.data.education[0].start_year=='2018'
    assert out.data.education[0].graduation_year is None
    assert out.data.education[1].start_year=='2013'
    assert out.data.education[1].graduation_year is None


def test_engineered_responsibility_is_not_lost_as_a_title():
    assert any('Engineered features' in text for text in replay(3).data.experience[1].responsibilities)



def test_physical_skill_rows_are_not_combined_into_a_fictitious_compound():
    from local_api.services.list_fields import skill_candidates
    from local_api.schemas.sections import SectionBlock
    pieces=['Working Capital Finance ', 'Supply Chain Finance']
    blocks=[];offset=0
    for text in pieces:
        blocks.append(SectionBlock(source_element_index=0,start=offset,end=offset+len(text),text=text,
            page_number=1,assignment='semantic',lane='source',reason='physical source row'))
        offset+=len(text)
    assert skill_candidates(blocks)==['Working Capital Finance','Supply Chain Finance']



def test_source_backed_project_descriptions_are_not_erased_by_consistency_checks():
    for index in (3,4):
        out=replay(index)
        assert out.data.projects
        assert all(project.description for project in out.data.projects)
        parent=next(p for p in out.section_schemas if p.category=='projects')
        assert all(next(a.items for a in r.attributes if a.name=='description') for r in parent.records)



def test_project_groups_follow_visible_titles_and_keep_domain_lists_out():
    aditya=replay(3)
    assert len(aditya.data.projects)==5
    assert aditya.data.projects[0].name.startswith('Heart Flow')
    assert aditya.data.projects[-1].name.startswith('AI Customer Support')
    levi=replay(4)
    assert len(levi.data.projects)==5
    assert not any(p.name in {'Domain Experience','Banking: ICICI Bank, State bank of India, HDFC bank,'} for p in levi.data.projects)


def test_aditya_project_urls_keep_record_local_exact_evidence():
    out = replay(3)
    expected = {
        'Essay Writer': 'github.com/av525/essay-writer-langgraph',
        'AI Customer Support': 'github.com/av525/ai-customer-support',
    }
    parent = next(s for s in out.section_schemas if s.category == 'projects')
    for prefix, url in expected.items():
        index = next(i for i, project in enumerate(out.data.projects) if project.name.startswith(prefix))
        assert out.data.projects[index].url == url
        attribute = next(a for a in parent.records[index].attributes if a.name == 'url')
        assert [item.value for item in attribute.items] == [url]
        assert any(q.quote == url for q in attribute.items[0].evidence)
    assert all(project.url is None for project in out.data.projects[:3])


@pytest.mark.parametrize('rows, expected', [
    (['https://example.com/project'], 'https://example.com/project'),
    (['github.com/team/one', 'github.com/team/two'], None),
    (['Developed software using github.com/team/one'], None),
    (['user@example.com'], None),
])
def test_standalone_project_url_requires_unambiguous_url_row(rows, expected):
    from types import SimpleNamespace
    from local_api.services.record_subfields import refine_record
    blocks = [SimpleNamespace(text=text, assignment='semantic') for text in rows]
    values, reasons = refine_record('projects', {'name': 'Example', 'url': None}, blocks)
    assert values['url'] == expected
    if len(rows) > 1:
        assert any('Multiple project URLs' in reason for reason in reasons)
