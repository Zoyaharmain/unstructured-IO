"""Synthetic, mocked-provider verification. No network or real resume transmission."""
import json
from pathlib import Path
from local_api.schemas.sections import SectionBlock, ResumeSection, SectionResponse
from scripts import llm_verify_resume_batch as batch


def prepare(tmp_path):
    source=tmp_path/'source';source.mkdir();output=tmp_path/'output';output.mkdir()
    for name in ('documents','provider-decisions','checkpoints'):(output/name).mkdir()
    elements=[{'type':'NarrativeText','text':t,'metadata':{},'page_number':1} for t in ['Python SQL','jane@example.com']]
    def block(i,assignment):
        return SectionBlock(source_element_index=i,start=0,end=len(elements[i]['text']),text=elements[i]['text'],page_number=1,lane='main',assignment=assignment,reason='synthetic fixture')
    local=SectionResponse(status='needs_review',sections=[ResumeSection(category='skills',label='Skills',text='Python SQL',blocks=[block(0,'semantic')])],needs_review=[block(1,'needs_review')],metadata={},warnings=[])
    extraction={'filename':'fixture.txt','file_type':'text/plain','strategy':'auto','text':'Python SQL\n\njane@example.com','elements':elements,'metadata':{'total_elements':2,'page_numbers':[1]}}
    (source/'fixture.json').write_text(json.dumps({'extraction':extraction,'sections':local.model_dump()}))
    row={'file':'fixture.txt','extension':'.txt','artifact':'fixture.json'}
    settings=batch.ReviewSettings(enabled=True,api_key='synthetic-not-a-real-key')
    return row,source,output,settings


def test_all_assigned_and_unassigned_spans_reviewed_and_checkpointed(tmp_path,monkeypatch):
    row,source,output,settings=prepare(tmp_path)
    def provider(config,path,body):
        spans=json.loads(body['messages'][1]['content'])['spans']
        assert [s['current_category'] for s in spans]==['skills','needs_review']
        assert [s['text'] for s in spans]==['Python SQL','jane@example.com']
        return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'assignments':[['u0','skills'],['u1','personal_information']]})}}],'usage':{'total_tokens':123}}
    monkeypatch.setattr(batch,'provider_json',provider)
    record=batch.review_document(row,source,output,tmp_path,settings)
    assert record['status']=='llm_reviewed_all_assigned'
    assert record['api_calls']==1 and record['usage']['total_tokens']==123
    assert record['invariant_errors']==[] and record['review_units']==0
    assert len(list((output/'checkpoints').glob('*.json')))==1
    artifact=json.loads((output/record['artifact']).read_text())
    assert artifact['local_sections']['needs_review'][0]['text']=='jane@example.com'
    assert not artifact['reviewed_sections']['needs_review']


def test_invalid_provider_output_is_not_reported_as_verified_complete(tmp_path,monkeypatch):
    row,source,output,settings=prepare(tmp_path)
    monkeypatch.setattr(batch,'provider_json',lambda *a,**k:{'choices':[{'finish_reason':'stop','message':{'content':'{"assignments":[]}'}}]})
    record=batch.review_document(row,source,output,tmp_path,settings)
    assert record['status']=='review_failed' and record['error_code']=='invalid_assignments'
    assert record['review_units']==1
    assert record['llm_review']['local_result_retained'] is True
