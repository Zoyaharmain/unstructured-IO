"""Boundary decisions use source/layout evidence, never fixture names."""
from dataclasses import replace
from types import MappingProxyType
import json
import pytest

from local_api.services.source_ownership import SourceSpan, Owner, Ownership, apply_operations
from local_api.services.section_boundaries import boundary_errors


def ledger(lanes=None, boxes=None, pages=None):
    texts = ['Old heading', 'Old item', 'New unfamiliar heading', 'New title', 'Wrapped detail', 'Next heading', 'Other item']
    spans = tuple(SourceSpan(f'e{i}:0:{len(t)}', i, 0, len(t), t,
                            (pages or [1]*7)[i], i, (lanes or ['main']*7)[i],
                            '{"lines":[]}', 'NarrativeText', (boxes or [None]*7)[i])
                  for i,t in enumerate(texts))
    owners = {s.source_id:Owner('certifications' if i<5 else 'awards',
              None if i in {0,5} else f'certifications@{spans[3].source_id}' if i in {3,4} else f'certifications@{s.source_id}',
              ('title',) if i==3 else (), heading=i in {0,5}) for i,s in enumerate(spans)}
    return Ownership('digest',spans,MappingProxyType(owners),MappingProxyType({}))


def correct(state):
    return apply_operations(state,[{'op':'heading','section':'projects',
        'source_ids':[state.spans[2].source_id]}],{'certifications','projects','awards'})


def test_single_column_moves_whole_record_and_stops_at_next_heading():
    state=ledger();out=correct(state)
    for i in [3,4]:
        o=out.owners[state.spans[i].source_id]
        assert o.section=='projects' and o.record==f'projects@{state.spans[3].source_id}'
        assert o.boundary_source==state.spans[2].source_id
    assert out.owners[state.spans[1].source_id]==state.owners[state.spans[1].source_id]
    assert out.owners[state.spans[6].source_id]==state.owners[state.spans[6].source_id]
    assert out.spans==state.spans and not boundary_errors(out)
    assert correct(out).owners==out.owners


def test_two_columns_preserve_separate_sidebar():
    boxes=[(.05,.1,.3,.13),(.05,.2,.3,.23),(.55,.3,.85,.33),(.55,.4,.85,.43),(.05,.4,.3,.43),(.55,.6,.85,.63),(.55,.7,.85,.73)]
    state=ledger(['left','left','right','right','left','right','right'],boxes)
    # Independent column content is its own record.
    owners=dict(state.owners);owners[state.spans[4].source_id]=Owner('certifications','sidebar')
    state=replace(state,owners=MappingProxyType(owners));out=correct(state)
    assert out.owners[state.spans[3].source_id].section=='projects'
    assert out.owners[state.spans[4].source_id]==state.owners[state.spans[4].source_id]


def test_mixed_layout_full_width_paragraph_establishes_region():
    boxes=[(.4,.1,.8,.13),(.4,.2,.8,.23),(.34,.3,.71,.33),(.06,.4,.35,.43),(.06,.44,.96,.5),(.45,.6,.7,.63),(.1,.7,.9,.73)]
    state=ledger(['right','right','right','left','wide','right','wide'],boxes)
    # Different physical rows of one extracted paragraph.
    spans=list(state.spans);spans[4]=replace(spans[4],element=3)
    state=replace(state,spans=tuple(spans));out=correct(state)
    assert all(out.owners[state.spans[i].source_id].section=='projects' for i in [3,4])


@pytest.mark.parametrize('lanes,pages', [(['unknown']*7,[1]*7),(['main']*7,[1,1,1,2,2,2,2])])
def test_ambiguous_scope_requires_review(lanes,pages):
    state=ledger(lanes=lanes,pages=pages);out=correct(state)
    for i in [3,4]:
        o=out.owners[state.spans[i].source_id]
        assert o.section=='certifications' and o.status=='needs_review'
    assert not boundary_errors(out)


