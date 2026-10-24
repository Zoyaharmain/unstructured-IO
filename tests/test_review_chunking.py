"""Deterministic chunking contracts, budgets and atomicity; mocked providers only."""
from copy import deepcopy
from dataclasses import replace
import json
import pytest
from local_api.services.review_chunking import (ChunkError,RequestBudget,section_plan,section_decisions,
                                               audit_plan,audit_decisions,run_schema_audit,measure,run_section_chunks)
from local_api.services.llm_section_review import ReviewSettings,ReviewError,source_ledger,review_sections
from local_api.schemas.sections import SectionRequest,SectionResponse,SectionBlock,ResumeSection,SectionEntry
from local_api.schemas.extraction import ExtractedElement
from local_api.services.source_validation import validate_result
from local_api.services.schema_mapping import map_schema
from local_api.schemas.mapping import SchemaMappingRequest


def fixture(count=8, text='Built services with SQL. '):
 elements=[ExtractedElement(type='NarrativeText',text=text+str(i),page_number=1+i//4,metadata={}) for i in range(count)]
 blocks=[SectionBlock(source_element_index=i,start=0,end=len(e.text),text=e.text,page_number=e.page_number,lane='left' if i%2 else 'right',assignment='heading_context',reason='fixture') for i,e in enumerate(elements)]
 entries=[SectionEntry(entry_id='experience-1',block_indices=list(range(count)),lane='mixed',boundary_reason='same established job across pages',fields={})]
 return SectionRequest(elements=elements),SectionResponse(status='provisional',sections=[ResumeSection(category='experience',label='Experience',text='\n'.join(b.text for b in blocks),blocks=blocks,entries=entries)],needs_review=[],metadata={},warnings=[])


def settings(**kw):return replace(ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),**kw)
def respond(messages,stage='section'):
 data=json.loads(messages[1]['content'])
 return json.dumps({'assignments':[[u['id'],u['current_category']] for u in data['targets']]}) if stage=='section' else json.dumps({'checked_ids':[u['id'] for u in data['targets']],'findings':[]})


def test_conservation_determinism_layout_and_cross_page_record_context():
 req,sec=fixture();s=settings(max_units=2);before=sec.model_dump();p=section_plan(req,sec,s,document_sha256='a'*64)
 assert p==section_plan(req,sec,s,document_sha256='a'*64)
 assert len(p['chunks'])==4 and not p['blocked']
 assert p['binding']['document_sha256']=='a'*64
 assert p['owned_target_ids']==p['original_target_ids']
 units=[u for c in p['chunks'] for u in c['targets']]
 assert {u['record_key'] for u in units}=={'experience/experience-1'}
 assert {u['page'] for u in units}=={1,2} and {u['lane'] for u in units}=={'left','right'}
 assert all(c['measurement']['fits'] for c in p['chunks']) and sec.model_dump()==before


def test_global_union_has_no_duplicate_or_lost_source():
 req,sec=fixture();state={'provider_calls':0};s=settings(max_units=2)
 decisions=run_section_chunks(req,sec,s,lambda cfg,msg:respond(msg),RequestBudget(),0,state)
 assert len(decisions)==8 and state['provider_calls']==4 and state['chunking']['status']=='complete'
 assert all(parts==[(0,len(req.elements[i].text),'experience')] for i,parts in enumerate(decisions.values()))


@pytest.mark.parametrize('kind',['unknown','context','overlap','gap','offset','conflict','word'])
def test_invalid_or_nonowned_decisions_rejected(kind):
 req,sec=fixture(1);c=section_plan(req,sec,settings())['chunks'][0];sid=c['targets'][0]['id'];n=len(c['targets'][0]['text'])
 rows={'unknown':[['foreign','skills']], 'context':[['e99:0:10','skills']],
       'overlap':[[sid,'skills'],[sid,'skills']], 'gap':[[sid,'skills',1,n]],
       'offset':[[sid,'skills',0,n+1]], 'conflict':[[sid,'skills'],[sid,'education']],
       'word':[[sid,'skills',0,2],[sid,'skills',2,n]]}[kind]
 with pytest.raises((ChunkError,ValueError,ReviewError)):section_decisions(c,json.dumps({'assignments':rows}),{'skills':'Skills','education':'Education'})


def test_failed_chunk_rolls_back_entire_review():
 req,sec=fixture();before=deepcopy(sec);calls=[]
 def transport(cfg,msg):
  calls.append(msg)
  if len(calls)==2:raise RuntimeError('synthetic failure')
  return respond(msg)
 result=review_sections(req,sec,settings=settings(max_units=2),transport=transport)
 assert result.metadata['llm_review']['status']=='failed' and result.metadata['llm_review']['local_result_retained']
 assert result.sections==before.sections and not validate_result(req.elements,result)
 assert result.metadata['llm_review']['chunking']['status']=='incomplete'


def test_context_only_assignment_and_record_anchors():
 req,sec=fixture(4);sec.sections[0].entries[0].fields={'employer':[0]}
 c=section_plan(req,sec,settings(max_units=1))['chunks'][1]
 ctx=json.loads(c['messages'][1]['content'])['context'];assert ctx[0]['source_id']==f'e0:0:{len(req.elements[0].text)}'
 bad={'assignments':[[ctx[0]['source_id'],'experience']]}
 with pytest.raises(ChunkError):section_decisions(c,json.dumps(bad),{'experience':'Experience'})


def test_oversized_record_splits_without_inventing_records_and_span_splits_at_safe_offsets():
 req,sec=fixture(1,'word '*400);s=settings(max_input_chars=5000,max_input_tokens=5000,max_context_tokens=22000)
 p=section_plan(req,sec,s);assert not p['blocked'] and len(p['chunks'])>1
 targets=[u for c in p['chunks'] for u in c['targets']];assert ''.join(u['text'] for u in targets)==req.elements[0].text
 assert len({u['record_key'] for u in targets})==1
 assert all(u['source_start']==0 or req.elements[0].text[u['source_start']-1].isspace() or req.elements[0].text[u['source_start']].isspace() for u in targets)


def test_unreviewable_span_or_context_never_sends_partial_document():
 req,sec=fixture(1,'x'*10000);calls=[]
 result=review_sections(req,sec,settings=settings(max_input_chars=1000),transport=lambda *a:calls.append(a))
 assert not calls and result.metadata['llm_review']['status']=='failed'
 assert result.sections==sec.sections


def test_feedback_and_output_allowance_are_budgeted():
 req,sec=fixture(1);p=section_plan(req,sec,settings(max_input_chars=3000),feedback={'issue':'x'*4000})
 assert p['blocked']
 assert not measure(settings(max_context_tokens=16001),[{'role':'system','content':'test'}])['fits']
 assert not measure(settings(),[],17000)['fits']


def test_per_pass_document_global_budget_exhaustion():
 b=RequestBudget(max_total=2,max_document=1,max_pass=1);b.take('a',0,'section')
 with pytest.raises(ChunkError):b.take('a',1,'audit')
 b.take('b',0,'section')
 with pytest.raises(ChunkError):b.take('c',0,'audit')
 b=RequestBudget(max_total=10,max_document=10,max_pass=1);b.take('a',0,'section')
 with pytest.raises(ChunkError):b.take('a',0,'audit')


def test_audit_coverage_acknowledgement_and_incomplete_failure():
 req,sec=fixture(2)
 from local_api.services.record_relationships import annotate_relationships
 annotate_relationships(sec.sections[0])
 schema=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source='fixture')).model_dump(mode='json')
 p=audit_plan(req.elements,sec,schema,settings(max_units=2))
 assert {'populated_field','unresolved_field','source_omission_check','legacy_value'} <= {u['kind'] for c in p['chunks'] for u in c['targets']}
 c=p['chunks'][0]
 with pytest.raises(ChunkError):audit_decisions(c,json.dumps({'checked_ids':[],'findings':[]}))
 result=run_schema_audit(req.elements,sec,schema,settings(max_units=2),lambda cfg,msg:respond(msg,'audit'),budget=RequestBudget(max_total=100,max_document=100,max_pass=100))
 assert result['status']=='complete' and len(result['checked_ids'])==len(set(result['checked_ids']))
 failed=run_schema_audit(req.elements,sec,schema,settings(max_units=2),lambda cfg,msg:respond(msg,'audit'),budget=RequestBudget(max_total=1,max_document=1,max_pass=1))
 assert failed['status']=='incomplete' and failed['reason']=='request_budget_exhausted'

