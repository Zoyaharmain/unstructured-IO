"""Independent paid batches overlap while preserving source validation and budgets."""
from dataclasses import replace
import json
from threading import Barrier
import pytest
from test_llm_schema_mapping import fixture,configured
from test_batch_failure_repairs import separate_section_budget
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import ResumeSection,SectionBlock
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.schema_mapping import map_schema
from local_api.services.review_chunking import new_budget


def two_batches():
    req,reply=fixture();text='Experienced software professional.'
    req.elements.append(ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={}))
    req.sections.sections.append(ResumeSection(category='summary',label='Summary',text=text,blocks=[SectionBlock(
        source_element_index=2,start=0,end=len(text),text=text,page_number=1,assignment='semantic',lane='main',reason='fixture')]))
    return req,reply


def test_independent_batches_run_concurrently_and_preserve_results():
    req,reply=two_batches();local=map_schema(req);barrier=Barrier(2);calls=[]
    settings=replace(separate_section_budget(req,recovery_attempts=0),field_workers=2)
    budget=new_budget(settings)
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry']);calls.append(categories)
        barrier.wait(timeout=5)
        return json.dumps(reply if categories == {'experience'} else {'sections':local_section_payload(local,categories)})
    mapped=map_with_field_review(req,settings=settings,transport=transport,budget=budget)
    assert mapped.meta['field_review']['status']=='complete'
    assert len(calls)==budget.total==mapped.meta['field_review']['provider_calls']==2
    assert mapped.meta['field_review']['batch_workers']==2
    assert mapped.data.summary=='Experienced software professional.'
    assert [j.company for j in mapped.data.experience]==['Acme Ltd','Beta Ltd']


def test_parallel_dispatch_respects_the_shared_request_budget():
    req,reply=two_batches();local=map_schema(req);calls=[]
    settings=replace(separate_section_budget(req,recovery_attempts=0),field_workers=2,max_total_requests=1)
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry']);calls.append(categories)
        return json.dumps(reply if categories == {'experience'} else {'sections':local_section_payload(local,categories)})
    mapped=map_with_field_review(req,settings=settings,transport=transport)
    assert len(calls)==mapped.meta['field_review']['provider_calls']==1
    assert mapped.meta['field_review']['status']=='partial'
    assert [j.company for j in mapped.data.experience]==['Acme Ltd','Beta Ltd']


def test_paid_http_errors_are_not_automatically_repeated(monkeypatch):
    from urllib.error import HTTPError
    from local_api.services.llm_section_review import provider_json,ReviewError
    calls=[]
    def failing(*args,**kwargs):
        calls.append(1)
        raise HTTPError('https://api.deepseek.com',503,'unavailable',{},None)
    monkeypatch.setattr('urllib.request.OpenerDirector.open',failing)
    with pytest.raises(ReviewError,match='provider_unavailable'):
        provider_json(configured(),'/chat/completions',{'messages':[]})
    assert len(calls)==1


def test_parallel_provider_failure_retains_the_validated_other_batch():
    from local_api.services.llm_section_review import ReviewError
    req,reply=two_batches();barrier=Barrier(2)
    settings=replace(separate_section_budget(req,recovery_attempts=0),field_workers=2)
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        barrier.wait(timeout=5)
        if categories=={'summary'}: raise ReviewError('provider_unavailable')
        return json.dumps(reply)
    mapped=map_with_field_review(req,settings=settings,transport=transport)
    assert mapped.meta['field_review']['status']=='partial'
    assert mapped.meta['field_review']['provider_calls']==2
    assert mapped.meta['field_review']['fallback_categories']==['summary']
    assert [j.company for j in mapped.data.experience]==['Acme Ltd','Beta Ltd']


@pytest.mark.parametrize('workers',[0,5,True])
def test_worker_setting_is_bounded(workers):
    from local_api.services.llm_section_review import ReviewError
    with pytest.raises(ReviewError,match='invalid_configuration'):
        replace(configured(),field_workers=workers).validate()
