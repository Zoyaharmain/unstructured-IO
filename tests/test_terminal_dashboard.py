from io import StringIO
import logging

from rich.console import Console

from local_api.services.terminal_dashboard import DashboardHandler
from local_api.services.trace_payloads import capture_payload


def send(handler, event, **fields):
    item = logging.LogRecord('resume.pipeline', logging.DEBUG, '', 0, '', (), None)
    item.trace_row = {'run_id': 'a' * 32, 'stage': 'test', 'event': event, **fields}
    handler.emit(item)


def test_large_run_displays_grouped_sources_without_debug_spam():
    stream = StringIO()
    handler = DashboardHandler(console=Console(file=stream, width=140), live=False)
    send(handler, 'document_received', input_bytes=65000)
    for i in range(120):
        send(handler, 'decision', decision_type='section_assignment',
             source_ids=[f'e{i}:0:5'], section='experience', rule='heading_context',
             confidence={'probability': None}, reason='Heading context')
    assert 'BLOCK CLASSIFICATION' not in stream.getvalue()
    send(handler, 'stage_summary', number=2, inputs='120 elements', outputs='120 blocks', method='local rules')
    output = stream.getvalue()
    assert 'RESUME INTELLIGENCE ENGINE' in output
    assert output.count('BLOCK CLASSIFICATION') == 1
    assert all(f'e{i}:0:5' in output for i in range(120))
    assert 'Rule-based' in output and 'Not calibrated' not in output
    handler.close()


def test_payload_capture_is_opt_in_private_and_redacts_credentials(monkeypatch, tmp_path):
    args = (tmp_path, 'run', 'call', 'request',
            {'authorization': 'secret-header', 'messages': ['Bearer abc123', 'echo secret-key']}, 'secret-key')
    assert capture_payload(*args) == (None, None)
    monkeypatch.setenv('RESUME_LOG_LEVEL', 'DEBUG')
    monkeypatch.setenv('RESUME_LOG_PAYLOADS', 'true')
    preview, path = capture_payload(*args)
    from pathlib import Path
    file = Path(path)
    assert file.stat().st_mode & 0o077 == 0
    assert preview == file.read_text()
    assert not any(secret in preview for secret in ('secret-header', 'abc123', 'secret-key'))


def test_renderer_failure_does_not_escape_logging():
    class BrokenConsole:
        is_terminal = False
        def print(self, _):
            raise OSError('broken terminal')

    handler = DashboardHandler(console=BrokenConsole(), live=False)
    send(handler, 'document_received', input_bytes=10)
    handler.close()


def test_provider_usage_distinguishes_missing_values_and_schema_audit():
    from local_api.services.trace_totals import summarize, update_totals

    state = {}
    for stage in ('section_judge', 'schema_audit'):
        update_totals(state, {'event': 'llm_call_start', 'request_kind': 'completion', 'stage': stage})
    update_totals(state, {'event': 'llm_call_end', 'token_usage': {'prompt_tokens': 0}})
    totals = summarize(state['totals'])
    assert totals['completion_calls'] == 2
    assert totals['judge_calls'] == totals['schema_audit_calls'] == 1
    assert totals['input_tokens_reported'] == 0
    assert 'output_tokens_reported' not in totals

    stream = StringIO()
    handler = DashboardHandler(console=Console(file=stream), live=False)
    send(handler, 'run_summary', totals=totals)
    assert 'Not available' in stream.getvalue()
    handler.close()


def test_failed_verification_does_not_display_agreement():
    from local_api.services.terminal_trace_format import format_event

    _, inputs, outputs = format_event({'event': 'verification_outcome', 'checked': 3,
                                       'agreed': 3, 'independent_response': False})
    assert inputs['targets'] == 3
    assert outputs['agreement'] == 'Not available'
    assert 'agreed' not in outputs


def test_dashboard_shows_confidence_and_why_judge_did_not_run():
    stream = StringIO()
    handler = DashboardHandler(console=Console(file=stream, width=132), live=False)
    send(handler, 'decision', decision_type='section_assignment', source_ids=['e1:0:5'],
         section='experience', rule='semantic', confidence={'probability': 0.82})
    send(handler, 'decision', decision_type='section_assignment', source_ids=['e2:0:5'],
         section='education', rule='semantic', margin=0.136, confidence={'probability': None})
    send(handler, 'stage_summary', number=2, inputs='2 elements', outputs='2 blocks', method='local')
    send(handler, 'section_judge_skipped', reason='Consensus is disabled')
    send(handler, 'run_summary', totals={'judge_calls': 0, 'schema_audit_calls': 2})
    output = stream.getvalue()
    assert 'CONFIDENCE SCORES' in output and '82.0%' in output
    assert '0.136 raw model margin' in output
    assert 'LLM-AS-A-JUDGE' in output and 'Consensus is disabled' in output
    assert 'Read-only schema audit calls' in output
    handler.close()
