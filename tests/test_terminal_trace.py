"""Terminal-first tracing is private, correlated, and observational."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
import json
import logging
from pathlib import Path

import pytest

from local_api.services import decision_trace as trace
from local_api.services.confidence import confidence_for
from local_api.services.calibration_evaluation import fit_calibration
from local_api.services.llm_section_review import ReviewSettings, ReviewError
from test_schema_mapping import sample


@pytest.fixture
def run(monkeypatch, tmp_path):
    monkeypatch.setenv('RESUME_TRACE_DIR', str(tmp_path))
    monkeypatch.delenv('RESUME_CALIBRATION_FILE', raising=False)
    monkeypatch.delenv('RESUME_CALIBRATION_DIR', raising=False)
    context, token = trace.start()
    yield context
    trace.reset(token)


def events(run):
    return [json.loads(x) for x in (run.root/run.run_id/'events.jsonl').read_text().splitlines()]


def test_terminal_and_private_events_have_no_resume_text(run):
    records = []
    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())
    handler = Capture(); old = trace.logger.level
    trace.logger.addHandler(handler); trace.logger.setLevel(logging.DEBUG)
    try:
        trace.decision('prediction', source_ids=['e0:0:10'], candidate='experience', raw_score=.6)
    finally:
        trace.logger.removeHandler(handler); trace.logger.setLevel(old)
    assert any('prediction' in x for x in records)
    data = events(run)[0]
    assert data['confidence']['probability'] is None and data['confidence']['state']=='not_calibrated'
    assert data['decision_id'] and data['run_id']==run.run_id
    assert (run.root/run.run_id/'events.jsonl').stat().st_mode & 0o077 == 0


def test_trace_does_not_change_mapping_or_export(run, monkeypatch):
    from local_api.services.schema_mapping import map_schema
    req = sample()
    monkeypatch.setenv('RESUME_TRACE_ENABLED', 'false')
    before = map_schema(req).model_dump(mode='json')
    monkeypatch.setenv('RESUME_TRACE_ENABLED', 'true')
    after = map_schema(req).model_dump(mode='json')
    assert before == after
    serialized = json.dumps(events(run))
    assert req.elements[0].text not in serialized
    assert 'jordan@example.com' not in serialized and 'alex@example.com' not in serialized
    assert any(e['event']=='stage_start' for e in events(run))
    assert 'decision_trace' not in after['meta']


def test_missing_storage_cannot_break_pipeline(run, monkeypatch):
    @trace.traced('fixture')
    def process():
        return 42
    def unavailable(*a, **kw):
        raise PermissionError('private diagnostic destination')
    with monkeypatch.context() as m:
        m.setattr(Path, 'mkdir', unavailable)
        assert process()==42


def test_binding_resumes_and_rebinds_different_documents(run):
    trace.emit('start')
    elements = sample().elements
    trace.bind_elements(elements)
    original = run.run_id
    second, token = trace.start(original)
    try:
        trace.bind_elements(elements)
        assert second.run_id==original
        changed=[e.model_copy(deep=True) for e in elements]
        changed[0].text='Different person'
        trace.bind_elements(changed)
        assert second.run_id!=original
    finally:
        trace.reset(token)


def test_parallel_events_are_unique_chronological_and_correlated(run):
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(copy_context().run, trace.emit, 'parallel') for _ in range(20)]
        for f in futures:f.result()
    rows=events(run)
    assert [x['sequence'] for x in rows]==list(range(1,21))
    assert len({x['event_id'] for x in rows})==20
    assert {x['run_id'] for x in rows}=={run.run_id}


def test_provider_logs_trigger_usage_latency_and_not_secrets(run):
    calls=[]
    @trace.provider_trace
    def provider(settings,path,body):
        calls.append(body)
        return {'usage':{'prompt_tokens':9,'completion_tokens':3},'choices':[]}
    @trace.traced('section_review','reviewed_mode_complete_section_review')
    def process():
        return provider(ReviewSettings(api_key='TOP-SECRET'),'/chat/completions',{'messages':[
            {'content':json.dumps({'spans':[{'id':'e0:0:10','text':'PRIVATE NAME','similarity':.6}]})}]})
    result=process()
    assert len(calls)==1 and result['usage']['prompt_tokens']==9
    rows=events(run); serialized=json.dumps(rows)
    assert 'TOP-SECRET' not in serialized and 'PRIVATE NAME' not in serialized
    start=next(x for x in rows if x['event']=='llm_call_start')
    end=next(x for x in rows if x['event']=='llm_call_end')
    assert start['trigger']=='reviewed_mode_complete_section_review'
    assert not start['confidence_based_routing'] and start['decision_ids']
    assert end['latency_ms']>=0 and end['token_usage']['completion_tokens']==3


def test_provider_errors_still_raise_and_usage_can_be_unknown(run):
    @trace.provider_trace
    def provider(*a):raise ReviewError('authentication_failed')
    with pytest.raises(ReviewError):provider(ReviewSettings(),'/chat/completions',{})
    assert events(run)[-1]['error_code']=='authentication_failed'
    assert events(run)[-1]['token_usage'] is None


def test_calibration_missing_incompatible_and_available(run, monkeypatch):
    params={'task':'section_content','model_revision':'revision','anchor_sha256':'anchors'}
    assert confidence_for(.4,**params)['probability'] is None
    file=run.root/'calibration.json'
    artifact={**params,'target':'ml_candidate_correct','label_source':'human_verified',
              'evaluation':{'test_count':100},'method':'platt','version':'v1','coefficient':1,'intercept':0}
    file.write_text(json.dumps(artifact));monkeypatch.setenv('RESUME_CALIBRATION_FILE',str(file))
    value=confidence_for(0,**params)
    assert value['probability']==.5 and value['calibration_version']=='v1'
    assert confidence_for(0,**{**params,'model_revision':'different'})['probability'] is None


@pytest.mark.parametrize('method',['platt','isotonic'])
def test_calibration_groups_do_not_leak_and_judge_labels_are_rejected(method):
    rows=[{'task':'section_content','document_group':f'doc-{i}','score':float(j)/10,
           'correct':int(j>=5),'label_source':'human_verified'} for i in range(12) for j in range(10)]
    artifact, metrics, bins=fit_calibration(rows,method=method)
    assert not set(metrics['calibration_groups']) & set(metrics['test_groups'])
    assert 0<=metrics['brier_score']<=1 and 0<=metrics['expected_calibration_error']<=1
    assert sum(b['count'] for b in bins)==metrics['test_count']
    rows[0]['label_source']='llm_judge'
    with pytest.raises(ValueError):fit_calibration(rows,method=method)


def test_browser_run_id_crosses_extraction_sections_and_mapping(run, monkeypatch):
    from fastapi.testclient import TestClient
    from local_api.app import app
    from local_api.routes import extraction, sections
    from local_api.schemas.extraction import ExtractionResponse,ExtractionMetadata
    req=sample()
    @trace.traced('extraction')
    def extract(*a,**kw):
        return ExtractionResponse(filename='synthetic.txt',file_type='text/plain',strategy='auto',
            text='\n'.join(e.text for e in req.elements),elements=req.elements,
            metadata=ExtractionMetadata(total_elements=len(req.elements),page_count=None,page_numbers=[1]))
    monkeypatch.setattr(extraction,'extract_text',extract)
    monkeypatch.setattr(sections,'detect_sections',lambda _:req.sections.model_copy(deep=True))
    with TestClient(app) as client:
        a=client.post('/api/v1/extract/text',files={'file':('synthetic.txt',b'synthetic')})
        run_id=a.headers['X-Resume-Run-ID']; headers={'X-Resume-Run-ID':run_id}
        b=client.post('/api/v1/resume/sections/local',headers=headers,json={'elements':a.json()['elements']})
        assert b.status_code==200,b.text
        c=client.post('/api/v1/resume/schema',headers=headers,json={
            'elements':a.json()['elements'],'sections':b.json(),'review_fields':False})
        assert c.status_code==200,c.text
        assert b.headers['X-Resume-Run-ID']==c.headers['X-Resume-Run-ID']==run_id
        assert c.json()['meta']['schema_audit']['provider_calls']==0
