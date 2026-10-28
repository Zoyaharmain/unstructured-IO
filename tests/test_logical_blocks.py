"""Logical context partitions sources without merging distinct resume records."""
import json
from pathlib import Path
from copy import deepcopy
from local_api.schemas.sections import ResumeSection, SectionBlock, SectionEntry, SectionResponse
from local_api.services.llm_schema_mapping import messages


def section(category, lines):
    return ResumeSection(category=category,label=category,blocks=[SectionBlock(
        source_element_index=i,start=0,end=len(text),text=text,page_number=1,
        assignment='semantic',lane='main',reason='fixture') for i,text in enumerate(lines)])


def test_summary_has_one_logical_block_and_preserves_seamless_source_offsets():
    s=section('summary',['Full summary ', 'continued.', 'Second paragraph.'])
    s.blocks[1].source_element_index=0; s.blocks[1].start=13; s.blocks[1].end=23
    s.blocks[2].source_element_index=1
    s.entries=[SectionEntry(entry_id='fragment',block_indices=[0],lane='main',boundary_reason='fragment')]
    before=deepcopy(s.blocks)
    groups=s.logical_blocks
    assert len(groups)==1
    assert groups[0]['text']=='Full summary continued.\nSecond paragraph.'
    assert groups[0]['block_indices']==[0,1,2]
    assert s.blocks==before
    assert s.model_dump()['logical_blocks']==groups


def test_jobs_are_complete_separate_records_not_one_selected_fragment():
    s=section('experience',['Experience','Acme','Engineer','Built services','Beta','Analyst','Analyzed data'])
    s.blocks[0].assignment='section_heading'
    s.entries=[SectionEntry(entry_id=f'job-{i}',block_indices=indices,lane='main',boundary_reason='employer boundary') for i,indices in enumerate([[1,2,3],[4,5,6]])]
    groups=s.logical_blocks
    assert len(groups)==2
    assert groups[0]['text']=='Acme\nEngineer\nBuilt services'
    assert groups[1]['text']=='Beta\nAnalyst\nAnalyzed data'
    assert not set(groups[0]['source_ids']) & set(groups[1]['source_ids'])
    assert [i for g in groups for i in g['block_indices']]==list(range(1,7))
    prompt=json.loads(messages([s])[1]['content'])['sections'][0]
    assert prompt['logical_blocks']==groups
    assert all(g['logical_id'] not in {b['source_id'] for b in prompt['blocks']} for g in groups)


def test_unowned_content_and_overlapping_records_are_not_guessed():
    s=section('education',['University A','Degree','Unassigned qualification'])
    s.entries=[SectionEntry(entry_id='education-1',block_indices=[0,1],lane='main',boundary_reason='source')]
    groups=s.logical_blocks
    assert groups[-1]['kind']=='unresolved'
    assert groups[-1]['block_indices']==[2]
    assert groups[-1]['relationship_status']=='needs_review'
    s.entries.append(SectionEntry(entry_id='education-2',block_indices=[1,2],lane='main',boundary_reason='conflicting'))
    assert len(s.logical_blocks)==1 and s.logical_blocks[0]['kind']=='unresolved'
    assert s.logical_blocks[0]['block_indices']==[0,1,2]


def test_derived_groups_refresh_when_review_changes_record_owners():
    s=section('projects',['Project A','Built API','Project B','Created UI'])
    assert s.logical_blocks[0]['kind']=='unresolved'
    s.entries=[SectionEntry(entry_id=f'project-{i}',block_indices=indices,lane='main',boundary_reason='reviewed') for i,indices in enumerate([[0,1],[2,3]])]
    assert len(s.logical_blocks)==2
    restored=ResumeSection.model_validate(s.model_dump())
    assert restored.logical_blocks==s.logical_blocks


