"""Tests for end-to-end section ownership architecture, heading integrity, and logical block grouping."""
import json
import os
import re
import pytest

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionRequest, SectionBlock, SectionResponse
from local_api.services.resume_sections import detect_sections, build_sections
from local_api.services.section_recovery import recover_sections
from local_api.services.contact_sections import recover_contact_sections
from local_api.services.education_date_recovery import recover_education_dates
from local_api.services.source_ownership import finalize_ownership
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from test_block_completion import fixture


REAL_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'real_resumes', '_Aashish Golhani.extraction (1).json')
ASTHA_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'real_resumes', 'AsthaSaraogi.extraction.json')
ABDUL_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'real_resumes', 'Abdul Shukoor.extraction.json')


@pytest.mark.skipif(not os.path.exists(REAL_FIXTURE_PATH), reason='Real resume fixture not available')
def test_aashish_golhani_10_architectural_invariants():
    with open(REAL_FIXTURE_PATH) as f:
        raw_data = json.load(f)

    elements = [ExtractedElement(**e) for e in (raw_data if isinstance(raw_data, list) else raw_data['elements'])]
    req = SectionRequest(elements=elements)
    
    # Run full detection & recovery pipeline
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = recover_contact_sections(res, req.elements)
    res = recover_education_dates(res, req.elements)
    res = finalize_ownership(req.elements, res)

    # 1. Profile Snapshot contains only its actual summary, no leakage
    summary_sec = next((s for s in res.sections if s.category == 'summary'), None)
    assert summary_sec is not None, "Summary section must exist"
    summary_text = ' '.join(b.text.strip() for b in summary_sec.blocks if b.assignment not in {'section_heading', 'structural_heading'})
    assert summary_text.endswith("aligned with strategic business goals.")
    assert "Core Banking &" not in summary_text

    # 2 & 3. Core Banking & Domain Expertise is one complete heading, not split
    skills_sec = next((s for s in res.sections if s.category == 'skills'), None)
    assert skills_sec is not None, "Skills section must exist"
    cb_headings = [b for b in skills_sec.blocks if 'Core Banking' in b.text and b.assignment in {'structural_heading', 'section_heading'}]
    assert len(cb_headings) == 1
    assert cb_headings[0].text == "Core Banking & Domain Expertise"

    # 4. Banking-domain content remains under skills / domain heading
    cb_content = [b for b in skills_sec.blocks if 'Corporate Lending' in b.text or 'Retail Lending' in b.text]
    assert len(cb_content) > 0, "Domain expertise content must be under skills section"

    # 5. Left-column skills remain separate from right-column snapshot
    agile_skills = [b for b in skills_sec.blocks if 'Agile & Waterfall' in b.text]
    assert len(agile_skills) > 0

    # 6. Certifications section remains separate
    cert_sec = next((s for s in res.sections if s.category == 'certifications'), None)
    assert cert_sec is not None, "Certifications section must exist"
    assert cert_sec.source_heading == 'Certifications'

    # Map to schema
    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)

    # 7 & 8. Multi-line bullets and page-spanning lists: exactly 4 certification records
    certs = mapped.data.certifications
    assert len(certs) == 4, f"Expected exactly 4 certifications, got {len(certs)}"
    
    cert_names = [c.name for c in certs]
    # Cert 1: Business Analysis & Agile
    assert any("Business Analysis & Agile" in name and "PSM-I" in name for name in cert_names)
    # Cert 2: Program & Project Management (spanning page 1 to page 2)
    pmo_cert = next((name for name in cert_names if "Program & Project Management" in name), None)
    assert pmo_cert is not None
    assert "PMO Certification" in pmo_cert
    assert "Management Essentials," in pmo_cert
    assert "Technical Program Management" in pmo_cert, "Page-spanning continuation must be present in Cert 2"
    # Cert 3: Technology & Transformation
    assert any("Technology & Transformation" in name and "DevOps Foundation" in name for name in cert_names)
    # Cert 4: AI & Emerging Technologies
    assert any("AI & Emerging Technologies" in name and "IBM Artificial Intelligence" in name for name in cert_names)

    # 9. Schema summary agrees with section output
    assert mapped.data.summary == summary_text
    assert "Core Banking &" not in mapped.data.summary

    # 10. Conservation invariant: Zero original content lost
    total_assigned_blocks = sum(len(s.blocks) for s in res.sections) + len(res.needs_review)
    assert total_assigned_blocks > 0
    all_text_elements = sum(len(e.text) for e in elements)
    all_text_blocks = sum(len(b.text) for s in res.sections for b in s.blocks) + sum(len(b.text) for b in res.needs_review)
    assert all_text_elements == all_text_blocks


