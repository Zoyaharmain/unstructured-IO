"""Cross-section, identity, transaction and review-status regressions."""
import json
import pytest
from dataclasses import replace
from types import MappingProxyType

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock,SectionEntry,ResumeSection,SectionResponse
from local_api.services.education_relations import aligned_education_elements
from local_api.services.source_ownership import snapshot,apply_operations,finalize_ownership
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.source_validation import validate_result


def physical(text,y,x=.1,right=.4):
    return ExtractedElement(text=text,type='NarrativeText',page_number=1,metadata={
        'pdf_source_lines':[{'start':0,'end':len(text),'bbox':[x,y,right,y+.02]}]})


def test_dates_need_unique_institution_alignment_not_just_a_year_range():
    elements=[physical('2012 - 2016',.7),physical('North Coast Institute',.7,.5,.9),
              physical('2018 - 2022',.3),physical('Engineer, Orbit Ltd',.3,.5,.9)]
    assert aligned_education_elements(elements)=={0,1}
    elements.append(physical('South Coast University',.7,.5,.9))
    assert aligned_education_elements(elements)==set()


def test_repeated_institution_rows_remain_distinct_education_records_without_inventing_degrees():
    from local_api.services.resume_sections import build_sections
    elements=[physical('2010 - 2014',.3),physical('North Coast Institute',.3,.5,.9),
              physical('2010 - 2014',.7),physical('North Coast Institute',.7,.5,.9)]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(e.text),text=e.text,page_number=1,
             lane='main',assignment='education_relation',reason='fixture') for i,e in enumerate(elements)]
    sections=build_sections({'education':blocks},elements)
    assert [e.block_indices for e in sections[0].entries]==[[0,1],[2,3]]
    assert all(e.relationship_status=='needs_review' and 'qualification_not_established' in e.review_reasons for e in sections[0].entries)
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    result=SectionResponse(status='needs_review',sections=sections,needs_review=[],metadata={},warnings=[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert len(mapped.data.education)==2 and all(not e.degree for e in mapped.data.education)


def employment_copies(second_company='Orbit Ltd'):
    texts=['EXPERIENCE','Engineer, Orbit Ltd','2019 - 2021','Built data services.',
           f'Engineer, {second_company}','2019 - 2021','Built data services.']
    elements=[physical(t,.1+i*.08) for i,t in enumerate(texts)]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,
            lane='main',assignment='structural_heading' if i==0 else 'semantic',reason='fixture') for i,t in enumerate(texts)]
    entries=[SectionEntry(entry_id=f'job-{i}',block_indices=[i,i+1,i+2],lane='main',boundary_reason='fixture',
                         fields={'employer':[i],'title':[i],'dates':[i+1],'responsibilities':[i+2]}) for i in [1,4]]
    result=SectionResponse(status='provisional',sections=[ResumeSection(category='experience',label='Experience',
           text='\n'.join(texts),blocks=blocks,entries=entries)],needs_review=[],metadata={},warnings=[])
    return elements,result


def test_duplicate_identity_can_merge_distinct_occurrences_without_losing_citations():
    from local_api.services.employment_identity import duplicate_groups
    elements,result=employment_copies();state=snapshot(elements,result)
    records=duplicate_groups(state)
    assert len(records)==1 and len(records[0])==2
    revised=apply_operations(state,[{'op':'merge','records':records[0]}],{'experience'})
    assert len({o.record for o in revised.owners.values() if o.record})==1
    assert revised.spans==state.spans and len(revised.owners)==7


def test_duplicate_identity_with_date_and_body_columns_preserves_every_source():
    elements,result=employment_copies()
    for i,b in enumerate(result.sections[0].blocks):
        b.lane='left' if i in {2,5} else 'right'
    out=finalize_ownership(elements,result)
    assert len(out.sections[0].entries)==1
    assert len(out.sections[0].blocks)==7
    assert len(out.metadata['duplicate_source_occurrences'])==1
    assert validate_result(elements,out)==[]
    from local_api.services.schema_mapping import map_schema
    from local_api.schemas.mapping import SchemaMappingRequest
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=out))
    assert len(mapped.data.experience)==1 and mapped.data.experience[0].role=='Engineer'