def test_supported_spans_detach_without_moving_the_contaminated_record():
    state=ledger();owners=dict(state.owners)
    owners[state.spans[1].source_id]=replace(owners[state.spans[1].source_id],record=owners[state.spans[3].source_id].record)
    state=replace(state,owners=MappingProxyType(owners));out=correct(state)
    assert out.owners[state.spans[3].source_id].status=='needs_review'
    assert out.owners[state.spans[3].source_id].section=='projects'
    assert out.owners[state.spans[3].source_id].record is None
    assert out.owners[state.spans[1].source_id]==state.owners[state.spans[1].source_id]


def test_identity_evidence_prevents_cross_category_transfer():
    state=ledger();owners=dict(state.owners)
    owners[state.spans[3].source_id]=replace(owners[state.spans[3].source_id],fields=('issuer',))
    state=replace(state,owners=MappingProxyType(owners));out=correct(state)
    assert out.owners[state.spans[3].source_id].status=='needs_review'


def test_boundary_validator_rejects_later_restoration_of_old_ownership():
    state=ledger();out=correct(state);owners=dict(out.owners)
    sid=state.spans[3].source_id;owners[sid]=replace(owners[sid],section='certifications')
    assert boundary_errors(replace(out,owners=MappingProxyType(owners)))==['unresolved_section_boundary_conflict']


def test_heading_and_dependent_assignment_share_one_transaction():
    state=ledger();sid=state.spans[3].source_id;head=state.spans[2].source_id
    out=apply_operations(state,[{'op':'heading','source_ids':[head],'section':'projects'},
        {'op':'assign','source_ids':[head],'section':'projects','record':None,'fields':[]},
        {'op':'assign','source_ids':[sid],'section':'projects','record':f'projects@{sid}','fields':['title']}],{'projects','certifications','awards'})
    assert out.owners[sid].section=='projects'
    assert out.owners[head].heading
    assert not boundary_errors(out)


def test_unfamiliar_styled_title_stops_explicit_context_without_lowering_thresholds():
    from local_api.services.resume_sections import SectionEngine, Unit
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionRequest
    texts=['SKILLS','Uncharted Portfolio','Built an independent research system using reliable services.']
    elements=[ExtractedElement(text=t,type='Title' if i==1 else 'NarrativeText',page_number=1,metadata={}) for i,t in enumerate(texts)]
    engine=object.__new__(SectionEngine)
    engine.units=lambda _:([Unit(i,0,len(t),t,'main',i==1) for i,t in enumerate(texts)],False)
    engine.encode_texts=lambda _: [[0]]*3
    class Scores:
        purity=1
        def __init__(self,values):self.values=values
        def score(self,*args,**kwargs):return self.values
    engine.headings=Scores([('skills',0,.95,.3),('summary',0,.2,-.1),('summary',0,.1,.01)])
    engine.content=Scores([('skills',0,.8,.3),('summary',0,.2,.01),('projects',0,.93,.4)])
    out=engine._detect(SectionRequest(elements=elements))
    assert any(b.source_element_index==1 and b.boundary_candidate for b in out.needs_review)
    assert any(b.source_element_index==2 and b.pending_boundary_id for b in out.needs_review)


