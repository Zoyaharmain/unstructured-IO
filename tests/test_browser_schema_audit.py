"""Browser judge is automatic in reviewed mode, source-bound, and read-only."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from test_schema_mapping import sample
from local_api.schemas.sections import SectionResponse
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.llm_section_review import ReviewSettings
from local_api.services import schema_audit


@pytest.fixture
def mapped_input(monkeypatch, tmp_path):
    monkeypatch.setenv('RESUME_AUDIT_LOG_DIR', str(tmp_path))
    request = sample()
    mapped = map_schema(request)
    sections = SectionResponse.model_validate(mapped.meta.get('reviewed_sections', request.sections.model_dump()))
    return request, sections, mapped


def settings(**kw):
    return replace(ReviewSettings(enabled=True, api_key='test-key'), **kw)


def clean(config, messages):
    body = json.loads(messages[1]['content'])
    return json.dumps({'checked_ids': [t['id'] for t in body['targets']], 'findings': []})


def test_clean_complete_read_only_and_private_diagnostics(mapped_input, tmp_path):
    req, sections, mapped = mapped_input
    before = deepcopy((req.model_dump(), sections.model_dump(), mapped.model_dump()))
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True,
                                       settings=settings(), transport=clean)
    assert result['status'] == 'complete' and result['outcome'] == 'no_findings'
    assert result['coverage']['checked_units'] == result['coverage']['expected_units'] > 0
    assert 'messages' not in json.dumps(result) and 'context_by_record' not in json.dumps(result)
    assert before == (req.model_dump(), sections.model_dump(), mapped.model_dump())
    log = tmp_path / result['diagnostic']['id']
    assert (log / 'result.json').exists() and (log / 'call-001-response.json').exists()
    assert (log / 'input.json').stat().st_mode & 0o077 == 0


def test_findings_and_incomplete_coverage(mapped_input):
    req, sections, mapped = mapped_input
    def finding(config, messages):
        body = json.loads(messages[1]['content'])
        target = next(t for t in body['targets'] if t['kind'] == 'source_omission_check' and t['text'].strip())
        return json.dumps({'checked_ids': [t['id'] for t in body['targets']], 'findings': [
            {'field': target['id'], 'issue': 'Inspect this source assignment.', 'source_ids': target['source_ids']}]})
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True,
                                       settings=settings(), transport=finding)
    assert result['status'] == 'complete' and result['outcome'] == 'issues_found'
    assert result['findings'][0]['source_ids']
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True,
        settings=settings(), transport=lambda *_: '{"checked_ids":[],"findings":[]}')
    assert result['status'] == 'incomplete' and result['outcome'] == 'unknown'
    assert result['errors'][0]['code'] == 'incomplete_audit_coverage'


def test_provider_failure_and_planning_failure_retain_mapping(mapped_input, monkeypatch):
    req, sections, mapped = mapped_input
    original = mapped.model_dump()
    def broken(*_):
        raise RuntimeError('PRIVATE RESUME OR SECRET')
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True,
                                       settings=settings(), transport=broken)
    assert result['status'] == 'incomplete' and result['provider_calls'] == 1
    assert 'PRIVATE' not in json.dumps(result)
    def invalid(*a, **kw):
        a[1].sections.clear()  # Prove the adapter supplied a detached copy.
        raise ValueError('PRIVATE')
    monkeypatch.setattr(schema_audit, 'run_schema_audit', invalid)
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True, settings=settings())
    assert result['status'] == 'incomplete' and sections.sections
    assert mapped.model_dump() == original


def test_local_only_never_calls_provider_or_reads_configuration(mapped_input, monkeypatch):
    req, sections, mapped = mapped_input
    monkeypatch.setattr(ReviewSettings, 'from_env', lambda: pytest.fail('Local mode read provider configuration'))
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=False,
                                       transport=lambda *_: pytest.fail('External call'))
    assert result['status'] == 'not_requested' and result['provider_calls'] == 0


def test_local_endpoint_never_calls_provider_even_when_configured(monkeypatch):
    from local_api.routes.schema_mapping import map_existing_sections
    monkeypatch.setenv('DEEPSEEK_REVIEW_ENABLED', 'true')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'must-not-be-used')
    monkeypatch.setattr(schema_audit, 'call_deepseek', lambda *_: pytest.fail('Local endpoint made a provider call'))
    out = asyncio.run(map_existing_sections(ReviewedSchemaMappingRequest(**sample().model_dump(), review_fields=False)))
    assert out.meta['schema_audit']['status'] == 'not_requested'
    assert out.consumer_export['processing_metadata']['schema_audit']['provider_calls'] == 0


def test_unconfigured_review_is_not_a_clean_audit(mapped_input):
    req, sections, mapped = mapped_input
    out = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True, settings=ReviewSettings())
    assert out['status'] == 'not_configured' and out['outcome'] == 'unknown'
    assert out['errors'] and out['provider_calls'] == 0


def test_http_response_keeps_compact_audit_metadata_in_download(monkeypatch):
    from fastapi.testclient import TestClient
    from local_api.app import app
    from local_api.services import llm_schema_mapping
    req = sample()
    mapped = map_schema(req)
    monkeypatch.setattr(llm_schema_mapping, 'map_with_field_review', lambda *_: mapped)
    audit = {'status': 'complete', 'outcome': 'issues_found', 'findings': [
        {'field': 'source:e0:0:11', 'issue': 'Inspect this association.', 'source_ids': ['e0:0:11']}],
        'partial_findings': [], 'coverage': {'expected_units': 1, 'checked_units': 1},
        'provider_calls': 1, 'errors': []}
    monkeypatch.setattr(schema_audit, 'audit_mapping', lambda *a, **kw: deepcopy(audit))
    with TestClient(app) as client:
        response = client.post('/api/v1/resume/schema', json={**req.model_dump(mode='json'), 'review_fields': True})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['meta']['schema_audit'] == audit
    assert data['consumer_export']['processing_metadata']['schema_audit'] == audit
    assert any(i['kind'] == 'schema_audit' for i in data['meta']['reviewed_sections']['review_issues'])
    assert 'messages' not in json.dumps(data['meta']['schema_audit'])


def test_prior_calls_exhaust_shared_budget(mapped_input):
    req, sections, mapped = mapped_input
    sections.metadata['llm_review'] = {'status': 'complete', 'provider_calls': 2}
    sections.metadata['structure_review'] = {'provider_calls': 1}
    mapped.meta['field_review'] = {'provider_calls': 1}
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True,
        settings=settings(max_document_requests=4), transport=lambda *_: pytest.fail('Budget exceeded'))
    assert result['status'] == 'incomplete' and result['provider_calls'] == 0
    assert result['errors'][0]['code'] == 'request_budget_exhausted'


@pytest.mark.parametrize('audit_status,findings', [('complete', []), ('complete', [
    {'field': 'source:e0:0:11', 'issue': 'Inspect name association.', 'source_ids': ['e0:0:11']}]), ('incomplete', [])])
def test_endpoint_returns_usable_export_and_needs_review(mapped_input, monkeypatch, audit_status, findings):
    from local_api.routes import schema_mapping as route
    from local_api.services import llm_schema_mapping
    req, sections, mapped = mapped_input
    sections.metadata['llm_review'] = {'status': 'failed', 'provider_calls': 1}
    mapped.meta['reviewed_sections'] = sections.model_dump(mode='json')
    mapped.meta['field_review'] = {'status': 'failed', 'provider_calls': 1}
    mapped.meta['mapping_result'] = {'status': 'fallback_used', 'fallback_used': True}
    original = mapped.data.model_dump()
    monkeypatch.setattr(llm_schema_mapping, 'map_with_field_review', lambda *_: mapped)
    seen = []
    def audit(elements, latest, value, *, requested):
        assert latest.metadata['llm_review']['status'] == 'failed'
        assert value.standardized_data is not None
        seen.append(requested)
        return {'status': audit_status, 'findings': findings, 'partial_findings': [],
                'coverage': {}, 'provider_calls': 1, 'errors': []}
    monkeypatch.setattr(schema_audit, 'audit_mapping', audit)
    out = asyncio.run(route.map_existing_sections(ReviewedSchemaMappingRequest(**req.model_dump(), review_fields=True)))
    assert seen == [True] and out.data.model_dump() == original
    assert out.meta['mapping_result']['status'] == 'fallback_used'
    assert out.consumer_export['processing_metadata']['schema_audit']['status'] == audit_status
    assert out.validation_status.requires_human_review
    issues = out.meta['reviewed_sections']['review_issues']
    if findings:
        assert any(i['kind'] == 'schema_audit' and i['source_ids'] == findings[0]['source_ids'] for i in issues)
    if audit_status == 'incomplete':
        assert any(i.get('stage') == 'schema_audit' for i in issues)


def test_partial_findings_survive_failed_later_chunk(mapped_input):
    req, sections, mapped = mapped_input
    calls = 0
    def provider(config, messages):
        nonlocal calls
        calls += 1
        body = json.loads(messages[1]['content'])
        if calls == 1:
            unit = next(t for t in body['targets'] if t['source_ids'])
            return json.dumps({'checked_ids': [t['id'] for t in body['targets']], 'findings': [
                {'field': unit['id'], 'issue': 'Inspect value.', 'source_ids': unit['source_ids']}]})
        raise RuntimeError('provider failed')
    result = schema_audit.audit_mapping(req.elements, sections, mapped, requested=True,
        settings=settings(max_units=2, max_document_requests=200, max_pass_requests=200), transport=provider)
    assert result['status'] == 'incomplete'
    assert result['partial_findings'] and result['coverage']['chunks_completed'] >= 1
