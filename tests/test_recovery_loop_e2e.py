"""Deterministic end-to-end tests for the missed-information recovery loop.

Proves:
1. Source contains education or employment field that initial pass leaves unmapped.
2. Coverage ledger identifies the field as 'present_but_unmapped'.
3. Recovery stage reprocesses the evidence and recovers the field.
4. Record is reconciled into schema without duplicating records.
5. Final validation succeeds with strict source-grounded evidence.
6. Bounded retry limits and unresolved cases terminate cleanly.
"""
import json
import pytest
from types import SimpleNamespace

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionBlock, SectionRequest, SectionResponse
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.section_recovery import recover_sections
from local_api.services.source_validation import validate_result
from local_api.services import llm_section_review as review
from scripts.single_resume_pipeline import run_feedback


@pytest.fixture(autouse=True)
def no_live_provider(monkeypatch):
    """Enforce strict offline isolation; fail if network socket connection is attempted."""
    for key in ['DEEPSEEK_REVIEW_ENABLED', 'DEEPSEEK_API_KEY', 'DEEPSEEK_MODEL']:
        monkeypatch.delenv(key, raising=False)
    import socket
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Offline recovery test attempted network'))


def make_deterministic_elements():
    """Synthetic elements with contact, experience, and education."""
    raw = [
        ('NarrativeText', "Jane Doe\njane.doe@example.com\n+1 555-0199\nSan Francisco, CA"),
        ('Title', "WORK EXPERIENCE"),
        ('NarrativeText', "Acme Corp | Senior Software Engineer | 2020 - Present\nArchitected scalable backend microservices using Python and Go."),
        ('NarrativeText', "Beta LLC | Software Developer | 2017 - 2020\nMaintained internal web services."),
        ('Title', "EDUCATION"),
        ('Title', "Master of Science in Computer Science, Stanford University, 2017."),
        ('Title', "Bachelor of Science in Mathematics, University of California, Berkeley, 2015.")
    ]
    return [
        ExtractedElement(type=t, text=text, page_number=1, metadata={'element_index': i})
        for i, (t, text) in enumerate(raw)
    ]


def test_recovery_loop_recovers_unmapped_education_without_duplication():
    """Pass 1 leaves education unmapped -> ledger detects present_but_unmapped ->

    Recovery reprocesses -> reconciles without duplicating -> validation passes.
    """
    elements = make_deterministic_elements()

    # Pass 1: Initial section assignments deliberately leave education blocks in needs_review
    b0 = SectionBlock(source_element_index=0, start=0, end=len(elements[0].text), text=elements[0].text,
                      page_number=1, lane='main', assignment='semantic', reason='Header')
    b1 = SectionBlock(source_element_index=1, start=0, end=len(elements[1].text), text=elements[1].text,
                      page_number=1, lane='main', assignment='structural_heading', reason='Heading')
    b2 = SectionBlock(source_element_index=2, start=0, end=len(elements[2].text), text=elements[2].text,
                      page_number=1, lane='main', assignment='semantic', reason='Job 1')
    b3 = SectionBlock(source_element_index=3, start=0, end=len(elements[3].text), text=elements[3].text,
                      page_number=1, lane='main', assignment='semantic', reason='Job 2')

    # Deliberately missed education heading & degrees in needs_review
    b4 = SectionBlock(source_element_index=4, start=0, end=len(elements[4].text), text=elements[4].text,
                      page_number=1, lane='main', assignment='needs_review', reason='Missed heading')
    b5 = SectionBlock(source_element_index=5, start=0, end=len(elements[5].text), text=elements[5].text,
                      page_number=1, lane='main', assignment='needs_review', reason='Unmapped degree 1')
    b6 = SectionBlock(source_element_index=6, start=0, end=len(elements[6].text), text=elements[6].text,
                      page_number=1, lane='main', assignment='needs_review', reason='Unmapped degree 2')

    local_pass1 = SectionResponse(
        status='needs_review',
        sections=build_sections({
            'personal_information': [b0],
            'experience': [b1, b2, b3],
        }, elements),
        needs_review=[b4, b5, b6],
        metadata={'total_units': 7, 'all_source_text_preserved': True},
        warnings=[]
    )

    # 1. First mapping pass
    req1 = SchemaMappingRequest(elements=elements, sections=local_pass1, source='synthetic_resume.pdf')
    res1 = map_schema(req1)

    # Confirm education is empty on pass 1
    assert len(res1.data.education) == 0
    # Confirm coverage ledger flags education as 'present_but_unmapped'
    ledger1 = res1.meta['source_coverage_ledger']['field_statuses']
    assert ledger1['education'] == 'present_but_unmapped'
    assert res1.meta['source_coverage_ledger']['status_counts']['present_but_unmapped'] >= 1

    # 2. Recovery stage reprocesses the evidence
    # Deterministic mock transport reassigns needs_review units to 'education'
    def deterministic_recovery_transport(settings, messages):
        data = json.loads(messages[1]['content'])
        assignments = []
        for span in data['spans']:
            uid = span['id']
            curr = span['current_category']
            if curr == 'needs_review':
                assignments.append([uid, 'education'])
            else:
                assignments.append([uid, curr])
        return json.dumps({'assignments': assignments})

    settings = review.ReviewSettings(enabled=True, api_key='test-key', model='test-model', recovery_attempts=1)
    recovered_sections = review.review_sections(
        SectionRequest(elements=elements),
        local_pass1,
        settings=settings,
        transport=deterministic_recovery_transport
    )

    # 3. Reconciled mapping pass
    req2 = SchemaMappingRequest(elements=elements, sections=recovered_sections, source='synthetic_resume.pdf')
    res2 = map_schema(req2)

    # 4. Verification: Education is recovered and reconciled without duplicate records
    assert len(res2.data.education) == 2
    degrees = [e.degree for e in res2.data.education]
    institutions = [e.institution for e in res2.data.education]
    assert any('Master' in d for d in degrees)
    assert any('Bachelor' in d for d in degrees)
    assert any('Stanford University' in inst for inst in institutions)
    assert any('University of California' in inst for inst in institutions)

    # Verification: Experience records were preserved and NOT duplicated
    assert len(res2.data.experience) == 2
    companies = [j.company for j in res2.data.experience]
    assert 'Acme Corp' in companies
    assert 'Beta LLC' in companies

    # Verification: Source coverage ledger updated to 'present_and_extracted'
    ledger2 = res2.meta['source_coverage_ledger']['field_statuses']
    assert ledger2['education'] == 'present_and_extracted'
    assert ledger2['experience'] == 'present_and_extracted'
    assert ledger2['contact.full_name'] == 'present_and_extracted'
    assert ledger2['contact.email'] == 'present_and_extracted'

    # Verification: Strict source validation passes
    errors = validate_result(elements, recovered_sections)
    assert errors == []


