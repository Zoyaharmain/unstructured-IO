"""Test duration calculation and experience totals for resumes with stated duration records (e.g. Yogendra Singh)."""
import pytest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export


def test_stated_duration_record_calculates_and_completes_experience_total():
    """When a role has explicit stated duration (e.g. 6 months internship) without calendar dates,

    its duration is normalized and does not leave total_experience_years null.
    """
    raw_data = {
        'contact': {'full_name': 'Yogendra Singh', 'email': 'nitbyogendrasingh@gmail.com'},
        'total_experience_years': 8.0,
        'experience': [
            {
                'company': 'Capefox technologies pvt ltd',
                'role': 'FullStack developer',
                'start_date': '2022-12-05',
                'end_date': None,
                'is_current': True,
                'duration': '05-12-2022 to till now'
            },
            {
                'company': 'Publicis Sapient',
                'role': 'FullStack developer',
                'start_date': '2022-06-17',
                'end_date': '2022-12-02',
                'duration': '17-06-2022 to till 02-12-2022'
            },
            {
                'company': 'apex tg india pvt ltd',
                'role': 'internship',
                'start_date': None,
                'end_date': None,
                'duration': '6 months'
            }
        ]
    }
    std, meta, status, warns = standardize_resume_data(raw_data)
    exported = standardized_export({
        'source': 'Yogendra Singh.pdf',
        'standardized_data': std.model_dump(),
        'standardization_metadata': meta.model_dump(),
        'validation_status': status.model_dump(),
        'warnings': [w.model_dump() for w in warns]
    })

    data = exported['data']
    assert data['total_experience_years'] is not None
    assert data['total_experience_years'] > 0
    assert data['stated_total_experience_years'] == 8.0

    # Verify internship duration calculation
    internship = next(e for e in data['experience'] if e['company'] == 'apex tg india pvt ltd')
    assert internship['duration'] == '6 months'
    assert internship['duration_months'] == 6
    assert internship['stated_duration'] == '6 months'

