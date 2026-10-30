import json
import subprocess
from copy import deepcopy
from pathlib import Path
from datetime import datetime,timezone
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export


def fixture():
    original={'contact':{'full_name':'Example Candidate','email':'example@example.com','phone':''},
              'experience':[{'company':'Example','role':'Analyst','start_date':'Aug 2022','end_date':'Present','duration':'Aug 2022 – Present'}]}
    std,meta,status,warnings=standardize_resume_data(original,reference_date=datetime(2026,10,29,tzinfo=timezone.utc))
    return {'source':'example.pdf','data':original,'standardized_data':std.model_dump(),
            'standardization_metadata':meta.model_dump(),'validation_status':status.model_dump(),
            'warnings':[w.model_dump() for w in warnings],'section_schemas':[]}


def test_primary_export_contains_calculated_duration_and_preserves_original_evidence():
    response=fixture();before=deepcopy(response)
    result=standardized_export(response)
    assert result['data']['experience'][0]['duration']=='4 years 3 months'
    assert result['data']['experience'][0]['duration_months']==51
    assert 'raw_duration' not in result['data']['experience'][0]
    assert result['source_evidence']['data']['experience'][0]['duration']=='Aug 2022 – Present'
    assert response==before


def test_browser_download_matches_python_export():
    source=Path('local_api/static/schema.js').read_text()
    function=source[source.index('function standardizedResumeExport('):source.index('function renderStandardizationWarnings(')]
    response=fixture()
    code=function+'\nconsole.log(JSON.stringify(standardizedResumeExport('+json.dumps(response)+')));'
    output=subprocess.run(['node'],input=code,text=True,check=True,capture_output=True)
    assert json.loads(output.stdout)==standardized_export(response)


def test_job_details_are_separate_from_technologies_and_calculation_metadata():
    response=fixture()
    response['standardized_data']['experience'][0]['technologies']=['Python','SQL']
    result=standardized_export(response)
    job=result['data']['experience'][0]
    assert job['technologies']==['Python','SQL']
    assert list(job).index('duration_months') < list(job).index('technologies')
    assert 'duration_as_of' not in job and 'start_date_iso' not in job
    details=result['standardization_metadata']['experience_calculations'][0]
    assert details['record_path']=='data.experience[0]'
    assert details['duration_as_of']=='2026-10-29'
    assert details['start_date_precision']=='month_year'
    assert response['standardized_data']['experience'][0]['duration_as_of']=='2026-10-29'
