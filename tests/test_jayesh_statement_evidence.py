"""Saved Jayesh source regressions; never call a live provider.

The current live response was not persisted. Candidate variants below are
explicitly controlled reproductions, not claimed captures of that response.
"""
import json
import re
from pathlib import Path

import pytest

from local_api.schemas.sections import SectionResponse, SectionRequest
from local_api.schemas.extraction import ExtractedElement
from local_api.services.llm_schema_mapping import parse_review
from local_api.services.schema_diagnostics import MappingValidationError, diagnose, client_diagnostic
from local_api.services.source_fragments import citations
from local_api.services.llm_section_review import review_sections, ReviewSettings

SAVED = Path(__file__).resolve().parents[1] / 'reports/single-jayesh-feedback-live-20261022'


def candidate():
    sections = SectionResponse.model_validate(json.loads((SAVED / 'sections.json').read_text()))
    summary = next(s for s in sections.sections if s.category == 'summary')
    blocks = [b for b in summary.blocks if b.source_element_index == 2]
    paragraph = ''.join(b.text for b in blocks)
    statements = re.split(r'(?<=\.)\s+', paragraph)[:4]
    assert len(statements) == 4 and statements[3].startswith('Experienced in client- facing')
    items = [{'value': value, 'evidence': citations(value, blocks)} for value in statements]
    payload = {'sections': [{'category': 'summary', 'records': [{
        'record_id': 'summary-1', 'source_ids': [f'e{b.source_element_index}:{b.start}:{b.end}' for b in blocks],
        'fields': {'statements': items, 'total_experience_years': []},
        'missing': {'total_experience_years': 'not_stated'}}]}]}
    return sections.model_copy(update={'sections': [summary], 'needs_review': []}), payload


def test_saved_jayesh_literal_fourth_statement_passes_across_split_blocks():
    sections, payload = candidate()
    hierarchy, _, _ = parse_review(json.dumps(payload), sections)
    item = hierarchy[0].records[0].attributes[0].items[3]
    assert len(item.evidence) == 3
    assert item.evidence[0].source_id == 'e2:439:551'
    assert item.evidence[-1].source_id == 'e2:662:772'


def test_jayesh_rewritten_fourth_statement_remains_rejected_without_source_text_logging(monkeypatch):
    sections, payload = candidate()
    item = payload['sections'][0]['records'][0]['fields']['statements'][3]
    item['value'] = item['value'].replace('client- facing', 'client-facing')
    with pytest.raises(MappingValidationError) as error:
        parse_review(json.dumps(payload), sections)
    diagnostic = diagnose(error.value, 'response_model_validation')
    assert diagnostic['code'] == 'unsupported_value'
    assert diagnostic['field'] == 'statements'
    assert diagnostic['path'].endswith('/items/3/value')
    assert diagnostic['evidence_analysis'] == {
        'item_index': 3, 'value_length': len(item['value']), 'evidence_count': 3,
        'all_quotes_valid': True, 'literal_in_record': False, 'whitespace_match_in_record': False,
        'evidence_source_ids': [ref['source_id'] for ref in item['evidence']],
        'evidence_quote_lengths': [len(ref['quote']) for ref in item['evidence']]}
    assert item['value'] not in json.dumps(diagnostic)
    monkeypatch.setenv('RESUME_APP_ENV', 'production')
    assert set(client_diagnostic(diagnostic)) == {'id', 'category', 'code', 'field', 'validation_message'}


def test_jayesh_invented_statement_is_rejected():
    sections, payload = candidate()
    payload['sections'][0]['records'][0]['fields']['statements'][3]['value'] = 'Managed an invented lunar accounting office.'
    with pytest.raises(MappingValidationError) as error:
        parse_review(json.dumps(payload), sections)
    assert error.value.code == 'unsupported_value'
    assert error.value.field == 'statements'


def test_saved_placement_review_preserves_element_offsets_and_exact_source_text():
    extraction = json.loads((SAVED / 'extraction.json').read_text())
    assert len(extraction['elements']) == 55
    request = SectionRequest(elements=[ExtractedElement.model_validate(e) for e in extraction['elements']])
    local = SectionResponse.model_validate(json.loads((SAVED / 'local-sections.json').read_text()))
    content = json.loads((SAVED / 'provider-response-1.json').read_text())['content']
    reviewed = review_sections(request, local, settings=ReviewSettings(enabled=True, api_key='mock-only'),
                              transport=lambda *_: content)
    assert reviewed.metadata['llm_review']['status'] == 'complete'
    assert reviewed.metadata['llm_review']['changed_units'] == 18  # saved run, not the unsaved live ten-change run
    for section in reviewed.sections:
        for block in section.blocks:
            assert request.elements[block.source_element_index].text[block.start:block.end] == block.text
    before = {(b.source_element_index, b.start, b.end) for s in local.sections for b in s.blocks}
    before |= {(b.source_element_index, b.start, b.end) for b in local.needs_review}
    after = {(b.source_element_index, b.start, b.end) for s in reviewed.sections for b in s.blocks}
    after |= {(b.source_element_index, b.start, b.end) for b in reviewed.needs_review}
    # Record construction can merge/split non-summary spans; IDs are generated
    # from the resulting ranges, not inherited from the previous inventory.
    assert {ref for ref in before if ref[0] == 2} == {ref for ref in after if ref[0] == 2}
    from local_api.services.source_validation import validate_result
    assert validate_result(request.elements, reviewed) == []
    from local_api.services.llm_schema_mapping import messages
    supplied = json.loads(messages(reviewed.sections)[1]['content'])
    for section in supplied['sections']:
        for block in section['blocks']:
            _, index, start, end = re.fullmatch(r'(e)(\d+):(\d+):(\d+)', block['source_id']).groups()
            assert block['text'] == request.elements[int(index)].text[int(start):int(end)]


def test_evidence_analysis_rejects_private_or_unrecognized_metadata():
    error = MappingValidationError('source_evidence_validation', 'unsupported_value',
        field='statements', evidence_analysis={
            'item_index': 3, 'private_resume': 'SECRET',
            'evidence_source_ids': ['SECRET'], 'evidence_quote_lengths': ['SECRET'],
            'literal_in_record': 'SECRET'})
    diagnostic = diagnose(error, 'response_model_validation')
    assert diagnostic['evidence_analysis'] == {'item_index': 3}
    assert 'SECRET' not in json.dumps(diagnostic)
