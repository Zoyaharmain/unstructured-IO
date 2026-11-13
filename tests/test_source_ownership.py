"""Structural contracts use invented employers/layouts, never a named resume."""
import json
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, SectionEntry, ResumeSection, SectionResponse
from local_api.services.source_ownership import snapshot, apply_operations, materialize, finalize_ownership
from local_api.services.llm_section_review import ReviewSettings


def document():
    texts = ['EXPERIENCE', 'Orbit Ltd', 'Engineer | 2019 - 2021', 'Built services across',
             'regions.', 'Senior Engineer | 2021 - Present', 'Led delivery.', 'SKILLS', 'Python, SQL']
    types = ['Title','Title','Header','Footer','Title','Header','Footer','Title','Title']
    elements = [ExtractedElement(type=t, text=s, page_number=1 if i<4 else 2,
                metadata={'coordinates':{'points':[[1,2],[3,4]]}}) for i,(s,t) in enumerate(zip(texts,types))]
    blocks = [SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=e.page_number,
              assignment='structural_heading' if i in {0,7} else 'semantic',lane='left',reason='test')
              for i,(t,e) in enumerate(zip(texts,elements))]
    exp = ResumeSection(category='experience',label='Experience',text='\n'.join(texts[:7]),blocks=blocks[:7],
        entries=[SectionEntry(entry_id='old',block_indices=list(range(1,7)),lane='left',boundary_reason='test',
                    fields={'employer':[1],'title':[2,5],'responsibilities':[3,4,6]})])
    skills=ResumeSection(category='skills',label='Skills',text='\n'.join(texts[7:]),blocks=blocks[7:])
    return elements, SectionResponse(status='provisional',sections=[exp,skills],needs_review=[],metadata={},warnings=[])


def test_ledger_is_immutable_stable_exact_and_keeps_weak_types():
    elements, result = document()
    before=[e.model_dump() for e in elements]
    a,b=snapshot(elements,result),snapshot(elements,result)
    assert a == b
    assert a.spans[3].upstream_type == 'Footer'
    assert a.spans[4].page == 2 and a.spans[4].text == 'regions.'
    assert json.loads(a.spans[0].coordinates_json)['element']['points'] == [[1,2],[3,4]]
    with pytest.raises(TypeError):a.owners['invented']=None
    assert before == [e.model_dump() for e in elements]


def test_split_roles_preserves_cross_page_duty_and_employer_parent():
    elements,result=document();state=snapshot(elements,result)
    rid=state.owners['e1:0:9'].record
    anchor=state.spans[5].source_id
    repaired=apply_operations(state,[{'op':'split','record':rid,'anchor':anchor}],{'experience','skills'})
    assert repaired.owners[state.spans[3].source_id].record == repaired.owners[state.spans[4].source_id].record
    assert repaired.owners[anchor].record != rid
    assert len(set(repaired.parents.values())) == 1
    out=materialize(elements,result,repaired)
    assert [e.block_indices for e in out.sections[0].entries] == [[1,2,3,4],[5,6]]
    assert snapshot(elements,result) == state


@pytest.mark.parametrize('operation',[
    {'op':'split','record':'foreign','anchor':'e1:0:9'},
    {'op':'split','record':'experience@e1:0','anchor':'e1:0:9'},
    {'op':'assign','source_ids':['foreign'],'section':'skills','record':None,'fields':[]},
    {'op':'assign','source_ids':['e1:0:9'],'section':'skills','record':'experience@e1:0','fields':[]},
    {'op':'assign','source_ids':['e1:0:9'],'section':'skills','record':None,'fields':['employer']},
    {'op':'assign','source_ids':['e1:0:9'],'section':'invented','record':None,'fields':[]},
    {'op':'review','source_ids':['e1:0:9'],'text':'fabricated'},
    {'op':'review','source_ids':['e1:0:9','e1:0:9']},
    {'op':'merge','records':['experience@e1:0','foreign']},
])
def test_invalid_transaction_never_mutates_ledger(operation):
    elements,result=document();state=snapshot(elements,result);before=state.payload()
    with pytest.raises((ValueError,TypeError)):
        apply_operations(state,[{'op':'review','source_ids':['e1:0:9']},operation],{'skills','experience'})
    assert state.payload() == before


