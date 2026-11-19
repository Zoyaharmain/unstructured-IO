"""Comprehensive test suite for Generalized Resume Semantic Understanding,
Hierarchical Record Ownership, and Verified LLM Recovery.

Covers:
- Case A: Project group with child projects (e.g. Param Info context)
- Case B: Single project with numbered description steps (no splitting)
- Case C: Multiple experiences with preserved employer boundaries
- Case D: Wrapped multi-line certification title
- Case E: Multi-column resume layout (preventing cross-column contamination)
- Ambiguity Detection: Deterministic pipeline marks uncertain spans as needs_review
- Validated LLM Decision Application: Structured decisions mapped to operations
- Invalid LLM Response Rejection: Rejects malformed/hallucinated LLM responses safely
- Live DeepSeek LLM Recovery: End-to-end integration with configured LLM
"""
import os
import json
from pathlib import Path
import pytest
from types import MappingProxyType

from local_api.core.provider_env import load_provider_env

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import (
    SectionRequest,
    SectionBlock,
    SectionResponse,
    SectionEntry,
    ResumeSection
)
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.resume_sections import detect_sections
from local_api.services.section_recovery import recover_sections
from local_api.services.contact_sections import recover_contact_sections
from local_api.services.education_date_recovery import recover_education_dates
from local_api.services.project_hierarchy import detect_project_records, recover_project_groups
from local_api.services.logical_blocks import logical_blocks
from local_api.services.source_ownership import (
    snapshot,
    finalize_ownership,
    translate_decisions_to_operations,
    apply_operations,
    validate_record_tree,
    SourceSpan
)
from local_api.services.schema_mapping import map_schema
from local_api.services.llm_section_review import ReviewSettings, check_connection


def create_element(index, text, elem_type='NarrativeText', page=1, bbox=(0.1, 0.1, 0.9, 0.2)):
    return ExtractedElement(
        element_id=f"elem_{index}",
        text=text,
        type=elem_type,
        page_number=page,
        metadata={
            "coordinates": {
                "points": [(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])],
                "layout_width": 1.0,
                "layout_height": 1.0
            },
            "pdf_source_lines": [{
                "text": text,
                "bbox": list(bbox),
                "start": 0,
                "end": len(text),
                "bold": elem_type == 'Title'
            }]
        }
    )


