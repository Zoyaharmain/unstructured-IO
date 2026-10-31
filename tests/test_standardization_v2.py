"""General regression cases for source-preserving consumer standardization."""
from copy import deepcopy
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from local_api.app import app
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export
from local_api.services.standardization.contacts import normalize_url
from local_api.services.standardization.mapping import mapping_input
from test_record_subfields import request
from local_api.services.schema_mapping import map_schema

ASOF = datetime(2026, 10, 30, tzinfo=timezone.utc)


def export(data):
    source = {'contact': {'full_name': 'Example Person', 'email': 'example@example.org', 'phone': ''}, **data}
    before = deepcopy(source)
    std, meta, status, warnings = standardize_resume_data(source, reference_date=ASOF)
    assert source == before
    wrapped = {'data': source, 'standardized_data': std.model_dump(),
               'standardization_metadata': meta.model_dump(), 'validation_status': status.model_dump(),
               'warnings': [w.model_dump() for w in warnings]}
    return standardized_export(wrapped, include_audit=True)


def test_consumer_schema_is_stable_and_has_no_duplicate_date_or_phone_fields():
    empty = export({})
    full = export({'education': [{'institution': 'University', 'degree': 'BSc', 'start_year': '2018', 'graduation_year': 'Jun 2022'}],
                   'certifications': [{'name': 'Credential', 'issue_year': '2024', 'expiry_date': '2027-05',
                                       'credential_id': 'ABC-123', 'verification_url': 'example.org/verify?id=ABC-123'}]})
    assert empty['data'].keys() == full['data'].keys()
    assert full['data']['education'][0]['end_date'] == '2022-06'
    cert = full['data']['certifications'][0]
    assert cert['issue_date'] == '2024' and cert['expiry_date'] == '2027-05'
    assert cert['credential_id'] == 'ABC-123'
    assert 'issue_year' not in cert and 'issue_year_iso' not in cert
    assert 'phone_e164' not in full['data']['contact']
    assert 'calculated_experience_years' not in full['data']
    assert empty['data']['contact']['phone'] is None
    assert all(empty['data'][key] == [] for key in ('experience', 'awards', 'projects', 'publications'))


@pytest.mark.parametrize('data', [
    {'contact': None}, {'skills': {'technical_skills': 'python'}},
    {'experience': [None, 12, {'company': None, 'role': ['Engineer'], 'responsibilities': [4, 'First duty', 'Last duty']}]},
    {'education': 'University'}, {'projects': [True]}, {'certifications': [{}]},
    {'languages': [False, 'English']}, {'awards': [3, 'Award statement']},
])
def test_malformed_values_do_not_crash_or_split_strings(data):
    result = export(data)
    assert result['validation_status']['requires_human_review']
    assert not result['validation_status']['usable']
    if data.get('skills'):
        assert result['data']['skills']['technical_skills'] == []


def test_phone_extension_is_separate_and_country_code_not_invented():
    result = export({'contact': {'full_name': 'Person', 'email': '', 'phone': '+1 (234) 567-8901 ext 22'}})
    assert result['data']['contact']['phone'] == '+12345678901'
    assert result['data']['contact']['phone_extension'] == '22'
    result = export({'contact': {'full_name': 'Person', 'email': '', 'phone': '98765 43210'}})
    assert result['data']['contact']['phone'] == '98765 43210'


@pytest.mark.parametrize('url,expected', [
    ('example.org', 'https://example.org'),
    ('example.org/a?x=1#part', 'https://example.org/a?x=1#part'),
    ('HTTPS://Example.org/a', 'HTTPS://Example.org/a'),
    ('//example.org/a', 'https://example.org/a'),
    ('ftp://example.org/a', None), ('javascript:alert(1)', None),
    ('https://example.org:invalid/a', None), ('not a url', None),
])
def test_url_rules_do_not_create_malformed_links(url, expected):
    assert normalize_url(url, 'projects[0].url')[0] == expected


def test_work_preferences_are_not_residential_location():
    result = export({'contact': {'full_name': 'Person', 'email': '', 'phone': '',
                      'location': 'Open to India, UAE, UK, or Remote'}})
    assert result['data']['contact']['location'] is None
    assert result['data']['contact']['work_preferences'] == 'Open to India, UAE, UK, or Remote'


def test_mapping_preserves_preferences_and_target_roles_with_source_evidence():
    mapped = map_schema(request('personal_information', [['Full Name: Example Person',
        'Open to India, UAE, UK, or Remote', 'Target Role: Senior Engineer']]))
    assert mapped.data.contact.location is None
    assert mapped.data.contact.work_preferences == 'Open to India, UAE, UK, or Remote'
    assert mapped.data.contact.target_role == 'Senior Engineer'
    assert mapped.data.professional_title is None