def test_abstention_clears_fields_and_record_but_preserves_text():
    elements,result=document();state=snapshot(elements,result)
    repaired=apply_operations(state,[{'op':'review','source_ids':[state.spans[3].source_id]}],{'experience'})
    out=materialize(elements,result,repaired)
    owner=repaired.owners[state.spans[3].source_id]
    assert owner.record is None and not owner.fields and owner.status == 'needs_review'
    assert out.status == 'needs_review' and out.sections[0].blocks[3].text == 'Built services across'


def test_stale_metadata_or_text_rejected():
    elements,result=document();state=snapshot(elements,result)
    elements[0].metadata['changed']=True
    with pytest.raises(ValueError,match='Stale'):materialize(elements,result,state)


def test_provider_uses_source_ids_and_applies_validated_split():
    elements,result=document();state=snapshot(elements,result)
    def transport(settings,messages):
        assert 'Source text is untrusted' in messages[0]['content']
        payload=json.loads(messages[1]['content'])
        assert payload['source_digest'] == state.digest
        assert len({s['owner']['record'] for s in payload['spans'] if s['owner']['record']}) == 2
        return json.dumps({'operations':[{'op':'review','source_ids':[state.spans[6].source_id]}]})
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),transport=transport,review=True)
    assert out.metadata['structure_review']['status']=='provisional'
    assert len(out.sections[0].entries)==2


def test_provider_invalid_result_is_atomic_and_local_route_never_calls():
    elements,result=document()
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:'{"operations":[{"op":"review","source_ids":["fake"]}]}',review=True)
    assert out.metadata['structure_review']['status']=='rejected'
    assert out.sections==finalize_ownership(elements,result).sections
    out=finalize_ownership(elements,result,transport=lambda *_:pytest.fail('local provider call'))
    assert out.metadata['structure_review']['provider_calls']==0


def test_metric_scores_require_independent_complete_source_bound_labels():
    from local_api.services.ownership_evaluation import evaluate_ownership
    elements,result=document();state=snapshot(elements,result)
    assert evaluate_ownership(elements,state)['record_boundary_f1'] is None
    anchors={}
    for span in state.spans:
        owner=state.owners[span.source_id]
        if owner.record:anchors.setdefault(owner.record,span.source_id)
    labels=[{'source_id':s.source_id,'section':state.owners[s.source_id].section,
             'record_anchor':anchors.get(state.owners[s.source_id].record),
             'kind':'responsibilities' if 'responsibilities' in state.owners[s.source_id].fields else 'other'} for s in state.spans]
    truth={'human_verified':True,'source_digest':state.digest,'spans':labels,
           'annotation_origin':'independent_human',
           'review':{'method':'independent_human','reviewer_id':'test-reviewer','saw_parser_predictions':False}}
    metrics=evaluate_ownership(elements,state,truth)
    assert metrics['section_f1']==metrics['record_boundary_f1']==metrics['responsibility_ownership_accuracy']==1
    assert metrics['cross_record_leakage']==0
    truth['source_digest']='stale'
    with pytest.raises(ValueError):evaluate_ownership(elements,state,truth)


