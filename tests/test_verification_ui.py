from fastapi.testclient import TestClient
from local_api.app import app

client = TestClient(app)


def compare(reference, extracted, **kwargs):
    return client.post('/api/v1/compare/text', json=dict(reference=reference, extracted=extracted, **kwargs))


def test_ui_and_local_assets():
    response = client.get('/')
    assert response.status_code == 200
    assert 'Resume Inspector' in response.text
    for asset in ['app.js', 'styles.css', 'docx-preview.html', 'docx-frame.js', 'vendor/jszip.min.js', 'vendor/docx-preview.min.js']:
        assert client.get('/static/' + asset).status_code == 200
    assert client.get('/docs').status_code == 200


def test_whitespace_normalized_reference_match():
    data = compare('Python\nSQL  experience', 'Python SQL\nexperience').json()
    assert data['reference_coverage'] == 100
    assert data['missing_words'] == data['extra_words'] == 0


def test_repeated_words_are_not_deduplicated():
    data = compare('Python SQL Python', 'Python SQL').json()
    assert data['matched_words'] == 2
    assert data['missing_words'] == 1
    assert data['reference_words'] == 3
    assert data['reference_coverage'] == 66.7


def test_replacement_has_both_missing_and_extra_words():
    data = compare('Built Python services', 'Built Java services').json()
    assert data['matched_words'] == 2
    assert data['missing_words'] == data['extra_words'] == 1
    assert {'kind': 'replace', 'reference': 'Python', 'extracted': 'Java'} in data['segments']


def test_case_and_punctuation_controls():
    assert compare('Python', 'python').json()['matched_words'] == 0
    assert compare('Python', 'python', ignore_case=True).json()['matched_words'] == 1
    assert compare('Python.', 'Python', ignore_case=True).json()['matched_words'] == 0


def test_empty_extraction_reports_all_reference_words_missing():
    data = compare('Python SQL experience', '').json()
    assert data['reference_coverage'] == 0
    assert data['missing_words'] == 3
    assert data['extra_words'] == 0


def test_reordering_is_not_reported_as_exact_match():
    data = compare('Education Skills Experience', 'Experience Education Skills').json()
    assert data['matched_words'] < 3
    assert data['missing_words'] > 0 and data['extra_words'] > 0


def test_comparison_limits_and_blank_reference():
    assert compare('   \n', 'text').status_code == 422
    assert compare('word ' * 5001, 'text').status_code == 422
    assert compare('word', 'x' * 100001).status_code == 422
