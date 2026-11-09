"""Deterministic regressions for the 5 repaired resumes from the Next-10 DeepSeek test cohort.

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


BASE_DIR = Path("reports/live-next-10-schema-mapping-20261106")


def replay_next10(folder: str):
    target = BASE_DIR / folder
    ext_data = json.load(open(target / "extraction.json"))
    sec_data = json.load(open(target / "sections.json"))
    elements = [ExtractedElement.model_validate(e) for e in ext_data["elements"]]
    sections = SectionResponse.model_validate(sec_data)
    sections.sections = build_sections({s.category: s.blocks for s in sections.sections}, elements)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=folder))
    std, meta, status, warns = standardize_resume_data(mapped.data.model_dump())
    return mapped, std, meta, status, warns


def test_02_aarunis_name_title_and_curly_quote_dates():
    mapped, std, meta, status, warns = replay_next10("02")
    # Candidate name separated from professional title
    assert std.contact.full_name == "Aaruni Shrivastava"
    assert "ANALYST" in mapped.data.professional_title

    # Dates with curly quote normalized (Feb ‘23 -> 2023-02)
    companies = [j.company for j in std.experience]
    assert "BlackRock" in companies
    blackrock = next(j for j in std.experience if j.company == "BlackRock")
    assert blackrock.start_date == "2023-02"

    # Total experience calculated with valid dates
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 4.0


def test_05_ajay_kumar_tiwari_multiline_job_merging():
    mapped, std, meta, status, warns = replay_next10("05")
    assert "Ajay Kumar Tiwari" in std.contact.full_name

    companies = [j.company for j in std.experience]
    assert "Expleo Solutions Limited" in companies
    assert "Shell India Markets Private Limited" in companies
    assert "Capgemini India Private Limited" in companies
    assert "Unisys Global Services Limited" in companies
    assert "ABB Global Services Limited" in companies

    expleo = next(j for j in std.experience if j.company == "Expleo Solutions Limited")
    assert "Solution Architect" in expleo.role
    assert expleo.start_date == "2023-07"

    shell = next(j for j in std.experience if j.company == "Shell India Markets Private Limited")
    assert "Solution Architect" in shell.role
    assert shell.start_date == "2015-11"

    cap = next(j for j in std.experience if j.company == "Capgemini India Private Limited")
    assert "Consultant" in cap.role
    assert cap.start_date == "2012-01"

    unisys = next(j for j in std.experience if j.company == "Unisys Global Services Limited")
    assert "Senior Software Engineer" in unisys.role
    assert unisys.start_date == "2008-10"

    abb = next(j for j in std.experience if j.company == "ABB Global Services Limited")
    assert "Developer" in abb.role
    assert abb.start_date == "2005-12"


def test_06_akanksha_bhand_earlier_experience_and_certifications():
    mapped, std, meta, status, warns = replay_next10("06")
    assert "Akanksha Bhand" in std.contact.full_name

    companies = [j.company for j in std.experience]
    # Earlier experience recovered: Capgemini, HPE, TCS
    assert "Bank of New York Mellon" in companies
    assert "Nihilent Technologies" in companies
    assert "Capgemini India" in companies
    assert "Hewlett Packard Enterprise" in companies
    assert "Tata Consultancy Services" in companies

    # Certifications separated into individual entries, not merged into 1 continuous string
    cert_names = [c.name for c in std.certifications]
    assert len(cert_names) == 8
    assert "Bank Credit" in cert_names
    assert "Certified Scrum Master" in cert_names
    assert "SAFe Agile" in cert_names
    assert "Foundation Certificate in Banking" in cert_names
    assert "Capital Markets" in cert_names
    assert "Consumer Lending" in cert_names
    assert "Canadian Banking" in cert_names
    assert "IBM DB2 Fundamentals" in cert_names


def test_07_akash_kumar_dates_and_education_institutions():
    mapped, std, meta, status, warns = replay_next10("07")
    assert "Akash Kumar" in std.contact.full_name

    # Dates positioned below headers recovered
    exp_by_company = {j.company: j for j in std.experience}
    assert "Gokwik Commerce Solutions" in exp_by_company
    assert exp_by_company["Gokwik Commerce Solutions"].start_date == "2024-03"

    assert "R Systems" in exp_by_company
    assert exp_by_company["R Systems"].start_date == "2022-07"

    assert "US Tech Solutions" in exp_by_company
    assert exp_by_company["US Tech Solutions"].start_date == "2021-04"

    assert "SilverEdge Technologies Pvt. Ltd." in exp_by_company
    assert exp_by_company["SilverEdge Technologies Pvt. Ltd."].start_date == "2019-09"

    # Education institution preserved for B.Tech / B.E.
    btech = next((e for e in std.education if "B.Tech" in e.degree or "B.E" in e.degree), None)
    assert btech is not None
    assert btech.institution == "Eshan College of Management"

    # Total experience calculated
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 6.0


def test_09_akshay_singla_betterplace_recovery_and_chicmic():
    mapped, std, meta, status, warns = replay_next10("09")
    assert "Akshay Singla" in std.contact.full_name

    companies = [j.company for j in std.experience]
    # Both Betterplace positions recovered
    betterplace_jobs = [j for j in std.experience if j.company == "Betterplace"]
    assert len(betterplace_jobs) == 2
    bp_roles = {j.role for j in betterplace_jobs}
    assert "SDE 3" in bp_roles
    assert "SDE 2" in bp_roles

    # ChicMic identified as company
    assert "ChicMic" in companies

    # Total experience calculated
    assert std.total_experience_years is not None
    assert std.total_experience_years >= 7.0

