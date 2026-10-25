"""Audits of source block accounting and main-to-subschema hierarchical mapping.

Verifies:
1. Source Block Audit: Original extracted blocks vs final mapped evidence and retained text:
   - Tracks mapped, unresolved, non-content artifacts, and 0 lost text.
   - Confirms no field is marked 'absent_in_source' when candidate text exists in unassigned blocks.
2. Main-Schema to Subschema Mapping Audit:
   - Valid and invalid subschema query paths.
   - Education and experience record arrays.
   - Multiple records inside one text block.
   - Mixed-content blocks (e.g. role, company, dates, responsibilities).
   - Records split across neighboring blocks.
   - Conformance of child results to parent subschema definitions (SUBSCHEMAS).
   - Strict source-backed citation evidence and provenance.
"""
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionBlock, SectionResponse, ResumeSection, SectionEntry
from local_api.schemas.subschema_spec import SUBSCHEMAS
from local_api.schemas.subschemas import SectionSchema
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.source_accounting import account_source
from local_api.services.subschema_validation import validate_hierarchy, query_subschemas
from local_api.vendor.handoff_schema.models import ResumeSchema


@pytest.fixture(autouse=True)
def no_live_provider(monkeypatch):
    for key in ['DEEPSEEK_REVIEW_ENABLED', 'DEEPSEEK_API_KEY', 'DEEPSEEK_MODEL']:
        monkeypatch.delenv(key, raising=False)
    import socket
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Offline test attempted network'))


def test_source_block_audit_accounts_for_every_character():
    """Verify that every single source block character is accounted for:

    either mapped to a section, retained in human review, or categorized as a non-content artifact.
    Zero characters are silently lost.
    """
    elements = [
        ExtractedElement(type='Header', text='Alice Walker\nalice@example.com\n+1 555-0100', page_number=1, metadata={}),
        ExtractedElement(type='Title', text='EXPERIENCE', page_number=1, metadata={}),
        ExtractedElement(type='NarrativeText', text='Tech Co | Senior Engineer | 2021 - Present\nBuilt distributed data pipelines.', page_number=1, metadata={}),
        ExtractedElement(type='NarrativeText', text='Unclassified training note in review', page_number=1, metadata={}),
        ExtractedElement(type='PageBreak', text='', page_number=1, metadata={}),
    ]
    b0 = SectionBlock(source_element_index=0, start=0, end=len(elements[0].text), text=elements[0].text,
                      page_number=1, lane='main', assignment='semantic', reason='Contact')
    b1 = SectionBlock(source_element_index=1, start=0, end=len(elements[1].text), text=elements[1].text,
                      page_number=1, lane='main', assignment='structural_heading', reason='Heading')
    b2 = SectionBlock(source_element_index=2, start=0, end=len(elements[2].text), text=elements[2].text,
                      page_number=1, lane='main', assignment='semantic', reason='Job 1')
    b3 = SectionBlock(source_element_index=3, start=0, end=len(elements[3].text), text=elements[3].text,
                      page_number=1, lane='main', assignment='needs_review', reason='Review block')
    b4 = SectionBlock(source_element_index=4, start=0, end=len(elements[4].text), text=elements[4].text,
                      page_number=1, lane='main', assignment='semantic', reason='Page break')

    sections = SectionResponse(
        status='needs_review',
        sections=build_sections({
            'personal_information': [b0],
            'experience': [b1, b2],
        }, elements),
        needs_review=[b3, b4],
        metadata={'total_units': 5, 'all_source_text_preserved': True},
        warnings=[]
    )

    req = SchemaMappingRequest(elements=elements, sections=sections, source='audit_test.pdf')
    res = map_schema(req)

    # 1. Source accounting audit
    accounting = res.meta['source_accounting']
    assert accounting['all_source_text_preserved'] is True
    assert accounting['total_spans'] == 5
    assert accounting['assigned_meaningful_spans'] == 3  # b0, b1, b2
    assert accounting['unresolved_meaningful_spans'] == 1  # b3
    assert accounting['non_content_artifacts'] == 1  # b4 (empty PageBreak)

    # 2. Total character accounting
    total_raw_chars = sum(len(e.text) for e in elements)
    accounted_chars = sum(len(o['reason'] or '') > 0 and (o['end'] - o['start']) for o in accounting['outcomes'])
    assert accounted_chars == total_raw_chars

    # 3. Residual and unmapped block audit
    unmapped = res.meta['unmapped_blocks']
    # b1 is structural heading so it's in unmapped blocks; b3 is in needs_review
    assert any(u['text'] == elements[1].text for u in unmapped)
    assert len(res.meta['needs_review']) == 2


