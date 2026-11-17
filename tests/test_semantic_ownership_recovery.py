"""Source contracts for generic hierarchy and selective structural correction."""
import json
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, SectionEntry, ResumeSection, SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.source_ownership import snapshot, apply_operations, materialize, finalize_ownership, validated_ownership_state
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy


def fixture(texts, entries, category='projects'):
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in texts]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t, page_number=1,
                           assignment='semantic', lane='main', reason='synthetic source') for i, t in enumerate(texts)]
    section = ResumeSection(category=category, label=category.title(), blocks=blocks, text='\n'.join(texts), entries=entries)
    return elements, SectionResponse(status='provisional', sections=[section], needs_review=[], metadata={}, warnings=[])


def entry(identifier, indices, fields=None, **kwargs):
    return SectionEntry(entry_id=identifier, block_indices=indices, fields=fields or {}, lane='main', boundary_reason='source fixture', **kwargs)


def test_generic_parent_chain_roundtrip_and_schema_projection():
    elements, result = fixture(['Research portfolio', 'Atlas platform', 'Search module', 'Built retrieval services.'], [
        entry('portfolio', [0], {'title': [0]}, record_kind='group'),
        entry('platform', [1], {'title': [1]}, record_kind='group', parent_entry_id='portfolio'),
        entry('module', [2, 3], {'title': [2], 'responsibilities': [3]}, parent_entry_id='platform')])
    reviewed = finalize_ownership(elements, result, settings=ReviewSettings(enabled=True, api_key='mock'),
                                   transport=lambda *_: '{"operations":[]}', review=True)
    validated_ownership_state(elements, reviewed)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=reviewed))
    assert len(mapped.data.projects) == 1
    tree = reviewed.sections[0].logical_blocks
    assert tree[0]['title'] == 'Research portfolio'
    assert tree[0]['children'][0]['children'][0]['text'].endswith('Built retrieval services.')
    records = next(s for s in mapped.section_schemas if s.category == 'projects').records
    assert [(r.record_id, r.parent_record_id, r.record_kind) for r in records] == [
        ('portfolio', None, 'group'), ('platform', 'portfolio', 'group'), ('module', 'platform', 'record')]
    assert not validate_result(elements, reviewed)
    validate_hierarchy(mapped.section_schemas, reviewed)


@pytest.mark.parametrize('operation', [
    {'op': 'link_parent', 'record': 'projects@e1:0:5', 'parent': 'foreign'},
    {'op': 'link_parent', 'record': 'projects@e1:0:5', 'parent': 'projects@e1:0:5'},
])
def test_bad_parent_transaction_is_atomic(operation):
    elements, result = fixture(['Portfolio', 'Atlas'], [entry('p', [0]), entry('c', [1])])
    state = snapshot(elements, result)
    before = state.payload()
    with pytest.raises(ValueError):
        apply_operations(state, [operation], {'projects'})
    assert state.payload() == before


def test_cycle_and_cross_lane_parent_links_rejected():
    elements, result = fixture(['Portfolio', 'Atlas'], [entry('p', [0]), entry('c', [1])])
    state = snapshot(elements, result)
    p, c = [state.owners[s.source_id].record for s in state.spans]
    with pytest.raises(ValueError, match='Cyclic'):
        apply_operations(state, [{'op': 'link_parent', 'record': c, 'parent': p}, {'op': 'link_parent', 'record': p, 'parent': c}], {'projects'})
    result.sections[0].blocks[1].lane = 'right'
    with pytest.raises(ValueError, match='lanes'):
        apply_operations(snapshot(elements, result), [{'op': 'link_parent', 'record': c, 'parent': p}], {'projects'})


def test_explicit_portfolio_context_owns_dates_without_child_leakage():
    elements, result = fixture(['Projects Worked at Example Studio', 'June 2025 - Feb 2026',
                               '1. Atlas Platform', 'Built services.', '2. Beacon Portal', 'Integrated workflows.'], [
        entry('a', [2, 3], {'title': [2], 'responsibilities': [3]}), entry('b', [4, 5], {'title': [4], 'responsibilities': [5]})])
    out = finalize_ownership(elements, result)
    parent, a, b = out.sections[0].entries
    assert parent.record_kind == 'group' and parent.block_indices == [0, 1]
    assert a.parent_entry_id == b.parent_entry_id == parent.entry_id
    assert [c['title'] for c in out.sections[0].logical_blocks[0]['children']] == ['1. Atlas Platform', '2. Beacon Portal']
    assert not validate_result(elements, out)