def test_audit_foreign_record_citation_is_rejected_even_when_other_record_in_chunk():
 req,sec=fixture(2)
 from local_api.services.record_relationships import annotate_relationships
 sec.sections[0].entries=[SectionEntry(entry_id=f'experience-{i+1}',block_indices=[i],lane='main',boundary_reason='separate job',fields={'employer':[i]}) for i in range(2)]
 annotate_relationships(sec.sections[0])
 schema=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source='fixture')).model_dump(mode='json')
 p=audit_plan(req.elements,sec,schema,settings())
 c=next(c for c in p['chunks'] if any(u['id']=='source:e0:0:26' for u in c['targets']))
 ids=[u['id'] for u in c['targets']]
 content={'checked_ids':ids,'findings':[{'field':'source:e0:0:26','issue':'wrong record quote','source_ids':['e1:0:26']}]}
 with pytest.raises(ChunkError,match='foreign_audit_source'):audit_decisions(c,json.dumps(content))


def test_unreviewable_audit_is_not_clean_and_no_calls():
 req,sec=fixture(1)
 schema=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source='fixture')).model_dump(mode='json')
 calls=[]
 result=run_schema_audit(req.elements,sec,schema,settings(max_input_chars=20),lambda *a:calls.append(a))
 assert result['status']=='incomplete' and not calls and result['coverage']['blocked']