def test_compound_heading_ampersand_atomic():
    """Headings like 'Research & Development' must not be split at '&'."""
    texts = [
        "Profile",
        "Senior researcher with extensive experience in machine learning.",
        "Research & Development",
        "Published 10 papers in top conferences."
    ]
    elements, result = fixture(texts, {'summary': [0, 1], 'skills': [2, 3]}, [])
    recovered = recover_sections(SectionRequest(elements=elements), result)
    
    rd_blocks = [b for s in recovered.sections for b in s.blocks if 'Research & Development' in b.text]
    assert len(rd_blocks) == 1
    assert rd_blocks[0].text == "Research & Development"


def test_compound_heading_slash_atomic():
    """Headings with slash like 'Tools / Technologies' must remain atomic."""
    texts = [
        "Executive Summary",
        "Experienced engineer.",
        "Tools / Technologies",
        "Python, Docker, Kubernetes."
    ]
    elements, result = fixture(texts, {'summary': [0, 1], 'skills': [2, 3]}, [])
    recovered = recover_sections(SectionRequest(elements=elements), result)
    
    tt_blocks = [b for s in recovered.sections for b in s.blocks if 'Tools / Technologies' in b.text]
    assert len(tt_blocks) == 1
    assert tt_blocks[0].text == "Tools / Technologies"


def test_compound_heading_and_atomic():
    """Headings with 'and' like 'Strategy and Operations' must not be split."""
    texts = [
        "Overview",
        "Consultant leading transformation.",
        "Strategy and Operations",
        "Scaled revenue by 50%."
    ]
    elements, result = fixture(texts, {'summary': [0, 1], 'experience': [2, 3]}, [])
    recovered = recover_sections(SectionRequest(elements=elements), result)
    
    so_blocks = [b for s in recovered.sections for b in s.blocks if 'Strategy and Operations' in b.text]
    assert len(so_blocks) == 1
    assert so_blocks[0].text == "Strategy and Operations"


def test_ampersand_in_body_sentence_not_split():
    """An ampersand inside regular body prose must never trigger section truncation."""
    texts = [
        "Experience",
        "Google | 2020 - Present",
        "Lead engineer managing R&D and product delivery for AI features.",
        "Collaborated with UX & design teams to build cohesive tools."
    ]
    elements, result = fixture(texts, {'experience': [0, 1, 2, 3]}, [])
    recovered = recover_sections(SectionRequest(elements=elements), result)
    
    exp_sec = next(s for s in recovered.sections if s.category == 'experience')
    exp_text = ' '.join(b.text for b in exp_sec.blocks)
    assert "R&D and product delivery" in exp_text
    assert "UX & design teams" in exp_text


