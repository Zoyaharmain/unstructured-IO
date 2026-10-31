"""Narrative actions never become employers; dates retain literal month evidence."""
import json
from copy import deepcopy
from datetime import datetime,timezone
import pytest
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.record_subfields import RANGE,employment_header_fields,responsibility_fragment
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.source_fragments import citations
from local_api.services.source_validation import validate_result


def test_glued_month_is_a_source_date_and_not_part_of_role():
    text='Example Banking Ltd. — Program Manager, Business TransformationSep 2013 – May 2024 (10 yrs 9 mos)'
    assert RANGE.search(text).group(1)=='Sep 2013'
    assert employment_header_fields(text)['role']=='Program Manager, Business Transformation'
    elements,sections=fixture([text],{'experience':[0]},[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    std,*_=standardize_resume_data(mapped.data,reference_date=datetime(2026,10,31,tzinfo=timezone.utc))
    assert std.experience[0].start_date=='2013-09'
    assert std.experience[0].duration=='10 years 8 months'
    assert std.experience[0].duration_months==128


@pytest.mark.parametrize('text',[
 'Applied prior employer transformation experience — process re-engineering and automation opportunity identification.',
 'Completed a diploma including an internship with Example Technologies (Jul–Dec 2024), to lead automation with greater depth.',
])
def test_action_led_prose_does_not_establish_employer(text):
    assert responsibility_fragment(text)
    assert not employment_header_fields(text)


def test_real_company_with_action_word_is_not_deleted():
    assert not responsibility_fragment('Applied Systems Ltd')
    assert employment_header_fields('Applied Systems Ltd — Software Engineer | Jan 2020 - Dec 2021')['company']=='Applied Systems Ltd'


def test_review_restores_richer_date_and_removes_glued_month_from_role():
    text='Example Banking Ltd. — Program Manager, Business TransformationSep 2013 – May 2024'
    elements,sections=fixture([text],{'experience':[0]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req)
    payload=local_section_payload(local,{'experience'})
    fields=payload[0]['records'][0]['fields']
    fields['start_date']=[{'value':'2013','evidence':citations('2013',sections.sections[0].blocks)}]
    value='Program Manager, Business TransformationSep'
    fields['role']=[{'value':value,'evidence':citations(value,sections.sections[0].blocks)}]
    mapped=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert mapped.meta['field_review']['status']=='complete'
    assert mapped.data.experience[0].start_date=='Sep 2013'
    assert mapped.data.experience[0].role=='Program Manager, Business Transformation'


def test_prose_provider_record_returns_to_its_original_employment_owner():
    from local_api.services.employment_integrity import repair_review_employment
    texts=['Analyst | Example Ltd | Jan 2020 - Dec 2021',
           'Applied prior banking experience — process re-engineering and program governance.',
           'Built additional expertise in transformation frameworks.']
    elements,sections=fixture(texts,{'experience':[0,1,2]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections);local=map_schema(req)
    # One source record; simulate a model splitting its prose into another job.
    payload=local_section_payload(local,{'experience'})
    record=payload[0]['records'][0];firstid=record['source_ids'][0]
    record['source_ids']=[firstid];record['fields']['responsibilities']=[];record['missing']['responsibilities']='unmapped'
    bogus=deepcopy(record);bogus['record_id']='bogus';bogus['source_ids']=[f'e{i}:0:{len(texts[i])}' for i in (1,2)]
    bogus['fields']['company']=[{'value':'Applied prior banking experience','evidence':citations('Applied prior banking experience',sections.sections[0].blocks)}]
    bogus['fields']['role']=[{'value':'process re-engineering and program governance.','evidence':citations('process re-engineering and program governance.',sections.sections[0].blocks)}]
    for name in ('start_date','end_date','duration'):
        bogus['fields'][name]=[];bogus['missing'][name]='unmapped'
    payload[0]['records'].append(bogus)
    mapped=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert mapped.meta['field_review']['status']=='complete'
    assert len(mapped.data.experience)==1
    assert texts[1] in mapped.data.experience[0].responsibilities
    assert texts[2] in mapped.data.experience[0].responsibilities


def test_independent_practice_area_does_not_become_an_employer():
    elements,sections=fixture(['Independent Consultant — Data Analytics','Jan 2020 - Present',
                              'Applied analytical methods to fictional demonstration services.'],{'experience':[0,1,2]},[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(mapped.data.experience)==1
    assert not mapped.data.experience[0].company
    assert mapped.data.experience[0].role=='Independent Consultant — Data Analytics'


def test_wrapped_independent_role_duty_is_complete_not_only_its_first_fragment():
    from local_api.schemas.sections import SectionBlock
    text='Completed a professional diploma including an internship with Example Technologies, to lead automation delivery.'
    elements,sections=fixture(['Independent Consultant — Data Analytics','Jan 2020 - Present',text],{'experience':[0,1,2]},[])
    section=sections.sections[0];original=section.blocks.pop();cut=text.index('Technologies')
    section.blocks.extend([original.model_copy(update={'end':cut,'text':text[:cut]}),
                           original.model_copy(update={'start':cut,'text':text[cut:]})])
    section.entries=[section.entries[0].model_copy(update={'block_indices':[0,1,2,3],'fields':{}})]
    assert not validate_result(elements,sections), validate_result(elements,sections)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert text in mapped.data.experience[0].responsibilities


def test_review_does_not_turn_independent_practice_area_into_employer():
    elements,sections=fixture(['Independent Consultant — Data Analytics | Jan 2020 - Present'],{'experience':[0]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections);local=map_schema(req)
    payload=local_section_payload(local,{'experience'});record=payload[0]['records'][0]
    blocks=sections.sections[0].blocks
    record['fields']['company']=[{'value':'Data Analytics','evidence':citations('Data Analytics',blocks)}]
    record['missing'].pop('company',None)
    record['fields']['role']=[{'value':'Independent Consultant','evidence':citations('Independent Consultant',blocks)}]
    mapped=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert mapped.meta['field_review']['status']=='complete'
    assert not mapped.data.experience[0].company
    assert mapped.data.experience[0].role=='Independent Consultant — Data Analytics'