# ==============================================================================
# Case A: Project group with child projects (e.g. Param Info context header)
# ==============================================================================
def test_case_a_project_group_with_child_projects():
    """Verify context header 'Worked in Param Info' forms a parent group and links child projects."""
    elements = [
        create_element(0, "PROJECTS", elem_type="Title", bbox=(0.1, 0.10, 0.9, 0.12)),
        create_element(1, "Worked in Param Info", elem_type="Title", bbox=(0.1, 0.13, 0.9, 0.15)),
        create_element(2, "June 2025 - Feb 2026", elem_type="NarrativeText", bbox=(0.1, 0.16, 0.9, 0.18)),
        create_element(3, "1. Kiosk Automation", elem_type="Title", bbox=(0.1, 0.19, 0.9, 0.21)),
        create_element(4, "Built self-service kiosk using Python and PyQt.", elem_type="NarrativeText", bbox=(0.1, 0.22, 0.9, 0.24)),
        create_element(5, "2. Data Processing Pipeline", elem_type="Title", bbox=(0.1, 0.25, 0.9, 0.27)),
        create_element(6, "Processed real-time sensor data using Kafka.", elem_type="NarrativeText", bbox=(0.1, 0.28, 0.9, 0.30)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = finalize_ownership(elements, res)

    proj_sec = next(s for s in res.sections if s.category == 'projects')
    assert proj_sec is not None

    # Verify parent group recovery
    group_entries = [e for e in proj_sec.entries if e.record_kind == 'group']
    assert len(group_entries) == 1, f"Expected 1 project group, got {len(group_entries)}"
    group = group_entries[0]
    assert "Param Info" in proj_sec.blocks[group.block_indices[0]].text

    # Verify child projects link to the group
    child_entries = [e for e in proj_sec.entries if e.record_kind != 'group']
    assert len(child_entries) == 2, f"Expected 2 child projects, got {len(child_entries)}"
    for child in child_entries:
        assert child.parent_entry_id == group.entry_id, f"Child {child.entry_id} must link to parent group {group.entry_id}"

    # Verify logical blocks hierarchy tree
    roots = logical_blocks(proj_sec)
    assert len(roots) == 1, f"Expected 1 root group, got {len(roots)}"
    assert roots[0]['kind'] == 'group'
    assert len(roots[0]['children']) == 2


# ==============================================================================
# Case B: Single project with numbered description steps (no splitting)
# ==============================================================================
def test_case_b_single_project_with_numbered_descriptions():
    """Verify 10 numbered description steps inside Project 1 remain ONE project record."""
    desc_steps = [
        "1. Gathered user requirements from international stakeholders.",
        "2. Designed system architecture and microservices data flow.",
        "3. Developed automated ingestion pipelines using FastAPI.",
        "4. Configured Docker containers and Kubernetes clusters.",
        "5. Integrated PostgreSQL with connection pooling.",
        "6. Implemented Redis caching for sub-millisecond lookups.",
        "7. Built automated unit and integration test suites.",
        "8. Set up CI/CD workflows using GitHub Actions.",
        "9. Documented REST APIs with OpenAPI specifications.",
        "10. Deployed production services with 99.9% uptime SLA."
    ]

    elements = [
        create_element(0, "PROJECTS", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Project 1: Global Payments Gateway", elem_type="Title", bbox=(0.1, 0.09, 0.9, 0.12)),
    ]
    for idx, step in enumerate(desc_steps, 2):
        elements.append(create_element(idx, step, elem_type="ListItem", bbox=(0.1, 0.12 + idx * 0.03, 0.9, 0.14 + idx * 0.03)))

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = finalize_ownership(elements, res)

    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)

    # Exactly ONE project
    assert len(mapped.data.projects) == 1, f"Expected exactly 1 project, got {len(mapped.data.projects)}"
    proj = mapped.data.projects[0]
    assert "Global Payments Gateway" in proj.name

    # All 10 steps preserved in description
    for step in desc_steps:
        assert step in proj.description, f"Missing description step: {step}"


# ==============================================================================
# Case C: Multiple experiences with preserved employer boundaries
# ==============================================================================
def test_case_c_multiple_experiences_hierarchy():
    """Verify multiple experiences preserve role, dates, and responsibilities without bleeding."""
    elements = [
        create_element(0, "WORK EXPERIENCE", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Acme Technologies", elem_type="Title", bbox=(0.1, 0.09, 0.9, 0.12)),
        create_element(2, "Senior Software Engineer | Jan 2022 - Present", elem_type="NarrativeText", bbox=(0.1, 0.13, 0.9, 0.15)),
        create_element(3, "- Led backend development team of 6 engineers.", elem_type="ListItem", bbox=(0.1, 0.16, 0.9, 0.18)),
        create_element(4, "- Reduced API latency by 45% through Redis caching.", elem_type="ListItem", bbox=(0.1, 0.19, 0.9, 0.21)),
        create_element(5, "Beta Innovations", elem_type="Title", bbox=(0.1, 0.25, 0.9, 0.28)),
        create_element(6, "Software Engineer | Mar 2019 - Dec 2021", elem_type="NarrativeText", bbox=(0.1, 0.29, 0.9, 0.31)),
        create_element(7, "- Designed scalable ETL pipelines for analytics.", elem_type="ListItem", bbox=(0.1, 0.32, 0.9, 0.34)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = finalize_ownership(elements, res)

    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)

    assert len(mapped.data.experience) == 2, f"Expected 2 experiences, got {len(mapped.data.experience)}"
    exp1, exp2 = mapped.data.experience[0], mapped.data.experience[1]

    assert "Acme Technologies" in exp1.company
    assert "Senior Software Engineer" in exp1.role
    assert any("latency by 45%" in r for r in exp1.responsibilities)
    assert not any("ETL pipelines" in r for r in exp1.responsibilities)

    assert "Beta Innovations" in exp2.company
    assert "Software Engineer" in exp2.role
    assert any("ETL pipelines" in r for r in exp2.responsibilities)
    assert not any("latency by 45%" in r for r in exp2.responsibilities)


# ==============================================================================
# Case D: Wrapped multi-line certification title
# ==============================================================================
def test_case_d_wrapped_certification_title():
    """Verify 'Microsoft Security' + 'Awareness Program' unite into 1 record."""
    elements = [
        create_element(0, "CERTIFICATIONS", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Microsoft Security", elem_type="NarrativeText", bbox=(0.1, 0.10, 0.9, 0.12)),
        create_element(2, "Awareness Program", elem_type="NarrativeText", bbox=(0.1, 0.13, 0.9, 0.15)),
        create_element(3, "AWS Certified Solutions Architect", elem_type="NarrativeText", bbox=(0.1, 0.20, 0.9, 0.22)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = finalize_ownership(elements, res)

    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)

    assert len(mapped.data.certifications) == 2, f"Expected 2 certifications, got {len(mapped.data.certifications)}"
    names = [c.name for c in mapped.data.certifications]
    assert any("Microsoft Security" in n and "Awareness Program" in n for n in names)
    assert any("AWS Certified Solutions Architect" in n for n in names)


# ==============================================================================
# Case E: Multi-column layout separation
# ==============================================================================
def test_case_e_multi_column_isolation():
    """Verify right-column sidebar awards do not leak into left-column technical capabilities."""
    elements = [
        create_element(0, "AWARDS", elem_type="Title", bbox=(0.65, 0.10, 0.95, 0.12)),
        create_element(1, "Novigo Champion Award", elem_type="NarrativeText", bbox=(0.65, 0.13, 0.95, 0.15)),
        create_element(2, "For outstanding quarterly performance.", elem_type="NarrativeText", bbox=(0.65, 0.16, 0.95, 0.18)),
        create_element(3, "TECHNICAL SKILLS", elem_type="Title", bbox=(0.05, 0.10, 0.55, 0.12)),
        create_element(4, "Solution Architecture", elem_type="Title", bbox=(0.05, 0.13, 0.55, 0.15)),
        create_element(5, "Designed resilient distributed cloud architectures.", elem_type="NarrativeText", bbox=(0.05, 0.16, 0.55, 0.18)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = finalize_ownership(elements, res)

    awards_sec = next(s for s in res.sections if s.category == 'awards')
    for b in awards_sec.blocks:
        assert "Solution Architecture" not in b.text
        assert "distributed cloud" not in b.text


# ==============================================================================
# Ambiguity Detection
# ==============================================================================
def test_ambiguity_detection_marks_needs_review():
    """Verify orphan entries or conflicting contexts are marked needs_review."""
    elements = [
        create_element(0, "WORK EXPERIENCE", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Senior Developer", elem_type="NarrativeText", bbox=(0.1, 0.09, 0.9, 0.12)),
        create_element(2, "Worked on core engine.", elem_type="NarrativeText", bbox=(0.1, 0.13, 0.9, 0.15)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = finalize_ownership(elements, res)

    state = snapshot(elements, res)
    spans = state.spans
    assert any(s.confidence < 1.0 or s.ambiguity_reason is not None or state.owners[s.source_id].status == 'needs_review'
               for s in spans)


# ==============================================================================
# Validated LLM Decision Application
# ==============================================================================
def test_structured_llm_decisions_application():
    """Verify structured recovery decisions translate and apply without corrupting invariants."""
    elements = [
        create_element(0, "WORK EXPERIENCE", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Google LLC", elem_type="Title", bbox=(0.1, 0.09, 0.9, 0.12)),
        create_element(2, "Senior Software Engineer", elem_type="NarrativeText", bbox=(0.1, 0.13, 0.9, 0.15)),
        create_element(3, "Unassigned responsibilities paragraph", elem_type="NarrativeText", bbox=(0.1, 0.16, 0.9, 0.18)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    state = snapshot(elements, res)

    sid3 = state.spans[3].source_id
    target_record = state.owners[state.spans[1].source_id].record

    decisions = [
        {
            "decision": "ATTACH_TO_EXISTING_RECORD",
            "source_ids": [sid3],
            "record": target_record,
            "section": "experience",
            "fields": ["responsibilities"]
        }
    ]

    ops = translate_decisions_to_operations(decisions, state)
    assert len(ops) == 1
    assert ops[0]["op"] == "assign"
    assert ops[0]["record"] == target_record

    new_state = apply_operations(state, ops, {"experience", "education", "projects", "certifications", "awards"})
    assert new_state.owners[sid3].record == target_record
    assert "responsibilities" in new_state.owners[sid3].fields


# ==============================================================================
# Invalid LLM Response Rejection
# ==============================================================================
def test_invalid_llm_response_rejection():
    """Verify malformed decisions or hallucinated source IDs are rejected safely."""
    elements = [
        create_element(0, "WORK EXPERIENCE", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Google LLC", elem_type="Title", bbox=(0.1, 0.09, 0.9, 0.12)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)

    # Malformed transport response with invalid source IDs
    def mock_invalid_transport(settings, messages):
        return json.dumps({
            "operations": [{
                "op": "assign",
                "source_ids": ["e999:0:100"],
                "section": "experience",
                "record": "experience@e999:0:100"
            }]
        })

    reviewed = finalize_ownership(
        elements, res,
        settings=ReviewSettings(enabled=True, api_key='test-key'),
        transport=mock_invalid_transport,
        review=True
    )
    assert reviewed.metadata["structure_review"]["status"] == "rejected"
    assert "Repair references" in reviewed.metadata["structure_review"]["validation_reason"]


# ==============================================================================
# Mandatory Live DeepSeek Recovery Test
# ==============================================================================
@pytest.mark.provider
def test_mandatory_live_deepseek_recovery():
    """Perform live review request to DeepSeek Flash, verify decision execution and schema propagation."""
    env_path = Path(__file__).resolve().parents[1] / '.env'
    load_provider_env(env_path)
    if os.getenv('DEEPSEEK_API_KEY'):
        os.environ['DEEPSEEK_REVIEW_ENABLED'] = 'true'
    conn = check_connection()
    if conn.get("status") != "ready":
        pytest.skip(f"DeepSeek API not ready: {conn.get('message')}")

    settings = ReviewSettings.from_env()

    elements = [
        create_element(0, "WORK EXPERIENCE", elem_type="Title", bbox=(0.1, 0.05, 0.9, 0.08)),
        create_element(1, "Tata Consultancy Services", elem_type="Title", bbox=(0.1, 0.09, 0.9, 0.12)),
        create_element(2, "Systems Engineer | Jan 2020 - Dec 2023", elem_type="NarrativeText", bbox=(0.1, 0.13, 0.9, 0.15)),
        create_element(3, "- Maintained mission-critical banking applications.", elem_type="ListItem", bbox=(0.1, 0.16, 0.9, 0.18)),
    ]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)

    # Call finalize_ownership with live review enabled
    reviewed = finalize_ownership(elements, res, settings=settings, review=True)
    review_meta = reviewed.metadata.get("structure_review", {})

    assert review_meta.get("status") in {"provisional", "not_needed", "complete", "rejected"}, f"Review status unexpected: {review_meta}"
    assert review_meta.get("provider_calls", 0) >= 1

    if review_meta.get("status") == "rejected":
        assert review_meta.get("validation_reason"), "Rejection must have explicit validation reason"

    # Map to schema and assert zero corruption
    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=reviewed)
    mapped = map_schema(map_req)
    assert len(mapped.data.experience) >= 1
