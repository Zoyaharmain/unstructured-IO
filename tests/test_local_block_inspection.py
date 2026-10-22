from fastapi.testclient import TestClient
from local_api.app import app
from local_api.routes import sections as route
from local_api.schemas.sections import SectionResponse, SectionBlock, ResumeSection


def test_local_inspection_skips_llm_even_when_enabled(monkeypatch):
    monkeypatch.setenv('DEEPSEEK_REVIEW_ENABLED', 'true')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'private-test-key')
    text = 'Python and SQL'
    block = SectionBlock(source_element_index=0, start=0, end=len(text), text=text,
                         page_number=1, assignment='semantic', reason='Local model', lane='main',
                         cluster_id=0, similarity=0.6)
    local = SectionResponse(status='provisional', sections=[ResumeSection(category='skills', label='Skills',
        text=text, blocks=[block])], needs_review=[], metadata={}, warnings=[])
    stages = []
    monkeypatch.setattr(route, 'detect_sections', lambda req: stages.append('detect') or local.model_copy(deep=True))
    monkeypatch.setattr(route, 'recover_sections', lambda req, result: stages.append('recover') or result)
    def forbidden(*args, **kwargs):
        raise AssertionError('Local inspection entered external review')
    monkeypatch.setattr(route, 'review_sections', forbidden)
    from local_api.services import llm_section_review
    monkeypatch.setattr(llm_section_review, 'provider_json', forbidden)
    response = TestClient(app).post('/api/v1/resume/sections/local', json={
        'elements': [{'type': 'NarrativeText', 'text': text, 'page_number': 1, 'metadata': {}}]})
    assert response.status_code == 200
    data = response.json()
    assert stages == ['detect', 'recover']
    assert data['metadata']['inspection_mode'] == 'local_only'
    assert data['metadata']['llm_review']['provider_calls'] == 0
    assert data['sections'][0]['blocks'][0]['text'] == text
    assert data['sections'][0]['blocks'][0]['reviewed_by_llm'] is False