def test_no_proper_noun_spelling_suggestions_and_no_corrected_skill_warning():
    result = export({'summary': 'Gathered requriements.',
        'skills': {'technical_skills': ['postgress', 'python3'], 'soft_skills': ['teams']},
        'experience': [{'company': 'Experiance Labs', 'role': 'Engineer', 'start_date': '2020-09',
                       'end_date': '2021-02', 'responsibilities': ['First duty', 'Managed requriements.', 'Last duty']}],
        'education': [{'institution': 'Knowlege University', 'degree': 'BSc'}]})
    warnings = result['audit']['warnings']
    spelling = [w for w in warnings if w['warning_type'] == 'possible_spelling_error']
    assert {w['field'] for w in spelling} == {'summary', 'experience[0].responsibilities[1]'}
    assert result['data']['skills']['technical_skills'] == ['PostgreSQL', 'python3']
    assert result['data']['skills']['soft_skills'] == ['teams']
    assert result['data']['experience'][0]['responsibilities'] == ['First duty', 'Managed requriements.', 'Last duty']
    assert result['data']['education'][0]['institution'] == 'Knowlege University'


def test_unparseable_dates_do_not_leak_non_iso_strings_or_invent_century():
    result = export({'experience': [{'company': 'A', 'role': 'B', 'start_date': 'Jan’22', 'end_date': 'Present'}],
                     'certifications': [{'name': 'C', 'issue_year': 'sometime last year'}]})
    assert result['data']['experience'][0]['start_date'] is None
    assert result['data']['certifications'][0]['issue_date'] is None
    assert result['validation_status']['requires_human_review']
    assert result['audit']['source_evidence']['data']['experience'][0]['start_date'] == 'Jan’22'


def test_certification_extended_fields_are_mapped_from_labels():
    mapped = map_schema(request('certifications', [['Certification: Cloud Credential',
        'Issued By: Example Org', 'Issue Date: 2024-02', 'Expiry Date: 2027-02',
        'Credential ID: A-123', 'Verification URL: https://example.org/A-123']]))
    cert = mapped.data.certifications[0]
    assert cert.issue_year == '2024-02' and cert.expiry_date == '2027-02'
    assert cert.credential_id == 'A-123' and cert.verification_url == 'https://example.org/A-123'


def test_awards_publications_and_unknown_fields_remain_in_candidate_data():
    result = export({'awards': [{'name': 'Prize', 'issuer': 'Org', 'date': 'March 2024', 'outcomes': ['Top 1%']}],
                     'publications': [{'title': 'Paper', 'publisher': 'Journal', 'date': '2023'}],
                     'custom_section': {'statement': 'Original statement'}})
    assert result['data']['awards'][0]['date'] == '2024-03'
    assert result['data']['awards'][0]['outcomes'] == ['Top 1%']
    assert result['data']['publications'][0]['name'] == 'Paper'
    assert any(r.get('value') == {'statement': 'Original statement'} for r in result['data']['additional_sections'])


def test_mapping_projects_awards_and_residuals_are_not_silently_lost():
    mapped = map_schema(request('awards', [['Award Name: Prize | Awarded By: Organization | Date: 2024',
                                           'Additional original statement with a measurable result of 40%.']]))
    result = export(mapping_input(mapped))
    assert result['data']['awards'][0]['name'] == 'Prize'
    text = str(result['data']['additional_sections'])
    assert '40%' in text


def test_stated_and_calculated_duration_are_separate_and_discrepancy_requires_review():
    result = export({'total_experience_years': 10,
        'experience': [{'company': 'A', 'role': 'B', 'start_date': '2020-09', 'end_date': '2021-02', 'duration': '6 months'}]})
    job = result['data']['experience'][0]
    assert job['duration'] == '5 months' and job['stated_duration'] == '6 months'
    assert result['data']['total_experience_years'] == 0.4
    assert result['data']['stated_total_experience_years'] == 10
    assert {'stated_duration_discrepancy', 'experience_duration_discrepancy'} <= {w['warning_type'] for w in result['audit']['warnings']}
    assert result['validation_status']['requires_human_review'] and not result['validation_status']['usable']
    assert result['validation_status']['issues_count'] == len(result['audit']['warnings'])


