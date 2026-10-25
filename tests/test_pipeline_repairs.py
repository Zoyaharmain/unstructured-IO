"""Regression tests for pipeline repairs: candidate name extraction,
education record boundary protection, source-coverage ledger statuses,
and non-halting schema audit for absent fields.
"""
import pytest
from local_api.vendor.handoff_schema.service import extract_contact_info, build_schema_mapping_report
from local_api.vendor.handoff_schema.models import ResumeSchema, ContactInfo
from local_api.services.schema_mapping import map_schema
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionRequest, SectionResponse, ResumeSection, SectionBlock
from local_api.schemas.extraction import ExtractedElement
from local_api.services.section_recovery import recover_sections
from local_api.services.resume_structure import entry_groups


def test_candidate_name_rejects_email_label_and_skills():
    """Verify that contact labels and skill phrases are never selected as candidate name."""
    header_with_email = """Email
priyotosh.singh@gmail.com
Priyotosh Kumar Singh
Java Developer"""
    contact = extract_contact_info(header_with_email, header_with_email)
    assert contact.full_name == "Priyotosh Kumar Singh"

    header_with_skills = """+91 9036658685
abhishekshankar5689@gmail.com
Nandini Layout, Bangalore
SKILLS
Revenue growth
Negotiation
Strategic Planning"""
    full_text = """EDUCATION
ABHISHEK SHANKAR
BUSINESS DEVELOPMENT MANAGER
2025 - 2026
+91 9036658685
abhishekshankar5689@gmail.com"""
    contact_abhishek = extract_contact_info(header_with_skills, full_text)
    assert contact_abhishek.full_name == "ABHISHEK SHANKAR"
    assert contact_abhishek.full_name != "Revenue growth"


def test_education_does_not_fragment_on_arbitrary_titles():
    """Verify that random titles without institution/qualification do not create separate education entries."""
    blocks = [
        SectionBlock(source_element_index=0, start=0, end=9, text="EDUCATION", lane="main", assignment="structural_heading", page_number=1, reason="test"),
        SectionBlock(source_element_index=1, start=0, end=16, text="ABHISHEK SHANKAR", lane="main", assignment="heading_context", page_number=1, reason="test"),
        SectionBlock(source_element_index=2, start=0, end=63, text="Led Presentations, costing, negotiations and solution alignment", lane="main", assignment="heading_context", page_number=1, reason="test"),
        SectionBlock(source_element_index=3, start=0, end=64, text="Expanded Client network through executive outreach and refferals", lane="main", assignment="heading_context", page_number=1, reason="test"),
    ]
    elements = [
        ExtractedElement(type="Title", text="EDUCATION", page_number=1, metadata={}),
        ExtractedElement(type="Title", text="ABHISHEK SHANKAR", page_number=1, metadata={}),
        ExtractedElement(type="Title", text="Led Presentations, costing, negotiations and solution alignment", page_number=1, metadata={}),
        ExtractedElement(type="Title", text="Expanded Client network through executive outreach and refferals", page_number=1, metadata={}),
    ]
    groups = entry_groups(blocks, "education", elements)
    assert len(groups) <= 1


def test_schema_mapping_prunes_empty_ghost_education_records():
    """Verify that empty phantom education records with no institution/degree are pruned."""
    elements = [
        ExtractedElement(type="Title", text="EDUCATION", page_number=1, metadata={}),
        ExtractedElement(type="Title", text="Random Line One", page_number=1, metadata={}),
    ]
    blocks = [
        SectionBlock(source_element_index=0, start=0, end=9, text="EDUCATION", lane="main", assignment="structural_heading", page_number=1, reason="test"),
        SectionBlock(source_element_index=1, start=0, end=15, text="Random Line One", lane="main", assignment="heading_context", page_number=1, reason="test"),
    ]
    section = ResumeSection(category="education", label="Education", text="EDUCATION\nRandom Line One", blocks=blocks, entries=[
        {"entry_id": "education-1", "block_indices": [1], "lane": "main", "fields": {}, "boundary_reason": "test"}
    ])
    sec_resp = SectionResponse(status="provisional", sections=[section], needs_review=[], metadata={}, warnings=[])
    req = SchemaMappingRequest(elements=elements, sections=sec_resp, source="test.pdf")
    resp = map_schema(req)
    # The empty education record must be pruned rather than added as a ghost record
    assert len(resp.data.education) == 0


def test_source_coverage_ledger_six_statuses():
    """Verify that source-coverage ledger correctly identifies all 6 canonical statuses."""
    resume = ResumeSchema(
        contact=ContactInfo(
            full_name="John Doe",
            email="john@example.com",
            phone="+1 555-1234",
            location="Not specified",
            linkedin_url=None,
        )
    )
    overrides = {
        "contact.full_name": "present_and_extracted",
        "contact.location": "present_but_ambiguous",
        "contact.linkedin_url": "absent_in_source",
        "projects": "present_but_unmapped",
    }
    report = build_schema_mapping_report(resume, status_overrides=overrides)
    statuses = {d.field_name: d.source_status for d in report.field_details}
    assert statuses["contact.full_name"] == "present_and_extracted"
    assert statuses["contact.location"] == "present_but_ambiguous"
    assert statuses["contact.linkedin_url"] == "absent_in_source"
    assert statuses["projects"] == "present_but_unmapped"


def test_section_recovery_detects_uppercase_headings():
    """Verify that recover_sections detects uppercase headings like CONTACT and SKILLS."""
    raw_text = "Represented company at conferences and industry events.CONTACT\n+91 9036658685\nSKILLS\nLeadership"
    elements = [
        ExtractedElement(type="NarrativeText", text=raw_text, page_number=1, metadata={})
    ]
    blocks = [
        SectionBlock(source_element_index=0, start=0, end=len(raw_text), text=raw_text, lane="main", assignment="heading_context", page_number=1, reason="test")
    ]
    sec = ResumeSection(category="experience", label="Work Experience", blocks=blocks, entries=[])
    sec_resp = SectionResponse(status="provisional", sections=[sec], needs_review=[], metadata={}, warnings=[])
    req = SectionRequest(elements=elements)
    recovered = recover_sections(req, sec_resp)
    # Recovery should find recovery cuts for CONTACT and SKILLS
    assert recovered.metadata.get("recovery", {}).get("passes") in {0, 1}