def test_missing_employer_is_not_inherited_from_previous_record():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    from test_block_completion import fixture
    elements,sections=fixture(['Engineer | Orbit Ltd | 2020 - 2021','Built services.',
                              'Analyst | 2022 - 2023','Managed reports.'],{'experience':[0,1,2,3]},[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(mapped.data.experience)==2
    assert mapped.data.experience[0].company=='Orbit Ltd'
    assert not mapped.data.experience[1].company


def test_close_roles_under_one_employer_keep_distinct_primary_ownership():
    from local_api.services.resume_structure import reviewed_employment_groups
    elements,result=document()
    blocks=result.sections[0].blocks[1:7]
    texts=['Orbit Ltd','Engineer','Built services.','Senior Engineer','Led delivery.']
    elements=[ExtractedElement(type='Header',text=t,page_number=1,metadata={
        'pdf_source_lines':[{'start':0,'end':len(t),'bbox':[.1,.1+i*.006,.8,.105+i*.006],'bold':i in {0,1,3}}]}) for i,t in enumerate(texts)]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,
        assignment='semantic',lane='left',reason='test') for i,t in enumerate(texts)]
    groups=reviewed_employment_groups(blocks,elements)
    assert len(groups)==2
    assert groups[0]['block_indices']==[0,1,2]
    assert groups[1]['block_indices']==[3,4]


def test_overlapping_jobs_and_missing_dates_remain_source_owned_in_columns():
    elements,result=document()
    section=result.sections[0]
    section.entries=[SectionEntry(entry_id='a',block_indices=[1,2,3,4],lane='left',boundary_reason='test',
        fields={'employer':[1],'title':[2],'responsibilities':[3,4]}),
        SectionEntry(entry_id='b',block_indices=[5,6],lane='right',boundary_reason='test',
        fields={'title':[5],'responsibilities':[6]})]
    section.blocks[5].lane=section.blocks[6].lane='right'
    state=snapshot(elements,result)
    assert state.owners[state.spans[3].source_id].record != state.owners[state.spans[6].source_id].record
    assert state.spans[6].lane=='right'
    assert len({o.record for o in state.owners.values() if o.record})==2
    # Ownership has no chronological sorting, inferred dates, or employer values.
    assert [s.text for s in state.spans]==[e.text for e in elements]


def test_metrics_count_wrong_role_as_leakage_and_abstention_as_unresolved():
    from local_api.services.ownership_evaluation import evaluate_ownership
    elements,result=document();state=snapshot(elements,result)
    anchor=state.spans[1].source_id
    labels=[{'source_id':s.source_id,'section':state.owners[s.source_id].section,
             'record_anchor':anchor if state.owners[s.source_id].record else None,
             'kind':'responsibilities' if 'responsibilities' in state.owners[s.source_id].fields else 'other'} for s in state.spans]
    truth={'human_verified':True,'source_digest':state.digest,'spans':labels,
           'annotation_origin':'independent_human',
           'review':{'method':'independent_human','reviewer_id':'test-reviewer','saw_parser_predictions':False}}
    wrong=apply_operations(state,[{'op':'split','record':state.owners[anchor].record,'anchor':state.spans[5].source_id}],{'experience'})
    metrics=evaluate_ownership(elements,wrong,truth)
    assert metrics['cross_record_leakage']==pytest.approx(1/3)
    assert metrics['responsibility_ownership_accuracy']==pytest.approx(2/3)
    assert metrics['record_boundary_f1']==pytest.approx(2/3)
    abstain=apply_operations(wrong,[{'op':'review','source_ids':[state.spans[6].source_id]}],{'experience'})
    metrics=evaluate_ownership(elements,abstain,truth)
    assert metrics['cross_record_leakage']==0
    assert metrics['responsibility_ownership_accuracy']==pytest.approx(2/3)
    assert metrics['unresolved_span_rate']>0


def test_split_merge_roundtrip_and_section_reassignment_only_use_existing_ids():
    elements,result=document();state=snapshot(elements,result)
    rid=state.owners[state.spans[1].source_id].record
    anchor=state.spans[5].source_id
    split=apply_operations(state,[{'op':'split','record':rid,'anchor':anchor}],{'experience','skills'})
    merged=apply_operations(split,[{'op':'merge','records':[rid,split.owners[anchor].record]}],{'experience','skills'})
    assert dict(merged.owners)==dict(state.owners)
    sid=state.spans[8].source_id
    moved=apply_operations(state,[{'op':'assign','source_ids':[sid],'section':'summary','record':None,'fields':[]}],{'summary'})
    out=materialize(elements,result,moved)
    assert next(s for s in out.sections if s.category=='summary').blocks[0].text=='Python, SQL'
    assert out.sections[0].entries==result.sections[0].entries


