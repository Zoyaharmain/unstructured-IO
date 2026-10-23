"""Contract, source, query and compatibility tests for the hierarchical extension."""
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import pytest
from pydantic import ValidationError
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse, ResumeSection, SectionBlock, SectionEntry
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.subschemas import SectionSchema
from local_api.schemas.subschema_spec import SUBSCHEMAS
from local_api.services.schema_mapping import map_schema
from local_api.services.subschema_validation import validate_hierarchy, query_subschemas
from local_api.vendor.handoff_schema.models import ResumeSchema


def education_request(lines):
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in lines]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t, page_number=1,
                           assignment='semantic', lane='source', reason='fixture') for i,t in enumerate(lines)]
    entries = [SectionEntry(entry_id=f'education-{i}', block_indices=[i], lane='source', boundary_reason='fixture',
                            fields={'qualification':[i], 'institution':[i], 'dates':[i]}) for i in range(len(lines))]
    return SchemaMappingRequest(elements=elements, sections=SectionResponse(status='provisional',
        sections=[ResumeSection(category='education', label='Education', blocks=blocks,
                                text='\n'.join(lines), entries=entries)], needs_review=[], metadata={}, warnings=[]))


def example():
    return education_request(['M.Sc. Computer Science, Example University, 2020–2022, GPA 8.5',
                              'B.Sc. Mathematics, Second University, 2017–2020, GPA 7.9'])


def values(record):
    return {a.name: [i.value for i in a.items] for a in record.attributes}


def test_registry_covers_all_detected_parents_and_legacy_children():
    anchors = json.loads(Path('local_api/data/section_anchors.json').read_text())
    assert set(anchors) <= set(SUBSCHEMAS)
    for field in ResumeSchema.model_fields:
        if field in {'contact','professional_title'}:
            assert field == 'contact' or field in SUBSCHEMAS['personal_information']
        elif field == 'total_experience_years':
            assert field in SUBSCHEMAS['summary']
        else:
            assert field in SUBSCHEMAS


def test_combined_education_decomposes_consistently_without_changing_source():
    request = example(); before = deepcopy(request.model_dump())
    mapped = map_schema(request)
    assert request.model_dump() == before
    first,second = mapped.section_schemas[0].records
    assert values(first)['institution'] == ['Example University']
    assert values(first)['degree'] == ['M.Sc.']
    assert values(first)['field_of_study'] == ['Computer Science']
    assert values(first)['start_year'] == ['2020']
    assert values(first)['graduation_year'] == ['2022']
    assert values(first)['grade_or_gpa'] == ['8.5']
    assert values(second)['institution'] == ['Second University']
    assert values(second)['degree'] == ['B.Sc.']
    # Shared-field consistency now applies the same source-backed decomposition
    # to legacy and hierarchical values; original source/request remains unchanged.
    assert mapped.data.education[0].degree == values(first)['degree'][0]
    assert ResumeSchema.model_validate(mapped.data.model_dump()) == mapped.data
    assert {ref.source_id for a in first.attributes for item in a.items for ref in item.evidence} == {f'e0:0:{len(request.elements[0].text)}'}


def test_queries_preserve_records_pointers_and_missing_values():
    out = map_schema(example())
    results = query_subschemas(out.section_schemas, 'education.institution')
    assert [r['record_id'] for r in results] == ['education-0','education-1']
    assert results[0]['items'][0]['value'] == 'Example University'
    filtered = query_subschemas(out.section_schemas, 'education.degree', 'education-1')
    assert filtered[0]['items'][0]['value'] == 'B.Sc.'
    doc = out.model_dump()
    for token in filtered[0]['items'][0]['pointer'].split('/')[1:]:
        doc = doc[int(token)] if isinstance(doc,list) else doc[token]
    assert doc == 'B.Sc.'
    absent = map_schema(education_request(['M.Sc. Computer Science']))
    assert query_subschemas(absent.section_schemas,'education.institution')[0]['status'] == 'unresolved'
    with pytest.raises(ValueError): query_subschemas(out.section_schemas,'education.invented')


def test_major_stops_before_dash_separated_institution_from_saved_resume():
    request=education_request(['Bachelor of Engineering in ECE – Gayatri Vidya Parishad, Andhra University, Visakhapatnam, India (2015)'])
    record=map_schema(request).section_schemas[0].records[0]
    assert values(record)['degree']==['Bachelor of Engineering']
    assert values(record)['field_of_study']==['ECE']
    assert values(record)['institution']==['Andhra University']


@pytest.mark.parametrize('mutation', ['unknown_child','unknown_parent','wrong_type','multiple_scalar','missing_child','empty_evidence','extra_key'])
def test_invalid_hierarchy_is_rejected(mutation):
    request = example(); raw = map_schema(request).section_schemas[0].model_dump()
    record = raw['records'][0]; attr = next(a for a in record['attributes'] if a['name']=='degree')
    if mutation=='unknown_child': attr['name']='invented'
    if mutation=='unknown_parent': raw['category']='invented'
    if mutation=='wrong_type': attr['items'][0]['value']=3.5
    if mutation=='multiple_scalar': attr['items']*=2
    if mutation=='missing_child': record['attributes'].pop()
    if mutation=='empty_evidence': attr['items'][0]['evidence']=[]
    if mutation=='extra_key': record['surprise']='bad'
    with pytest.raises(ValidationError): SectionSchema.model_validate(raw)


