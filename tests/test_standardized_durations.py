from datetime import datetime, timezone
from copy import deepcopy
import pytest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.dates import parse_date_string

ASOF=datetime(2026,10,29,tzinfo=timezone.utc)


def payload(start='Aug 2022',end='Present'):
    return {'contact':{'full_name':'Example Candidate','email':'example@example.com','phone':''},
            'experience':[{'company':'Example Ltd','role':'Analyst','start_date':start,'end_date':end,'duration':f'{start} – {end}','location':'Unknown Location','responsibilities':['Managed requriements.']} ]}


def test_current_duration_is_derived_and_original_is_immutable():
    original=payload();before=deepcopy(original)
    std,meta,status,warnings=standardize_resume_data(original,reference_date=ASOF)
    job=std.experience[0]
    assert job.duration=='4 years 3 months' and job.duration_months==51
    assert job.duration_as_of=='2026-10-29' and job.is_current
    assert job.raw_duration=='Aug 2022 – Present'
    assert original==before
    suggestion=next(w for w in warnings if w.warning_type=='possible_spelling_error')
    assert suggestion.suggested_value=='Managed requirements.'
    assert not suggestion.applied
    assert std.experience[0].responsibilities==['Managed requriements.']
    assert meta.field_verification['locations']=='not_externally_verified'
    assert status.requires_human_review


@pytest.mark.parametrize('start,end,months', [('JAN 2022','JUN 2022',6),('01/2022','2022-06',6),("Jan’22",'June 2022',6)])
def test_date_variants_have_same_computed_month_count(start,end,months):
    std,*_=standardize_resume_data(payload(start,end),reference_date=ASOF)
    assert std.experience[0].duration_months==months


@pytest.mark.parametrize('start,end',[('2022','2023'),('05/06/2022','Present'),('2022-02-30','Present'),('June 2026','Jan 2026'),('Jan 2030','Present'),('Aug 2022',None)])
def test_insufficient_ambiguous_invalid_or_future_dates_do_not_invent_duration(start,end):
    std,meta,status,warnings=standardize_resume_data(payload(start,end),reference_date=ASOF)
    assert std.experience[0].duration is None
    assert std.experience[0].duration_months is None
    assert status.requires_human_review


def test_document_location_consensus_suggests_but_never_changes_or_verifies():
    original=payload();original['contact']['location']='Hyderbad'
    original['experience']*=2
    for r in original['experience']:r['location']='Hyderabad'
    std,meta,status,warnings=standardize_resume_data(original,reference_date=ASOF)
    suggestion=next(w for w in warnings if w.warning_type=='possible_location_spelling_variant')
    assert suggestion.suggested_value=='Hyderabad'
    assert suggestion.original_value=='Hyderbad' and not suggestion.applied
    assert std.contact.location=='Hyderbad'
    assert suggestion.verification_status=='rule_based_not_independently_verified'


def test_iso_end_date_in_future_same_month_is_not_calculated():
    std,*_=standardize_resume_data(payload('2026-10-01','2026-10-30'),reference_date=ASOF)
    assert std.experience[0].duration is None


def test_standardize_api_exposes_derived_duration_without_mutating_source():
    from fastapi.testclient import TestClient
    from local_api.app import app
    raw=payload('JAN 2022','JUN 2022');before=deepcopy(raw)
    response=TestClient(app).post('/api/v1/resume/schema/standardize',json={'data':raw})
    assert response.status_code==200
    result=response.json()
    assert result['standardized_data']['experience'][0]['duration']=='6 months'
    assert result['standardization_metadata']['schema_version']=='1.1.0'
    assert raw==before


def test_exact_day_duration_does_not_turn_one_day_into_one_month():
    std,*_=standardize_resume_data(payload('2022-01-01','2022-01-02'),reference_date=ASOF)
    assert std.experience[0].duration=='1 day'
    assert std.experience[0].duration_months==0
    assert not std.experience[0].duration_is_approximate
