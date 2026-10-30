"""Unit and integration tests for the Safe JSON Standardization and Validation Layer."""
import pytest
from datetime import datetime, timezone
from local_api.services.standardization.dates import (
    parse_date_string,
    calculate_non_overlapping_experience,
)
from local_api.services.standardization.skills import (
    canonicalize_skill_name,
    standardize_skills_categorized,
)
from local_api.services.standardization.contacts import (
    normalize_phone,
    normalize_email,
    normalize_url,
    standardize_contact,
)
from local_api.services.standardization.spelling import correct_ocr_or_spelling
from local_api.services.standardization.service import standardize_resume_data
from local_api.vendor.handoff_schema.models import CategorizedSkills, ContactInfo


def test_contact_phone_e164_normalization():
    # Phone with explicit country code and punctuation
    norm, e164, warns = normalize_phone("+91-9494916311")
    assert norm == "+919494916311"
    assert e164 == "+919494916311"
    assert len(warns) == 1
    assert warns[0].warning_type == "phone_e164_normalized"

    # Phone with '00' international prefix
    norm_00, e164_00, warns_00 = normalize_phone("00919494916311")
    assert norm_00 == "+919494916311"
    assert e164_00 == "+919494916311"

    # Domestic phone without country code - must NOT invent a country code
    norm_dom, e164_dom, warns_dom = normalize_phone("9494916311")
    assert norm_dom == "9494916311"
    assert e164_dom is None
    assert any(w.warning_type == "phone_lacks_country_code" for w in warns_dom)


def test_contact_email_and_urls():
    # Whitespace trimmed
    norm_em, warns_em = normalize_email("  candidate@example.com  ")
    assert norm_em == "candidate@example.com"
    assert any(w.warning_type == "email_whitespace_trimmed" for w in warns_em)

    # Invalid email syntax flagged but preserved
    bad_em, bad_warns = normalize_email("not-an-email")
    assert bad_em == "not-an-email"
    assert any(w.warning_type == "invalid_email_syntax" for w in bad_warns)

    # LinkedIn URL scheme added
    li_url, li_warns = normalize_url("linkedin.com/in/john-doe", "linkedin_url")
    assert li_url == "https://linkedin.com/in/john-doe"
    assert any(w.warning_type == "url_scheme_canonicalized" for w in li_warns)

    # Bare profile label rejected
    bare_li, bare_warns = normalize_url("LinkedIn", "linkedin_url")
    assert bare_li is None
    assert any(w.warning_type == "bare_profile_label_rejected" for w in bare_warns)


def test_date_parsing_and_precision():
    # Month + Year
    iso, prec, curr, warns = parse_date_string("Aug 2022")
    assert iso == "2022-08"
    assert prec == "month_year"
    assert curr is False

    # Year only
    iso_y, prec_y, curr_y, warns_y = parse_date_string("2015")
    assert iso_y == "2015"
    assert prec_y == "year"
    assert curr_y is False

    # Present / Current
    iso_p, prec_p, curr_p, warns_p = parse_date_string("Present")
    assert iso_p is None
    assert curr_p is True

    # Ambiguous numeric date
    iso_amb, prec_amb, curr_amb, warns_amb = parse_date_string("05/06/2022")
    assert iso_amb is None
    assert any(w.warning_type == "ambiguous_numeric_date" for w in warns_amb)


def test_non_overlapping_experience_calculation():
    # Two overlapping positions:
    # Job A: 2020-01 to 2021-06 (18 months)
    # Job B: 2021-01 to 2021-12 (12 months, overlaps Job A by 6 months)
    # Merged span: 2020-01 to 2021-12 = 24 months = 2.0 years
    records = [
        {"start_date_iso": "2020-01", "end_date_iso": "2021-06", "start_date_precision": "month_year", "end_date_precision": "month_year", "is_current": False},
        {"start_date_iso": "2021-01", "end_date_iso": "2021-12", "start_date_precision": "month_year", "end_date_precision": "month_year", "is_current": False},
    ]
    ref_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    total_years, overlap_detected, warns = calculate_non_overlapping_experience(records, reference_date=ref_dt)
    assert overlap_detected is True
    assert total_years == 2.0
    assert any(w.warning_type == "experience_overlap_resolved" for w in warns)


def test_skills_canonicalization():
    raw_skills = CategorizedSkills(
        technical_skills=["Postgres", "Redis", "Kafka", "Kafkka"],
        tools_and_platforms=["MS Visio", "JIRA", "Apache Tomcat9"],
        domain_and_functional=["Agile", "Business Analysis"],
        soft_skills=[],
        all_skills=["Postgres", "MS Visio"]
    )
    std_skills, warns = standardize_skills_categorized(raw_skills)

    # Postgres -> PostgreSQL
    assert "PostgreSQL" in std_skills.technical_skills
    assert "Postgres" not in std_skills.technical_skills

    # Kafkka -> Kafka
    assert "Kafka" in std_skills.technical_skills
    # Deduplication check: Kafka should appear once
    assert std_skills.technical_skills.count("Kafka") == 1

    # MS Visio -> Microsoft Visio
    assert "Microsoft Visio" in std_skills.tools_and_platforms

    # Apache Tomcat9 -> Apache Tomcat 9
    assert "Apache Tomcat 9" in std_skills.tools_and_platforms

    # JIRA -> Jira
    assert "Jira" in std_skills.tools_and_platforms

    # Warnings recorded
    assert any(w.original_value == "MS Visio" and w.normalized_value == "Microsoft Visio" for w in warns)
    assert any(w.original_value == "Apache Tomcat9" and w.normalized_value == "Apache Tomcat 9" for w in warns)