def test_two_column_adjacent_headings_remain_distinct():
    """Left column heading and right column heading must not be merged across lanes."""
    texts = [
        "Technical Skills",
        "Python, Go, Rust",
        "Work History",
        "Software Engineer at Acme Corp"
    ]
    elements, result = fixture(texts, {'skills': [0, 1], 'experience': [2, 3]}, [], lanes=['left', 'left', 'right', 'right'])
    recovered = recover_sections(SectionRequest(elements=elements), result)
    
    skills = next(s for s in recovered.sections if s.category == 'skills')
    exp = next(s for s in recovered.sections if s.category == 'experience')
    
    assert any('Technical Skills' in b.text for b in skills.blocks)
    assert any('Work History' in b.text for b in exp.blocks)
    assert not any('Work History' in b.text for b in skills.blocks)


def test_multiline_certification_grouping_and_schema():
    """Multi-line bullet groups in certifications must map with full name and evidence."""
    texts = [
        "Certifications",
        "Agile Coaching & Leadership: Scrum Master Certified, Agile Coach Professional,",
        "Enterprise Transformation Consultant"
    ]
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in texts]
    elements[2].page_number = 2  # Spans across page boundary
    
    def block(i):
        return SectionBlock(source_element_index=i, start=0, end=len(texts[i]), text=texts[i],
                            page_number=elements[i].page_number, lane='left', assignment='heading_context',
                            reason='cert block')
    elements[0].type = 'Title'
    
    b0 = SectionBlock(source_element_index=0, start=0, end=len(texts[0]), text=texts[0], page_number=1,
                      lane='left', assignment='structural_heading', reason='title')
    cert_sec = build_sections({'certifications': [b0, block(1), block(2)]}, elements)[0]
    res = SectionResponse(status='needs_review', sections=[cert_sec], needs_review=[], metadata={}, warnings=[])
    
    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)
    
    assert len(mapped.data.certifications) == 1
    c = mapped.data.certifications[0]
    assert "Agile Coaching & Leadership:" in c.name
    assert "Scrum Master Certified" in c.name
    assert "Enterprise Transformation Consultant" in c.name


def test_conservation_invariant_across_complex_elements():
    """Text conservation must be preserved contiguous and lossless."""
    texts = [
        "Profile Snapshot",
        "Senior Executive with 15+ years experience in Corporate & Wholesale Banking.",
        "Core Banking & Domain Expertise",
        "Core Banking, Payments, Lending, Trade Finance."
    ]
    elements, result = fixture(texts, {'summary': [0, 1], 'skills': [2, 3]}, [])
    recovered = recover_sections(SectionRequest(elements=elements), result)
    final = finalize_ownership(elements, recovered)
    
    all_blocks = [b for s in final.sections for b in s.blocks] + final.needs_review
    reconstructed = ''.join(b.text for b in sorted(all_blocks, key=lambda b: (b.source_element_index, b.start)))
    original = ''.join(texts)
    assert reconstructed == original


ASTHA_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'real_resumes', 'AsthaSaraogi.extraction.json')


@pytest.mark.skipif(not os.path.exists(ASTHA_FIXTURE_PATH), reason='Astha Saraogi fixture not available')
def test_astha_saraogi_education_ownership_and_date_attribution():
    """Verify education dates attach to education institution and not experience."""
    with open(ASTHA_FIXTURE_PATH) as f:
        raw_data = json.load(f)
    elements = [ExtractedElement(**e) for e in (raw_data if isinstance(raw_data, list) else raw_data['elements'])]
    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = recover_contact_sections(res, req.elements)
    res = recover_education_dates(res, req.elements)
    res = finalize_ownership(req.elements, res)

    # 1. Experience must not have 2010 - 2014 education dates
    exp_sec = next(s for s in res.sections if s.category == 'experience')
    assert exp_sec is not None
    for b in exp_sec.blocks:
        assert '2010 – 2014' not in b.text
        assert 'Bhopal (M.P)' not in b.text

    # 2. Education section must contain recovered dates and institution
    edu_sec = next(s for s in res.sections if s.category == 'education')
    assert edu_sec is not None
    edu_texts = [b.text for b in edu_sec.blocks]
    assert any('2010 – 2014' in t for t in edu_texts)
    assert any('Rajiv Gandhi Proudyogiki Vishwavidyalaya' in t for t in edu_texts)

    # 3. Schema mapping produces valid Education record
    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)
    assert len(mapped.data.education) == 1, f"Expected 1 education record, got {len(mapped.data.education)}"
    edu = mapped.data.education[0]
    assert edu.institution == "Rajiv Gandhi Proudyogiki Vishwavidyalaya"
    assert edu.start_year == "2010"
    assert edu.graduation_year == "2014"


