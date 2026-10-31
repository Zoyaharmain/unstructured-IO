"""Year-only source dates produce labelled estimates, never invented months."""
from datetime import datetime,timezone
from copy import deepcopy
import pytest
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export

ASOF=datetime(2026,10,31,tzinfo=timezone.utc)


def payload():
    return {'contact':{'full_name':'Synthetic Example'},'experience':[
        {'company':'Example One','role':'Engineer','start_date':'2023','end_date':'Present','duration':'2023–Present'},
        {'company':'Example Two','role':'Engineer','start_date':'2020','end_date':'2023','duration':'2020–2023'},
        {'company':'Example Three','role':'Engineer','start_date':'2018','end_date':'2019','duration':'2018–2019'}]}


def test_year_ranges_have_explicit_estimates_and_unchanged_source_dates():
    raw=payload();before=deepcopy(raw)
    std,metadata,status,warnings=standardize_resume_data(raw,reference_date=ASOF)
    assert raw==before
    assert [j.duration for j in std.experience]==['Approximately 3 years','Approximately 3 years','Approximately 1 year']
    assert [j.duration_months for j in std.experience]==[36,36,12]
    assert all(j.duration_status=='estimated_year_precision' and j.duration_is_approximate for j in std.experience)
    assert [j.start_date for j in std.experience]==['2023','2020','2018']
    assert std.experience[0].duration_as_of=='2026-10-31'
    assert std.total_experience_years==7.0 and std.calculated_experience_complete
    assert std.calculated_experience_is_approximate
    assert sum(w.warning_type=='duration_estimated_year_precision' and w.applied for w in warnings)==3
    assert status.requires_human_review
    export=standardized_export({'standardized_data':std.model_dump(),'standardization_metadata':metadata.model_dump(),
        'validation_status':status.model_dump(),'warnings':[w.model_dump() for w in warnings]})
    assert export['standardization_metadata']['experience_summary']['calculated_experience_is_approximate']
    assert all(j['duration_status']=='estimated_year_precision' for j in export['standardization_metadata']['experience_calculations'])


@pytest.mark.parametrize('start,end,text',[
    ('2026','Present','Less than 1 year (year precision)'),
    ('2020','2020','Less than 1 year (year precision)'),
    ('2020','2023-06','Approximately 3 years'),
    ('2020-06','2023','Approximately 3 years')])
def test_year_or_mixed_precision_never_invents_a_month(start,end,text):
    raw=payload();raw['experience']=raw['experience'][:1];raw['experience'][0].update(start_date=start,end_date=end)
    std,*_=standardize_resume_data(raw,reference_date=ASOF)
    assert std.experience[0].duration==text
    assert std.experience[0].start_date==start


@pytest.mark.parametrize('start,end',[('2027','Present'),('2023','2020'),('2023','2026-12'),('2026-12','2026')])
def test_invalid_or_future_year_ranges_still_do_not_get_a_duration(start,end):
    raw=payload();raw['experience']=raw['experience'][:1];raw['experience'][0].update(start_date=start,end_date=end)
    std,*_=standardize_resume_data(raw,reference_date=ASOF)
    assert std.experience[0].duration is None


def test_overlapping_year_labels_do_not_double_count_estimated_total():
    raw=payload();raw['experience']=[dict(raw['experience'][0],start_date='2020',end_date='2024'),dict(raw['experience'][1],start_date='2022',end_date='2025')]
    std,*_=standardize_resume_data(raw,reference_date=ASOF)
    assert std.total_experience_years==5.0 and std.experience_overlap_detected
