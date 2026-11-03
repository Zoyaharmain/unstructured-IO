"""Tests for generalized multi-line headers, location parsing, and multi-column date alignment."""
import json
import pytest
from local_api.services.resume_sections import detect_sections
from local_api.services.schema_mapping import map_schema
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.mapping import mapping_input
from local_api.services.record_subfields import employment_header_fields, is_place


def test_employment_header_fields_company_location():
    # Piped Company | Location
    res1 = employment_header_fields("FIS Global Business Solutions | Chennai, India")
    assert res1.get("company") == "FIS Global Business Solutions"
    assert res1.get("location") == "Chennai, India"

    # Comma Company, Location
    res2 = employment_header_fields("BlackBox, Bangalore")
    assert res2.get("company") == "BlackBox"
    assert res2.get("location") == "Bangalore"

    res3 = employment_header_fields("Hewlett-Packard, Bangalore")
    assert res3.get("company") == "Hewlett-Packard"
    assert res3.get("location") == "Bangalore"


def test_benjamin_resume_schema_mapping_and_standardization():
    with open(".upstream/batch-validation/documents/bca3cd60195c524070c2.json") as f:
        doc = json.load(f)
    req = SectionRequest(elements=doc["extraction"]["elements"])
    sec = detect_sections(req)
    schema_req = SchemaMappingRequest(elements=doc["extraction"]["elements"], sections=sec)
    res = map_schema(schema_req)
    std_resume, metadata, status, warnings = standardize_resume_data(mapping_input(res))

    # All 7 real jobs must be recognized
    assert len(std_resume.experience) == 7
    # Calculated total experience must be ~26 years
    assert std_resume.total_experience_years is not None
    assert 25.0 <= std_resume.total_experience_years <= 27.0

    # First job: FIS Global Business Solutions
    j0 = std_resume.experience[0]
    assert "FIS Global Business Solutions" in j0.company
    assert j0.role == "Value Stream Lead / Senior Project Manager & Delivery Lead"
    assert j0.location == "Chennai, India"
    assert j0.start_date_iso == "2021-04"
    assert j0.duration_months == 63

    # D&B job: Company must not be corrupted into "Projects"
    j4 = std_resume.experience[4]
    assert "Dun & Bradstreet" in j4.company
    assert "Associate Manager" in j4.role
    assert j4.location == "Chennai, India"
    assert j4.start_date_iso == "2008-06"
    assert j4.duration_months == 61


def test_anita_das_resume_schema_mapping_and_standardization():
    with open(".upstream/batch-validation/documents/8b78a8031de85874736d.json") as f:
        doc = json.load(f)
    req = SectionRequest(elements=doc["extraction"]["elements"])
    sec = detect_sections(req)
    schema_req = SchemaMappingRequest(elements=doc["extraction"]["elements"], sections=sec)
    res = map_schema(schema_req)
    std_resume, metadata, status, warnings = standardize_resume_data(mapping_input(res))

    # All 6 jobs across 20 years must be recognized
    assert len(std_resume.experience) == 6
    assert std_resume.total_experience_years is not None
    assert 19.0 <= std_resume.total_experience_years <= 21.0

    companies = [j.company for j in std_resume.experience]
    assert "BlackBox" in companies
    assert "Hewlett-Packard" in companies
    assert "iOPEX Technologies" in companies
    assert "AT&T" in companies
    assert any("IBM" in c for c in companies)

    # Locations must be populated
    assert all(j.location == "Bangalore" for j in std_resume.experience)

    # Durations must be calculated
    assert all(j.duration_months is not None for j in std_resume.experience)

