"""Provider-independent validation tests: never send a resume to a live API."""
import json
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient

from local_api.app import app
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, SectionRequest, SectionResponse
from local_api.services.resume_sections import build_sections
from local_api.services import llm_section_review as review


@pytest.fixture(autouse=True)
def no_live_provider(monkeypatch):
    for key in ['DEEPSEEK_REVIEW_ENABLED', 'DEEPSEEK_API_KEY', 'DEEPSEEK_MODEL']:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def document():
    texts = ['Work history', 'Built Python SQL Python services for an employer.',
             'Bachelor of Science, Example University.']
    request = SectionRequest(elements=[ExtractedElement(type='NarrativeText', text=t, metadata={}) for t in texts])
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t,
                page_number=1, lane='main', assignment='semantic', reason='Local evidence') for i,t in enumerate(texts)]
    blocks[0].assignment = 'structural_heading'
    blocks[2].assignment = 'needs_review'
    local = SectionResponse(status='needs_review', sections=build_sections({'experience':[blocks[0]],'skills':[blocks[1]]}, request.elements),
                needs_review=[blocks[2]], metadata={'total_units':3,'all_source_text_preserved':True}, warnings=[])
    return request, local


def configured(**kwargs):
    return review.ReviewSettings(enabled=True, api_key='test-private-key', model='test-model', **kwargs)


def reply(*categories):
    return json.dumps({'assignments':[[f'u{i}',category] for i,category in enumerate(categories)]})


def test_one_review_checks_assigned_and_unassigned_and_applies_atomically(document):
    request, local = document
    before = local.model_dump_json()
    calls = []
    def provider(settings, messages):
        calls.append(messages)
        data = json.loads(messages[1]['content'])
        assert [s['current_category'] for s in data['spans']] == ['experience','skills','needs_review']
        assert [s['text'] for s in data['spans']] == [e.text for e in request.elements]
        assert settings.api_key not in json.dumps(messages)
        return reply('experience','experience','education')
    result = review.review_sections(request, local, settings=configured(), transport=provider)
    assert len(calls) == 1
    assert local.model_dump_json() == before
    sections = {s.category:s for s in result.sections}
    assert set(sections) == {'experience','education'}
    assert sections['experience'].source_heading == 'Work history'
    assert request.elements[1].text in sections['experience'].text
    assert sections['education'].text == request.elements[2].text
    blocks = [b for s in result.sections for b in s.blocks]
    assert all(b.reviewed_by_llm for b in blocks)
    assert next(b for b in blocks if b.source_element_index==1).local_section == 'skills'
    state = result.metadata['llm_review']
    assert state['status'] == 'complete' and state['reviewed_units'] == 3
    assert state['changed_units'] == 2 and state['resolved_units'] == 1
    assert result.extraction_verified is False
    review.assert_coverage(request.elements, review.source_ledger(result))


def test_llm_can_abstain_without_forcing_an_assignment(document):
    request, local = document
    result = review.review_sections(request, local, settings=configured(), transport=lambda *_:reply('experience','needs_review','needs_review'))
    assert result.status == 'needs_review'
    assert len(result.needs_review) == 2
    assert all(b.reviewed_by_llm for b in result.needs_review)
    assert result.metadata['llm_review']['reviewed_units'] == 3
    review.assert_coverage(request.elements, review.source_ledger(result))


@pytest.mark.parametrize('content', [
    '{}', 'not JSON', '{"assignments":[]}',
    '{"assignments":[["u0","experience"],["u0","skills"],["u2","education"]]}',
    '{"assignments":[["u0","experience"],["u1","made_up"],["u2","education"]]}',
    '{"assignments":[["u0","experience"],["u1","skills"],["new-id","education"]]}',
    '{"assignments":[["u0","experience"],["u1","skills"],["u2","education"]],"text":"rewritten"}',
    '{"assignments":[["u0","experience"],["u1","skills"],["u2","education"],["u3","skills"]]}',
])
def test_invalid_reply_never_partially_changes_local_blocks(document, content):
    request, local = document
    result = review.review_sections(request, local, settings=configured(), transport=lambda *_:content)
    assert result.metadata['llm_review']['status'] == 'failed'
    assert result.metadata['llm_review']['local_result_retained']
    assert result.sections == local.sections and result.needs_review == local.needs_review


