"""Inline credential inventories retain separate records and exact source evidence."""
import json
from copy import deepcopy
import pytest
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.llm_section_review import ReviewSettings

NAMES=['Project Management Professional (PMP)','Certified Information Security Manager (CISM)',
       'Certified ScrumMaster (CSM)','ITIL 4','AWS Solutions Architect','Microsoft Azure Fundamentals (AZ-900)']

@pytest.mark.parametrize('separator',[' · ',' • ','; ',' | '])
def test_inline_inventory_has_one_record_per_title(separator):
    text=separator.join(NAMES)
    elements,sections=fixture(['CERTIFICATIONS',text],{'certifications':[0,1]},[])
    before=deepcopy([e.model_dump() for e in elements])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [c.name for c in out.data.certifications]==NAMES
    assert all(c.issuer is None and c.issue_year is None for c in out.data.certifications)
    repaired=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert not validate_result(elements,repaired)
    assert ''.join(b.text for s in repaired.sections for b in s.blocks if b.source_element_index==1)==text
    assert [e.model_dump() for e in elements]==before
    again=map_schema(SchemaMappingRequest(elements=elements,sections=repaired))
    assert [c.name for c in again.data.certifications]==NAMES


def test_metadata_pipes_remain_owned_by_their_title():
    text='Cloud Architect | Issued July 2022 | Credential ID: ABC123 · Security Professional | Issued May 2024 | Credential ID: DEF456'
    elements,sections=fixture([text],{'certifications':[0]},[])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [c.name for c in out.data.certifications]==['Cloud Architect','Security Professional']
    assert [c.credential_id for c in out.data.certifications]==['ABC123','DEF456']
    assert [c.issue_year for c in out.data.certifications]==['July 2022','May 2024']

@pytest.mark.parametrize('name',[
    'Cloud, Security & Architecture / Professional – Associate',
    'Professional Certificate (Cloud · Security)',
    'Cloud Certified Solutions Architect\nAssociate',
])
def test_name_punctuation_is_not_a_record_boundary(name):
    elements,sections=fixture([name],{'certifications':[0]},[])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [c.name for c in out.data.certifications]==[name]


def test_review_cannot_merge_explicit_inline_cards():
    elements,sections=fixture([' · '.join(NAMES)],{'certifications':[0]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req);payload=local_section_payload(local,{'certifications'})
    merged=deepcopy(payload[0]['records'][0])
    merged['source_ids']=[sid for r in payload[0]['records'] for sid in r['source_ids']]
    payload[0]['records']=[merged]
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert out.meta['field_review']['status']=='complete'
    assert [c.name for c in out.data.certifications]==NAMES


def test_issuer_pipe_is_not_another_certificate():
    from local_api.services.certification_integrity import inline_credential_cuts
    assert not inline_credential_cuts('Cloud Architect | Example Institute')
    assert not inline_credential_cuts('Project Management Professional (PMP) | PMI')


def test_registry_metadata_labels_do_not_start_new_cards():
    text='Certification: Cloud Practitioner | Issuing Organization: Example | Year: 2024'
    elements,sections=fixture([text],{'certifications':[0]},[])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(out.data.certifications)==1
    assert out.data.certifications[0].name=='Cloud Practitioner'
    assert out.data.certifications[0].issue_year=='2024'