def test_confirmed_chunk_review_preserves_entries_and_coalesces_transport_splits():
 req,sec=fixture(4);calls=[]
 def transport(cfg,msg):calls.append(msg);return respond(msg)
 result=review_sections(req,sec,settings=settings(max_units=1),transport=transport)
 assert result.metadata['llm_review']['status']=='complete' and len(calls)==4
 assert result.sections[0].entries==sec.sections[0].entries
 assert not validate_result(req.elements,result)
 req,sec=fixture(1,'word '*400)
 result=review_sections(req,sec,settings=settings(max_input_chars=5000,max_input_tokens=5000,max_context_tokens=22000),transport=transport)
 assert result.metadata['llm_review']['status']=='complete'
 assert len(result.sections[0].blocks)==1 and result.sections[0].entries==sec.sections[0].entries


def test_audit_duplicate_acknowledgements_cannot_complete():
 req,sec=fixture(1);schema=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source='fixture')).model_dump(mode='json')
 c=audit_plan(req.elements,sec,schema,settings())['chunks'][0]
 ids=[u['id'] for u in c['targets']]
 with pytest.raises(ChunkError):audit_decisions(c,json.dumps({'checked_ids':ids+[ids[0]],'findings':[]}))


def test_required_field_absence_can_be_reported_without_invented_source_quote():
 req,sec=fixture(1)
 schema=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source='fixture')).model_dump(mode='json')
 schema['meta']['missing_required_fields']=['contact.email']
 c=next(c for c in audit_plan(req.elements,sec,schema,settings())['chunks']
        if any(u['kind']=='required_field_candidate' for u in c['targets']))
 missing=next(u['id'] for u in c['targets'] if u['kind']=='required_field_candidate')
 ids=[u['id'] for u in c['targets']]
 assert audit_decisions(c,json.dumps({'checked_ids':ids,'findings':[{
     'field':missing,'issue':'No supported email value was found.','source_ids':[]}]}))