@pytest.mark.parametrize('settings, expected', [
    (review.ReviewSettings(), 'disabled'),
    (review.ReviewSettings(enabled=True), 'not_configured'),
    (configured(max_units=2), 'failed'),
    (configured(max_input_chars=50), 'failed'),
    (configured(base_url='http://example.com'), 'failed'),
    (configured(base_url='https://user:secret@example.com'), 'failed'),
])
def test_disabled_missing_or_over_limit_never_sends_text(document, settings, expected):
    request, local = document
    def forbidden(*args):
        pytest.fail('Provider must not be called')
    result = review.review_sections(request, local, settings=settings, transport=forbidden)
    assert result.metadata['llm_review']['status'] == expected
    assert result.sections == local.sections and result.needs_review == local.needs_review


def test_provider_failure_does_not_leak_secrets_or_resume(document, caplog):
    request, local = document
    def broken(*_):
        raise RuntimeError('test-private-key private resume content')
    result = review.review_sections(request, local, settings=configured(), transport=broken)
    assert result.metadata['llm_review']['status'] == 'failed'
    assert 'test-private-key' not in caplog.text + result.model_dump_json()
    assert 'private resume content' not in caplog.text + result.model_dump_json()


def test_transport_uses_json_mode_without_streaming_or_redirects(monkeypatch):
    captured = {}
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self, size):
            assert size == review.MAX_RESPONSE_BYTES + 1
            return json.dumps({'choices':[{'finish_reason':'stop','message':{'content':reply('experience')}}]}).encode()
    class Opener:
        def open(self, request, timeout):
            captured.update(url=request.full_url, payload=json.loads(request.data), auth=request.get_header('Authorization'), timeout=timeout)
            return Response()
    def opener(handler):
        assert isinstance(handler, review.NoRedirect)
        return Opener()
    monkeypatch.setattr(review,'build_opener',opener)
    assert review.call_deepseek(configured(), [{'role':'user','content':'JSON'}]) == reply('experience')
    assert captured['url'] == 'https://api.deepseek.com/chat/completions'
    assert captured['payload']['response_format'] == {'type':'json_object'}
    assert captured['payload']['stream'] is False
    assert captured['auth'] == 'Bearer test-private-key'


@pytest.mark.parametrize('finish', ['length','content_filter',None])
def test_incomplete_provider_responses_are_not_applied(monkeypatch, finish):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self, size):return json.dumps({'choices':[{'finish_reason':finish,'message':{'content':reply('experience')}}]}).encode()
    class Opener:
        def open(self,*args,**kwargs):return Response()
    monkeypatch.setattr(review,'build_opener',lambda *_:Opener())
    with pytest.raises(review.ReviewError,match='incomplete_response'):
        review.call_deepseek(configured(), [])


def test_http_same_pipeline_returns_llm_reviewed_sections(document, monkeypatch):
    from local_api.routes import sections as route
    request, local = document
    monkeypatch.setattr(route,'detect_sections',lambda _:local)
    monkeypatch.setenv('DEEPSEEK_REVIEW_ENABLED','true')
    monkeypatch.setenv('DEEPSEEK_API_KEY','test-private-key')
    monkeypatch.setenv('DEEPSEEK_MODEL','test-model')
    monkeypatch.setattr(review,'call_deepseek',lambda *_:reply('experience','experience','education'))
    with TestClient(app) as client:
        response = client.post('/api/v1/resume/sections',json=request.model_dump())
        assert response.status_code == 200
        assert response.json()['metadata']['llm_review']['status'] == 'complete'
        assert {s['category'] for s in response.json()['sections']} == {'experience','education'}
        status = client.get('/api/v1/resume/review-status')
        assert status.json()['configured']
        assert 'test-private-key' not in status.text


