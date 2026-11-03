"""Reduce provider output without weakening source ownership or public contracts."""
from copy import deepcopy
from dataclasses import replace
import json
import pytest
from test_llm_schema_mapping import fixture,configured
from test_batch_failure_repairs import separate_section_budget
from local_api.services.llm_schema_mapping import expand_compact_review,parse_review,map_with_field_review,messages
from local_api.services.llm_section_review import ReviewSettings


def compact(payload):
    result=deepcopy(payload);result['format']='compact_fields_v1'
    for section in result['sections']:
        for record in section['records']:
            record['fields']={k:[{'value':v['value'],'source_ids':list(dict.fromkeys(q['source_id'] for q in v['evidence']))} for v in items]
                              for k,items in record['fields'].items() if items}
    return result


def test_compact_reply_expands_to_identical_validated_public_schema():
    req,reply=fixture();wire=compact(reply)
    expanded=expand_compact_review(json.dumps(wire),req.sections)
    old=parse_review(json.dumps(reply),req.sections)[0]
    new=parse_review(expanded,req.sections)[0]
    assert [s.model_dump() for s in new]==[s.model_dump() for s in old]
    mapped=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(wire))
    assert mapped.meta['field_review']['status']=='complete'
    assert [j.company for j in mapped.data.experience]==['Acme Ltd','Beta Ltd']
    assert len(json.dumps(wire)) < len(json.dumps(reply))


def test_unreported_empty_fields_remain_unmapped_instead_of_assumed_absent():
    req,reply=fixture();wire=compact(reply)
    for row in wire['sections'][0]['records']:row.pop('missing')
    expanded=json.loads(expand_compact_review(json.dumps(wire),req.sections))
    assert expanded['sections'][0]['records'][0]['missing']['location']=='unmapped'


@pytest.mark.parametrize('mutation',['foreign_record','fabrication','heading','unknown_field'])
def test_compact_response_cannot_escape_source_validation(mutation):
    req,reply=fixture();wire=compact(reply)
    record=wire['sections'][0]['records'][0];item=record['fields']['company'][0]
    if mutation=='foreign_record':item['source_ids']=wire['sections'][0]['records'][1]['source_ids']
    if mutation=='fabrication':item['value']='Invented Company'
    if mutation=='heading':item['source_ids']=['unowned-heading']
    if mutation=='unknown_field':record['fields']['made_up_field']=[item]
    with pytest.raises(ValueError):expand_compact_review(json.dumps(wire),req.sections)


def test_legacy_missing_fields_are_still_rejected_without_compact_marker():
    req,reply=fixture();del reply['sections'][0]['records'][0]['fields']['company']
    with pytest.raises(ValueError):parse_review(expand_compact_review(json.dumps(reply),req.sections),req.sections)


def test_production_defaults_use_three_workers(monkeypatch):
    monkeypatch.delenv('DEEPSEEK_FIELD_WORKERS',raising=False)
    assert ReviewSettings.from_env().field_workers==3


def test_prompt_keeps_source_text_without_logical_block_text_duplication():
    req,_=fixture();section=req.sections.sections[0]
    prompt=messages([section]);document=json.loads(prompt[1]['content'])
    def check_structure(value):
        if isinstance(value,dict):
            assert 'text' not in value
            for child in value.values(): check_structure(child)
        elif isinstance(value,list):
            for child in value: check_structure(child)
    check_structure(document['sections'][0]['logical_blocks'])
    assert document['sections'][0]['blocks'][0]['text']==section.blocks[0].text


def test_compact_evidence_failure_retains_original_diagnostic_not_key_error():
    req,reply=fixture();wire=compact(reply)
    wire['sections'][0]['records'][0]['fields']['company'][0]['value']='Invented Company'
    mapped=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(wire))
    diagnostic=mapped.meta['field_review']['diagnostics'][-1]
    assert diagnostic['category']=='source_evidence_validation'
    assert diagnostic['code']=='invalid_or_cross_record_quote'
    assert all(d.get('exception_type')!='KeyError' for d in mapped.meta['field_review']['diagnostics'])
    assert not any(job.company=='Invented Company' for job in mapped.data.experience)


def test_compact_whitespace_variants_use_literal_owned_quotes():
    req,reply=fixture();wire=compact(reply)
    text=req.elements[0].text.replace('Acme Ltd','Acme  Ltd')
    req.elements[0].text=text
    block=req.sections.sections[0].blocks[0]
    block.text=text;block.end=len(text)
    req.sections.sections[0].text='\n'.join(b.text for b in req.sections.sections[0].blocks)
    sid=f'e0:0:{len(text)}'
    record=wire['sections'][0]['records'][0]
    old=record['source_ids'][0];record['source_ids']=[sid]
    for items in record['fields'].values():
        for item in items:item['source_ids']=[sid if i==old else i for i in item['source_ids']]
    expanded=expand_compact_review(json.dumps(wire),req.sections)
    hierarchy,_,_=parse_review(expanded,req.sections)
    company=next(a for a in hierarchy[0].records[0].attributes if a.name=='company')
    assert company.items[0].value=='Acme Ltd'
    assert company.items[0].evidence[0].quote=='Acme  Ltd'


def test_bad_compact_summary_keeps_successful_experience_batch():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import ResumeSection,SectionBlock
    from local_api.services.schema_mapping import map_schema
    from local_api.services.llm_schema_mapping import local_section_payload
    req,reply=fixture()
    text='Built reliable payment services.'
    req.elements.append(ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={}))
    req.sections.sections.append(ResumeSection(category='summary',label='Summary',text=text,blocks=[
        SectionBlock(source_element_index=2,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='semantic',reason='fixture')]))
    local=map_schema(req)
    def transport(settings,prompt):
        categories={s['category'] for s in json.loads(prompt[1]['content'])['sections']}
        if categories=={'experience'}:return json.dumps(compact(reply))
        wire=compact({'sections':local_section_payload(local,categories)})
        wire['sections'][0]['records'][0]['fields']['statements'][0]['value']='An invented summary statement'
        return json.dumps(wire)
    result=map_with_field_review(req,settings=separate_section_budget(req,recovery_attempts=0),transport=transport)
    assert result.meta['field_review']['status']=='partial'
    assert result.meta['field_review']['fallback_categories']==['summary']
    assert [j.company for j in result.data.experience]==['Acme Ltd','Beta Ltd']
    assert result.data.summary==text
    assert any(d['category']=='source_evidence_validation' and not d['recovered'] for d in result.meta['field_review']['diagnostics'])
