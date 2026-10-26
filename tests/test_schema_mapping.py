from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from local_api.app import app
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse,SectionBlock,ResumeSection,SectionEntry
from local_api.schemas.extraction import ExtractedElement
from local_api.services.schema_mapping import map_schema


def sample():
 specs=[('personal_information','Alex Morgan'),('personal_information','alex@example.com'),
 ('skills','Python, C#, C++, SQL, BespokeTool'),
 ('experience','Acme Ltd | Software Engineer | Jan 2020 - Dec 2022'),
 ('experience','Software Engineer'),('experience','Implemented the source system.'),
 ('education','BSc Computer Science'),('education','Example University'),('education','2019'),
 ('awards','Regional community prize')]
 elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={}) for category,text in specs]
 grouped={}
 for i,(cat,text) in enumerate(specs):grouped.setdefault(cat,[]).append(SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='source',assignment='semantic',reason='source'))
 sections=[ResumeSection(category=k,label=k,blocks=bs,text='\n'.join(b.text for b in bs)) for k,bs in grouped.items()]
 for s in sections:
  if s.category=='experience':s.entries=[SectionEntry(entry_id='job-1',block_indices=[0,1,2],lane='source',boundary_reason='source',fields={'employer':[0],'title':[1],'dates':[0],'responsibilities':[2]})]
  if s.category=='education':s.entries=[SectionEntry(entry_id='edu-1',block_indices=[0,1,2],lane='source',boundary_reason='source',fields={'qualification':[0],'institution':[1],'dates':[2]})]
 return SchemaMappingRequest(elements=elements,sections=SectionResponse(status='provisional',sections=sections,needs_review=[],metadata={},warnings=[]))


def test_mapping_preserves_records_source_and_unknowns_without_network(monkeypatch):
 import socket
 monkeypatch.setenv('OPENAI_API_KEY','must-not-be-used')
 monkeypatch.setattr(socket.socket,'connect',lambda *args:pytest.fail('Mapping made a network call'))
 req=sample();before=deepcopy(req.model_dump());out=map_schema(req)
 assert req.model_dump()==before
 assert out.data.contact.full_name=='Alex Morgan' and out.data.contact.email=='alex@example.com'
 assert out.data.contact.phone=='' and out.data.languages==[] and out.data.total_experience_years is None
 assert out.data.experience[0].company=='Acme Ltd'
 assert out.data.experience[0].role=='Software Engineer'
 assert out.data.experience[0].start_date=='Jan 2020' and out.data.experience[0].end_date=='Dec 2022'
 assert out.data.experience[0].responsibilities==['Implemented the source system.']
 assert out.data.education[0].institution=='Example University'
 assert out.data.education[0].graduation_year=='2019'
 assert {'C#','C++','BespokeTool'}<=set(out.data.skills.all_skills)
 assert 'contact.phone' in out.meta['missing_required_fields']
 assert any(b['text']=='Regional community prize' for b in out.meta['unmapped_blocks'])
 assert out.meta['field_evidence']['experience[0].company'][0].startswith('e3:0:')


def test_record_boundaries_do_not_merge_or_borrow_fields():
 req=sample();sec=next(s for s in req.sections.sections if s.category=='experience')
 sec.entries=[SectionEntry(entry_id='job-1',block_indices=[0],lane='source',boundary_reason='first',fields={'employer':[0],'dates':[0]}),SectionEntry(entry_id='job-2',block_indices=[1,2],lane='source',boundary_reason='second',fields={'title':[1],'responsibilities':[2]})]
 out=map_schema(req)
 assert len(out.data.experience)==2
 assert out.data.experience[0].role==''
 assert out.data.experience[1].company=='' and out.data.experience[1].duration is None
 assert out.data.experience[1].role=='Software Engineer'


@pytest.mark.parametrize('change',['text','canonical','ownership','field','gap'])
def test_rejects_changed_source_and_invalid_record_binding(change):
 req=sample();sec=next(s for s in req.sections.sections if s.category=='experience')
 if change=='text':sec.blocks[0].text='altered'
 if change=='canonical':sec.text='altered'
 if change=='ownership':sec.entries.append(sec.entries[0].model_copy(update={'entry_id':'duplicate'}))
 if change=='field':sec.entries[0].fields['employer']=[99]
 if change=='gap':sec.blocks[0].start=1
 with pytest.raises(ValueError):map_schema(req)


