"""Comprehensive regression tests for targeted architectural corrections.

Covers:
1. Current employment detection (10 scenarios)
2. Role / company / date tokenization and header parsing (5 scenarios)
3. Employer validation and heading protection (4 scenarios)
"""
import pytest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.dates import parse_date_string
from local_api.services.record_subfields import employment_header_fields
from local_api.services.resume_structure import heading_boundary
from local_api.services.resume_sections import ALIASES
def _make_resume_with_exp(exp_list):
    experiences = [
        {
            "company": e.get("company", "Acme Corp"),
            "role": e.get("role", "Software Engineer"),
            "start_date": e.get("start_date"),
            "end_date": e.get("end_date"),
            "duration": e.get("duration") or (f"{e.get('start_date')} – {e.get('end_date')}" if e.get("end_date") else None),
            "responsibilities": e.get("responsibilities", ["Developed software"])
        }
        for e in exp_list
    ]
    return {
        "contact": {"full_name": "Test Candidate", "email": "test@example.com", "phone": "1234567890"},
        "experience": experiences
    }


def test_current_employment_explicit_present():
    """1. Explicit Present marker confirms current employment and calculates duration."""
    resume = _make_resume_with_exp([{"start_date": "August 2024", "end_date": "Present"}])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp = std.experience[0]
    assert exp.is_current is True
    assert exp.start_date == "2024-08"
    assert exp.end_date is None
    assert exp.duration is not None
    assert "year" in exp.duration or "month" in exp.duration


def test_current_employment_explicit_current():
    """2. Explicit Current marker confirms current employment and calculates duration."""
    resume = _make_resume_with_exp([{"start_date": "August 2024", "end_date": "Current"}])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp = std.experience[0]
    assert exp.is_current is True
    assert exp.start_date == "2024-08"
    assert exp.end_date is None
    assert exp.duration is not None


def test_current_employment_since_prefix():
    """3. 'Since August 2024' confirms current employment and standardizes date."""
    resume = _make_resume_with_exp([{"start_date": "Since August 2024", "end_date": None}])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp = std.experience[0]
    assert exp.is_current is True
    assert exp.start_date == "2024-08"
    assert exp.end_date is None
    assert exp.duration is not None


def test_current_employment_from_prefix():
    """4. 'From August 2024' with open end confirms current employment."""
    resume = _make_resume_with_exp([{"start_date": "From August 2024", "end_date": None}])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp = std.experience[0]
    assert exp.is_current is True
    assert exp.start_date == "2024-08"
    assert exp.end_date is None
    assert exp.duration is not None


def test_first_listed_historical_job_missing_end_date():
    """5. First-listed job with no end date and NO marker must NOT assume current."""
    resume = _make_resume_with_exp([{"start_date": "August 2022", "end_date": None}])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp = std.experience[0]
    assert exp.is_current is False
    assert exp.end_date is None
    assert exp.duration is None
    # Must emit review warning
    assert any(w.warning_type == "unconfirmed_current_role" for w in warnings)


def test_latest_listed_job_missing_end_date_no_current_evidence():
    """6. Latest-listed job missing end date with no current evidence stays unconfirmed."""
    resume = _make_resume_with_exp([
        {"start_date": "2024-08", "end_date": None},
        {"start_date": "2021-04", "end_date": "2023-09"}
    ])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp0 = std.experience[0]
    assert exp0.is_current is False
    assert exp0.duration is None
    assert any(w.warning_type == "unconfirmed_current_role" for w in warnings)


def test_chronological_oldest_first_with_open_end():
    """7. Chronological oldest-first ordering where first entry has open date."""
    resume = _make_resume_with_exp([
        {"start_date": "2015-06", "end_date": None},
        {"start_date": "2019-01", "end_date": "2024-05"}
    ])
    std, meta, status, warnings = standardize_resume_data(resume)
    assert std.experience[0].is_current is False
    assert std.experience[0].duration is None


def test_reverse_chronological_unmarked_first_entry():
    """8. Reverse chronological list: index 0 cannot independently establish current status."""
    resume = _make_resume_with_exp([
        {"start_date": "2023-01", "end_date": None},
        {"start_date": "2020-01", "end_date": "2022-12"}
    ])
    std, meta, status, warnings = standardize_resume_data(resume)
    assert std.experience[0].is_current is False
    assert std.experience[0].duration is None