def test_heading_correction_survives_materialization_schema_mapping_and_source_validation():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock,SectionEntry,ResumeSection,SectionResponse
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.source_ownership import snapshot,finalize_ownership,validated_ownership_state
    from local_api.services.llm_section_review import ReviewSettings
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    texts=['CERTIFICATIONS','Cloud credential','Independent Work','Telemetry service','Built reliable reporting.','AWARDS','Delivery distinction']
    elements=[ExtractedElement(text=t,type='NarrativeText',page_number=1,metadata={}) for t in texts]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='main',reason='fixture',
                         assignment='structural_heading' if i in {0,5} else 'heading_context') for i,t in enumerate(texts)]
    cert=ResumeSection(category='certifications',label='Certifications',text='\n'.join(texts[:5]),blocks=blocks[:5],entries=[
        SectionEntry(entry_id='c1',block_indices=[1],lane='main',boundary_reason='fixture',fields={'title':[1]}),
        SectionEntry(entry_id='c2',block_indices=[2],lane='main',boundary_reason='fixture',fields={'title':[2]}),
        SectionEntry(entry_id='c3',block_indices=[3,4],lane='main',boundary_reason='fixture',fields={'title':[3]})])
    awards=ResumeSection(category='awards',label='Awards',text='\n'.join(texts[5:]),blocks=blocks[5:],entries=[
        SectionEntry(entry_id='a1',block_indices=[1],lane='main',boundary_reason='fixture',fields={'title':[1]})])
    result=SectionResponse(status='provisional',sections=[cert,awards],needs_review=[],metadata={},warnings=[])
    state=snapshot(elements,result);hid=state.spans[2].source_id
    revised=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':[{'op':'heading','source_ids':[hid],'section':'projects'}]}),review=True)
    assert revised.metadata['structure_review']['status']=='provisional'
    assert not validate_result(elements,revised)
    validated_ownership_state(elements,revised)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=revised))
    projects=next(s for s in mapped.section_schemas if s.category=='projects')
    assert set(projects.records[0].source_ids)=={state.spans[3].source_id,state.spans[4].source_id}
    assert next(s for s in revised.sections if s.category=='projects').source_heading=='Independent Work'

    # Section-review classification can recognize the same unfamiliar boundary
    # before structural review. Explicit confirmations of its body must survive.
    from local_api.services.llm_section_review import review_sections
    from local_api.schemas.sections import SectionRequest
    result.sections[0].blocks[2].boundary_candidate=True
    def classify(settings,messages):
        payload=json.loads(messages[1]['content'])
        return json.dumps({'assignments':[[b['id'],'projects' if b['source_element']==2 else b['current_category']]
                                          for b in payload['spans']]})
    reviewed=review_sections(SectionRequest(elements=elements),result,
        settings=ReviewSettings(enabled=True,api_key='mock'),transport=classify)
    assert reviewed.metadata['llm_review']['status']=='complete'
    validated_ownership_state(elements,reviewed)
    assert next(s for s in reviewed.sections if s.category=='projects').source_heading=='Independent Work'
    remapped=map_schema(SchemaMappingRequest(elements=elements,sections=reviewed))
    # The provider explicitly confirmed the dependent body as Certifications.
    # A heading-only decision must flag that contradiction, not override it.
    assert not next(s for s in remapped.section_schemas if s.category=='projects').records
    body = next(s for s in reviewed.sections if s.category=='certifications')
    assert all(b.assignment=='ownership_needs_review' for b in body.blocks if b.source_element_index in {3,4})


def test_employment_transition_terminates_an_earlier_sidebar_heading():
    state=ledger();spans=list(state.spans);owners=dict(state.owners)
    # A supported dated employment anchor is a boundary even without Title style.
    spans[3]=replace(spans[3],source_assignment='employment_boundary')
    for i in [3,4]:
        owners[spans[i].source_id]=Owner('experience','job',('responsibilities',) if i==4 else ())
    state=replace(state,spans=tuple(spans),owners=MappingProxyType(owners))
    out=correct(state)
    assert all(out.owners[spans[i].source_id]==state.owners[spans[i].source_id] for i in [3,4])


def test_reviewed_wrapped_responsibility_cannot_be_implicitly_reclassified():
    state=ledger();spans=list(state.spans);owners=dict(state.owners)
    for i in [3,4]:
        spans[i]=replace(spans[i],reviewed_section='experience',element=3)
        owners[spans[i].source_id]=Owner('experience','job',('responsibilities',) if i==4 else ())
    state=replace(state,spans=tuple(spans),owners=MappingProxyType(owners))
    out=correct(state)
    for i in [3,4]:
        owner=out.owners[spans[i].source_id]
        assert (owner.section,owner.record)==('experience','job')
        assert owner.status=='needs_review'
    # Explicit, source-bound corrections remain possible after review.
    out=apply_operations(out,[{'op':'assign','source_ids':[spans[i].source_id for i in [3,4]],
        'section':'projects','record':None,'fields':[]}],{'experience','projects'})
    assert all(out.owners[spans[i].source_id].section=='projects' for i in [3,4])
