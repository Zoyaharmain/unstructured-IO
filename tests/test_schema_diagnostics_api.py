"""HTTP diagnostics and fallback contract; live provider calls forbidden."""
import json
import pytest
from fastapi.testclient import TestClient
from local_api.app import app
from local_api.services import llm_schema_mapping as service
from test_llm_schema_mapping import fixture, configured


@pytest.mark.parametrize('mode', ['development', 'production'])
def test_field_failure_http_retains_original_diagnostic_and_usable_local_result(monkeypatch, mode):
    monkeypatch.setenv('RESUME_APP_ENV', mode)
    request, _ = fixture()
    original = service.map_with_field_review
    monkeypatch.setattr(service, 'map_with_field_review', lambda req: original(req,
        settings=configured(recovery_attempts=0), transport=lambda *_: 'malformed provider JSON'))
    with TestClient(app) as client:
        response = client.post('/api/v1/resume/schema', json=request.model_dump() | {'review_fields': True})
    assert response.status_code == 200
    data = response.json()
    assert data['meta']['field_review']['status'] == 'failed'
    assert data['meta']['mapping_result']['status'] == 'fallback_used'
    assert data['meta']['mapping_result']['usable'] is True
    diagnostic = data['meta']['field_review']['diagnostic']
    assert diagnostic['category'] == 'json_parsing'
    assert ('exception_type' in diagnostic) == (mode == 'development')
    assert diagnostic['validation_message'] == 'Provider response is not valid JSON.'
    assert diagnostic['code'] == 'invalid_json'
    assert ('path' in diagnostic) == (mode == 'development')


def test_invalid_source_is_failed_without_usable_fallback(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, _ = fixture()
    payload = request.model_dump() | {'review_fields': True}
    payload['sections']['sections'][0]['blocks'][0]['text'] = 'changed source'
    def forbidden(*args): pytest.fail('Provider must not be called')
    monkeypatch.setattr(service, 'call_deepseek', forbidden)
    with TestClient(app) as client:
        response = client.post('/api/v1/resume/schema', json=payload)
    assert response.status_code == 422
    detail = response.json()['detail']
    assert detail['mapping_result']['status'] == 'failed'
    assert detail['mapping_result']['usable'] is False
    assert detail['diagnostic']['category'] == 'source_binding_validation'


def test_invalid_query_path_fails_before_field_review(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, _ = fixture()
    def forbidden(*args): pytest.fail('Invalid query must not enter provider review')
    monkeypatch.setattr(service, 'map_with_field_review', forbidden)
    with TestClient(app) as client:
        response = client.post('/api/v1/resume/schema/query', json=request.model_dump() |
            {'query_path': 'experience.unknown', 'review_fields': True})
    assert response.status_code == 422
    assert response.json()['detail']['diagnostic']['category'] == 'subschema_path_validation'
