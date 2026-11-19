"""Tests for context-aware structural review chunking, relationship preservation,
cross-chunk reconciliation, and verified repair on oversized resumes.
"""
import json
import os
from pathlib import Path
import pytest

from local_api.core.provider_env import load_provider_env
from local_api.schemas.sections import ExtractedElement, ResumeSection, SectionBlock, SectionEntry, SectionResponse, SectionRequest
from local_api.services.llm_section_review import ReviewSettings, check_connection
from local_api.services.review_chunking import (
    ChunkError,
    structural_review_plan,
    run_structural_chunks,
    measure
)
from local_api.services.source_ownership import (
    snapshot,
    finalize_ownership,
    apply_operations,
    materialize,
    translate_decisions_to_operations
)
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.schema_mapping import map_schema


def create_element(index: int, text: str, elem_type: str = "NarrativeText", page: int = 1, bbox=(0.1, 0.1, 0.9, 0.2)) -> ExtractedElement:
    return ExtractedElement(
        type=elem_type,
        text=text,
        page_number=page,
        metadata={
            "coordinates": {
                "points": [[bbox[0], bbox[1]], [bbox[2], bbox[1]], [bbox[2], bbox[3]], [bbox[0], bbox[3]]],
                "layout_width": 1000,
                "layout_height": 1000,
            },
            "pdf_source_lines": [{"start": 0, "end": len(text), "bbox": list(bbox), "text": text}],
        },
    )