def test_automatic_review_skips_clear_records():
    elements, result = fixture(['Atlas Platform', 'Built services.'], [entry('a', [0, 1], {'title': [0], 'responsibilities': [1]})])
    out = finalize_ownership(elements, result, settings=ReviewSettings(enabled=True, api_key='mock'),
                             transport=lambda *_: pytest.fail('Unnecessary provider call'), review='ambiguous')
    assert out.metadata['structure_review']['status'] == 'not_needed'


def test_focused_recovery_clears_abstention_and_survives_mapping():
    elements, result = fixture(['Atlas Platform', 'Integrated reporting.', 'Beacon Portal', 'Built retrieval.'], [
        entry('a', [0], {'title': [0]}), entry('b', [2, 3], {'title': [2], 'responsibilities': [3]})])
    result.sections[0].blocks[1].assignment = 'ownership_needs_review'
    before = finalize_ownership(elements, result)
    state = snapshot(elements, before)
    sid = state.spans[1].source_id
    assert state.owners[sid].status == 'needs_review'
    rid = state.owners[state.spans[0].source_id].record
    def transport(settings, messages):
        package = json.loads(messages[1]['content'])
        assert package['ambiguities'] and any(s['source_id'] == sid for s in package['spans'])
        return json.dumps({'operations': [{'op': 'assign', 'source_ids': [sid], 'section': 'projects', 'record': rid, 'fields': ['responsibilities']}]})
    out = finalize_ownership(elements, before, settings=ReviewSettings(enabled=True, api_key='mock'), transport=transport, review='ambiguous')
    assert out.metadata['structure_review']['status'] == 'provisional'
    assert snapshot(elements, out).owners[sid].status == 'provisional'
    assert out.status == 'provisional'
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=out))
    assert 'Integrated reporting.' in mapped.data.projects[0].description
    assert 'Integrated reporting.' not in (mapped.data.projects[1].description or '')
    assert not out.sections[0].logical_blocks[0]['review_reasons']
    validated_ownership_state(elements, out)


@pytest.mark.parametrize('content', ['{"operations": [null]}', '{"operations": {}}', '{"operations": [{"op":"assign","source_ids":["foreign"],"section":"projects","record":null,"fields":[]}]}'])
def test_invalid_provider_response_cannot_change_source_or_records(content):
    elements, result = fixture(['Atlas Platform', 'Unclear continuation'], [entry('a', [0], {'title': [0]})])
    before = finalize_ownership(elements, result)
    out = finalize_ownership(elements, result, settings=ReviewSettings(enabled=True, api_key='mock'), transport=lambda *_:content, review='ambiguous')
    assert out.metadata['structure_review']['status'] == 'rejected'
    assert out.sections == before.sections
    assert out.metadata['source_ownership'] == before.metadata['source_ownership']


def test_persisted_parent_tampering_rejected_before_mapping():
    elements, result = fixture(['Portfolio', 'Atlas Platform'], [entry('p', [0], {'title':[0]}, record_kind='group'), entry('a', [1], {'title':[1]}, parent_entry_id='p')])
    out = finalize_ownership(elements, result, settings=ReviewSettings(enabled=True, api_key='mock'), transport=lambda *_:'{"operations":[]}', review=True)
    out.sections[0].entries[1].parent_entry_id = None
    with pytest.raises(ValueError, match='relationships changed'):
        map_schema(SchemaMappingRequest(elements=elements, sections=out))


def test_focused_package_excludes_unrelated_records_and_keeps_style_evidence():
    elements, result = fixture(['Atlas', 'Unclear continuation', 'Beacon', 'Built services.', 'Cedar', 'Built tooling.'], [
        entry('a', [0], {'title':[0]}), entry('b', [2, 3], {'title':[2], 'responsibilities':[3]}),
        entry('c', [4, 5], {'title':[4], 'responsibilities':[5]})])
    elements[1].metadata = {'font': {'weight':'bold'}, 'table_cell': {'row':1,'column':2}}
    from local_api.services.source_ownership import ambiguity_package
    package = ambiguity_package(snapshot(elements, result), result)
    assert {row['element'] for row in package['spans']} == {0, 1, 2, 3}
    assert package['spans'][1]['source_metadata'] == elements[1].metadata
    assert package['ambiguities'][0]['question']