def test_required_field_candidate_accepts_own_record_evidence_not_other_record():
 req,sec=fixture(3)
 texts=['Acme Ltd','Business Development Manager','Other Systems']
 for i,text in enumerate(texts):
  req.elements[i].text=text
  sec.sections[0].blocks[i].text=text;sec.sections[0].blocks[i].end=len(text)
 sec.sections[0].text='\n'.join(texts)
 sec.sections[0].entries=[
  SectionEntry(entry_id='experience-1',block_indices=[0,1],lane='main',boundary_reason='first',fields={'employer':[0],'title':[1]}),
  SectionEntry(entry_id='experience-2',block_indices=[2],lane='main',boundary_reason='second',fields={'employer':[2]}),
 ]
 schema=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source='fixture')).model_dump(mode='json')
 schema['meta']['missing_required_fields']=['experience[0].role']
 p=audit_plan(req.elements,sec,schema,settings())
 c=next(c for c in p['chunks'] if any(u['id']=='missing:0' for u in c['targets']))
 missing=next(u for u in c['targets'] if u['id']=='missing:0')
 assert missing['record_key']=='experience/experience-1'
 assert missing['source_ids']==[f'e0:0:{len(texts[0])}',f'e1:0:{len(texts[1])}']
 ids=[u['id'] for u in c['targets']]
 assert audit_decisions(c,json.dumps({'checked_ids':ids,'findings':[{
  'field':'missing:0','issue':'A supported role exists in this record.','source_ids':[f'e1:0:{len(texts[1])}']
 }]}))
 with pytest.raises(ChunkError,match='foreign_audit_source'):
  audit_decisions(c,json.dumps({'checked_ids':ids,'findings':[{
   'field':'missing:0','issue':'This citation belongs to another record.','source_ids':[f'e2:0:{len(texts[2])}']
  }]}))


def audit_citation_chunk():
    def source(record, source_id):
        return {'id':'source:'+source_id, 'record_key':record, 'kind':'source_omission_check', 'source_ids':[source_id], 'text':'visible'}
    left, right, other = 'experience/job-1', 'experience/job-2', 'education/education-2'
    degree_record = 'education/education-1'
    targets=[
        source(degree_record, 'e22:0:37'), source(degree_record, 'e22:37:55'),
        source(left, 'e6:0:69'), source(left, 'e6:69:101'),
        source(right, 'e33:29:50'), source(other, 'e32:28:50'),
        {'id':'field:education/education-1/degree/0', 'record_key':degree_record, 'kind':'populated_field',
         'source_ids':['e22:0:37'], 'evidence':[{'source_id':'e22:0:37','quote':'Bachelor of Engineering'}]},
        {'id':'field:experience/job-1/responsibilities/0', 'record_key':left, 'kind':'populated_field',
         'source_ids':['e6:0:69'], 'evidence':[{'source_id':'e6:0:69','quote':'Working on concept'}]},
        {'id':'boundary:experience/job-1:job-2', 'record_key':'boundary:experience/job-1:job-2',
         'kind':'cross_record_association', 'source_ids':[], 'boundary_record_keys':[left,right]},
    ]
    return {'targets':targets, 'context_by_record':{}}


def audit_response(chunk, field, source_ids):
    return json.dumps({'checked_ids':[unit['id'] for unit in chunk['targets']], 'findings':[
        {'field':field, 'issue':'Synthetic source-bound audit finding.', 'source_ids':source_ids}]})


def test_populated_field_accepts_visible_same_record_continuation_only():
    chunk=audit_citation_chunk()
    assert audit_decisions(chunk, audit_response(chunk, 'field:education/education-1/degree/0', ['e22:0:37','e22:37:55']))
    context_chunk=audit_citation_chunk()
    context_chunk['targets']=[unit for unit in context_chunk['targets'] if unit['id']!='source:e22:37:55']
    context_chunk['context_by_record']={'education/education-1':['e22:37:55']}
    assert audit_decisions(context_chunk, audit_response(context_chunk, 'field:education/education-1/degree/0', ['e22:0:37','e22:37:55']))
    with pytest.raises(ChunkError,match='foreign_audit_source'):
        audit_decisions(chunk, audit_response(chunk, 'field:education/education-1/degree/0', ['e32:28:50']))
    with pytest.raises(ChunkError,match='foreign_audit_source'):
        audit_decisions(chunk, audit_response(chunk, 'field:education/education-1/degree/0', ['e22:99:111']))