def test_sibling_roles_share_only_standalone_employer_evidence():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    from local_api.services.subschema_validation import validate_hierarchy
    elements,result=document()
    out=finalize_ownership(elements,result)
    first,second=out.sections[0].entries
    assert second.context_fields=={'company':[1]}
    assert not validate_result(elements,out)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=out))
    assert len(mapped.data.experience)==2
    assert [job.company for job in mapped.data.experience]==['Orbit Ltd','Orbit Ltd']
    assert [job.start_date for job in mapped.data.experience]==['2019','2021']
    assert 'Led delivery.' not in mapped.data.experience[0].responsibilities
    assert not any('Built services' in duty for duty in mapped.data.experience[1].responsibilities)
    revised=mapped.meta.get('reviewed_sections',out.model_dump())
    validate_hierarchy(mapped.section_schemas,SectionResponse.model_validate(revised))
    assert 1 not in second.block_indices
    assert first.block_indices==[1,2,3,4]


def test_shared_employer_context_rejects_foreign_dates_and_other_column():
    from local_api.services.source_validation import validate_result
    elements,result=document();out=finalize_ownership(elements,result)
    second=out.sections[0].entries[1]
    second.context_fields={'start_date':[2]}
    assert 'invalid_record_context' in validate_result(elements,out)
    second.context_fields={'company':[1]}
    out.sections[0].blocks[5].lane='right'
    assert 'invalid_record_context' in validate_result(elements,out)


@pytest.mark.parametrize('later_title', ['Senior Engineer | 2020 - Present', 'Senior Engineer'])
def test_sibling_role_dates_can_overlap_or_be_absent_without_inference(later_title):
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    elements,result=document()
    elements[5].text=later_title
    result.sections[0].blocks[5]=result.sections[0].blocks[5].model_copy(update={'text':later_title,'end':len(later_title)})
    result.sections[0].text='\n'.join(b.text for b in result.sections[0].blocks)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert len(mapped.data.experience)==2
    assert [j.company for j in mapped.data.experience]==['Orbit Ltd','Orbit Ltd']
    assert mapped.data.experience[0].start_date=='2019'
    if '2020' in later_title:
        assert mapped.data.experience[1].start_date=='2020'
    else:
        assert not mapped.data.experience[1].start_date and not mapped.data.experience[1].end_date


def test_provider_limit_prevents_calls_and_preserves_review_state():
    elements,result=document()
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock',max_units=1),
        transport=lambda *_:pytest.fail('over-budget call'),review=True)
    assert out.metadata['structure_review']=={'status':'budget_exceeded','provider_calls':0}
    assert out.status=='needs_review'