def test_multiple_jobs_missing_end_dates():
    """9. Multiple jobs missing end dates: neither is blindly assumed current."""
    resume = _make_resume_with_exp([
        {"start_date": "2023-01", "end_date": None},
        {"start_date": "2020-01", "end_date": None}
    ])
    std, meta, status, warnings = standardize_resume_data(resume)
    assert std.experience[0].is_current is False
    assert std.experience[1].is_current is False
    assert std.experience[0].duration is None
    assert std.experience[1].duration is None


def test_confirmed_current_job_with_valid_historical_job():
    """10. Confirmed current job (Present) alongside valid historical job."""
    resume = _make_resume_with_exp([
        {"start_date": "2021-10", "end_date": "Present"},
        {"start_date": "2018-05", "end_date": "2021-10"}
    ])
    std, meta, status, warnings = standardize_resume_data(resume)
    exp0 = std.experience[0]
    exp1 = std.experience[1]
    assert exp0.is_current is True
    assert exp0.end_date is None
    assert exp0.duration is not None
    assert exp1.is_current is False
    assert exp1.end_date == "2021-10"
    assert exp1.duration == "3 years 5 months"


# ==============================================================================
# 2. Header Parsing & Tokenization (5 scenarios)
# ==============================================================================

def test_header_role_at_company_with_date_range():
    """1. 'Role at Company (Date Range)' correctly splits role and company."""
    header = "Senior Consultant at Ernst & Young LLP (October 2021 – Present)"
    fields = employment_header_fields(header)
    assert fields.get("role") == "Senior Consultant"
    assert fields.get("company") == "Ernst & Young LLP"


def test_header_all_caps_joined_with_slash_date():
    """2. ALL CAPS header joined with date separated by slash."""
    header = "ASSOCIATE DATA ANALYST ATYATI TECHNOLOGIES PVT.LTD / 06/2018 - 08/2021"
    fields = employment_header_fields(header)
    assert fields.get("role") == "ASSOCIATE DATA ANALYST"
    assert fields.get("company") == "ATYATI TECHNOLOGIES PVT.LTD"


def test_header_date_above_employer_and_role():
    """3. Date range followed by Employer, Role."""
    header = "08/2024 - PRESENT ACCENTURE SOLUTIONS PVT.LTD | SENIOR ANALYST"
    fields = employment_header_fields(header)
    assert fields.get("role") == "SENIOR ANALYST"
    assert "ACCENTURE SOLUTIONS" in fields.get("company", "")


def test_header_company_with_location_and_role():
    """4. Employer, Location | Role format."""
    header = "Ernst & Young LLP, London | Senior Consultant"
    fields = employment_header_fields(header)
    assert fields.get("company") == "Ernst & Young LLP"
    assert fields.get("location") == "London"
    assert fields.get("role") == "Senior Consultant"


def test_header_client_name_in_employment():
    """5. Explicit Client notation separated from role/company."""
    header = "Cognizant | Client: PreStone Products | Power Apps Developer"
    fields = employment_header_fields(header)
    assert fields.get("client") == "PreStone Products"
    assert fields.get("role") == "Power Apps Developer"


# ==============================================================================
# 3. Employer Validation & Heading Protection (4 scenarios)
# ==============================================================================

def test_skills_heading_rejected_as_employer():
    """1. Technology Stack or skills headings are classified as skills, not employer."""
    boundary, cut = heading_boundary("TECHNOLOGY STACK", ALIASES)
    assert boundary == "skills"


def test_experience_history_heading_not_employer():
    """2. Section headings like EXPERIENCE HISTORY are classified as experience section, not company."""
    boundary, cut = heading_boundary("EXPERIENCE HISTORY", ALIASES)
    assert boundary == "experience"


def test_missing_employer_remains_unresolved():
    """3. Ambiguous generic labels do not produce invented employers."""
    fields = employment_header_fields("Development and Operations")
    assert "company" not in fields


def test_valid_unfamiliar_employer_extractable():
    """4. Valid unfamiliar employer with standard corporate suffix extracts cleanly."""
    header = "Senior Cloud Architect at Nexus Dynamic Global Solutions Ltd (Jan 2020 - Dec 2023)"
    fields = employment_header_fields(header)
    assert fields.get("role") == "Senior Cloud Architect"
    assert fields.get("company") == "Nexus Dynamic Global Solutions Ltd"
