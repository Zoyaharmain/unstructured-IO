"""Expertise heading recovery and unresolved-only contextual review."""
import json
from copy import deepcopy
import pytest
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionRequest,SectionResponse,SectionBlock
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.llm_section_review import review_sections,ReviewSettings,source_ledger,assert_coverage
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload


def expertise_fixture():
    texts=['Example Person','example@example.org','AREAS OF EXPERTISE & INTEREST',
      'Platform Architecture: Designed reliable platforms across distributed teams and multiple delivery groups. Program Leadership: Led strategic programs with governance and measurable business outcomes.',
      'Migration Expertise: Led successful cloud migrations for business platforms. • Business Strategy: Managed growth initiatives and secured new partnerships.',
      'EXPERIENCE','Engineer | Example Ltd | Jan 2020 – Present','Built reliable services.']
    elements,sections=fixture(texts,{'personal_information':[0,1],'experience':[5,6,7]},[2,3,4])
    elements[2].type=elements[5].type='Title'
    return texts,elements,sections


def test_labeled_expertise_maps_to_skills_and_profile_with_literal_evidence():
    texts,elements,sections=expertise_fixture();before=deepcopy([e.model_dump() for e in elements])
    req=SchemaMappingRequest(elements=elements,sections=sections);out=map_schema(req)
    names={'Platform Architecture','Program Leadership','Migration Expertise','Business Strategy'}
    assert names<=set(out.data.skills.domain_and_functional)
    assert 'Designed reliable platforms' in out.data.summary and 'secured new partnerships' in out.data.summary
    revised=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert not revised.needs_review and not validate_result(elements,revised)
    assert [e.model_dump() for e in elements]==before
    assert len(out.data.experience)==1 and out.data.experience[0].company=='Example Ltd'
    again=map_schema(req.model_copy(update={'sections':revised}))
    assert names<=set(again.data.skills.all_skills)


def test_field_review_cannot_omit_competency_names_and_descriptions():
    texts,elements,sections=expertise_fixture();req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req);payload=local_section_payload(local,{s.category for s in local.section_schemas if s.category!='needs_review'})
    for row in payload:
        if row['category'] not in {'skills','summary'}:continue
        fields=row['records'][0]['fields']
        for name in fields:fields[name]=[];row['records'][0]['missing'][name]='unmapped'
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        return json.dumps({'sections':[s for s in payload if s['category'] in categories]})
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert out.meta['field_review']['status']=='complete'
    assert 'Platform Architecture' in out.data.skills.domain_and_functional
    assert 'Designed reliable platforms' in out.data.summary and 'secured new partnerships' in out.data.summary


def fallback_fixture():
    elements,sections=fixture(['Example Person','example@example.org','Engineer | Example Ltd | Jan 2020 – Present','C# and Rust'],{'personal_information':[0,1],'experience':[2]},[3])
    original=sections.needs_review[0]
    sections.needs_review=[original.model_copy(update={'start':0,'end':7,'text':'C# and '}),original.model_copy(update={'start':7,'end':11,'text':'Rust'})]
    return elements,sections


@pytest.mark.parametrize('chunked',[False,True])
def test_second_pass_reviews_only_unresolved_with_full_paragraph_context(chunked):
    elements,sections=fallback_fixture();seen=[]
    def transport(settings,messages):
        doc=json.loads(messages[1]['content']);targets=doc.get('spans',doc.get('targets'))
        contextual=doc.get('review_mode')=='unresolved_contextual_review' or 'Targeted second review' in messages[0]['content']
        seen.append((contextual,doc))
        if contextual:
            assert {t.get('source_element',t.get('source_element_index')) for t in targets}=={3}
            assert doc.get('context_read_only') is True
            context=json.dumps(doc.get('unresolved_groups',doc.get('context')))
            assert 'C# and Rust' in context
        return json.dumps({'assignments':[[t['id'],'skills' if contextual else t['current_category']] for t in targets]})
    settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=1,max_units=1 if chunked else 1000,max_input_chars=1000000,max_input_tokens=1000000,max_context_tokens=1016000)
    out=review_sections(SectionRequest(elements=elements),sections,settings=settings,transport=transport)
    assert out.metadata['llm_review']['status']=='complete' and out.metadata['llm_review']['pass_count']==2
    assert not out.needs_review and out.metadata['llm_review']['classification_complete']
    assert any(targeted for targeted,_ in seen)
    before=next(s for s in sections.sections if s.category=='experience');after=next(s for s in out.sections if s.category=='experience')
    assert [e.block_indices for e in after.entries]==[e.block_indices for e in before.entries]
    assert_coverage(elements,source_ledger(out));assert not validate_result(elements,out)


def test_genuine_abstention_is_not_described_as_confirmed_placement():
    elements,sections=fallback_fixture()
    def transport(settings,messages):
        doc=json.loads(messages[1]['content']);targets=doc['spans']
        return json.dumps({'assignments':[[t['id'],t['current_category']] for t in targets],**({'abstention_reasons':{t['id']:'The source does not establish the intended section.' for t in targets}} if doc.get('review_mode') else {})})
    out=review_sections(SectionRequest(elements=elements),sections,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=1,max_units=1000,max_input_chars=1000000,max_input_tokens=1000000,max_context_tokens=1016000),transport=transport)
    assert out.needs_review and not out.metadata['llm_review']['classification_complete']
    assert all(b.llm_action=='abstained' and 'confirmed placement' not in b.reason for b in out.needs_review)
    assert all('source does not establish' in b.reason for b in out.needs_review)


def test_locally_recovered_competencies_are_reviewed_without_separator_targets():
    texts,elements,sections=expertise_fixture();calls=[]
    def transport(settings,messages):
        document=json.loads(messages[1]['content']);calls.append(document)
        assert all(span['text'].strip() for span in document['spans'])
        assert any('Designed reliable platforms' in span['text'] for span in document['spans'])
        return json.dumps({'assignments':[[span['id'],span['current_category']] for span in document['spans']]})
    out=review_sections(SectionRequest(elements=elements),sections,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=1,max_units=1000,max_input_chars=1000000,max_input_tokens=1000000,max_context_tokens=1016000),transport=transport)
    assert out.metadata['llm_review']['status']=='complete' and len(calls)==1
    assert not out.needs_review and not validate_result(elements,out)
    assert all(block.text.strip() for section in out.sections for block in section.blocks)