def test_saved_jayesh_summary_is_single_context_with_exact_original_text():
    root=Path('reports/single-jayesh-feedback-live-20261022')
    sections=SectionResponse.model_validate(json.loads((root/'sections.json').read_text()))
    summary=next(s for s in sections.sections if s.category=='summary')
    assert len(summary.logical_blocks)==1
    group=summary.logical_blocks[0]
    blocks=[b for b in summary.blocks if b.assignment not in {'section_heading','structural_heading'}]
    assert group['text']==''.join(b.text for b in blocks)
    assert len(group['source_ids'])==len(blocks)>1


def test_unowned_bullet_markers_do_not_become_fake_job_cards():
    s=section('experience',['Employer','Engineer',' • '])
    s.entries=[SectionEntry(entry_id='job-1',block_indices=[0,1],lane='main',boundary_reason='job')]
    assert len(s.logical_blocks)==1
    assert s.blocks[2].text==' • '


def test_semantic_shape_uses_existing_registry_and_record_local_sources_only():
    from local_api.schemas.subschema_spec import SUBSCHEMAS
    s=section('experience',['Acme','Engineer','Beta'])
    s.entries=[SectionEntry(entry_id='job',block_indices=[0,1],lane='main',boundary_reason='source',
                           fields={'employer':[0,2], 'title':[1], 'invented':[2]})]
    groups=s.logical_blocks
    frame=groups[0]['semantic_frame']
    assert frame['schema_target']=='experience'
    assert frame['scope']=='one_record'
    slots={slot['name']:slot for slot in frame['field_slots']}
    assert set(slots)==set(SUBSCHEMAS['experience'])
    assert slots['company']['source_hints']==[groups[0]['source_ids'][0]]
    assert slots['role']['source_hints']==[groups[0]['source_ids'][1]]
    assert slots['location']['source_hints']==[]
    assert groups[1]['semantic_frame']['schema_target'] == 'experience'
    assert groups[1]['semantic_frame']['interpretation_status']=='requires_association'


def test_shape_hints_refresh_when_ownership_changes_and_never_invent_values():
    s=section('projects',['Project One','Description'])
    s.entries=[SectionEntry(entry_id='project',block_indices=[0,1],lane='main',boundary_reason='source',fields={'title':[0]})]
    frame=s.logical_blocks[0]['semantic_frame']
    assert next(slot for slot in frame['field_slots'] if slot['name']=='name')['source_hints']==['e0:0:11']
    assert all('value' not in slot for slot in frame['field_slots'])
    s.entries[0].block_indices=[1]
    assert all(not slot['source_hints'] for slot in s.logical_blocks[-1]['semantic_frame']['field_slots'])


def test_summary_shape_collects_all_paragraphs_in_one_statement_context():
    s=section('summary',['First paragraph.','Second paragraph.'])
    groups=s.logical_blocks
    assert len(groups)==1
    frame=groups[0]['semantic_frame']
    assert frame['scope']=='complete_section'
    assert next(slot for slot in frame['field_slots'] if slot['name']=='statements')['source_hints']==groups[0]['source_ids']


def test_exact_heading_with_stale_content_assignment_is_context_not_orphan():
    s=section('projects',['PROJECTS and POCs:','Project A','Built APIs'])
    s.entries=[SectionEntry(entry_id='project-1',block_indices=[1,2],lane='main',boundary_reason='source')]
    assert len(s.logical_blocks)==1
    assert s.logical_blocks[0]['block_indices']==[1,2]
    assert s.blocks[0].text=='PROJECTS and POCs:'


def test_unowned_fragments_keep_known_schema_and_do_not_merge_across_records():
    s=section('experience',['Ambiguous preceding duties','Employer','Engineer','Ambiguous following duties'])
    s.entries=[SectionEntry(entry_id='job',block_indices=[1,2],lane='main',boundary_reason='source')]
    unresolved=[g for g in s.logical_blocks if g['kind']=='unresolved']
    assert [g['block_indices'] for g in unresolved]==[[0],[3]]
    assert all(g['semantic_frame']['schema_target']=='experience' for g in unresolved)
    assert all(g['relationship_status']=='needs_review' for g in unresolved)