def test_candidate_field_not_marked_absent_when_present_in_unassigned_blocks():
    """Ensure a field is marked 'present_but_unmapped' instead of 'absent_in_source'

    when relevant evidence exists in unassigned or needs_review blocks.
    """
    elements = [
        ExtractedElement(type='NarrativeText', text='Bob Martin\nbob@example.com\n555-432-1098', page_number=1, metadata={}),
        ExtractedElement(type='NarrativeText', text='Completed Bachelor of Science in Electrical Engineering at MIT in 2019.', page_number=1, metadata={})
    ]
    b0 = SectionBlock(source_element_index=0, start=0, end=len(elements[0].text), text=elements[0].text,
                      page_number=1, lane='main', assignment='semantic', reason='Contact')
    b1 = SectionBlock(source_element_index=1, start=0, end=len(elements[1].text), text=elements[1].text,
                      page_number=1, lane='main', assignment='needs_review', reason='Unplaced education')

    sections = SectionResponse(
        status='needs_review',
        sections=build_sections({'personal_information': [b0]}, elements),
        needs_review=[b1],
        metadata={'total_units': 2, 'all_source_text_preserved': True},
        warnings=[]
    )

    req = SchemaMappingRequest(elements=elements, sections=sections, source='unmapped_test.pdf')
    res = map_schema(req)

    statuses = res.meta['source_coverage_ledger']['field_statuses']
    # Education is present in unassigned block b1, so it must NOT be marked 'absent_in_source'
    assert statuses['education'] == 'present_but_unmapped'
    # Contact fields are mapped and extracted
    assert statuses['contact.full_name'] == 'present_and_extracted'
    assert statuses['contact.email'] == 'present_and_extracted'
    assert statuses['contact.phone'] == 'present_and_extracted'
    # Truly absent fields are correctly marked absent
    assert statuses['certifications'] == 'absent_in_source'


def test_subschema_query_paths_valid_and_invalid():
    """Audit valid and invalid subschema query paths, verifying resolution, record targeting,

    and strict path validation against SUBSCHEMAS.
    """
    lines = [
        "Master of Science in Software Engineering, Carnegie Mellon University, 2021",
        "Bachelor of Science in Physics, Columbia University, 2018"
    ]
    elements = [ExtractedElement(type='Title', text=t, page_number=1, metadata={}) for t in lines]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t, page_number=1,
                           assignment='semantic', lane='source', reason='test') for i, t in enumerate(lines)]
    entries = [SectionEntry(entry_id=f'education-{i+1}', block_indices=[i], lane='source', boundary_reason='test',
                            fields={'qualification': [i], 'institution': [i], 'dates': [i]}) for i in range(len(lines))]
    sections = SectionResponse(
        status='provisional',
        sections=build_sections({'education': blocks}, elements),
        needs_review=[], metadata={}, warnings=[]
    )
    res = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source='subschema_test.pdf'))

    # 1. Valid parent.child query across all records
    results = query_subschemas(res.section_schemas, 'education.institution')
    assert len(results) == 2
    assert results[0]['record_id'] == 'education-1'
    assert results[0]['items'][0]['value'] == 'Carnegie Mellon University'
    assert results[1]['record_id'] == 'education-2'
    assert results[1]['items'][0]['value'] == 'Columbia University'

    # 2. Valid query targeted to a specific record_id
    targeted = query_subschemas(res.section_schemas, 'education.degree', record_id='education-1')
    assert len(targeted) == 1
    assert targeted[0]['items'][0]['value'] == 'Master of Science'

    # 3. Invalid paths rejected with descriptive error
    with pytest.raises(ValueError, match='Unknown parent.child path'):
        query_subschemas(res.section_schemas, 'education.invalid_field')

    with pytest.raises(ValueError, match='Unknown parent.child path'):
        query_subschemas(res.section_schemas, 'non_existent_section.degree')

    with pytest.raises(ValueError, match='Unknown parent.child path'):
        query_subschemas(res.section_schemas, 'malformed_path_without_dot')


