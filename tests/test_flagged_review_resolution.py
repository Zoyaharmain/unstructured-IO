"""Source-backed abstention regressions. All provider responses mocked/replayed."""
import json
from pathlib import Path
import pytest
from local_api.schemas.sections import SectionRequest,SectionResponse,SectionBlock
from local_api.schemas.extraction import ExtractedElement
from local_api.services.resume_sections import build_sections
from local_api.services.llm_section_review import review_sections,ReviewSettings,assert_coverage,source_ledger
from local_api.services.review_resolution import document_scope


def fixture(texts,assigned=None,types=None):
 elements=[ExtractedElement(type=(types or {}).get(i,'NarrativeText'),text=t,page_number=1,metadata={}) for i,t in enumerate(texts)]
 grouped={};pending=[]
 for i,e in enumerate(elements):
  b=SectionBlock(source_element_index=i,start=0,end=len(e.text),text=e.text,page_number=1,lane='main',assignment='needs_review',reason='test')
  if assigned and i in assigned:grouped.setdefault(assigned[i],[]).append(b)
  else:pending.append(b)
 return SectionRequest(elements=elements),SectionResponse(status='needs_review',sections=build_sections(grouped,elements),needs_review=pending,metadata={},warnings=[])


def invoke(request,local,categories,**settings):
 calls=[]
 def provider(config,messages):
  calls.append(messages);return json.dumps({'assignments':[[f'u{i}',c] for i,c in enumerate(categories)]})
 result=review_sections(request,local,settings=ReviewSettings(enabled=True,api_key='mock',model='mock',**settings),transport=provider)
 assert_coverage(request.elements,source_ledger(result));return result,calls


def test_combined_heading_resolved_at_source_word_boundary_without_second_call():
 req,local=fixture(['AWARDS & CERTIFICATIONS ','Innovation Star','Professional Certificate'],{1:'awards',2:'certifications'})
 result,calls=invoke(req,local,['needs_review','awards','certifications'])
 assert len(calls)==1 and not result.needs_review
 parts=sorted((b.start,b.end,b.text,s.category) for s in result.sections for b in s.blocks if b.source_element_index==0)
 assert ''.join(p[2] for p in parts)==req.elements[0].text
 assert [p[3] for p in parts]==['awards','certifications']


def test_combined_heading_without_supporting_sections_is_not_forced():
 req,local=fixture(['AWARDS & CERTIFICATIONS '])
 result,calls=invoke(req,local,['needs_review'],recovery_attempts=0)
 assert len(result.needs_review)==1 and result.metadata['llm_review']['resolution_status']=='unresolved_meaningful_content'


def test_declaration_with_explicit_attestation_and_signoff_is_personal_information():
 req,local=fixture(['Declaration','I do hereby declare that these facts are true.','Place: Hyderabad Date: 9 June 2026','Signature'])
 result,calls=invoke(req,local,['needs_review']*4)
 assert len(calls)==1 and not result.needs_review
 assert {s.category for s in result.sections}=={'personal_information'}


def test_declaration_keyword_without_attestation_cannot_promote_unknown_body():
 req,local=fixture(['Declaration','Unclear material about something else'])
 result,_=invoke(req,local,['needs_review']*2,recovery_attempts=0)
 assert len(result.needs_review)==2


def test_requirements_form_is_out_of_scope_not_successful_candidate_history():
 req,local=fixture(['Job title: *','Work Base Location: *','No. of Positions: *','Education and Work Experience Requirements:','Mandatory Skills:','A bachelor degree is required.'])
 assert document_scope(req.elements)['candidate_resume'] is False
 result,calls=invoke(req,local,['needs_review']*6)
 assert len(calls)==1
 assert result.status=='needs_review' and result.metadata['llm_review']['resolution_status']=='out_of_scope'
 assert all(x['reason']=='out_of_scope_job_requirements' for x in result.metadata['unresolved_details'])
 assert result.metadata['candidate_sections_are_applicable'] is False
 assert any('not candidate employment' in warning for warning in result.warnings)


def test_ordinary_resume_mentions_requirements_without_being_excluded():
 req,_=fixture(['Gathered work requirements and mandatory skills for a team.'])
 assert document_scope(req.elements)['candidate_resume'] is None


@pytest.mark.parametrize('noise,kind',[('   ','NarrativeText'),('2','Footer'),('page 2 of 3','Footer'),('','PageBreak')])
def test_noise_does_not_trigger_semantic_retry_or_needs_review_status(noise,kind):
 req,local=fixture(['Software Engineer',noise],{0:'experience'},types={1:kind})
 result,calls=invoke(req,local,['experience','needs_review'])
 assert len(calls)==1 and result.status=='provisional'
 assert result.metadata['llm_review']['remaining_meaningful_review_units']==0
 assert result.needs_review[0].text==noise


def test_meaningful_unknown_is_explicit_and_preserved_not_silently_successful():
 req,local=fixture(['C#'])
 result,calls=invoke(req,local,['needs_review'],recovery_attempts=0)
 assert result.status=='needs_review' and result.needs_review[0].text=='C#'
 assert result.metadata['unresolved_details'][0]['classification']=='UNKNOWN'


@pytest.mark.parametrize('file',['Java Aws backend.pdf','NagaVishnu.pdf','Prasad PR.pdf'])
def test_replay_real_first_response_keeps_source_and_work_education_memberships(file):
 import hashlib
 root=Path('reports/pilot-full-review-20261020-075828/deepseek');id=hashlib.sha256(file.encode()).hexdigest()[:20]
 if not (root/'documents'/(id+'.json')).exists():pytest.skip('Private pilot artifact unavailable')
 a=json.loads((root/'documents'/(id+'.json')).read_text());responses=json.loads((root/'provider-decisions'/(id+'.json')).read_text());request=SectionRequest(elements=a['extraction']['elements']);local=SectionResponse.model_validate(a['local_sections']);original=local.model_dump_json();calls=[]
 def provider(settings,messages):calls.append(messages);return responses[0]['content']
 # This frozen response uses the historical whole-document uN contract.
 # Match its explicit large character budget with large token-policy budgets;
 # never reinterpret a historical whole response as chunk-local decisions.
 result=review_sections(request,local,settings=ReviewSettings(enabled=True,api_key='mock',model='mock',max_units=1000,max_input_chars=1000000,max_input_tokens=1000000,max_context_tokens=1016000),transport=provider)
 assert len(calls)==1 and result.metadata['llm_review']['status']=='complete'
 assert_coverage(request.elements,source_ledger(result));assert local.model_dump_json()==original
 # Deterministic abstention recovery cannot change the provider's work/education source ownership.
 from local_api.services.llm_section_review import parse_decisions
 original_ledger=source_ledger(local); decisions=parse_decisions(responses[0]['content'],len(original_ledger),{s.category for s in result.sections},{f'u{i}':len(b.text) for i,(b,_) in enumerate(original_ledger)})
 expected=sorted((b.source_element_index,b.start+x,b.start+y,c) for i,(b,_) in enumerate(original_ledger) for x,y,c in decisions[f'u{i}'] if c in {'experience','education'})
 actual=sorted((b.source_element_index,b.start,b.end,c) for b,c in source_ledger(result) if c in {'experience','education'})
 assert actual==expected
 if file=='Java Aws backend.pdf':assert result.metadata['llm_review']['resolution_status']=='out_of_scope'
 else:assert result.metadata['llm_review']['remaining_meaningful_review_units']==0