def test_no_education_or_english_or_experience_invented_for_skills_only():
 text='Python, SQL';e=ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={});b=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='source',assignment='semantic',reason='source')
 req=SchemaMappingRequest(elements=[e],sections=SectionResponse(status='provisional',sections=[ResumeSection(category='skills',label='Skills',text=text,blocks=[b])],needs_review=[],metadata={},warnings=[]))
 out=map_schema(req)
 assert out.data.education==out.data.experience==out.data.languages==[]
 assert out.data.contact.full_name==out.data.contact.email==out.data.contact.phone==''


def test_real_http_contract_and_validation():
 with TestClient(app) as client:
  assert client.get('/api/v1/resume/schema/definition').json()['title']=='ResumeSchema'
  spec=client.get('/api/v1/resume/schema/mapping').json()
  assert spec['target_model']=='ResumeSchema' and spec['integration']['provider_calls']==0
  response=client.post('/api/v1/resume/schema',json=sample().model_dump())
  assert response.status_code==200,response.text
  assert response.json()['extraction_mode']=='existing_blocks_schema_mapping'
  data=sample().model_dump();data['sections']['sections'][0]['blocks'][0]['text']='changed'
  assert client.post('/api/v1/resume/schema',json=data).status_code==422
  assert client.post('/api/v1/resume/schema',json={'text':'do not reparse raw text'}).status_code==422


def test_role_first_header_is_not_mapped_as_company():
 req=sample();text='Software Engineer | Acme Ltd | Jan 2020 - Dec 2022';req.elements[3].text=text
 sec=next(s for s in req.sections.sections if s.category=='experience');sec.blocks[0].text=text;sec.blocks[0].end=len(text);sec.text='\n'.join(b.text for b in sec.blocks)
 out=map_schema(req)
 assert out.data.experience[0].company=='Acme Ltd'
 assert out.data.experience[0].role=='Software Engineer'


def test_action_with_executive_is_responsibility_not_competing_role_title():
 from local_api.services.record_relationships import annotate_relationships
 texts=['Turn Turtle Private Limited','Buisness Development Manager','Expanded Client network through executive outreach and refferals']
 elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={}) for text in texts]
 blocks=[SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='source',assignment='semantic',reason='source') for i,text in enumerate(texts)]
 experience=ResumeSection(category='experience',label='Experience',blocks=blocks,text='\n'.join(texts),entries=[
  SectionEntry(entry_id='experience-1',block_indices=[0,1,2],lane='source',boundary_reason='source')])
 annotate_relationships(experience)
 assert experience.entries[0].fields['title']==[1]
 assert experience.entries[0].fields['responsibilities']==[2]
 request=SchemaMappingRequest(elements=elements,sections=SectionResponse(status='provisional',sections=[experience],needs_review=[],metadata={},warnings=[]))
 out=map_schema(request)
 assert out.data.experience[0].role=='Buisness Development Manager'
 assert out.data.experience[0].responsibilities==[texts[2]]


def test_supervisor_header_is_role_while_took_a_lead_is_responsibility():
 from local_api.services.record_relationships import annotate_relationships
 texts=['Jagran Solutions Pvt Ltd', 'Sales Team Supervisor', 'Took a lead in the Karnataka team in achieving their targets.']
 elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={}) for text in texts]
 blocks=[SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='source',assignment='semantic',reason='source') for i,text in enumerate(texts)]
 experience=ResumeSection(category='experience',label='Experience',blocks=blocks,text='\n'.join(texts),entries=[
  SectionEntry(entry_id='experience-1',block_indices=[0,1,2],lane='source',boundary_reason='source')])
 annotate_relationships(experience)
 assert experience.entries[0].fields['title']==[1]
 assert experience.entries[0].fields['responsibilities']==[2]
 out=map_schema(SchemaMappingRequest(elements=elements,sections=SectionResponse(status='provisional',sections=[experience],needs_review=[],metadata={},warnings=[])))
 assert out.data.experience[0].role==texts[1]
 assert out.data.experience[0].responsibilities==[texts[2]]