@pytest.mark.skipif(not os.path.exists(ASTHA_FIXTURE_PATH), reason='Astha Saraogi fixture not available')
def test_astha_saraogi_awards_segmentation_and_deduplication():
    """Verify awards are segmented into 3 distinct items and deduplicated."""
    with open(ASTHA_FIXTURE_PATH) as f:
        raw_data = json.load(f)
    elements = [ExtractedElement(**e) for e in (raw_data if isinstance(raw_data, list) else raw_data['elements'])]
    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = recover_contact_sections(res, req.elements)
    res = recover_education_dates(res, req.elements)
    res = finalize_ownership(req.elements, res)

    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)

    awards_sec = next((s for s in mapped.section_schemas if s.category == 'awards'), None)
    assert awards_sec is not None, "Awards subschema must exist"
    assert len(awards_sec.records) == 3, f"Expected exactly 3 awards, got {len(awards_sec.records)}"

    names = [next((it.value for a in r.attributes if a.name == 'name' for it in a.items), '') for r in awards_sec.records]
    descs = [next((it.value for a in r.attributes if a.name == 'description' for it in a.items), '') for r in awards_sec.records]

    # Award 1: Customer Champion
    assert any("Customer Champion" in n for n in names)
    # Award 2: Quarterly spot Award
    q_idx = next(i for i, n in enumerate(names) if "Quarterly spot Award" in n)
    assert "For top 5 performers." in descs[q_idx]
    assert "Customer Satisfaction" not in descs[q_idx], "Award 2 must not merge Award 3 description"
    # Award 3: 100% rate of Customer Satisfaction
    cs_idx = next(i for i, n in enumerate(names) if "100% rate" in n)
    assert "Received a 100% rate of Customer Satisfaction." in descs[cs_idx]


@pytest.mark.skipif(not os.path.exists(ASTHA_FIXTURE_PATH), reason='Astha Saraogi fixture not available')
def test_astha_saraogi_experience_deduplication():
    """Verify duplicate experience entries are cleanly unified to 4 distinct employers."""
    with open(ASTHA_FIXTURE_PATH) as f:
        raw_data = json.load(f)
    elements = [ExtractedElement(**e) for e in (raw_data if isinstance(raw_data, list) else raw_data['elements'])]
    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = recover_contact_sections(res, req.elements)
    res = recover_education_dates(res, req.elements)
    res = finalize_ownership(req.elements, res)

    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)

    # 4 distinct employers: Mastercard, Deutsche Bank, Allstate, Cognizant
    assert len(mapped.data.experience) == 4, f"Expected 4 experience records, got {len(mapped.data.experience)}"
    companies = [e.company for e in mapped.data.experience]
    assert any("Mastercard" in c for c in companies)
    assert any("Duestche Bank" in c or "Deutsche Bank" in c for c in companies)
    assert any("Allstate" in c for c in companies)
    assert any("Cognizant" in c for c in companies)

    # Invariant: Conservation of text and evidence
    total_assigned_blocks = sum(len(s.blocks) for s in res.sections) + len(res.needs_review)
    assert total_assigned_blocks > 0
    all_text_elements = sum(len(e.text) for e in elements)
    all_text_blocks = sum(len(b.text) for s in res.sections for b in s.blocks) + sum(len(b.text) for b in res.needs_review)
    assert all_text_elements == all_text_blocks


