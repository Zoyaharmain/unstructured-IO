"""Regression cases for schema placement, stable record identity and coverage."""
from copy import deepcopy
import pytest

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionBlock, SectionEntry, SectionResponse, ResumeSection
from local_api.services.schema_mapping import map_schema
from local_api.services.resume_structure import heading_boundary, employment_start
from local_api.services.resume_sections import ALIASES


@pytest.fixture(scope='module')
def engine():
    from local_api.services.resume_sections import get_engine
    return get_engine()


def request(category, lines):
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in lines]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t,
                          page_number=1, lane='main', assignment='semantic', reason='fixture') for i, t in enumerate(lines)]
    section = ResumeSection(category=category, label=category, blocks=blocks, text='\n'.join(lines))
    return SchemaMappingRequest(elements=elements, sections=SectionResponse(
        status='provisional', sections=[section], needs_review=[], metadata={}, warnings=[]))


def test_pruned_record_keeps_its_entry_identity_and_reindexed_evidence():
    req = request('education', ['Uninterpretable fragment', 'Bachelor of Science, Example University, 2020'])
    req.sections.sections[0].entries = [SectionEntry(
        entry_id=f'education-{i}', block_indices=[i], lane='main', boundary_reason='fixture',
        fields={} if i == 0 else {'qualification': [i], 'institution': [i], 'dates': [i]}) for i in range(2)]
    before = deepcopy(req.model_dump())
    result = map_schema(req)
    assert req.model_dump() == before
    assert len(result.data.education) == 1
    assert result.meta['record_bindings']['education'] == {'education-1': 0}
    assert [r['mapped_index'] for r in result.meta['record_reviews']] == [None, 0]
    assert [r.record_id for r in result.section_schemas[0].records] == ['education-1']
    assert result.meta['field_evidence']['education[0].institution'] == [f'e1:0:{len(req.elements[1].text)}']
    assert not any(p.startswith('education[1]') for p in result.meta['field_evidence'])
    attrs = {a.name: a.items for a in result.section_schemas[0].records[0].attributes}
    assert attrs['institution'][0].value == 'Example University'
    assert attrs['institution'][0].evidence[0].source_id.startswith('e1:')


def test_contact_in_wrong_section_is_unmapped_instead_of_absent():
    result = map_schema(request('skills', ['Python, SQL', 'Email: alex@example.com', 'Phone: +44 20 7946 0958']))
    statuses = result.meta['field_source_status']
    assert statuses['contact.email'] == 'present_but_unmapped'
    assert statuses['contact.phone'] == 'present_but_unmapped'
    assert result.data.contact.email == ''
    dates_only = map_schema(request('skills', ['Python, SQL, 2020 - 2024']))
    assert dates_only.meta['field_source_status']['contact.phone'] == 'absent_in_source'


def test_conflicting_contact_labels_are_ambiguous():
    result = map_schema(request('personal_information', ['Email: first@example.com', 'Email: second@example.com']))
    assert result.data.contact.email == ''
    assert result.meta['field_source_status']['contact.email'] == 'present_but_ambiguous'


def test_record_statuses_include_optional_children_and_local_conflicts():
    req = request('experience', ['Company: Acme Ltd', 'Role: Engineer', 'Role: Analyst'])
    req.sections.sections[0].entries = [SectionEntry(entry_id='job', block_indices=[0, 1, 2],
        lane='main', boundary_reason='fixture', fields={'employer': [0], 'title': [1, 2]})]
    result = map_schema(req)
    assert result.meta['field_source_status']['experience[0].role'] == 'present_but_ambiguous'
    assert result.meta['field_source_status']['experience[0].location'] == 'absent_in_source'


def test_heading_and_award_boundaries_do_not_reclassify_project_titles_as_jobs():
    assert heading_boundary('Training App- Leading Waste management company', ALIASES) == (None, None)
    assert heading_boundary('KEY PROJECTS AND ROLES:', ALIASES)[0] == 'experience'
    assert heading_boundary('INDEPENDENT PROJECT', ALIASES)[0] == 'projects'
    assert heading_boundary('ACADEMIC DETAILS', ALIASES)[0] == 'education'
    assert not employment_start('Spotlight Award, UB Technology Innovations - May 2021')
    assert employment_start('Software Engineer | Acme Ltd | May 2021 - Present')


def test_professional_engagement_after_skills_restores_experience(engine):
    from local_api.schemas.sections import SectionRequest
    from local_api.services.section_recovery import recover_sections
    from local_api.services.source_validation import validate_result
    lines = ['Alex Morgan', 'alex@example.com', 'WORK EXPERIENCE',
             'Software Engineer | Acme Ltd | 2020 - Present', 'TECHNICAL SKILLS', 'Python, SQL',
             'Role: Software Engineer. Project: Warehouse System. Client: Flight Services.',
             'Developed reliable backend applications and REST APIs.']
    req = SectionRequest(elements=[ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in lines])
    result = recover_sections(req, engine.detect(req))
    experience = next(s for s in result.sections if s.category == 'experience')
    assert {6, 7} <= {b.source_element_index for b in experience.blocks}
    assert validate_result(req.elements, result) == []


def test_project_training_title_and_technology_prose_keep_project_context(engine):
    from local_api.schemas.sections import SectionRequest
    from local_api.services.section_recovery import recover_sections
    lines = ['PROJECTS', 'PROJECT 6 Training App- Leading Waste management company',
             'Technology: PowerApps, Microsoft Projects, SQL Server',
             'Developed training schedules and managed employee assignments.']
    req = SectionRequest(elements=[ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in lines])
    result = recover_sections(req, engine.detect(req))
    assert {s.category for s in result.sections} == {'projects'}