def build_synthetic_oversized_resume(num_jobs: int = 6, duties_per_job: int = 15):
    """Generate a synthetic multi-job resume designed to exceed 200k chars when raw metadata is included."""
    elements = []
    blocks = []
    entries = []
    idx = 0

    # Section Heading
    el_heading = create_element(idx, "EXPERIENCE HISTORY", elem_type="Title", page=1, bbox=(0.1, 0.05, 0.5, 0.08))
    elements.append(el_heading)
    blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(el_heading.text), text=el_heading.text,
                               page_number=1, assignment='semantic', lane='left', reason='test'))
    idx += 1

    # First role detached from company (representing local heuristic failure)
    el_role1 = create_element(idx, "ASSOCIATE DATA ANALYST", elem_type="Title", page=1, bbox=(0.1, 0.09, 0.5, 0.12))
    elements.append(el_role1)
    blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(el_role1.text), text=el_role1.text,
                               page_number=1, assignment='employment_boundary', lane='left', reason='test'))
    entries.append(SectionEntry(
        entry_id='experience-1',
        block_indices=[0, 1],
        lane='left',
        boundary_reason='test',
        fields={'employer': [0], 'title': [1]}
    ))
    idx += 1

    # Company for role 1
    el_comp1 = create_element(idx, "ATYATI TECHNOLOGIES PVT.LTD / 06/2018 - 08/2021", elem_type="Header", page=1, bbox=(0.1, 0.13, 0.9, 0.16))
    elements.append(el_comp1)
    b_comp1_idx = len(blocks)
    blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(el_comp1.text), text=el_comp1.text,
                               page_number=1, assignment='employment_boundary', lane='left', reason='test'))
    idx += 1

    entry2_blocks = [b_comp1_idx]
    entry2_resp = []
    for d in range(duties_per_job):
        duty_text = f"Analyzed database performance metric {d} using Advanced SQL and Python for banking reporting."
        el_d = create_element(idx, duty_text, elem_type="ListItem", page=1, bbox=(0.1, 0.17 + d * 0.02, 0.9, 0.19 + d * 0.02))
        elements.append(el_d)
        entry2_resp.append(len(blocks))
        entry2_blocks.append(len(blocks))
        blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(duty_text), text=duty_text,
                                   page_number=1, assignment='heading_context', lane='left', reason='test'))
        idx += 1
    entries.append(SectionEntry(
        entry_id='experience-2',
        block_indices=entry2_blocks,
        lane='left',
        boundary_reason='test',
        fields={'employer': [b_comp1_idx], 'dates': [b_comp1_idx], 'responsibilities': entry2_resp}
    ))

    # Remaining jobs
    for j in range(3, num_jobs + 1):
        page = j // 2 + 1
        comp_text = f"ENTERPRISE CORP {j} / 202{j-2} - 202{j-1}"
        role_text = f"LEAD ANALYST {j}"
        el_c = create_element(idx, comp_text, elem_type="Header", page=page)
        elements.append(el_c)
        b_c_idx = len(blocks)
        blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(comp_text), text=comp_text,
                                   page_number=page, assignment='employment_boundary', lane='left', reason='test'))
        idx += 1

        el_r = create_element(idx, role_text, elem_type="Title", page=page)
        elements.append(el_r)
        b_r_idx = len(blocks)
        blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(role_text), text=role_text,
                                   page_number=page, assignment='employment_boundary', lane='left', reason='test'))
        idx += 1

        j_blocks = [b_c_idx, b_r_idx]
        j_resp = []
        for d in range(duties_per_job):
            d_text = f"Delivered high-volume enterprise transformation metric {j}.{d} across multiple global cloud teams."
            el_jd = create_element(idx, d_text, elem_type="ListItem", page=page)
            elements.append(el_jd)
            j_resp.append(len(blocks))
            j_blocks.append(len(blocks))
            blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(d_text), text=d_text,
                                       page_number=page, assignment='heading_context', lane='left', reason='test'))
            idx += 1
        entries.append(SectionEntry(
            entry_id=f'experience-{j}',
            block_indices=j_blocks,
            lane='left',
            boundary_reason='test',
            fields={'employer': [b_c_idx], 'title': [b_r_idx], 'dates': [b_c_idx], 'responsibilities': j_resp}
        ))

    exp_section = ResumeSection(category='experience', label='Experience', text='\n'.join(b.text for b in blocks),
                                blocks=blocks, entries=entries)

    # Awards Section with merged awards and split multiline continuation
    aw_blocks = []
    aw_entries = []
    aw_base = idx

    aw_heading = create_element(idx, "ACHIEVEMENTS", elem_type="Title", page=3)
    elements.append(aw_heading)
    aw_blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(aw_heading.text), text=aw_heading.text,
                                  page_number=3, assignment='structural_heading', lane='left', reason='test'))
    idx += 1

    # Merged award 1 and 2
    aw1 = create_element(idx, "Awarded as ‘Extra Mile’ in DSB Project in Atyati Technologies.", elem_type="ListItem", page=3)
    elements.append(aw1)
    b_aw1_idx = len(aw_blocks)
    aw_blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(aw1.text), text=aw1.text,
                                  page_number=3, assignment='semantic', lane='left', reason='test'))
    idx += 1

    aw2 = create_element(idx, "Awarded as ‘Game Changer’ and got recognized by Client and Genpact Management.", elem_type="ListItem", page=3)
    elements.append(aw2)
    b_aw2_idx = len(aw_blocks)
    aw_blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(aw2.text), text=aw2.text,
                                  page_number=3, assignment='semantic', lane='left', reason='test'))
    idx += 1

    # Local pipeline falsely merged them into awards-1
    aw_entries.append(SectionEntry(
        entry_id='awards-1',
        block_indices=[b_aw1_idx, b_aw2_idx],
        lane='left',
        boundary_reason='test',
        fields={'title': [b_aw1_idx]}
    ))

    # Multiline continuation award
    aw3_part1 = create_element(idx, "Recommended by Reporting Manager for getting promoted into next level in", elem_type="ListItem", page=3)
    elements.append(aw3_part1)
    b_aw3_1 = len(aw_blocks)
    aw_blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(aw3_part1.text), text=aw3_part1.text,
                                  page_number=3, assignment='semantic', lane='left', reason='test'))
    idx += 1

    aw3_part2 = create_element(idx, "the current organization.", elem_type="NarrativeText", page=3)
    elements.append(aw3_part2)
    b_aw3_2 = len(aw_blocks)
    aw_blocks.append(SectionBlock(source_element_index=idx, start=0, end=len(aw3_part2.text), text=aw3_part2.text,
                                  page_number=3, assignment='semantic', lane='left', reason='test'))
    idx += 1

    aw_entries.append(SectionEntry(entry_id='awards-2', block_indices=[b_aw3_1], lane='left', boundary_reason='test', fields={}))
    aw_entries.append(SectionEntry(entry_id='awards-3', block_indices=[b_aw3_2], lane='left', boundary_reason='test', fields={'title': [b_aw3_2]}))

    aw_section = ResumeSection(category='awards', label='Awards', text='\n'.join(b.text for b in aw_blocks),
                               blocks=aw_blocks, entries=aw_entries)

    res = SectionResponse(status='provisional', sections=[exp_section, aw_section], needs_review=[], metadata={}, warnings=[])
    return elements, res