def test_project_duties_are_not_copied_into_the_only_job():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    from test_block_completion import fixture
    elements,result=fixture(['Engineer | Orbit Ltd | 2019 - 2021','Project: Independent Atlas',
                            '• Built an independent research search platform.'],{'experience':[0],'projects':[1,2]},[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert len(mapped.data.experience)==1
    assert not mapped.data.experience[0].responsibilities
    assert not any(path.startswith('experience[0].responsibilities') for path in mapped.meta['field_evidence'])


def test_clear_unowned_job_can_be_created_only_from_existing_source_ids():
    elements,result=document();state=snapshot(elements,result)
    unowned=apply_operations(state,[{'op':'review','source_ids':[s.source_id for s in state.spans[1:7]]}],{'experience'})
    ss=[s.source_id for s in state.spans[1:7]]
    rid='experience@'+ss[0]
    created=apply_operations(unowned,[{'op':'create','section':'experience','source_ids':ss},
        {'op':'assign','section':'experience','source_ids':[ss[0]],'record':rid,'fields':['employer']},
        {'op':'assign','section':'experience','source_ids':[ss[1]],'record':rid,'fields':['title']}],{'experience'})
    assert created.owners[ss[0]].record==rid
    assert created.owners[ss[1]].record==rid
    assert created.owners[ss[2]].status=='needs_review'
    assert created.spans==state.spans
    with pytest.raises(ValueError):apply_operations(unowned,[{'op':'create','section':'experience','source_ids':['invented']}],{'experience'})


def test_explicit_review_survives_canonical_heading_rebuild_and_mapping():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    elements,result=document();heading='e0:0:10'
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':[{'op':'review','source_ids':[heading]}]}),review=True)
    assert snapshot(elements,out).owners[heading].status=='needs_review'
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=out))
    span=next(s for s in mapped.meta['source_ownership']['spans'] if s['source_id']==heading)
    assert span['owner']['status']=='needs_review'


def test_accepted_primary_ownership_is_not_replaced_by_local_healing():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    elements,result=document();sid=f'e6:0:{len(elements[6].text)}'
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':[{'op':'review','source_ids':[sid]}]}),review=True)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=out))
    assert all('Led delivery.' not in duty for job in mapped.data.experience for duty in job.responsibilities)
    out.metadata['source_ownership']['spans'][0]['owner']['record']='invented'
    with pytest.raises(ValueError):map_schema(SchemaMappingRequest(elements=elements,sections=out))


def test_reference_intervals_and_logical_bullets_do_not_follow_parser_splits():
    from local_api.services.ownership_evaluation import evaluate_ownership
    elements,result=document();state=snapshot(elements,result)
    anchor=state.spans[1].source_id
    labels=[{'source_id':s.source_id,'text':s.text,'section':state.owners[s.source_id].section,
             'record_anchor':anchor if state.owners[s.source_id].record else None,
             'kind':'responsibilities' if 'responsibilities' in state.owners[s.source_id].fields else 'other',
             'unit_id':'wrapped-bullet' if s.order in {3,4} else None} for s in state.spans]
    last=labels.pop()
    labels += [{**last,'source_id':'e8:0:7','text':elements[8].text[:7]},
               {**last,'source_id':f'e8:7:{len(elements[8].text)}','text':elements[8].text[7:]}]
    truth={'human_verified':True,'source_digest':state.digest,'spans':labels,'annotation_origin':'independent_human',
           'review':{'method':'independent_human','reviewer_id':'test-reviewer','saw_parser_predictions':False}}
    metrics=evaluate_ownership(elements,state,truth)
    assert metrics['section_f1']==1 and metrics['scored_responsibilities']==2


def test_validated_achievement_keeps_its_role_and_is_exported_with_source_evidence():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    elements,result=document()
    local=finalize_ownership(elements,result)
    state=snapshot(elements,local)
    sid=f'e6:0:{len(elements[6].text)}'
    rid=state.owners[sid].record
    reviewed=finalize_ownership(elements,local,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':[{'op':'assign','source_ids':[sid],
            'section':'experience','record':rid,'fields':['achievements']}]}),review=True)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=reviewed))
    assert 'Led delivery.' in mapped.data.experience[1].responsibilities
    assert 'Led delivery.' not in mapped.data.experience[0].responsibilities
    owner=next(s['owner'] for s in mapped.meta['source_ownership']['spans'] if s['source_id']==sid)
    assert owner['fields']==['achievements']


def test_merged_roles_in_different_columns_require_review_instead_of_proximity_guess():
    elements,result=document()
    result.sections[0].blocks[5].lane='right'
    out=finalize_ownership(elements,result)
    state=snapshot(elements,out)
    assert all(state.owners[s.source_id].record is None for s in state.spans[1:7])
    assert all(state.owners[s.source_id].status=='needs_review' for s in state.spans[1:7])
    assert ''.join(s.text for s in state.spans)==''.join(e.text for e in elements)