def test_recovery_loop_bounded_retries_and_unresolved_case():
    """When unassigned content contains unresolvable non-resume text,

    the recovery loop respects retry limits, halts gracefully, and records unresolved status.
    """
    elements = [
        ExtractedElement(type='NarrativeText', text='John Smith\njohn@example.com\n555-123-4567', page_number=1, metadata={}),
        ExtractedElement(type='NarrativeText', text='Random noise footer and scanner distortion artifacts', page_number=1, metadata={})
    ]
    b0 = SectionBlock(source_element_index=0, start=0, end=len(elements[0].text), text=elements[0].text,
                      page_number=1, lane='main', assignment='semantic', reason='Header')
    b1 = SectionBlock(source_element_index=1, start=0, end=len(elements[1].text), text=elements[1].text,
                      page_number=1, lane='main', assignment='needs_review', reason='Unresolvable noise')

    local = SectionResponse(
        status='needs_review',
        sections=build_sections({'personal_information': [b0]}, elements),
        needs_review=[b1],
        metadata={'total_units': 2, 'all_source_text_preserved': True},
        warnings=[]
    )

    request = SectionRequest(elements=elements)
    call_count = 0

    def noisy_transport(settings, messages):
        nonlocal call_count
        call_count += 1
        # Reviewer cannot place noise; returns needs_review assignment
        return json.dumps({'assignments': [['u0', 'needs_review']]})

    settings = review.ReviewSettings(enabled=True, api_key='test-key', model='test-model', recovery_attempts=2)

    def dummy_audit(sections, schema):
        return {'status': 'complete', 'findings': []}

    saved_passes = []
    def save_pass(idx, sections, schema, audit, row):
        saved_passes.append((idx, row))

    sections_out, schema_out, audit_out, meta_out = run_feedback(
        request, local, settings, 'synthetic_noisy.pdf', noisy_transport, dummy_audit, save_pass
    )

    # Verify loop halted cleanly and respected bounds
    assert meta_out['stop_reason'] in {'no_source_or_mapping_progress', 'recovery_budget_exhausted', 'section_review_failed'}
    assert len(saved_passes) <= 3  # Initial + bounded retries
    # Verify unresolved case is preserved in ledger without crashing
    statuses = schema_out['meta']['source_coverage_ledger']['field_statuses']
    assert statuses['contact.full_name'] == 'present_and_extracted'
    assert statuses['contact.email'] == 'present_and_extracted'
    # Unmentioned sections are absent_in_source, not fabricated
    assert statuses['education'] == 'absent_in_source'
    assert statuses['experience'] == 'absent_in_source'
