"""The aggregate skills field must survive every canonical export path."""
from fastapi.testclient import TestClient
from local_api.app import app
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export


def test_all_skills_is_deduplicated_union_in_default_and_audited_exports():
    raw={'contact':{'full_name':'Example Person'},'skills':{
        'technical_skills':['Python','SQL'], 'tools_and_platforms':['Power BI','Jira','Microsoft Excel'],
        'domain_and_functional':['KYC','AML'], 'soft_skills':['Agile','Project Management','Leadership'],
        'all_skills':['python','Additional source skill']}}
    std,meta,status,warnings=standardize_resume_data(raw)
    response={'standardized_data':std.model_dump(),'standardization_metadata':meta.model_dump(),
              'validation_status':status.model_dump(),'warnings':[w.model_dump() for w in warnings]}
    expected=['Python','SQL','Power BI','Jira','Microsoft Excel','KYC','AML','Agile','Project Management','Leadership','Additional source skill']
    for audit in (False,True):
        exported=standardized_export(response,include_audit=audit)
        assert exported['data']['skills']['all_skills']==expected
        assert exported['data']['skills']['technical_skills']==['Python','SQL']


def test_api_default_output_and_definition_include_all_skills_even_when_empty():
    client=TestClient(app)
    response=client.post('/api/v1/resume/schema/standardize',json={'contact':{'full_name':'Example Person'}})
    assert response.status_code==200
    assert response.json()['data']['skills']['all_skills']==[]
    schema=client.get('/api/v1/resume/schema/standardized-definition').json()
    assert 'all_skills' in schema['$defs']['ConsumerSkills']['properties']
