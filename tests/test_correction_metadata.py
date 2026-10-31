"""System changes stay visible in default JSON, and totals use dated interval unions."""
from copy import deepcopy
from datetime import datetime, timezone
import pytest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export

ASOF = datetime(2026, 10, 31, tzinfo=timezone.utc)


def run(jobs, stated=14, **extra):
    source = {'contact': {'full_name': 'Example Person', 'email': 'person@example.org'},
              'total_experience_years': stated, 'experience': jobs, **extra}
    before = deepcopy(source)
    std, meta, status, warnings = standardize_resume_data(source, reference_date=ASOF)
    assert source == before
    return standardized_export({'standardized_data': std.model_dump(),
        'standardization_metadata': meta.model_dump(), 'validation_status': status.model_dump(),
        'warnings': [w.model_dump() for w in warnings]})


def job(start, end, duration=None):
    return {'company': 'Example Ltd', 'role': 'Analyst', 'start_date': start,
            'end_date': end, 'duration': duration}


@pytest.mark.parametrize('stated_duration', ['10 years 9 months', '10 yrs 9 mos', '10 years and 9 months', 'Sep 2013 – May 2024 (10 yrs 9 mos)'])
def test_default_export_identifies_actual_duration_correction(stated_duration):
    result = run([job('2013-09', '2024-05', stated_duration)])
    assert 'audit' not in result
    corrected = next(w for w in result['standardization_metadata']['corrections']
                     if w['warning_type'] == 'stated_duration_discrepancy')
    assert corrected['applied'] and corrected['original_value'] == stated_duration
    assert corrected['normalized_value'] == '10 years 8 months'
    assert corrected['field'] == 'experience[0].duration' and corrected['basis']
    assert corrected in result['warnings']


def test_total_uses_dates_and_current_reference_instead_of_source_claim():
    result = run([job('2013-09', '2024-05'), job('2024-06', 'Currently working')],
                 summary='Professional with 14+ years of experience.')
    data = result['data']
    assert data['total_experience_years'] == 13.0
    assert data['stated_total_experience_years'] == 14
    assert data['summary'] == 'Professional with 14+ years of experience.'
    assert result['standardization_metadata']['as_of_date'] == '2026-10-31'
    assert data['experience'][1]['duration'] == '2 years 4 months'
    assert any(w['warning_type'] == 'total_experience_calculated' and w['applied'] for w in result['warnings'])


def test_overlapping_roles_count_once_and_gaps_do_not_count():
    result = run([job('2020-01', '2022-01'), job('2021-01', '2023-01'),
                  job('2024-01', '2025-01')])
    assert result['data']['total_experience_years'] == 4
    assert result['standardization_metadata']['experience_summary']['experience_overlap_detected']


def test_incomplete_dates_do_not_present_partial_total_as_complete():
    result = run([job('2020-01', '2021-01'), job('2018', None)])
    assert result['data']['total_experience_years'] is None
    assert result['data']['stated_total_experience_years'] == 14
    assert result['standardization_metadata']['experience_summary']['calculated_experience_years'] == 1
    assert any(w['warning_type'] == 'total_experience_incomplete' for w in result['warnings'])


def test_applied_alias_and_whitespace_changes_have_metadata_but_suggestions_are_not_applied():
    result = run([dict(job('2020-01', '2021-01'), responsibilities=[' Managed requriements. '])],
                 skills={'technical_skills': ['postgress']})
    corrections = result['standardization_metadata']['corrections']
    assert all(w['applied'] for w in corrections)
    assert any(w['field'] == 'experience[0].responsibilities[0]' for w in corrections)
    assert any(w['warning_type'] == 'skill_canonicalization' for w in corrections)
    suggestions = [w for w in result['warnings'] if w['warning_type'] == 'possible_spelling_error']
    assert suggestions and all(not w['applied'] for w in suggestions)


def test_reprocessing_preserves_original_stated_total():
    first = run([job('2020-01', '2021-01')])
    std, *_ = standardize_resume_data(first['data'], reference_date=ASOF)
    assert std.stated_total_experience_years == 14
    assert std.total_experience_years == 1


def test_local_duration_literal_keeps_parenthetical_claim_without_rewriting_source():
    from local_api.services.record_subfields import RANGE, employment_duration_literal
    source = 'Example Ltd Sep 2013 – May 2024 (10 yrs 9 mos)'
    match = RANGE.search(source)
    assert employment_duration_literal(match) == 'Sep 2013 – May 2024 (10 yrs 9 mos)'


def test_rejected_employment_input_cannot_make_partial_total_look_complete():
    result = run([job('2020-01', '2021-01'), 'Unstructured earlier employment'])
    assert result['data']['total_experience_years'] is None
    assert not result['standardization_metadata']['experience_summary']['calculated_experience_complete']


def test_date_representation_changes_are_explicit_corrections_in_default_json():
    result = run([job('Jan 2020','Dec 2021')])
    dates = [w for w in result['standardization_metadata']['corrections'] if w['warning_type'] == 'date_standardized']
    assert {w['field'] for w in dates} == {'experience[0].start_date','experience[0].end_date'}
    assert all(w['applied'] and 'System corrected the date' in w['message'] for w in dates)
    assert {w['normalized_value'] for w in dates} == {'2020-01','2021-12'}
