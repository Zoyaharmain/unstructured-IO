"""Phase 1: body continuations and semantic recovery progress; no live provider."""
from copy import deepcopy
import pytest
from local_api.schemas.sections import SectionResponse,SectionBlock,ResumeSection
from local_api.services.record_relationships import field_kinds
from scripts.single_resume_pipeline import fingerprint

@pytest.mark.parametrize('text',[
 'delivering high-integrity data feeds to downstream Fund accounting systems.',
 'Delivering validated data to downstream accounting systems',
 '• delivering reports for regulatory systems.',
])
def test_delivering_clause_is_responsibility(text):
 assert field_kinds(text,'experience')==['responsibilities']

@pytest.mark.parametrize('text',['Persistent Systems','Delivering Systems','Delivering Systems Ltd','Company: Delivering Systems','Engineer | Persistent Systems | 2020 - 2024','BNP Paribas ISPL'])
def test_company_headers_are_preserved(text):
 assert 'employer' in field_kinds(text,'experience')

@pytest.mark.parametrize('text',['systems','Delivering results','Data for systems','delivering systems','Systems for Everyone Ltd'])
def test_no_broad_delivering_or_systems_rule(text):
 assert field_kinds(text,'experience')!=['responsibilities']

def fixture():
 block=SectionBlock(source_element_index=0,start=0,end=3,text='SQL',page_number=1,assignment='semantic',reason='initial',lane='main')
 sections=SectionResponse(status='provisional',sections=[ResumeSection(category='skills',label='Skills',blocks=[block])],needs_review=[],metadata={},warnings=[])
 schema={'data':{'skills':['SQL']},'section_schemas':[{'category':'skills','label':'Skills','records':[{'record_id':'skills','source_ids':['e0:0:3'],'review_reasons':[],'attributes':[{'name':'technical_skills','status':'mapped','items':[{'value':'SQL','status':'source_supported','evidence':[{'source_id':'e0:0:3','quote':'SQL'}]}]}]}],'residual_blocks':[]}]}
 return sections,schema

@pytest.mark.parametrize('change',['value','record_id','ownership','quote','evidence_id','parent','residual'])
def test_meaningful_hierarchy_state_changes_progress(change):
 sec,before=fixture();after=deepcopy(before);parent=after['section_schemas'][0];record=parent['records'][0];item=record['attributes'][0]['items'][0]
 if change=='value':item['value']='Python'
 elif change=='record_id':record['record_id']='skills-2'
 elif change=='ownership':record['source_ids']=['e1:0:3']
 elif change=='quote':item['evidence'][0]['quote']='SQ'
 elif change=='evidence_id':item['evidence'][0]['source_id']='e1:0:3'
 elif change=='parent':parent['category']='experience'
 else:parent['residual_blocks']=[{'source_id':'e0:0:3','quote':'SQL'}]
 assert fingerprint(sec,before)!=fingerprint(sec,after)

def test_diagnostic_changes_do_not_keep_feedback_alive():
 sec,before=fixture();other=sec.model_copy(deep=True);after=deepcopy(before)
 other.metadata={'retry_count':100,'warning_count':999};other.warnings=['new warning'];other.sections[0].blocks[0].reason='different explanation'
 after['meta']={'warnings':['new diagnostic'],'provider_calls':999}
 after['section_schemas'][0]['records'][0]['review_reasons']=['different diagnostic']
 assert fingerprint(sec,before)==fingerprint(other,after)

def test_entry_explanations_do_not_count_but_field_ownership_does():
 from local_api.schemas.sections import SectionEntry
 sec,schema=fixture()
 sec.sections[0].entries=[SectionEntry(entry_id='skills-1',block_indices=[0],lane='main',boundary_reason='source',fields={'title':[0]})]
 other=sec.model_copy(deep=True);other.sections[0].entries[0].boundary_reason='new explanation';other.sections[0].entries[0].review_reasons=['diagnostic only']
 assert fingerprint(sec,schema)==fingerprint(other,schema)
 other.sections[0].entries[0].fields={'responsibilities':[0]}
 assert fingerprint(sec,schema)!=fingerprint(other,schema)

def test_continuation_keeps_its_existing_record_and_company_header():
 from local_api.schemas.sections import SectionEntry
 from local_api.services.record_relationships import annotate_relationships
 texts=['Persistent Systems','BNP Paribas ISPL','Drove BA scope for a pricing platform,','delivering high-integrity data feeds to downstream Fund accounting systems.']
 blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='main',assignment='heading_context',reason='saved context') for i,t in enumerate(texts)]
 section=ResumeSection(category='experience',label='Experience',blocks=blocks,entries=[SectionEntry(entry_id='experience-1',block_indices=[0],lane='main',boundary_reason='header'),SectionEntry(entry_id='experience-2',block_indices=[1,2,3],lane='main',boundary_reason='header')])
 annotate_relationships(section)
 assert section.entries[0].fields['employer']==[0]
 assert section.entries[1].fields['employer']==[1]
 assert section.entries[1].fields['responsibilities']==[2,3]
 assert [e.block_indices for e in section.entries]==[[0],[1,2,3]]
