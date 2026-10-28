"""Detected candidate contacts must reach local and reviewed schemas."""
from copy import deepcopy
import json
import pytest
from test_schema_envelope_contacts import contact_fixture
from test_llm_schema_mapping import configured
from local_api.schemas.sections import SectionBlock, ResumeSection, SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.schemas.subschema_spec import SUBSCHEMAS


def add(req,text,category=None):
    i=len(req.elements)
    req.elements.append(ExtractedElement(type='NarrativeText',text=text,metadata={}))
    b=SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='needs_review' if category is None else 'semantic',reason='detected')
    if category is None:req.sections.needs_review.append(b)
    else:req.sections.sections.append(ResumeSection(category=category,label=category,text=text,blocks=[b]))
    return b


@pytest.mark.parametrize('category',[None,'skills','summary'])
def test_detected_labelled_contacts_are_assigned_without_llm(category):
    req,_=contact_fixture('Candidate Name')
    email=add(req,'Email-ID: candidate+tag@example.org',category)
    phone=add(req,'Contact Details: +91 98765 43210',None)
    before=deepcopy(req.model_dump())
    out=map_schema(req)
    assert req.model_dump()==before
    assert out.data.contact.email=='candidate+tag@example.org'
    assert out.data.contact.phone=='+91 98765 43210'
    normalized=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert validate_result(req.elements,normalized)==[]
    assert len(normalized.needs_review)==0
    person=next(s for s in normalized.sections if s.category=='personal_information')
    assert any(b.text==email.text and b.start==email.start and b.end==email.end for b in person.blocks)
    validate_hierarchy(out.section_schemas,normalized)


def test_reference_contacts_and_contact_in_job_prose_are_not_reassigned():
    req,_=contact_fixture('Candidate Name')
    add(req,'Handled email notifications for operations.',None)
    add(req,'Reference: ref@example.org | 9876543210','references')
    add(req,'Email-ID: another-reference@example.org',None)
    out=map_schema(req)
    assert not out.data.contact.email and not out.data.contact.phone
    assert 'reviewed_sections' not in out.meta


def test_field_review_prompt_and_final_schema_use_recovered_contact_owner():
    req,_=contact_fixture('Candidate Name')
    add(req,'Email-ID: candidate@example.org')
    add(req,'Contact No: 9876543210')
    def provider(settings,prompt):
        context=json.loads(prompt[1]['content'])
        parent=next(s for s in context['sections'] if s['category']=='personal_information')
        assert len(parent['blocks'])==3
        fields={k:[] for k in SUBSCHEMAS['personal_information']}
        fields['full_name']=[{'value':'Candidate Name','evidence':[{'source_id':parent['blocks'][0]['source_id'],'quote':'Candidate Name'}]}]
        return json.dumps({'sections':[{'category':'personal_information','records':[{'record_id':'person-1','source_ids':[b['source_id'] for b in parent['blocks']],'fields':fields,'missing':{k:'not_stated' for k,v in fields.items() if not v}}]}]})
    out=map_with_field_review(req,settings=configured(recovery_attempts=0),transport=provider)
    assert out.meta['field_review']['status']=='complete'
    assert out.data.contact.email=='candidate@example.org'
    assert out.data.contact.phone=='9876543210'
    validate_hierarchy(out.section_schemas,SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_joined_phone_email_uses_explicit_country_prefix_without_changing_source():
    from local_api.services.contact_sections import contact_values
    req,_=contact_fixture('Candidate Name | +91 7982016518avmsv1996@gmail.com')
    values=contact_values(req.sections.sections[0].blocks)
    assert values['email']=={'avmsv1996@gmail.com'}
    assert values['phone']=={'+91 7982016518'}
    out=map_schema(req)
    assert out.data.contact.email=='avmsv1996@gmail.com'
    assert out.data.contact.phone=='+91 7982016518'


def test_inline_contact_value_mistaken_for_heading_is_not_discarded():
    req,_=contact_fixture('Email-ID: candidate@example.org | Phone: 9876543210')
    req.sections.sections[0].blocks[0].assignment='structural_heading'
    out=map_schema(req)
    assert out.data.contact.email=='candidate@example.org'
    assert out.data.contact.phone=='9876543210'
    sections=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert len(sections.sections[0].blocks)==1
    assert validate_result(req.elements,sections)==[]


def test_header_phone_prefixed_with_layout_pipe_is_still_candidate_contact():
    req,_=contact_fixture('Candidate Name')
    original=add(req,'| +91-7411300272')
    out=map_schema(req)
    assert out.data.contact.phone=='+91-7411300272'
    revised=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert any(b.text==original.text for s in revised.sections for b in s.blocks)
    assert validate_result(req.elements,revised)==[]