@pytest.mark.skipif(not os.path.exists(ABDUL_FIXTURE_PATH), reason='Abdul Shukoor fixture not available')
def test_abdul_shukoor_invariants():
    """Verify Abdul Shukoor certifications (2), awards (1), and numbered projects (10 under Param Info)."""
    from local_api.services.standardization.mapping import mapping_input

    with open(ABDUL_FIXTURE_PATH) as f:
        raw_data = json.load(f)
    elements = [ExtractedElement(**e) for e in (raw_data if isinstance(raw_data, list) else raw_data['elements'])]
    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    res = recover_sections(req, res)
    res = recover_contact_sections(res, req.elements)
    res = recover_education_dates(res, req.elements)
    res = finalize_ownership(req.elements, res)

    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=res)
    mapped = map_schema(map_req)
    inp = mapping_input(mapped)

    # 1. Certifications: exactly 2 visible certifications
    certs = mapped.data.certifications
    assert len(certs) == 2, f"Expected exactly 2 certifications, got {len(certs)}"
    assert certs[0].name == "Office Master in Power BI Advance"
    assert certs[1].name == "Microsoft Security Awareness Program"

    # 2. Awards: exactly 1 award (Novigo Champion award) in right sidebar
    # No leakage of main-column capability headings
    awards = inp.get("awards", [])
    assert len(awards) == 1, f"Expected exactly 1 award, got {len(awards)}"
    assert awards[0]["name"] == "Novigo Champion award"

    forbidden_capability = [
        "Solution Architecture",
        "Technical Leadership",
        "Governance & Compliance",
        "Data Modelling & Integration",
        "Stakeholder Collaboration",
        "Application Lifecycle Management (ALM)",
    ]
    awards_sec = next(s for s in res.sections if s.category == "awards")
    for b in awards_sec.blocks:
        for f in forbidden_capability:
            assert f.lower() not in b.text.lower(), f"Capability block '{f}' leaked into awards"

    # 3. Projects: Param Info contains 10 numbered projects
    projects = mapped.data.projects
    assert len(projects) >= 10, f"Expected at least 10 projects, got {len(projects)}"
    param_info_projects = projects[:10]
    expected_titles = [
        "Government Relations Kiosk Automation",
        "MOBARO Results Data Processing Automation",
        "Risk Assessment Framework",
        "Arabic Contract Automation Solution",
        "IT Loan Devices Tracking System",
        "Email-Driven Data Extraction & Excel Automation",
        "Machine Availability & RPA Alerting Framework",
        "Access Governance & Environment Management",
        "Copilot",
        "Created Power pages",
    ]
    for i, exp_title in enumerate(expected_titles):
        p = param_info_projects[i]
        assert p.name and exp_title.lower() in p.name.lower(), f"Project {i+1} title mismatch: {p.name!r} vs {exp_title!r}"

    # Verify element 93 semantic split: Project 8 has description, Project 9 has title
    assert param_info_projects[7].description and "Documented for Production environment access requests" in param_info_projects[7].description
    assert param_info_projects[8].name and "Copilot" in param_info_projects[8].name

    # 4. Other project groups retained under Epiroc
    epiroc_projects = [p for p in projects if "epiroc" in (p.name or "").lower() or "epiroc" in (p.description or "").lower()]
    assert len(epiroc_projects) >= 1, "Epiroc client projects must be retained"

    # 5. Work Experience: all 4 employers present
    companies = [e.company for e in mapped.data.experience]
    assert any("PARAM Info" in c for c in companies)
    assert any("Trigent Software" in c for c in companies)
    assert any("Novigo Solution" in c for c in companies)
    assert any("Percoyo" in c for c in companies)

    # 6. Conservation of text and evidence
    all_text_elements = sum(len(e.text) for e in elements)
    all_text_blocks = sum(len(b.text) for s in res.sections for b in s.blocks) + sum(len(b.text) for b in res.needs_review)
    assert all_text_elements == all_text_blocks
