"""Nested mapping must preserve source, boundaries, and unresolved information."""
import importlib.util
from pathlib import Path
from copy import deepcopy
from local_api.services.schema_mapping import map_schema
from local_api.services.section_subschemas import build_subschemas

spec = importlib.util.spec_from_file_location('mapping_sample', Path(__file__).with_name('test_schema_mapping.py'))
sample_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample_module)
sample = sample_module.sample


def test_nested_contact_and_jobs_have_individual_exact_evidence():
    request = sample(); before = deepcopy(request.model_dump())
    out = map_schema(request)
    source = {f'e{b.source_element_index}:{b.start}:{b.end}': b.text for s in request.sections.sections for b in s.blocks}
    contact = next(s for s in out.section_schemas if s.category == 'personal_information')
    fields = {a.name: a for a in contact.records[0].attributes}
    assert fields['full_name'].items[0].value == 'Alex Morgan'
    assert fields['phone'].status == 'unresolved'
    for section in out.section_schemas:
        for record in section.records:
            for field in record.attributes:
                for item in field.items:
                    assert item.evidence
                    assert all(ref.quote in source[ref.source_id] for ref in item.evidence)
    assert request.model_dump() == before


def test_unsupported_value_is_not_inherited_from_another_record():
    request = sample(); out = map_schema(request)
    out.data.experience[0].company = 'Invented employer'
    nested = build_subschemas(request.sections, out.data, {'candidate_resume': True})
    job = next(s for s in nested if s.category == 'experience').records[0]
    assert next(a for a in job.attributes if a.name == 'company').items == []
    assert next(a for a in job.attributes if a.name == 'role').items


def test_fragments_do_not_hide_rest_of_block_and_unlabelled_awards_stay_unresolved():
    out = map_schema(sample())
    job = next(s for s in out.section_schemas if s.category == 'experience')
    assert any('Acme Ltd |' in b.quote for b in job.residual_blocks)
    awards = next(s for s in out.section_schemas if s.category == 'awards')
    assert all(not a.items for a in awards.records[0].attributes)
    assert awards.residual_blocks[0].quote == 'Regional community prize'


def test_ambiguous_associations_remain_flagged():
    request = sample()
    entry = next(s for s in request.sections.sections if s.category == 'experience').entries[0]
    entry.relationship_status = 'needs_review'; entry.review_reasons = ['Uncertain employer/date association']
    job = next(s for s in map_schema(request).section_schemas if s.category == 'experience').records[0]
    assert job.review_reasons
    assert all(item.status == 'needs_review' for a in job.attributes for item in a.items)


def test_non_resume_does_not_populate_candidate_attributes():
    request = sample(); data = map_schema(request).data
    nested = build_subschemas(request.sections, data, {'candidate_resume': False})
    assert all(not s.records for s in nested)
    assert sum(len(s.residual_blocks) for s in nested) == sum(len(s.blocks) for s in request.sections.sections)


def test_nested_contract_is_returned_by_http_and_has_discoverable_definition():
    from fastapi.testclient import TestClient
    from local_api.app import app
    with TestClient(app) as client:
        response = client.post('/api/v1/resume/schema', json=sample().model_dump())
        assert response.status_code == 200
        assert response.json()['section_schemas'][0]['records'][0]['attributes']
        assert client.get('/api/v1/resume/schema/subschema-definition').json()['title'] == 'SectionSchema'


def test_bulleted_languages_map_separately_with_exact_unicode_evidence():
    from local_api.schemas.sections import SectionResponse, ResumeSection, SectionBlock
    from local_api.vendor.handoff_schema.models import ResumeSchema, ContactInfo
    texts = ['LANGUAGES', 'English - Full Professional Proficiency (C1)', '\u2022',
             'Fran\u00e7ais - D\u00e9butant (cours intensif en cours)']
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(text), text=text,
              page_number=1, lane='source', assignment='section_heading' if i == 0 else 'semantic',
              reason='source') for i, text in enumerate(texts)]
    sections = SectionResponse(status='provisional', sections=[ResumeSection(category='languages',
               label='Languages', blocks=blocks, text='\n'.join(texts))], needs_review=[], metadata={}, warnings=[])
    data = ResumeSchema(contact=ContactInfo(full_name='', email='', phone=''))
    before = deepcopy(sections.model_dump())
    for combined in (False, True):
        if combined:
            text = '\u2022 ' + texts[1] + ' \u2022 ' + texts[3]
            sections.sections[0].blocks = [blocks[0], blocks[1].model_copy(update={'text': text, 'end': len(text)})]
            sections.sections[0].text = texts[0] + '\n' + text
        result = build_subschemas(sections, data, {'candidate_resume': True})[0]
        assert len(result.records) == 2
        for record, expected in zip(result.records, [('English', 'Full Professional Proficiency (C1)'),
                                      ('Fran\u00e7ais', 'D\u00e9butant (cours intensif en cours)')]):
            assert not record.review_reasons
            for attr, value in zip(record.attributes, expected):
                assert attr.status == 'mapped'
                assert attr.items[0].value == value
                assert attr.items[0].status == 'source_supported'
                assert attr.items[0].evidence[0].quote == value
        assert all(b.quote in {'LANGUAGES', '\u2022'} for b in result.residual_blocks)
        if not combined:
            assert sections.model_dump() == before


def test_language_without_proficiency_does_not_invent_a_level():
    from local_api.schemas.sections import SectionResponse, ResumeSection, SectionBlock
    data = map_schema(sample()).data
    block = SectionBlock(source_element_index=0, start=0, end=7, text='English',
                         page_number=1, lane='source', assignment='semantic', reason='source')
    sections = SectionResponse(status='provisional', sections=[ResumeSection(category='languages',
        label='Languages', blocks=[block], text='English')], needs_review=[], metadata={}, warnings=[])
    record = build_subschemas(sections, data, {'candidate_resume': True})[0].records[0]
    assert record.attributes[0].items[0].value == 'English'
    assert record.attributes[1].status == 'unresolved'
    assert record.review_reasons