def test_api_consumer_and_optional_audit_contract():
    client = TestClient(app)
    payload = {'contact': {'full_name': 'Person', 'email': 'person@example.org', 'phone': ''}}
    clean = client.post('/api/v1/resume/schema/standardize', json=payload).json()
    audited = client.post('/api/v1/resume/schema/standardize?include_audit=true', json=payload).json()
    assert 'audit' not in clean and 'audit' in audited
    assert clean['data'] == audited['data']
    assert audited['audit']['source_evidence']['data'] == payload
    assert client.post('/api/v1/resume/schema/standardize', json={'data': []}).status_code == 422
    definition = client.get('/api/v1/resume/schema/standardized-definition').json()
    assert definition['title'] == 'ConsumerResume'
    assert 'experience_summary' in audited['audit']['standardization_metadata']


def test_broad_evidence_quote_does_not_consume_unmapped_text():
    text = 'Prize; achieved a 40% reduction.'
    mapped = {'data': {}, 'section_schemas': [{'category': 'awards', 'label': 'Awards',
        'records': [{'attributes': [{'name': 'name', 'items': [{'value': 'Prize',
                     'evidence': [{'source_id': 'e0:0:30', 'quote': text}]}]}]}],
        'residual_blocks': [{'source_id': 'e0:0:30', 'quote': text}]}]}
    result = mapping_input(mapped)
    assert result['awards'][0]['name'] == 'Prize'
    assert '40%' in result['additional_sections'][0]['text']


def test_language_proficiency_without_a_legacy_slot_remains_visible():
    mapped = {'data': {'languages': ['English']}, 'section_schemas': [
        {'category': 'languages', 'label': 'Languages', 'records': [{'attributes': [
            {'name': 'language', 'items': [{'value': 'English', 'evidence': [{'source_id': 'e0', 'quote': 'English'}]}]},
            {'name': 'proficiency', 'items': [{'value': 'Fluent', 'evidence': [{'source_id': 'e0', 'quote': 'Fluent'}]}]}]}],
         'residual_blocks': [{'source_id': 'e0', 'quote': 'English: Fluent'}]}]}
    result = mapping_input(mapped)
    assert 'Fluent' in result['additional_sections'][0]['text']


def test_overlapping_exact_day_jobs_do_not_become_whole_months():
    result = export({'experience': [
        {'company': 'A', 'role': 'Engineer', 'start_date': '2022-01-01', 'end_date': '2022-01-02'},
        {'company': 'B', 'role': 'Engineer', 'start_date': '2022-01-01', 'end_date': '2022-01-03'}]})
    assert [r['duration'] for r in result['data']['experience']] == ['1 day', '2 days']
    summary = result['audit']['standardization_metadata']['experience_summary']
    assert summary['experience_overlap_detected']
    assert summary['calculated_experience_years'] == 0.0


def test_conflicting_supplemental_fields_and_date_aliases_require_review():
    result = export({'awards': [{'name': 'Prize A', 'title': 'Prize B'}],
                     'certifications': [{'name': 'Credential', 'issue_year': '2024', 'issue_date': '2023'}]})
    assert result['data']['awards'][0]['name'] is None
    assert result['data']['awards'][0]['details'] == {'name': 'Prize A', 'title': 'Prize B'}
    assert result['data']['certifications'][0]['issue_date'] is None
    assert result['validation_status']['requires_human_review']


def test_normalization_counts_are_applied_logs_not_suggestions():
    result = export({'summary': 'Gather requriements.',
                     'skills': {'technical_skills': ['postgress', 'PostgreSQL']}})
    audit = result['audit']
    assert audit['standardization_metadata']['total_normalizations'] == sum(w['applied'] for w in audit['warnings'])
    assert 'possible_spelling_error' not in audit['standardization_metadata']['corrections_by_type']
    assert any(w['warning_type'] == 'collection_standardized' for w in audit['warnings'])


def test_source_detail_keys_named_raw_are_not_removed_by_export():
    result = export({'custom_section': {'raw_detail': 'Original custom information'},
                     'awards': [{'name': 'Prize', 'raw_details': 'Original award details'}]})
    assert result['data']['additional_sections'][0]['value']['raw_detail'] == 'Original custom information'
    assert result['data']['awards'][0]['details']['raw_details'] == 'Original award details'


def test_consumer_data_can_be_standardized_again_without_changing_candidate_meaning():
    first = export({'awards': [{'name': 'Prize', 'issuer': 'Org', 'date': '2024', 'custom_detail': 'Original'}],
        'experience': [{'company': 'Org', 'role': 'Engineer', 'start_date': '2020-09',
                        'end_date': 'Present', 'duration': '2020-09 – Present'}]})
    second = export(first['data'])
    assert second['data'] == first['data']
