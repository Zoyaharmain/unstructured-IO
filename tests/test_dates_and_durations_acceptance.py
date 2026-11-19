"""Acceptance tests for dates, durations, overlapping intervals, gaps, and unresolved status."""
from datetime import datetime, timezone, date
import pytest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.dates import (
    parse_date_string,
    calculated_duration,
    calculate_non_overlapping_experience,
)

REF_DATE = datetime(2026, 11, 1, tzinfo=timezone.utc)


def _exp_payload(records):
    return {
        "contact": {"full_name": "Test Candidate", "email": "test@example.com", "phone": "1234567890"},
        "experience": [
            {
                "company": r.get("company", "Test Co"),
                "role": r.get("role", "Software Engineer"),
                "start_date": r.get("start_date"),
                "end_date": r.get("end_date"),
                "duration": r.get("duration"),
                "responsibilities": ["Responsibility 1"]
            }
            for r in records
        ]
    }


def test_explicit_present_and_current():
    """Verify explicit Present and Current markers."""
    payload = _exp_payload([
        {"company": "Co A", "start_date": "August 2024", "end_date": "Present"},
        {"company": "Co B", "start_date": "January 2023", "end_date": "Current"}
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    expA = std.experience[0]
    expB = std.experience[1]
    assert expA.is_current is True
    assert expA.end_date is None
    assert expA.duration_as_of == "2026-11-01"
    assert expA.duration_months == 27  # Aug 2024 to Nov 2026 = 27 months = 2 years 3 months
    assert expA.duration == "2 years 3 months"

    assert expB.is_current is True
    assert expB.end_date is None
    assert expB.duration_as_of == "2026-11-01"
    assert expB.duration_months == 46  # Jan 2023 to Nov 2026 = 46 months = 3 years 10 months
    assert expB.duration == "3 years 10 months"


def test_since_and_from_date_prefixes():
    """Verify Since and From prefixes are recognized and normalized."""
    payload = _exp_payload([
        {"company": "Co A", "start_date": "Since August 2024", "end_date": None},
        {"company": "Co B", "start_date": "From January 2023", "end_date": None}
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    expA = std.experience[0]
    expB = std.experience[1]
    assert expA.is_current is True
    assert expA.start_date == "2024-08"
    assert expA.end_date is None
    assert expA.duration == "2 years 3 months"

    assert expB.is_current is True
    assert expB.start_date == "2023-01"
    assert expB.end_date is None
    assert expB.duration == "3 years 10 months"


def test_missing_end_date_without_current_evidence():
    """Missing end date with NO marker must be unresolved, not current, and not invent duration."""
    payload = _exp_payload([
        {"company": "Co A", "start_date": "August 2022", "end_date": None}
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    exp = std.experience[0]
    assert exp.is_current is False
    assert exp.end_date is None
    assert exp.duration is None
    assert exp.duration_months is None
    assert exp.duration_status == "insufficient_dates"
    assert any(w.warning_type == "unconfirmed_current_role" for w in warnings)
    assert status.requires_human_review is True


def test_historical_positions_exact_durations():
    """Historical position with both start and end date computes exact elapsed duration."""
    payload = _exp_payload([
        {"company": "Co Historical", "start_date": "May 2018", "end_date": "October 2021"}
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    exp = std.experience[0]
    assert exp.is_current is False
    assert exp.start_date == "2018-05"
    assert exp.end_date == "2021-10"
    assert exp.duration == "3 years 5 months"
    assert exp.duration_months == 41


def test_overlapping_intervals_union():
    """Overlapping intervals are unioned and experience_overlap_detected is True."""
    payload = _exp_payload([
        {"company": "Co 1", "start_date": "2020-01", "end_date": "2022-01"},  # 24 months
        {"company": "Co 2", "start_date": "2021-01", "end_date": "2023-01"},  # 24 months, overlaps Co 1
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    assert std.experience_overlap_detected is True
    # Union is 2020-01 to 2023-01 = 36 months = 3.0 years (not 4.0 years)
    assert std.calculated_experience_years == 3.0


def test_employment_gaps_not_counted():
    """Employment gaps between non-overlapping intervals are excluded from total."""
    payload = _exp_payload([
        {"company": "Job 1", "start_date": "2018-01", "end_date": "2019-01"},  # 12 months = 1.0 yr
        {"company": "Job 2", "start_date": "2020-01", "end_date": "2021-01"},  # 12 months = 1.0 yr, 1 yr gap
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    assert std.experience_overlap_detected is False
    # Total is 2.0 years (the 2019-2020 gap is not counted)
    assert std.calculated_experience_years == 2.0


def test_partial_dates_and_year_precision():
    """Year-only precision computes estimated duration and flags warning."""
    payload = _exp_payload([
        {"company": "Year Range Co", "start_date": "2020", "end_date": "2023"},
        {"company": "Single Year Co", "start_date": "2019", "end_date": "2019"}
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    exp0 = std.experience[0]
    exp1 = std.experience[1]
    assert exp0.duration_status == "estimated_year_precision"
    assert exp0.duration == "Approximately 3 years"
    assert exp0.duration_months == 36

    assert exp1.duration_status == "estimated_year_precision"
    assert exp1.duration == "Less than 1 year (year precision)"
    assert exp1.duration_months == 0


def test_explicit_as_of_date_behavior():
    """Explicit reference_date shifts duration computation as of that snapshot."""
    as_of = datetime(2025, 1, 1, tzinfo=timezone.utc)
    payload = _exp_payload([
        {"company": "Current Co", "start_date": "2024-01", "end_date": "Present"}
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=as_of)
    exp = std.experience[0]
    assert exp.is_current is True
    assert exp.duration_as_of == "2025-01-01"
    assert exp.duration == "1 year"
    assert exp.duration_months == 12


def test_unresolved_intervals_not_counted_as_confirmed_experience():
    """Unresolved open-ended intervals are excluded from calculated experience."""
    payload = _exp_payload([
        {"company": "Unresolved Co", "start_date": "2023-01", "end_date": None},  # No current evidence!
        {"company": "Confirmed Historical Co", "start_date": "2020-01", "end_date": "2022-01"}  # 2.0 years
    ])
    std, meta, status, warnings = standardize_resume_data(payload, reference_date=REF_DATE)
    # The unresolved job cannot be dated safely
    assert std.experience[0].duration is None
    assert std.experience[0].is_current is False
    # Calculated experience must count ONLY Confirmed Historical Co (2.0 years), NOT the unresolved job!
    assert std.calculated_experience_years == 2.0
    assert std.total_experience_years is None  # Total experience is None when some records cannot be dated
