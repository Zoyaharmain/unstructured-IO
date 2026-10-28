"""Provider-shape recovery and deterministic contacts without paid calls."""
import json
import pytest
from test_llm_schema_mapping import fixture, configured
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionBlock, ResumeSection, SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.subschema_spec import SUBSCHEMAS
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.subschema_validation import validate_hierarchy


@pytest.mark.parametrize('variant', ['label','object','both'])
def test_section_representation_recovery_runs_full_validation(variant):
    req,payload=fixture();row=payload['sections'][0]
    # A single-record object can represent only one existing record.
    row['records']=row['records'][:1]
    if variant in {'label','both'}:row['label']=req.sections.sections[0].label
    if variant in {'object','both'}:row['records']=row['records'][0]
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status']=='complete'
    assert out.meta['field_review']['provider_calls']==1
    assert out.data.experience[0].company=='Acme Ltd'
    validate_hierarchy(out.section_schemas,SectionResponse.model_validate(out.meta['reviewed_sections']))


@pytest.mark.parametrize('variant',['unknown_key','wrong_label','wrong_records','unsupported_value'])
def test_section_recovery_does_not_hide_unsupported_shapes_or_values(variant):
    req,payload=fixture();row=payload['sections'][0]
    row['label']=req.sections.sections[0].label
    if variant=='unknown_key':row['invented']='unknown'
    if variant=='wrong_label':row['label']='Wrong section'
    if variant=='wrong_records':row['records']='not an array'
    if variant=='unsupported_value':row['records'][0]['fields']['company'][0]['value']='Invented employer'
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status']=='failed'


def contact_fixture(text):
    block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='semantic',reason='header')
    section=ResumeSection(category='personal_information',label='Contact',text=text,blocks=[block])
    req=SchemaMappingRequest(elements=[ExtractedElement(type='NarrativeText',text=text,metadata={})],sections=SectionResponse(status='provisional',sections=[section],needs_review=[],metadata={},warnings=[]))
    fields={k:[] for k in SUBSCHEMAS['personal_information']}
    fields['full_name']=[{'value':'Candidate Name','evidence':[{'source_id':f'e0:0:{len(text)}','quote':'Candidate Name'}]}]
    payload={'sections':[{'category':'personal_information','records':[{'record_id':'contact-1','source_ids':[f'e0:0:{len(text)}'],'fields':fields,'missing':{k:'not_stated' for k,v in fields.items() if not v}}]}]}
    return req,payload


@pytest.mark.parametrize('phone',['+91 98765 43210','+44 20 7123 4567','(212) 555-0199','9876543210'])
def test_omitted_contacts_are_recovered_from_unique_literal_header(phone):
    req,payload=contact_fixture('Candidate Name | candidate+tag@example.org | '+phone)
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status']=='complete'
    assert out.data.contact.email=='candidate+tag@example.org'
    assert out.data.contact.phone==phone
    validate_hierarchy(out.section_schemas,SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_ambiguous_contacts_are_not_arbitrarily_selected():
    req,payload=contact_fixture('Candidate Name | a@example.org | b@example.org | 9876543210 | 9123456780')
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert not out.data.contact.email and not out.data.contact.phone
    assert out.meta['mapping_result']['requires_review'] is True
    attrs={a.name:a for a in out.section_schemas[0].records[0].attributes}
    assert attrs['email'].status==attrs['phone'].status=='ambiguous'


def test_email_digits_and_dates_do_not_create_phone_number():
    req,payload=contact_fixture('Candidate Name | 9876543210@example.org | 2010 - 2014')
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.data.contact.email=='9876543210@example.org'
    assert not out.data.contact.phone


def test_reference_contact_is_not_borrowed_as_candidate_contact():
    req,payload=contact_fixture('Candidate Name')
    text='Reference Person | reference@example.org | 9876543210'
    req.elements.append(ExtractedElement(type='NarrativeText',text=text,metadata={}))
    req.sections.sections.append(ResumeSection(category='references',label='References',text=text,blocks=[SectionBlock(source_element_index=1,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='semantic',reason='reference')]))
    payload['sections'].append({'category':'references','records':[]})
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status']=='complete'
    assert not out.data.contact.email and not out.data.contact.phone