def test_review_cannot_split_a_proven_duplicate_and_strand_its_dates():
    elements,result=employment_copies();state=snapshot(elements,result)
    rid=state.owners[state.spans[1].source_id].record
    ops=[{'op':'split','record':rid,'anchor':state.spans[4].source_id},
         {'op':'assign','source_ids':[state.spans[5].source_id],'section':'experience','record':rid,'fields':['dates']}]
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
        transport=lambda *_:json.dumps({'operations':ops}),review=True)
    assert out.metadata['structure_review']['status']=='rejected'
    assert len(out.sections[0].entries)==1 and len(out.sections[0].blocks)==7
    assert any(i['kind']=='review_execution' for i in out.review_issues)


def test_same_role_and_dates_do_not_make_different_employers_duplicates():
    from local_api.services.employment_identity import duplicate_groups
    elements,result=employment_copies('Nebula Ltd')
    assert duplicate_groups(snapshot(elements,result))==[]


def test_duties_cannot_be_retagged_as_employer_and_title_or_start_a_job():
    elements,result=employment_copies();state=snapshot(elements,result)
    sid=state.spans[3].source_id;record=state.owners[sid].record
    with pytest.raises(ValueError,match='positive source compatibility'):
        apply_operations(state,[{'op':'assign','source_ids':[sid],'section':'experience','record':record,
                                 'fields':['employer','title','responsibilities']}],{'experience'})
    with pytest.raises(ValueError,match='identity or date evidence'):
        apply_operations(state,[{'op':'split','record':record,'anchor':sid}],{'experience'})


def test_repeated_source_records_consolidate_but_different_duties_need_review():
    from local_api.services.employment_identity import repeated_occurrence_operations
    elements,result=employment_copies();state=snapshot(elements,result)
    assert len(repeated_occurrence_operations(state))==1
    elements[6].text='Designed a different product.'
    result.sections[0].blocks[6].text=elements[6].text
    result.sections[0].blocks[6].end=len(elements[6].text)
    state=snapshot(elements,result)
    assert repeated_occurrence_operations(state)==[]


def test_conflicting_transaction_does_not_discard_independent_repair():
    elements,result=employment_copies()
    section=result.sections[0]
    # A heading changes the section but a dependent assign contradicts it.
    state=snapshot(elements,result);head=state.spans[1].source_id
    last=state.spans[6].source_id
    operations=[{'op':'heading','source_ids':[head],'section':'projects'},
                {'op':'assign','source_ids':[state.spans[2].source_id],'section':'experience',
                 'record':state.owners[state.spans[2].source_id].record,'fields':['dates']},
                {'op':'review','source_ids':[last]}]
    # Place a terminating heading before the independent record.
    section.blocks[4].assignment='structural_heading'
    section.entries[1].block_indices=[5,6];section.entries[1].fields={'dates':[5],'responsibilities':[6]}
    out=finalize_ownership(elements,result,settings=ReviewSettings(enabled=True,api_key='mock'),
                           transport=lambda *_:json.dumps({'operations':operations}),review=True)
    status=out.metadata['structure_review']
    assert status['status']=='provisional' and status['execution_status']=='partial'
    assert any(x['op']=='review' for x in status['accepted_operations'])
    assert any(x['operation']['op']=='heading' for x in status['rejected_operations'])
    assert any(i['kind']=='review_execution' for i in out.review_issues)
    assert validate_result(elements,out)==[]


def test_unresolved_records_and_failed_field_review_are_top_level_issues():
    elements,result=employment_copies()
    result.sections[0].entries[0].relationship_status='needs_review'
    result.sections[0].entries[0].review_reasons=['association_unresolved']
    result.metadata['field_review']={'status':'failed','message':'Unsupported field evidence.'}
    result.metadata['structure_review']={'status':'rejected','validation_reason':'Conflicting ownership.'}
    assert result.needs_review==[]
    issues=result.model_dump()['review_issues']
    assert {i['kind'] for i in issues}=={'record','review_execution'}
    assert {i['stage'] for i in issues if i['kind']=='review_execution'}=={'field_review','structure_review'}
