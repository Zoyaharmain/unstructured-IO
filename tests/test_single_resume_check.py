import json
import pytest
from scripts.check_single_resume import parse_audit


def test_schema_audit_requires_real_source_evidence():
    finding = {'field': 'data.name', 'issue': 'Mismatch', 'source_ids': ['e0:0:5']}
    assert parse_audit(json.dumps({'findings': [finding]}), {'e0:0:5'})['findings'] == [finding]
    with pytest.raises(ValueError):
        parse_audit(json.dumps({'findings': [finding]}), {'e1:0:5'})
    finding['source_ids'] = []
    with pytest.raises(ValueError):
        parse_audit(json.dumps({'findings': [finding]}), set())


def test_schema_audit_rejects_unexpected_rewrites():
    with pytest.raises(ValueError):
        parse_audit('{"findings": [], "replacement_schema": {}}', set())


def test_missing_resume_reports_usage_without_traceback(tmp_path):
    import subprocess
    import sys
    result = subprocess.run([
        sys.executable, 'scripts/check_single_resume.py',
        '--file', str(tmp_path / 'missing.pdf'),
        '--output', str(tmp_path / 'output'), '--llm-review',
    ], capture_output=True, text=True)
    assert result.returncode == 2
    assert 'Supply the actual document path' in result.stderr
    assert 'Traceback' not in result.stderr
    assert not (tmp_path / 'output').exists()


def feedback_fixture():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionRequest, SectionBlock, SectionResponse
    text = 'Python'
    request = SectionRequest(elements=[ExtractedElement(type='NarrativeText', text=text, metadata={})])
    block = SectionBlock(source_element_index=0, start=0, end=len(text), text=text,
                         page_number=1, lane='main', assignment='needs_review', reason='uncertain')
    return request, SectionResponse(status='needs_review', sections=[], needs_review=[block], metadata={}, warnings=[])


def test_feedback_reenters_recovery_and_remaps_until_stagnant(monkeypatch):
    from scripts import single_resume_pipeline as pipeline
    from local_api.services.llm_section_review import ReviewSettings
    from local_api.services.source_validation import validate_result
    request, local = feedback_fixture()
    recovery, calls, audits, passes = [], [], [], []
    monkeypatch.setattr(pipeline, 'recover_sections', lambda req, result: recovery.append(1) or result)
    def provider(settings, messages):
        calls.append(messages)
        return '{"assignments": [["u0", "skills"]]}'
    def audit(sections, schema):
        audits.append(schema)
        return {'status': 'complete', 'findings': []}
    result, schema, audit, state = pipeline.run_feedback(request, local,
        ReviewSettings(enabled=True, api_key='test', recovery_attempts=3), 'synthetic', provider, audit,
        lambda *args: passes.append(args))
    assert len(calls) == 2 and len(recovery) == 1 and len(audits) == 2
    assert len(calls[1]) == 3 and 'missing_required_fields' in calls[1][-1]['content']
    assert state['stop_reason'] == 'no_source_or_mapping_progress'
    assert not validate_result(request.elements, result)
    assert result.sections[0].category == 'skills'
    assert len(local.needs_review) == 1  # Input never mutated.


def test_failed_feedback_keeps_complete_first_result(monkeypatch):
    from scripts import single_resume_pipeline as pipeline
    from local_api.services.llm_section_review import ReviewSettings, ReviewError
    request, local = feedback_fixture()
    monkeypatch.setattr(pipeline, 'recover_sections', lambda req, result: result)
    calls = []
    def provider(*args):
        calls.append(1)
        if len(calls) > 1:
            raise ReviewError('provider_unavailable')
        return '{"assignments": [["u0", "skills"]]}'
    result, _, _, state = pipeline.run_feedback(request, local,
        ReviewSettings(enabled=True, api_key='test', recovery_attempts=2), 'synthetic', provider,
        lambda *_: {'status': 'complete', 'findings': []}, lambda *_: None)
    assert result.metadata['llm_review']['status'] == 'complete'
    assert state['stop_reason'] == 'section_review_failed'
    assert state['passes'][-1]['previous_valid_result_retained'] is True