def test_named_school_stays_institution_when_no_credential_is_stated():
 from local_api.services.record_relationships import annotate_relationships
 texts=['PCME', '2001 - 2011', 'ST.LOURDES HIGH SCHOOL']
 elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={}) for text in texts]
 blocks=[SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='source',assignment='semantic',reason='source') for i,text in enumerate(texts)]
 education=ResumeSection(category='education',label='Education',blocks=blocks,text='\n'.join(texts),entries=[
  SectionEntry(entry_id='education-1',block_indices=[0,1,2],lane='source',boundary_reason='source')])
 annotate_relationships(education)
 assert 'qualification' not in education.entries[0].fields
 assert education.entries[0].fields['institution']==[2]
 out=map_schema(SchemaMappingRequest(elements=elements,sections=SectionResponse(status='provisional',sections=[education],needs_review=[],metadata={},warnings=[])))
 assert out.data.education[0].institution==texts[2]
 assert out.data.education[0].degree==''
 assert 'education[0].degree' in out.meta['missing_required_fields']


def test_dated_organization_without_suffix_maps_own_employer_and_current_date():
 req=sample();text='NTT Data, Noida (November 2022- Currently working)';req.elements[3].text=text
 sec=next(s for s in req.sections.sections if s.category=='experience');sec.blocks[0].text=text;sec.blocks[0].end=len(text);sec.text='\n'.join(b.text for b in sec.blocks)
 out=map_schema(req)
 assert out.data.experience[0].company=='NTT Data'
 assert out.data.experience[0].end_date=='Currently working'


@pytest.mark.parametrize('merged', [False, True])
def test_candidate_name_and_french_location_have_schema_evidence(merged):
 name = 'Manjunath MURUGAN'
 title = 'Senior Business Analyst | Financial Markets'
 lines = ([name + ' ' + title] if merged else [name, title]) + [
  'Noisy-le-Grand, France | 9176398910 | manjunathmurugan50@gmail.com LinkedIn:',
  'www.linkedin.com/in/profilemanjunathmurugan',
  'Fully Authorized to work in France | Availability - Immediate']
 elements = [ExtractedElement(type='NarrativeText', text=text, page_number=1, metadata={}) for text in lines]
 blocks = [SectionBlock(source_element_index=i, start=0, end=len(text), text=text, page_number=1, lane='source', assignment='semantic', reason='source') for i, text in enumerate(lines)]
 req = SchemaMappingRequest(elements=elements, sections=SectionResponse(status='provisional', sections=[ResumeSection(category='personal_information', label='Personal information', blocks=blocks, text='\n'.join(lines))], needs_review=[], metadata={}, warnings=[]))
 out = map_schema(req)
 assert out.data.contact.full_name == name
 assert out.data.professional_title == title
 assert out.data.contact.location == 'Noisy-le-Grand, France'
 assert out.data.contact.email == 'manjunathmurugan50@gmail.com'
 assert out.data.contact.phone == '9176398910'
 assert out.data.contact.linkedin_url == 'www.linkedin.com/in/profilemanjunathmurugan'
 attrs = {a.name: a for a in out.section_schemas[0].records[0].attributes}
 for field, expected in [('full_name', name), ('location', 'Noisy-le-Grand, France')]:
  assert attrs[field].status == 'mapped'
  assert attrs[field].items[0].evidence[0].quote == expected
 assert attrs['github_url'].status == attrs['portfolio_url'].status == 'unresolved'


def test_explicit_field_review_http_keeps_contracts_aligned(monkeypatch):
 from local_api.services import llm_schema_mapping as reviewed
 from test_llm_schema_mapping import fixture, configured
 import json
 req, reply = fixture()
 original = reviewed.map_with_field_review
 calls = []
 def mapping(request):
  calls.append(request.review_fields)
  return original(request, settings=configured(), transport=lambda *_: json.dumps(reply))
 monkeypatch.setattr(reviewed, 'map_with_field_review', mapping)
 with TestClient(app) as client:
  data = req.model_dump() | {'review_fields': True}
  response = client.post('/api/v1/resume/schema', json=data)
 assert response.status_code == 200, response.text
 out = response.json()
 assert calls == [True]
 assert out['meta']['field_review']['status'] == 'complete'
 assert out['data']['experience'][1]['company'] == 'Beta Ltd'
 assert out['field_index']['experience.company'][1]['items'][0]['value'] == 'Beta Ltd'
 assert out['field_index']['experience.location'][0]['status'] == 'not_stated'
