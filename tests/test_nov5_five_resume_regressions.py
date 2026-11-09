"""Deterministic regressions for the 5 November resumes.

Offline only: zero LLM or network calls.
"""
import json
from pathlib import Path
import pytest

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.standardization.service import standardize_resume_data


BASE_DIR = Path("reports/live-five-new-resumes-20261105")


def replay_nov5(folder: str):
    target = BASE_DIR / folder
    ext_data = json.load(open(target / "extraction.json"))
    sec_data = json.load(open(target / "sections.json"))
    elements = [ExtractedElement.model_validate(e) for e in ext_data["elements"]]
    sections = SectionResponse.model_validate(sec_data)
    sections.sections = build_sections({s.category: s.blocks for s in sections.sections}, elements)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=folder))
    std, meta, status, warns = standardize_resume_data(mapped.data.model_dump())
    return mapped, std, meta, status, warns


def test_01_a_lokhande_employers_and_clean_responsibilities():
    mapped, std, meta, status, warns = replay_nov5("01")
    assert "Lokhande" in std.contact.full_name
    
    companies = [j.company for j in std.experience]
    roles = [j.role for j in std.experience]
    
    # Capgemini and Cognizant identified, not swallowed by responsibilities
    assert "Capgemini" in companies
    assert any("Cognizant" in c for c in companies)
    assert any("Aurus" in c for c in companies)
    
    # Responsibilities must not become company names
    for comp in companies:
        assert "AWS" not in comp
        assert "EC2" not in comp
        assert "services" != comp.lower()

    assert any("Senior Java Consultant" in r for r in roles)
    assert any("Java Developer" in r for r in roles)
    assert std.total_experience_years is not None
    assert std.total_experience_years > 5.0


def test_02_a_madhavi_certifications_and_employers():
    mapped, std, meta, status, warns = replay_nov5("02")
    assert "MADHAVI" in std.contact.full_name.upper()
    
    # CSPO certification name separated from year 2025
    cspo = next(c for c in std.certifications if "CSPO" in c.name)
    assert "2025" not in cspo.name
    assert cspo.issue_year == "2025" or cspo.issue_date == "2025" or cspo.issue_year_iso == "2025"
    
    # Issuers clean
    assert any("Vector India" in (c.issuer or "") for c in std.certifications)
    assert any("MVLCO" in (c.issuer or "") for c in std.certifications)
    
    # Total experience calculated
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 8.0


def test_03_ajay_kumar_chaudhar_clean_roles_clients_dates():
    mapped, std, meta, status, warns = replay_nov5("03")
    assert "AJAY KUMAR" in std.contact.full_name
    
    roles = [j.role for j in std.experience]
    companies = [j.company for j in std.experience]

    # Virtusa role is Product Owner, free from duty descriptions
    assert "Product Owner" in roles
    for r in roles:
        assert "Coordinate" not in r
        assert "Delivered" not in r
        assert "✓" not in r
    
    # Responsibilities/prose fragments must not be company names
    for c in companies:
        assert "stakeholders" not in c.lower()
        assert "product" not in c.lower()
        assert not c.lower().startswith("with ")

    # Virtusa is employer for CITI Bank and HSBC engagements
    virtusa_jobs = [j for j in std.experience if "Virtusa" in j.company]
    assert len(virtusa_jobs) == 2
    assert any("Product Owner" in j.role for j in virtusa_jobs)
    assert any("Agile Business Analyst" in j.role for j in virtusa_jobs)

    # CMS IT Service and Destar Infotech recovered
    assert any("CMS IT Service" in c for c in companies)
    destar = next(j for j in std.experience if "Destar" in j.company)
    assert destar.role == "Business Analyst"
    assert destar.start_date == "2018-04" and destar.end_date == "2018-07"
    
    # Pinga role is Functional Consultant
    assert "Functional Consultant" in roles
    
    # Education institution has leading 'from ' stripped
    institutions = [e.institution for e in std.education]
    assert any("Uttar Pradesh Technical University" in inst for inst in institutions)
    for inst in institutions:
        assert not inst.lower().startswith("from ")

    # All employment records dated and total experience calculated
    dated_jobs = [j for j in std.experience if j.start_date]
    assert len(dated_jobs) == 7
    pinga = next(j for j in std.experience if "Pinga" in j.company)
    assert pinga.start_date == "2010-12" and pinga.end_date == "2013-05"
    assert std.total_experience_years is not None
    assert 13.0 <= std.total_experience_years <= 15.0


def test_04_amit_rana_six_employment_records_and_education():
    mapped, std, meta, status, warns = replay_nov5("04")
    assert "AMIT RANA" in std.contact.full_name.upper()

    # Certifications free of leading ❖ glyphs
    assert len(std.certifications) > 0
    for cert in std.certifications:
        assert not cert.name.startswith("❖")
        assert not cert.name.startswith("•")
    
    # 6 distinct employment records
    assert len(std.experience) == 6
    companies = [j.company for j in std.experience]
    assert any("Mercor" in c for c in companies)
    assert any("TMO" in c or "T-Mobile" in c for c in companies)
    assert any("AT&T" in c for c in companies)
    assert any("Sungard" in c for c in companies)
    assert any("Telefonica" in c for c in companies)
    assert any("Datamatics" in c for c in companies)

    # AT&T role is Scrum Master
    att_job = next(j for j in std.experience if "AT&T" in j.company)
    assert "Scrum Master" in att_job.role

    # Redmond, WA not confused as company
    for c in companies:
        assert "Redmond" not in c
        assert "WA" not in c

    # Education institution is Bhagalpur College of Engineering (not truncated to College of Engineering)
    edu = next(e for e in std.education if "Bhagalpur" in e.institution)
    assert edu.institution == "Bhagalpur College of Engineering"
    assert "Bachelor" in edu.degree
    assert "Mechanical" in (edu.field_of_study or "")
    assert edu.graduation_year_iso == "2001" or edu.graduation_year == "2001"

    # Total experience
    assert std.total_experience_years is not None
    assert 17.0 <= std.total_experience_years <= 19.0


def test_05_anandkumar_candidate_name_not_father_and_full_recovery():
    mapped, std, meta, status, warns = replay_nov5("05")
    
    # Candidate name is ANAND KUMAR, not father "Late Rameshwar Shah"
    assert "ANAND" in std.contact.full_name.upper()
    assert "RAMESHWAR" not in std.contact.full_name.upper()
    
    # Location is Bangalore, not candidate name "Anand Kumar,"
    assert std.contact.location is not None
    assert "Bangalore" in std.contact.location
    assert "Anand" not in std.contact.location

    # "CURRICULUM VITAE" is not a certification
    assert len(std.certifications) == 0

    # 4 dated employment records
    assert len(std.experience) == 4
    for j in std.experience:
        assert j.start_date_iso is not None or j.start_date is not None
        assert j.end_date_iso is not None or j.end_date is not None or j.is_current

    # 4 education records recovered (M.Tech, B.Tech, HSC, SSC)
    assert len(std.education) == 4
    degrees = [e.degree for e in std.education]
    assert any("M.Tech" in d for d in degrees)
    assert any("B.Tech" in d for d in degrees)
    assert any("HSC" in d or "Intermediate" in d or "12th" in d for d in degrees)
    assert any("SSC" in d or "Matric" in d or "10th" in d for d in degrees)

    # Total experience calculated (10.8 years)
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 10.0