def test_local_only_never_calls_provider():
    from scripts.single_resume_pipeline import run_feedback
    from local_api.services.llm_section_review import ReviewSettings
    request, local = feedback_fixture()
    def forbidden(*args):
        pytest.fail('Local-only called an external provider')
    _, _, audit, state = run_feedback(request, local, ReviewSettings(enabled=False),
        'synthetic', forbidden, forbidden, lambda *_: None)
    assert state['stop_reason'] == 'local_only'
    assert audit['status'] == 'disabled'


def test_unresolved_text_is_sent_again_and_can_be_resolved(monkeypatch):
    from scripts import single_resume_pipeline as pipeline
    from local_api.services.llm_section_review import ReviewSettings
    request, local = feedback_fixture()
    monkeypatch.setattr(pipeline, 'recover_sections', lambda req, result: result)
    calls = []
    def provider(settings, messages):
        calls.append(messages)
        category = 'needs_review' if len(calls) == 1 else 'skills'
        return json.dumps({'assignments': [['u0', category]]})
    result, _, _, state = pipeline.run_feedback(request, local,
        ReviewSettings(enabled=True, api_key='test', recovery_attempts=2), 'synthetic', provider,
        lambda *_: {'status': 'complete', 'findings': []}, lambda *_: None)
    assert state['passes'][0]['unresolved_meaningful_spans'] == 1
    assert state['passes'][1]['unresolved_meaningful_spans'] == 0
    assert len(calls) <= 3
    assert 'unresolved_meaningful_spans' in calls[1][-1]['content']
    assert result.sections[0].blocks[0].text == 'Python'
    assert not result.needs_review


def test_mode_must_be_explicit(tmp_path):
    import subprocess
    import sys
    source = tmp_path / 'source.pdf'
    source.write_bytes(b'not processed because mode is missing')
    result = subprocess.run([sys.executable, 'scripts/check_single_resume.py',
                             '--file', str(source), '--output', str(tmp_path / 'out')],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert 'Choose --llm-review' in result.stderr
    assert not (tmp_path / 'out').exists()


def test_server_launcher_loads_settings_and_enables_review(monkeypatch):
    import os
    import sys
    import uvicorn
    from scripts import serve_resume_api
    from scripts import check_pilot_fallback
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.setenv('DEEPSEEK_REVIEW_ENABLED', 'false')
    monkeypatch.setattr(check_pilot_fallback, 'load_provider_env',
                        lambda _: monkeypatch.setenv('DEEPSEEK_API_KEY', 'private-test-key'))
    monkeypatch.setattr(sys, 'argv', ['serve_resume_api.py', '--llm-review'])
    calls = []
    monkeypatch.setattr(uvicorn, 'run', lambda *args, **kwargs: calls.append((args, kwargs)))
    serve_resume_api.main()
    assert os.environ['DEEPSEEK_REVIEW_ENABLED'] == 'true'
    assert calls[0][1]['port'] == 8000


def test_invalid_followup_retains_audit_feedback_for_next_retry(monkeypatch):
    from scripts import single_resume_pipeline as pipeline
    from local_api.services.llm_section_review import ReviewSettings
    request, local = feedback_fixture()
    monkeypatch.setattr(pipeline, 'recover_sections', lambda req, result: result)
    calls = []
    def provider(settings, messages):
        calls.append(messages)
        if len(calls) == 2:
            return '{"assignments": []}'
        return '{"assignments": [["u0", "skills"]]}'
    finding = {'field': 'data.skills', 'issue': 'Source-supported concern', 'source_ids': ['e0:0:6']}
    pipeline.run_feedback(request, local, ReviewSettings(enabled=True, api_key='test', recovery_attempts=2),
        'synthetic', provider, lambda *_: {'status': 'complete', 'findings': [finding]}, lambda *_: None)
    assert len(calls) == 3
    feedback = calls[2][-1]['content']
    assert 'Source-supported concern' in feedback
    assert 'placement_validation_failures' in feedback
