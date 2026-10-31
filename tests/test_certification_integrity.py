"""One credential title owns its ID, issue/expiry dates and verification rows."""
import json
from copy import deepcopy
from datetime import datetime,timezone
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.source_fragments import citations
from local_api.services.certification_integrity import detail_row


def credential_fixture():
    texts=['Project Management Professional (PMP)® — Project Management Institute (PMI)',
           'Certification #1234567 | Issued July 2026 | Valid through July 2029',
           'Verify: example.org/credential/registry (search last name in registry)']
    elements,sections=fixture(texts,{'certifications':[0,1,2]},[],['left','left','wide'])
    return texts,elements,sections


def test_card_and_all_literal_fields_are_one_certificate():
    texts,elements,sections=credential_fixture()
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(mapped.data.certifications)==1
    cert=mapped.data.certifications[0]
    assert cert.name=='Project Management Professional (PMP)®'
    assert cert.issuer=='Project Management Institute (PMI)'
    assert cert.credential_id=='1234567' and cert.issue_year=='July 2026'
    assert cert.expiry_date=='July 2029' and cert.verification_url=='example.org/credential/registry'
    std,*_=standardize_resume_data(mapped.data,reference_date=datetime(2026,10,31,tzinfo=timezone.utc))
    assert std.certifications[0].issue_year=='2026-07' and std.certifications[0].expiry_date=='2029-07'


def test_named_certificate_after_details_remains_separate():
    texts,elements,sections=credential_fixture()
    texts.append('Cloud Professional — Example Institute')
    elements,sections=fixture(texts,{'certifications':list(range(4))},[],['left','left','wide','left'])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(mapped.data.certifications)==2
    assert mapped.data.certifications[1].name=='Cloud Professional'
    assert mapped.data.certifications[1].credential_id is None


def test_reviewed_metadata_record_is_rejoined_to_named_certificate():
    texts,elements,sections=credential_fixture();req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req);payload=local_section_payload(local,{'certifications'})
    first=payload[0]['records'][0];allids=list(first['source_ids']);first['source_ids']=[allids[0]]
    for name in ('credential_id','issue_year','expiry_date','verification_url'):
        first['fields'][name]=[];first['missing'][name]='unmapped'
    second=deepcopy(first);second['record_id']='metadata-only';second['source_ids']=allids[1:]
    second['fields']['name']=[{'value':texts[1],'evidence':citations(texts[1],sections.sections[0].blocks)}]
    second['fields']['issuer']=[];second['missing']['issuer']='unmapped'
    payload[0]['records'].append(second)
    result=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert result.meta['field_review']['status']=='complete'
    assert len(result.data.certifications)==1
    assert result.data.certifications[0].credential_id=='1234567'


def test_metadata_prefixes_are_not_certificate_titles():
    for text in ['Certification #1234','Issued July 2026','Valid through July 2029','Verify: example.org/registry']:
        assert detail_row(text)


def test_combined_heading_fragment_and_date_range_are_not_three_certificates():
    texts=['Education',' & Certification',
           'B.E. Computer Science and Engineering – Example College of Engineering, Karnataka',
           '2012–2016','AWS Certified Solutions Architect – Associate','2026–2029']
    elements,sections=fixture(texts,{'education':[0,2,3],'certifications':[1,4,5]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections)
    mapped=map_schema(req)
    assert len(mapped.data.certifications)==1
    cert=mapped.data.certifications[0]
    assert cert.name=='AWS Certified Solutions Architect – Associate'
    assert cert.issue_year=='2026' and cert.expiry_date=='2029'
    assert len(mapped.data.education)==1
    assert mapped.data.education[0].start_year=='2012'
    assert mapped.data.education[0].graduation_year=='2016'
    assert cert.issuer is None


def test_orphan_date_is_preserved_without_inventing_certificate_identity():
    elements,sections=fixture(['2026–2029'],{'certifications':[0]},[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert not mapped.data.certifications
    assert '2026–2029' in mapped.raw_sections['certifications']


def test_review_drops_heading_record_and_attaches_date_record_to_same_certificate():
    texts=[' & Certification','AWS Certified Solutions Architect – Associate','2026–2029']
    elements,sections=fixture(texts,{'certifications':[0,1,2]},[])
    req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req)
    from local_api.schemas.sections import SectionResponse
    repaired=SectionResponse.model_validate(local.meta['reviewed_sections'])
    req=req.model_copy(update={'sections':repaired})
    payload=local_section_payload(local,{'certifications'})
    first=payload[0]['records'][0];ids=list(first['source_ids'])
    first['source_ids']=[ids[0]]
    for key in ('issue_year','expiry_date'):
        first['fields'][key]=[];first['missing'][key]='unmapped'
    second=deepcopy(first);second['record_id']='date-only';second['source_ids']=[ids[-1]]
    second['fields']['name']=[{'value':'2026–2029','evidence':citations('2026–2029',repaired.sections[0].blocks)}]
    heading=deepcopy(first);heading['record_id']='heading-only';heading['source_ids']=['e0:0:'+str(len(texts[0]))]
    heading['fields']['name']=[{'value':'& Certification','evidence':citations('& Certification',repaired.sections[0].blocks)}]
    payload[0]['records']=[heading,first,second]
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert out.meta['field_review']['status']=='complete'
    assert len(out.data.certifications)==1
    assert out.data.certifications[0].issue_year=='2026' and out.data.certifications[0].expiry_date=='2029'


def test_combined_footer_rows_are_split_and_classified_using_source_geometry():
    from copy import deepcopy
    degree='B.E. Computer Science and Engineering – Example College'
    cert='AWS Certified Solutions Architect – Associate'
    texts=['Education & Certification',degree+' '+cert,'2012–2016 2026–2029']
    elements,sections=fixture(texts,{'certifications':[0,1,2]},[])
    def row(first,last,y,x1,x2):return {'start':first,'end':last,'bbox':[x1,y,x2,y+.01]}
    elements[1].type='Footer';elements[2].type='Footer'
    elements[1].metadata={'pdf_source_lines':[row(0,len(degree),.5,.05,.65),row(len(degree)+1,len(texts[1]),.6,.05,.5)]}
    elements[2].metadata={'pdf_source_lines':[row(0,9,.5,.8,.9),row(10,19,.6,.8,.9)]}
    before=deepcopy([e.model_dump() for e in elements])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(out.data.education)==len(out.data.certifications)==1
    assert out.data.education[0].start_year=='2012' and out.data.education[0].graduation_year=='2016'
    assert out.data.certifications[0].name==cert
    assert out.data.certifications[0].issue_year=='2026' and out.data.certifications[0].expiry_date=='2029'
    assert [e.model_dump() for e in elements]==before


def test_single_year_is_metadata_and_reversed_combined_heading_is_not_identity():
    from local_api.services.certification_integrity import credential_heading
    assert detail_row('2026')
    assert credential_heading('Certification & Education')
    assert credential_heading(' & Certification:')