def test_footer_type_cannot_hide_numeric_content_or_pagebreak_hide_a_title():
    from types import SimpleNamespace
    from local_api.services.source_accounting import artifact_reason
    for kind,text in [('Footer','24/7'),('Footer','3'),('PageBreak','Software Engineer')]:
        element=ExtractedElement(type=kind,text=text,page_number=1,metadata={})
        assert artifact_reason(element,SimpleNamespace(text=text,start=0,end=len(text))) is None
    element=ExtractedElement(type='NarrativeText',text='Page 1 of 2',page_number=1,metadata={})
    assert artifact_reason(element,SimpleNamespace(text=element.text,start=0,end=len(element.text)))


def test_explicit_company_link_never_inherits_parent_title_dates_or_duties():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    from local_api.services.subschema_validation import validate_hierarchy
    from test_block_completion import fixture
    elements,result=fixture(['Engineer | Orbit Ltd | 2019 - 2021','Built the original service.',
                             'Analyst','Client: Fictional Customer','Managed separate reports.'],
                            {'experience':[0,1,2,3,4]},[])
    # Supply two explicit source-owned roles; no company relation is guessed.
    result.sections[0].entries=[SectionEntry(entry_id='a',block_indices=[0,1],lane='main',boundary_reason='test',
        fields={'employer':[0],'title':[0],'dates':[0],'responsibilities':[1]}),
        SectionEntry(entry_id='b',block_indices=[2,3,4],lane='main',boundary_reason='test',
        fields={'title':[2],'client':[3],'responsibilities':[4]})]
    local=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert not local.data.experience[1].company
    state=snapshot(elements,result)
    parent=state.spans[0].source_id
    child=state.owners[state.spans[2].source_id].record
    reviewed=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':[{'op':'link_employer','record':child,'source_id':parent}]}),review=True)
    assert reviewed.metadata['structure_review']['status']=='provisional'
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=reviewed))
    job=mapped.data.experience[1]
    assert job.company=='Orbit Ltd' and job.role=='Analyst'
    assert not job.start_date and not job.end_date
    assert 'Built the original service.' not in job.responsibilities
    assert 'Managed separate reports.' in job.responsibilities
    validate_hierarchy(mapped.section_schemas,reviewed)


def test_local_role_split_abstains_when_employer_occurs_after_the_first_role():
    from test_block_completion import fixture
    texts=['Engineer','Built services.','Senior Engineer','Other Ltd','Led delivery.']
    elements,result=fixture(texts,{'experience':list(range(5))},[])
    result.sections[0].entries=[SectionEntry(entry_id='mixed',block_indices=list(range(5)),lane='main',
        boundary_reason='test',fields={'title':[0,2],'employer':[3],'responsibilities':[1,4]})]
    out=finalize_ownership(elements,result)
    state=snapshot(elements,out)
    first=out.sections[0].entries[0]
    assert not first.context_fields and first.relationship_status=='needs_review'
    assert state.owners['e0:0:8'].status=='needs_review'
    later_company=f'e3:0:{len(texts[3])}'
    rid=state.owners['e0:0:8'].record
    reviewed=finalize_ownership(elements,out,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':[{'op':'link_employer','record':rid,'source_id':later_company}]}),review=True)
    assert reviewed.metadata['structure_review']['status']=='rejected'
    assert not reviewed.sections[0].entries[0].context_fields


def test_persisted_ownership_accepts_json_object_key_reordering():
    elements,result=document()
    reviewed=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:'{"operations":[]}',review=True)
    reordered=SectionResponse.model_validate(json.loads(json.dumps(reviewed.model_dump(),sort_keys=True)))
    accepted=finalize_ownership(elements,reordered)
    assert [e.block_indices for e in accepted.sections[0].entries]==[e.block_indices for e in reviewed.sections[0].entries]
    assert accepted.metadata['structure_review']['provider_calls']==1