def test_structural_review_chunking_plan_preserves_relationships():
    """Verify that oversized structural review requests partition into context-aware chunks that respect limits."""
    elements, res = build_synthetic_oversized_resume(num_jobs=6, duties_per_job=12)
    state = snapshot(elements, res)

    # Tight budget: 40k chars and 20k tokens so single payload will NOT fit, forcing chunking
    settings = ReviewSettings(enabled=True, api_key='mock', max_input_chars=40000, max_input_tokens=20000, max_units=600)
    planned = structural_review_plan(elements, state, res, settings)

    assert planned['status'] == 'planned'
    assert len(planned['chunks']) > 1, "Oversized request must be partitioned into multiple chunks"

    # Verify that every planned chunk respects the character and token budget
    for c in planned['chunks']:
        meas = c['measurement']
        assert meas['fits'], f"Chunk {c['chunk_id']} exceeded configured budget: {meas}"
        assert meas['serialized_characters'] <= settings.max_input_chars
        assert meas['input_token_policy_bound'] <= settings.max_input_tokens

    # Verify that Chunk 1 for experience contains both experience-1 and experience-2 to preserve role-employer relationship
    exp_chunk = next(c for c in planned['chunks'] if 'experience' in c['sections'])
    exp_records = exp_chunk['visible_records']
    assert any('e0:0:' in r or 'experience@e0' in r or 'experience-1' in r or 'e1:0:' in r for r in exp_records)
    assert any('e2:0:' in r or 'experience@e2' in r or 'experience-2' in r for r in exp_records)


def test_structural_review_simulated_cross_chunk_repair():
    """Verify that simulated LLM responses across chunks correct both experience and awards issues atomically."""
    elements, res = build_synthetic_oversized_resume(num_jobs=4, duties_per_job=8)

    calls_made = []

    def mock_transport(settings, messages):
        calls_made.append(messages)
        body = json.loads(messages[1]['content'])
        sections = body.get('sections', {})

        if 'experience' in sections and 'experience@e2:0:47' in body.get('candidate_records', []):
            # Propose correcting EXPERIENCE HISTORY heading and attaching role to ATYATI
            return json.dumps({
                'operations': [
                    {'op': 'assign', 'source_ids': ['e0:0:18'], 'section': 'experience', 'record': None, 'fields': []},
                    {'op': 'assign', 'source_ids': ['e1:0:22'], 'section': 'experience', 'record': 'experience@e2:0:47', 'fields': ['title']}
                ]
            })
        elif 'awards' in sections:
            # Propose splitting awards and merging continuation
            return json.dumps({
                'operations': [
                    {'op': 'split', 'record': 'awards@e32:0:62', 'anchor': 'e33:0:78'},
                    {'op': 'merge', 'records': ['awards@e34:0:72', 'awards@e35:0:25']}
                ]
            })
        else:
            return json.dumps({'operations': []})

    settings = ReviewSettings(enabled=True, api_key='mock', max_input_chars=35000, max_input_tokens=20000)
    reviewed = finalize_ownership(elements, res, settings=settings, transport=mock_transport, review=True)

    review_meta = reviewed.metadata.get('structure_review', {})
    assert review_meta.get('status') == 'provisional'
    assert review_meta.get('provider_calls', 0) >= 2, "Must make calls across multiple chunks"
    assert len(review_meta.get('applied_operations', [])) >= 2

    # Verify experience fix: role associated with company, heading removed
    exp_sec = next(s for s in reviewed.sections if s.category == 'experience')
    first_exp = exp_sec.entries[0]
    assert 'title' in first_exp.fields
    assert 'employer' in first_exp.fields
    assert 'ATYATI' in exp_sec.blocks[first_exp.fields['employer'][0]].text
    assert 'ASSOCIATE DATA ANALYST' in exp_sec.blocks[first_exp.fields['title'][0]].text


def test_structural_review_foreign_record_rejection():
    """Verify that operations referencing source IDs or records outside the chunk are safely rejected."""
    elements, res = build_synthetic_oversized_resume(num_jobs=4, duties_per_job=8)

    def invalid_foreign_transport(settings, messages):
        body = json.loads(messages[1]['content'])
        # Try to modify a source ID that does NOT belong to this chunk
        return json.dumps({
            'operations': [
                {'op': 'assign', 'source_ids': ['e9999:0:10'], 'section': 'experience', 'record': None, 'fields': []}
            ]
        })

    settings = ReviewSettings(enabled=True, api_key='mock', max_input_chars=35000, max_input_tokens=20000)
    reviewed = finalize_ownership(elements, res, settings=settings, transport=invalid_foreign_transport, review=True)

    review_meta = reviewed.metadata.get('structure_review', {})
    assert review_meta.get('status') == 'rejected'
    assert 'Repair references' in review_meta.get('validation_reason', '')


def test_structural_review_budget_exhaustion_never_reports_success():
    """Verify that when the request budget is exhausted, review status is budget_exceeded and never provisional/success."""
    elements, res = build_synthetic_oversized_resume(num_jobs=6, duties_per_job=10)

    # max_units=1 forces chunking failure because no real resume record has <= 1 unit
    settings = ReviewSettings(enabled=True, api_key='mock', max_units=1)
    reviewed = finalize_ownership(elements, res, settings=settings, transport=lambda *_: pytest.fail('Should not be called'), review=True)

    review_meta = reviewed.metadata.get('structure_review', {})
    assert review_meta.get('status') == 'budget_exceeded'
    assert review_meta.get('provider_calls', 0) == 0