def test_subschema_mixed_content_and_split_neighboring_blocks():
    """Audit subschema mapping with mixed-content blocks and records split across neighboring blocks.

    Ensures child results conform to parent schema and retain source citations.
    """
    # Block 0: Employer and Role on adjacent rows (neighboring blocks forming one record)
    # Block 1: Role and Dates
    # Block 2: Responsibilities (mixed-content)
    raw_texts = [
        "Acme Global Inc",
        "Lead Solutions Architect | Jan 2021 - Present",
        "Designed microservices architecture; mentored 8 engineers; reduced cloud costs by 35%."
    ]
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in raw_texts]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t, page_number=1,
                           assignment='semantic', lane='source', reason='test') for i, t in enumerate(raw_texts)]
    # All 3 neighboring blocks belong to entry job-1
    entries = [SectionEntry(entry_id='job-1', block_indices=[0, 1, 2], lane='source', boundary_reason='split rows')]

    sections = SectionResponse(
        status='provisional',
        sections=[ResumeSection(category='experience', label='Work Experience', blocks=blocks, entries=entries)],
        needs_review=[], metadata={}, warnings=[]
    )

    data = ResumeSchema(
        contact={'full_name': '', 'email': '', 'phone': ''},
        experience=[{
            'company': 'Acme Global Inc',
            'role': 'Lead Solutions Architect',
            'start_date': 'Jan 2021',
            'end_date': 'Present',
            'responsibilities': [
                'Designed microservices architecture',
                'mentored 8 engineers',
                'reduced cloud costs by 35%'
            ]
        }]
    )

    from local_api.services.section_subschemas import build_subschemas
    nested = build_subschemas(sections, data, {'candidate_resume': True})

    # Strict hierarchy validation
    validated = validate_hierarchy(nested, sections)
    assert len(validated) == 1
    exp_schema = validated[0]
    assert exp_schema.category == 'experience'
    assert len(exp_schema.records) == 1
    rec = exp_schema.records[0]

    # Verify attributes conform to SUBSCHEMAS['experience']
    attr_names = {a.name for a in rec.attributes}
    assert attr_names <= set(SUBSCHEMAS['experience'])

    # Verify exact citations across neighboring blocks
    company_attr = next(a for a in rec.attributes if a.name == 'company')
    assert company_attr.items[0].value == 'Acme Global Inc'
    assert company_attr.items[0].evidence[0].source_id == 'e0:0:15'
    assert company_attr.items[0].evidence[0].quote == 'Acme Global Inc'

    role_attr = next(a for a in rec.attributes if a.name == 'role')
    assert role_attr.items[0].value == 'Lead Solutions Architect'
    assert role_attr.items[0].evidence[0].source_id == 'e1:0:45'
    assert 'Lead Solutions Architect' in role_attr.items[0].evidence[0].quote

    # Verify responsibilities from mixed-content block retain exact quotes
    resp_attr = next(a for a in rec.attributes if a.name == 'responsibilities')
    assert len(resp_attr.items) == 3
    for item in resp_attr.items:
        assert item.evidence[0].source_id == 'e2:0:86'
        assert item.value in item.evidence[0].quote
