"""Reduce provider output without weakening source ownership or public contracts."""
from copy import deepcopy
from dataclasses import replace
import json
import pytest
from test_llm_schema_mapping import fixture,configured
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