def test_conservative_spelling_preserves_names():
    # Names and companies must never be altered
    corrected_name, warns_name = correct_ocr_or_spelling("A MADHAVI", is_protected=True)
    assert corrected_name == "A MADHAVI"
    assert len(warns_name) == 0

    corrected_company, warns_co = correct_ocr_or_spelling("Tech Mahindra", is_protected=True)
    assert corrected_company == "Tech Mahindra"
    assert len(warns_co) == 0

    # Whitelisted OCR typo corrected
    corrected_text, warns_txt = correct_ocr_or_spelling("requriements gathering", is_protected=False)
    assert "requirements gathering" in corrected_text
    assert len(warns_txt) == 1


def test_end_to_end_madhavi_standardization():
    madhavi_data = {
        "contact": {
            "full_name": "A MADHAVI",
            "email": "madhavi.aradhyula03@gmail.com",
            "phone": "+91-9494916311",
            "location": None,
            "linkedin_url": "linkedin.com/in/madhavi-av-a3ba34b0",
            "github_url": None,
            "portfolio_url": None,
        },
        "professional_title": None,
        "summary": "Results-driven professional with 8 years of experience...",
        "total_experience_years": 8.0,
        "skills": {
            "technical_skills": ["Linux", "Windows", "Oracle", "Postgres", "Redis", "Cassandra", "Kafka"],
            "tools_and_platforms": ["MS Visio", "JIRA", "Apache Tomcat9", "Postman", "Draw.io"],
            "domain_and_functional": ["Business Analysis & Requirement Gathering", "Agile & Scrum"],
            "soft_skills": [],
            "all_skills": ["Postgres", "MS Visio", "JIRA", "Apache Tomcat9"],
        },
        "experience": [
            {
                "company": "Tech Mahindra",
                "role": "Business Analyst cum UAT Tester",
                "start_date": "Aug 2022",
                "end_date": "Present",
                "duration": "Aug 2022 – Present",
                "location": "Hyderabad",
                "responsibilities": ["Gathered requirements.", "Converted requirements into user stories."],
                "technologies": []
            },
            {
                "company": "Pine Labs",
                "role": "Sr QA Cum Product Owner",
                "start_date": "Jan 2022",
                "end_date": "June 2022",
                "duration": "Jan 2022 – June 2022",
                "location": "Hyderabad",
                "responsibilities": ["Owned product backlog."],
                "technologies": []
            },
            {
                "company": "Capgemini",
                "role": "Consultant",
                "start_date": "May 2021",
                "end_date": "Dec 2021",
                "duration": "May 2021 – Dec 2021",
                "location": "Hyderabad",
                "responsibilities": ["Conducted gap analysis."],
                "technologies": []
            },
            {
                "company": "National Payments Corporation of India",
                "role": "Senior Associate",
                "start_date": "Jan 2017",
                "end_date": "May 2021",
                "duration": "Jan 2017 – May 2021",
                "location": "Hyderabad",
                "responsibilities": [],
                "technologies": []
            }
        ],
        "education": [
            {
                "institution": "Gayatri Vidya Parishad",
                "degree": "Bachelor of Engineering",
                "field_of_study": "ECE",
                "start_year": None,
                "graduation_year": "2015",
                "grade_or_gpa": None
            }
        ],
        "certifications": [
            {
                "name": "Certified Scrum Product Owner (CSPO)",
                "issuer": None,
                "issue_year": "2025"
            }
        ],
        "projects": [],
        "languages": []
    }

    std_resume, metadata, status, warnings = standardize_resume_data(madhavi_data)

    # 1. Contact validation
    assert std_resume.contact.phone_e164 == "+919494916311"
    assert std_resume.contact.raw_phone == "+91-9494916311"
    assert std_resume.contact.linkedin_url == "https://linkedin.com/in/madhavi-av-a3ba34b0"

    # 2. Skills validation
    assert "PostgreSQL" in std_resume.skills.technical_skills
    assert "Microsoft Visio" in std_resume.skills.tools_and_platforms
    assert "Apache Tomcat 9" in std_resume.skills.tools_and_platforms
    assert "Jira" in std_resume.skills.tools_and_platforms

    # 3. Date standardization & Current status
    assert std_resume.experience[0].is_current is True
    assert std_resume.experience[0].start_date_iso == "2022-08"
    assert std_resume.experience[0].raw_start_date == "Aug 2022"

    assert std_resume.experience[1].is_current is False
    assert std_resume.experience[1].start_date_iso == "2022-01"
    assert std_resume.experience[1].end_date_iso == "2022-06"

    assert std_resume.experience[3].start_date_iso == "2017-01"
    assert std_resume.experience[3].end_date_iso == "2021-05"

    # 4. Total experience calculated
    assert std_resume.total_experience_years == 8.0
    assert std_resume.calculated_experience_years is not None
    assert std_resume.calculated_experience_years > 8.0

    # 5. Metadata and validation status
    assert metadata.schema_version == "1.1.0"
    assert metadata.total_normalizations > 0
    assert status.is_valid is True
    assert status.usable is True