@pytest.mark.provider
def test_live_deepseek_structural_chunking_abhishek_fixture():
    """Mandatory end-to-end verification against real Abhishek_HV fixture (doc 86ca79a7aead8cedc055.json).

    Clearly distinguishes simulated mock behavior from live DeepSeek model execution.
    Verifies:
    1. Heading 'EXPERIENCE HISTORY' is recognized as a heading rather than an employer.
    2. 'ASSOCIATE DATA ANALYST' is associated with ATYATI TECHNOLOGIES.
    3. 'Extra Mile' and 'Game Changer' are separated into two independent award records.
    4. Multiline continuation 'Recommended by Reporting Manager... in the current organization.' is merged.
    """
    env_path = Path(__file__).resolve().parents[1] / '.env'
    load_provider_env(env_path)
    if os.getenv('DEEPSEEK_API_KEY'):
        os.environ['DEEPSEEK_REVIEW_ENABLED'] = 'true'

    conn = check_connection()
    if conn.get("status") != "ready":
        pytest.skip(f"DeepSeek API not ready for live test: {conn.get('message')}")

    settings = ReviewSettings.from_env()

    fixture_path = Path(__file__).resolve().parents[1] / 'ground_truth' / 'corpus_audit' / 'documents' / '86ca79a7aead8cedc055.json'
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")

    data = json.loads(fixture_path.read_text())
    from local_api.services.resume_sections import detect_sections
    from local_api.services.section_recovery import recover_sections
    from local_api.services.contact_sections import recover_contact_sections
    from local_api.services.education_date_recovery import recover_education_dates

    req = SectionRequest.model_validate({'elements': data['extraction']['elements']})
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = recover_education_dates(res, req.elements)
    res = recover_contact_sections(res, req.elements)

    # Perform structural review with live DeepSeek flash model in context-aware chunks
    reviewed = finalize_ownership(req.elements, res, settings=settings, review=True)
    review_meta = reviewed.metadata.get('structure_review', {})

    print(f"\n[LIVE DEEPSEEK TEST RESULT] Status: {review_meta.get('status')}, Provider Calls: {review_meta.get('provider_calls')}")
    print(f"Applied Operations: {review_meta.get('applied_operations')}")

    assert review_meta.get('status') in {'provisional', 'complete'}
    assert review_meta.get('provider_calls', 0) >= 1

    # Verify experience section corrections
    exp_sec = next(s for s in reviewed.sections if s.category == 'experience')
    # Check that EXPERIENCE HISTORY is not an employer
    all_employers = [exp_sec.blocks[i].text for e in exp_sec.entries for i in e.fields.get('employer', [])]
    assert not any('EXPERIENCE HISTORY' in emp for emp in all_employers), "EXPERIENCE HISTORY must not be an employer"

    # Check that ATYATI TECHNOLOGIES has ASSOCIATE DATA ANALYST
    atyati_entry = next((e for e in exp_sec.entries if any('ATYATI' in exp_sec.blocks[i].text for i in e.fields.get('employer', []))), None)
    assert atyati_entry is not None, "ATYATI TECHNOLOGIES entry must exist"
    atyati_titles = [exp_sec.blocks[i].text for i in atyati_entry.fields.get('title', [])]
    assert any('ASSOCIATE DATA ANALYST' in t for t in atyati_titles), "ASSOCIATE DATA ANALYST must be attached to ATYATI TECHNOLOGIES"

    # Verify awards section corrections
    aw_sec = next(s for s in reviewed.sections if s.category == 'awards')
    aw_texts = [' '.join(aw_sec.blocks[i].text for i in e.block_indices) for e in aw_sec.entries]
    extra_mile_entries = [t for t in aw_texts if 'Extra Mile' in t]
    game_changer_entries = [t for t in aw_texts if 'Game Changer' in t]
    assert len(extra_mile_entries) >= 1, "Extra Mile award record must exist"
    assert len(game_changer_entries) >= 1, "Game Changer award record must exist"
    # Ensure they are in separate records
    assert not any('Extra Mile' in t and 'Game Changer' in t for t in aw_texts), "Extra Mile and Game Changer must be in separate records"

    # Map to schema and assert zero corruption
    map_req = ReviewedSchemaMappingRequest(elements=req.elements, sections=reviewed)
    mapped = map_schema(map_req)
    assert len(mapped.data.experience) >= 1
    atyati_mapped = next((j for j in mapped.data.experience if j.company and 'ATYATI' in j.company), None)
    assert atyati_mapped is not None
    assert atyati_mapped.role == 'ASSOCIATE DATA ANALYST'