@pytest.mark.parametrize('mutation',['wrong_quote','foreign_block','unsupported_value','wrong_record'])
def test_evidence_is_source_bound_and_record_local(mutation):
    request = example(); raw = [s.model_dump() for s in map_schema(request).section_schemas]
    item = next(a for a in raw[0]['records'][0]['attributes'] if a['name']=='degree')['items'][0]
    if mutation=='wrong_quote': item['evidence'][0]['quote']='Invented quote'
    if mutation=='foreign_block': item['evidence'][0]['source_id']='e99:0:3'
    if mutation=='unsupported_value': item['value']='Ph.D.'
    if mutation=='wrong_record':
        b=request.sections.sections[0].blocks[1]
        item['evidence']=[{'source_id':f'e1:0:{len(b.text)}','quote':b.text}]
    with pytest.raises(ValueError): validate_hierarchy(raw,request.sections)


def test_expected_graduation_and_merged_qualifications_stay_uncertain():
    out = map_schema(education_request(['M.Sc. Computer Science, Example University, 2024–2026, expected']))
    record = out.section_schemas[0].records[0]
    assert any('Expected' in reason for reason in record.review_reasons)
    assert all(item.status=='needs_review' for a in record.attributes for item in a.items)
    merged = map_schema(education_request(['B.Sc. Physics and M.Sc. Chemistry, Example University, 2020–2024']))
    record = merged.section_schemas[0].records[0]
    assert record.review_reasons
    assert not any(a.items for a in record.attributes)
    unrecognized = map_schema(education_request(['PGDM, Example Institute, expected 2026']))
    assert any('Expected' in reason for reason in unrecognized.section_schemas[0].records[0].review_reasons)


def test_query_endpoint_reuses_mapping_and_rejects_invalid_paths():
    from fastapi.testclient import TestClient
    from local_api.app import app
    with TestClient(app) as client:
        payload = dict(example().model_dump(), query_path='education.institution', record_id='education-1')
        response = client.post('/api/v1/resume/schema/query',json=payload)
        assert response.status_code==200,response.text
        assert response.json()['provider_calls']==0
        assert response.json()['matches'][0]['items'][0]['value']=='Second University'
        payload['query_path']='education.unknown'
        assert client.post('/api/v1/resume/schema/query',json=payload).status_code==422
        definition=client.get('/api/v1/resume/schema/subschema-definition').json()
        assert set(SUBSCHEMAS)==set(definition['x-hierarchy']['parents'])


def test_existing_offline_gate_preserves_raw_and_quarantines_malformed_output():
    # Test the real evaluation safeguards; do not import the batch runner or make calls.
    spec=importlib.util.spec_from_file_location('existing_offline_gate',Path('reports/deepseek-schema-full350-20261022/schema_gate.py'))
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    raw={'data':{'contact':{'email':'a@example.com'}},'evidence':{'contact/email':[{'source_id':'e0:0:13','quote':'a@example.com'}]}}
    before=deepcopy(raw)
    candidate,normalizations,rejections=gate.normalize_evidence_pointers(raw)
    assert raw==before and candidate['data']==before['data']
    assert '/contact/email' in candidate['evidence'] and normalizations and not rejections
    parsed,failure=gate.parse_response_with_quarantine('{"data":{}}}')
    assert parsed is None and failure['automatic_repair_attempted'] is False
    incomplete=gate.validate({'data':{},'evidence':{}},[])
    assert incomplete['schema_valid'] is False


def test_email_is_not_propagated_as_a_name_and_zero_length_source_is_preserved():
    from local_api.services.section_subschemas import build_subschemas
    data = ResumeSchema(contact={'full_name':'a@example.com','email':'a@example.com','phone':''})
    block=SectionBlock(source_element_index=0,start=0,end=13,text='a@example.com',page_number=1,
                       assignment='semantic',lane='source',reason='fixture')
    empty=SectionBlock(source_element_index=1,start=0,end=0,text='',page_number=1,
                       assignment='semantic',lane='source',reason='fixture')
    sections=SectionResponse(status='provisional',sections=[ResumeSection(category='personal_information',label='Contact',blocks=[block,empty])],needs_review=[],metadata={},warnings=[])
    nested=build_subschemas(sections,data,{'candidate_resume':True})
    assert not next(a for a in nested[0].records[0].attributes if a.name=='full_name').items
    assert next(a for a in nested[0].records[0].attributes if a.name=='email').items
    assert any(b.quote=='' for b in nested[0].residual_blocks)
    assert data.contact.full_name=='a@example.com'


def test_multiple_jobs_and_responsibility_lists_keep_their_record_ids():
    from local_api.services.section_subschemas import build_subschemas
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,assignment='semantic',lane='source',reason='fixture')
            for i,t in enumerate(['Acme Ltd','Engineer','Built A.','Other Ltd','Analyst','Built B.'])]
    entries=[SectionEntry(entry_id=f'job-{i}',block_indices=list(range(i*3,i*3+3)),lane='source',boundary_reason='fixture') for i in range(2)]
    sections=SectionResponse(status='provisional',sections=[ResumeSection(category='experience',label='Jobs',blocks=blocks,entries=entries)],needs_review=[],metadata={},warnings=[])
    data=ResumeSchema(contact={'full_name':'','email':'','phone':''},experience=[{'company':'Acme Ltd','role':'Engineer','responsibilities':['Built A.']},{'company':'Other Ltd','role':'Analyst','responsibilities':['Built B.']}])
    nested=build_subschemas(sections,data,{'candidate_resume':True})
    assert [values(r)['company'] for r in nested[0].records]==[['Acme Ltd'],['Other Ltd']]
    assert [values(r)['responsibilities'] for r in nested[0].records]==[['Built A.'],['Built B.']]
    assert query_subschemas(nested,'experience.role','job-1')[0]['items'][0]['value']=='Analyst'