def test_create_parent_and_link_existing_children_uses_only_source_evidence():
    elements, result = fixture(['Portfolio', 'Atlas', 'Built services.', 'Beacon', 'Built workflows.'], [
        entry('a', [1, 2], {'title':[1], 'responsibilities':[2]}), entry('b', [3, 4], {'title':[3], 'responsibilities':[4]})])
    state = snapshot(elements, result)
    parent_sid = state.spans[0].source_id
    parent = 'projects@'+parent_sid
    children = [state.owners[state.spans[i].source_id].record for i in (1, 3)]
    operations = [{'op':'create_group', 'section':'projects', 'source_ids':[parent_sid]},
                  {'op':'assign', 'source_ids':[parent_sid], 'record':parent, 'section':'projects', 'fields':['title']}]
    operations += [{'op':'link_parent', 'record':child, 'parent':parent} for child in children]
    repaired = apply_operations(state, operations, {'projects'})
    out = materialize(elements, result, repaired)
    assert len(out.sections[0].logical_blocks[0]['children']) == 2
    assert out.sections[0].entries[0].record_kind == 'group'
    assert not validate_result(elements, out)
    assert repaired.spans == state.spans


def test_field_review_cannot_resplit_accepted_canonical_records():
    from local_api.services.llm_schema_mapping import local_section_payload, parse_review
    elements, result = fixture(['Atlas Platform', 'Built services.'], [entry('a', [0, 1], {'title':[0], 'responsibilities':[1]})])
    out = finalize_ownership(elements, result, settings=ReviewSettings(enabled=True, api_key='mock'), transport=lambda *_:'{"operations":[]}', review=True)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=out))
    payload = {'sections': local_section_payload(mapped, {'projects'})}
    row = payload['sections'][0]['records'][0]
    row['source_ids'] = row['source_ids'][:1]
    with pytest.raises(ValueError):
        parse_review(json.dumps(payload), out)


def test_hierarchy_renderers_execute_actual_javascript(tmp_path):
    import subprocess
    elements, result = fixture(['Research portfolio', 'Atlas Platform', 'Built services.'], [
        entry('p', [0], {'title':[0]}, record_kind='group'), entry('a', [1, 2], {'title':[1], 'responsibilities':[2]}, parent_entry_id='p')])
    out = finalize_ownership(elements, result, settings=ReviewSettings(enabled=True, api_key='mock'), transport=lambda *_:'{"operations":[]}', review=True)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=out))
    sections_file, schema_file = tmp_path/'sections.json', tmp_path/'schema.json'
    sections_file.write_text(out.model_dump_json())
    schema_file.write_text(mapped.model_dump_json())
    subprocess.run(['node', 'tests/semantic_ownership_ui.cjs', str(sections_file), str(schema_file)], check=True, capture_output=True, text=True)


def test_orphan_parent_group_is_not_silently_resolved():
    elements, result = fixture(['Research portfolio'], [entry('p', [0], {'title':[0]}, record_kind='group')])
    out = finalize_ownership(elements, result)
    assert out.status == 'needs_review'
    assert snapshot(elements, out).owners['e0:0:18'].status == 'needs_review'


def test_wrapped_credential_merge_is_source_preserving_and_cross_lane_safe():
    elements, result = fixture(['Cloud Security', 'Awareness Program'], [entry('a', [0], {'title':[0]}), entry('b', [1], {'title':[1]})], category='certifications')
    state = snapshot(elements, result)
    records = [state.owners[span.source_id].record for span in state.spans]
    merged = apply_operations(state, [{'op':'merge', 'records':records}], {'certifications'})
    out = materialize(elements, result, merged)
    assert len(out.sections[0].entries) == 1
    assert out.sections[0].entries[0].block_indices == [0, 1]
    assert ''.join(s.text for s in merged.spans) == ''.join(e.text for e in elements)
    result.sections[0].blocks[1].lane = 'right'
    with pytest.raises(ValueError, match='lanes'):
        apply_operations(snapshot(elements, result), [{'op':'merge', 'records':records}], {'certifications'})