def test_responsibility_and_boundary_accept_only_visible_owned_records():
    chunk=audit_citation_chunk()
    assert audit_decisions(chunk, audit_response(chunk, 'field:experience/job-1/responsibilities/0', ['e6:0:69','e6:69:101']))
    assert audit_decisions(chunk, audit_response(chunk, 'boundary:experience/job-1:job-2', ['e6:69:101','e33:29:50']))
    legacy_chunk=audit_citation_chunk()
    next(unit for unit in legacy_chunk['targets'] if unit['kind']=='cross_record_association').pop('boundary_record_keys')
    assert audit_decisions(legacy_chunk, audit_response(legacy_chunk, 'boundary:experience/job-1:job-2', ['e6:69:101','e33:29:50']))
    with pytest.raises(ChunkError,match='foreign_audit_source'):
        audit_decisions(chunk, audit_response(chunk, 'boundary:experience/job-1:job-2', ['e32:28:50']))


def test_global_budget_shared_across_two_documents_and_retry_budget():
 req,sec=fixture(4);budget=RequestBudget(max_total=3,max_document=10,max_pass=10)
 first=review_sections(req,sec,settings=settings(max_units=2),transport=lambda cfg,msg:respond(msg),_budget=budget)
 assert first.metadata['llm_review']['status']=='complete' and budget.total==2
 other_req,other_sec=fixture(4,'Built other services. ')
 second=review_sections(other_req,other_sec,settings=settings(max_units=2),transport=lambda cfg,msg:respond(msg),_budget=budget)
 assert second.metadata['llm_review']['aggregate_status']=='incomplete' and budget.total==3
 assert second.sections==other_sec.sections


def test_two_established_records_are_not_concatenated_by_chunk_planning():
 req,sec=fixture(4);sec.sections[0].entries=[SectionEntry(entry_id='job-a',block_indices=[0,2],lane='left',boundary_reason='column job'),SectionEntry(entry_id='job-b',block_indices=[1,3],lane='right',boundary_reason='column job')]
 p=section_plan(req,sec,settings(max_units=2))
 assert [{u['record_key'] for u in c['targets']} for c in p['chunks']]==[{'experience/job-a'},{'experience/job-b'}]
 state={'provider_calls':0}
 decisions=run_section_chunks(req,sec,settings(max_units=2),lambda cfg,msg:respond(msg),RequestBudget(),0,state)
 assert list(decisions)==['u0','u1','u2','u3']


def test_binding_changes_when_original_inventory_or_document_hash_changes():
 req,sec=fixture(1);p=section_plan(req,sec,settings(),document_sha256='a'*64)
 assert p['plan_sha256']!=section_plan(req,sec,settings(),document_sha256='b'*64)['plan_sha256']
 other=sec.model_copy(deep=True);other.sections[0].blocks[0].text='altered'
 with pytest.raises(Exception):section_plan(req,other,settings())


def test_record_crosswalk_reports_changes_without_inventing_record_identity():
 from local_api.services.review_chunking import ownership_crosswalk
 req,sec=fixture(2)
 changed=sec.model_copy(deep=True);changed.sections[0].category='skills';changed.sections[0].entries=[]
 rows=ownership_crosswalk(sec,changed)
 assert len(rows)==1 and rows[0]['old_record_id']=='experience-1'
 assert rows[0]['new_owners'][0]['parent']=='skills' and rows[0]['new_owners'][0]['record_id'] is None
 assert rows[0]['new_owners'][0]['source_ids']==[f'e{i}:0:26' for i in range(2)]