def test_only_api_key_is_needed_for_default_model_and_endpoint(monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY','test-private-key')
    settings = review.ReviewSettings.from_env()
    assert settings.enabled
    assert settings.model == 'deepseek-flash'
    assert settings.base_url == 'https://api.deepseek.com'
    assert settings.thinking == 'disabled'
    assert 'test-private-key' not in repr(settings)
    monkeypatch.setenv('DEEPSEEK_REVIEW_ENABLED','false')
    assert review.ReviewSettings.from_env().enabled is False


@pytest.mark.parametrize('status,code', [(401,'authentication_failed'),(402,'insufficient_balance'),(403,'provider_forbidden'),(429,'rate_limited'),(503,'provider_unavailable')])
def test_provider_http_errors_have_safe_actionable_codes(monkeypatch,status,code):
    class Opener:
        def open(self,*args,**kwargs):
            raise HTTPError('https://api.deepseek.com',status,'private provider response',{},None)
    monkeypatch.setattr(review,'build_opener',lambda *_:Opener())
    with pytest.raises(review.ReviewError,match=code) as caught:
        review.call_deepseek(configured(),[])
    assert 'private provider response' not in str(caught.value)


def test_connection_check_sends_no_resume_or_prompt(monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY','test-private-key')
    def provider(settings,path,body=None):
        assert path == '/models' and body is None
        assert settings.timeout <= 15
        return {'data':[{'id':'deepseek-flash'}]}
    monkeypatch.setattr(review,'provider_json',provider)
    result=review.check_connection()
    assert result['status']=='ready'
    assert 'test-private-key' not in json.dumps(result)


def test_rejected_key_is_visible_in_connection_and_review(document,monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY','test-private-key')
    def rejected(*args,**kwargs):raise review.ReviewError('authentication_failed')
    monkeypatch.setattr(review,'provider_json',rejected)
    status=review.check_connection()
    assert status['status']=='failed'
    assert '401' in status['message'] and '.env' in status['message']
    request,local=document
    result=review.review_sections(request,local,settings=configured(),transport=rejected)
    assert result.metadata['llm_review']['error_code']=='authentication_failed'
    assert '401' in result.metadata['llm_review']['message']
    assert result.sections==local.sections and result.needs_review==local.needs_review
    assert 'test-private-key' not in result.model_dump_json()


def test_llm_splits_mixed_span_with_exact_source_coverage():
    text='Python SQL. Bachelor of Science.';cut=text.index('Bachelor')
    request=SectionRequest(elements=[ExtractedElement(type='NarrativeText',text=text,metadata={})])
    block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='needs_review',reason='Mixed source')
    local=SectionResponse(status='needs_review',sections=[],needs_review=[block],metadata={'all_source_text_preserved':True},warnings=[])
    content=json.dumps({'assignments':[['u0','skills',0,cut],['u0','education',cut,len(text)]]})
    result=review.review_sections(request,local,settings=configured(),transport=lambda *_:content)
    assert result.metadata['llm_review']['split_units']==1
    assert {s.category for s in result.sections}=={'skills','education'}
    assert ''.join(b.text for b,_ in review.source_ledger(result))==text
    review.assert_coverage(request.elements,review.source_ledger(result))


@pytest.mark.parametrize('ranges', [[(0,4),(5,10)],[(0,6),(5,10)],[(0,11)],[(0,0),(0,10)],[(-1,10)]])
def test_split_offsets_reject_gaps_overlaps_and_invalid_ranges(ranges):
    content=json.dumps({'assignments':[['u0','skills',a,b] for a,b in ranges]})
    with pytest.raises(review.ReviewError,match='invalid_assignments'):
        review.parse_decisions(content,1,{'skills':'Skills'},{'u0':10})


def test_unresolved_content_gets_one_bounded_full_context_followup(document):
    request,local=document;calls=[]
    def provider(settings,messages):
        calls.append(json.loads(messages[1]['content']))
        return reply('experience','experience','needs_review' if len(calls)==1 else 'education')
    result=review.review_sections(request,local,settings=configured(),transport=provider)
    assert len(calls)==2 and all(len(call['spans'])==3 for call in calls)
    assert result.metadata['llm_review']['pass_count']==2
    assert not result.needs_review
    review.assert_coverage(request.elements,review.source_ledger(result))


def test_full_source_inventory_and_record_hints_are_supplied(document):
    request,local=document
    def provider(settings,messages):
        data=json.loads(messages[1]['content'])
        assert [e['text'] for e in data['source_elements']]==[e.text for e in request.elements]
        assert len(data['spans'])==3 and 'record_hints' in data
        assert 'source_id' in data['spans'][0]
        return reply('experience','experience','education')
    result=review.review_sections(request,local,settings=configured(),transport=provider)
    accounting=result.metadata['source_accounting']
    assert accounting['all_source_text_preserved'] and accounting['all_meaningful_text_assigned']
    assert accounting['semantic_correctness_verified'] is False


def test_invalid_decision_recovery_is_bounded_and_preserves_source(document):
    request,local=document;calls=[]
    def provider(*args):
        calls.append(1)
        return '{"assignments":[]}' if len(calls)==1 else reply('experience','experience','education')
    result=review.review_sections(request,local,settings=configured(recovery_attempts=1),transport=provider)
    assert len(calls)==2 and result.metadata['llm_review']['status']=='complete'
    assert result.metadata['llm_review']['provider_calls']==2
    review.assert_coverage(request.elements,review.source_ledger(result))


def test_short_meaningful_text_is_not_dropped_as_artifact(document):
    request,local=document
    request.elements[2].text='R';local.needs_review[0].text='R';local.needs_review[0].end=1
    result=review.review_sections(request,local,settings=configured(recovery_attempts=0),transport=lambda *_:reply('experience','experience','needs_review'))
    assert result.metadata['source_accounting']['unresolved_meaningful_spans']==1
    assert result.metadata['source_accounting']['non_content_artifacts']==0


def test_accounting_preserves_duplicate_text_and_marks_only_explicit_artifacts():
    from local_api.services.source_accounting import account_source
    texts=['Python','Python','Page 1','R']
    elements=[ExtractedElement(type='Footer' if i==2 else 'NarrativeText',text=t,metadata={}) for i,t in enumerate(texts)]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='main',assignment='semantic',reason='source') for i,t in enumerate(texts)]
    result=SectionResponse(status='needs_review',sections=build_sections({'skills':blocks[:2]},elements),needs_review=blocks[2:],metadata={},warnings=[])
    accounting=account_source(elements,result)
    assert accounting['duplicates_excluded']==0 and accounting['assigned_meaningful_spans']==2
    assert accounting['non_content_artifacts']==1 and accounting['unresolved_meaningful_spans']==1
    assert len(accounting['outcomes'])==4


