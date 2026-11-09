"""Deterministic regressions for the 5 resumes from the November 8 DeepSeek test cohort.

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


BASE_DIR = Path("reports/live-five-new-resumes-20261108")


def replay_nov8(folder: str):
    target = BASE_DIR / folder
    ext_data = json.load(open(target / "extraction.json"))
    sec_data = json.load(open(target / "sections.json"))
    elements = [ExtractedElement.model_validate(e) for e in ext_data["elements"]]
    sections = SectionResponse.model_validate(sec_data)
    sections.sections = build_sections({s.category: s.blocks for s in sections.sections}, elements)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=folder))
    std, meta, status, warns = standardize_resume_data(mapped.data.model_dump())
    return mapped, std, meta, status, warns


def test_01_bahubalikhot_regression():
    mapped, std, meta, status, warns = replay_nov8("01_Bahubalikhot")
    assert std.contact.full_name == "Bahubali Subhash Khot"
    assert std.contact.email == "khotbahubali07@gmail.com"

    companies = [j.company for j in std.experience]
    assert "Infosys BPM Ltd." in companies
    assert "State Street Services Pvt. Ltd." in companies

    assert std.total_experience_years is not None
    assert std.total_experience_years >= 4.0


def test_02_barsita_priyadarshini_nanda_regression():
    mapped, std, meta, status, warns = replay_nov8("02_BarsitaPriyadarshiniNanda")
    assert std.contact.full_name == "Barsita Priyadarshini Nanda"
    assert "Workday" in mapped.data.professional_title

    companies = [j.company for j in std.experience]
    assert "Carelon Global Solutions" in companies
    assert "SGB Brandsafway" in companies
    assert "Deloitte" in companies

    assert std.total_experience_years is not None
    assert std.total_experience_years >= 4.0


def test_03_bharat_duhan_regression():
    mapped, std, meta, status, warns = replay_nov8("03_BharatDuhan")
    assert std.contact.full_name == "BHARAT DUHAN"

    companies = [j.company for j in std.experience]
    assert "Oracle Cloud Infrastructure (OCI)" in companies
    assert "Juniper Networks" in companies
    assert "Capgemini (Cisco TAC)" in companies

    assert std.total_experience_years is not None
    assert std.total_experience_years >= 4.0


def test_04_bharatkumar_machhi_name_clean_all_employers_and_experience():
    mapped, std, meta, status, warns = replay_nov8("04_BharatkumarMachhi")
    # Clean candidate name without parenthesized title contamination
    assert std.contact.full_name == "Bharatkumar Machhi"
    assert "Cyber Security Project Manager" in (mapped.data.professional_title or "")

    companies = [j.company for j in std.experience]
    assert "Grant Thornton Bharat LLP" in companies
    assert "Samona Limited" in companies
    assert "Fortuna Identity Pvt. Ltd" in companies
    assert "Glorywebs Creative Pvt. Ltd." in companies
    assert "Global IT Solutions– Bharuch" in companies
    assert "Trio Hat Intelligence, Bharuch, Gujarat" in companies

    # Check that Fortuna has valid dates
    fortuna = next(j for j in std.experience if "Fortuna Identity" in j.company)
    assert fortuna.start_date == "2022-03"
    assert fortuna.end_date == "2024-05"

    # Check Glorywebs
    glory = next(j for j in std.experience if "Glorywebs" in j.company)
    assert glory.start_date == "2019-04"
    assert glory.end_date == "2022-02"

    # Total experience calculated across all positions
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 10.0


def test_05_bhavyashree_ry_narrative_employment_responsibilities_education_cert():
    mapped, std, meta, status, warns = replay_nov8("05_BhavyashreeRY")
    assert "Bhavyashree" in std.contact.full_name

    # Narrative employment line parsed
    assert len(std.experience) >= 1
    job = std.experience[0]
    assert job.company == "Inventus Info Consulting (INFOSYS)"
    assert job.role == "ServiceNow Developer"
    assert job.location == "Bangalore"
    assert job.start_date == "2022-04"
    assert job.is_current is True

    # Associated responsibilities from HYGO and NEXTEC project sections
    assert len(job.responsibilities) >= 15

    # Education: degree separate from institution
    assert len(std.education) >= 1
    edu = std.education[0]
    assert "Bachelor of Science" in edu.degree
    assert "Kalpataru First grade college" in edu.institution
    assert "Bachelor of Science" not in edu.institution

    # Certification: intact CAD and CSA without line-split truncation
    cert_names = [c.name for c in std.certifications]
    assert len(cert_names) >= 1
    assert any("CSA" in c and "CAD" in c for c in cert_names)
    assert not any(c.strip().startswith("Developer)") for c in cert_names)

    # Total experience calculated
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 4.0