def test_failed_followup_retains_first_valid_review(document):
    request,local=document;calls=[]
    def provider(*_):
        calls.append(1)
        if len(calls)==1:return reply('experience','experience','needs_review')
        raise review.ReviewError('provider_unavailable')
    result=review.review_sections(request,local,settings=configured(),transport=provider)
    assert result.metadata['llm_review']['status']=='complete'
    assert result.metadata['llm_review']['recovery_status']=='failed'
    assert result.metadata['llm_review']['provider_calls']==2
    assert 'skills' not in {s.category for s in result.sections}
    assert result.metadata['source_accounting']['unresolved_meaningful_spans']==1


def test_reviewed_job_fields_and_embedded_projects_do_not_start_new_employers():
    from local_api.services.resume_structure import entry_groups
    texts=['Engineer | Alpha Systems | 2020 - Present','Organization','Designation','Duration',
           'Project: Warehouse System','Responsibilities: built services']
    elements=[ExtractedElement(type='Title',text=t,metadata={}) for t in texts]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='main',
             assignment='llm_reassigned',reason='reviewed',reviewed_by_llm=True,context_source_element_index=i) for i,t in enumerate(texts)]
    entries=entry_groups(blocks,'experience',elements)
    assert len(entries)==1
    assert entries[0]['block_indices']==list(range(len(texts)))
