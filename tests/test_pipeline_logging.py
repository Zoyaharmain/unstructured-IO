from io import BytesIO
import asyncio
import logging
from urllib.error import HTTPError

from starlette.requests import Request
from starlette.responses import Response

from local_api.app import log_resume_pipeline
from local_api.core.pipeline_logging import HEADER, LOGGER, trace
from local_api.services import llm_section_review as review


def test_pipeline_log_correlates_requests_and_counts_provider_attempts(monkeypatch, caplog):
    class Opener:
        def open(self, request, timeout):
            return BytesIO(b'{"usage":{"prompt_tokens":42},"candidate":"private-response"}')

    monkeypatch.setattr(review, 'build_opener', lambda *_: Opener())
    settings = review.ReviewSettings(api_key='private-key')

    def request(path, headers=()):
        return Request({'type': 'http', 'method': 'POST', 'path': path, 'headers': list(headers)})

    async def extract(_):
        return Response()

    async def map_resume(_):
        review.provider_json(settings, '/chat/completions', {'messages': ['private-prompt']})
        review.provider_json(settings, '/models')
        return Response()

    async def run():
        response = await log_resume_pipeline(request('/api/v1/extract/text'), extract)
        run_id = response.headers[HEADER]
        headers = [(HEADER.lower().encode(), run_id.encode())]
        reviewed = await log_resume_pipeline(request('/api/v1/resume/schema', headers), map_resume)
        assert reviewed.headers[HEADER] == run_id
        return run_id

    with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
        run_id = asyncio.run(run())

    assert trace.get() is None
    assert f'run={run_id} event=provider_attempt kind=completion number=1' in caplog.text
    assert f'run={run_id} event=provider_attempt kind=connection_check number=2' in caplog.text
    assert 'provider_attempts=2 completion_attempts=1' in caplog.text
    assert 'prompt_tokens=42' in caplog.text
    assert 'private-' not in caplog.text


def test_read_only_retry_counts_individual_attempts_and_logs_safe_warning(monkeypatch, caplog):
    responses = iter((HTTPError('https://example.invalid', 503, 'private-error', {}, BytesIO()), BytesIO(b'{}')))

    class Opener:
        def open(self, request, timeout):
            result = next(responses)
            if isinstance(result, HTTPError):
                raise result
            return result

    monkeypatch.setattr(review, 'build_opener', lambda *_: Opener())
    monkeypatch.setattr(review.time, 'sleep', lambda *_: None)

    async def check(_):
        review.provider_json(review.ReviewSettings(api_key='private-key'), '/models')
        return Response()

    request = Request({'type': 'http', 'method': 'POST', 'path': '/api/v1/resume/review-connection',
                       'headers': [(HEADER.lower().encode(), b'private-header')]})
    with caplog.at_level(logging.INFO, logger=LOGGER.name):
        asyncio.run(log_resume_pipeline(request, check))

    assert 'provider_attempts=2 completion_attempts=0' in caplog.text
    assert any(record.levelno == logging.WARNING and 'code=provider_unavailable' in record.message
               for record in caplog.records)
    assert 'private-' not in caplog.text


def test_readable_trace_names_stage_and_explains_rejected_record(caplog):
    from local_api.core.pipeline_logging import ReadablePipelineFormatter, stage_io
    from local_api.services.schema_diagnostics import MappingValidationError, record_failure

    async def mapping(_):
        stage_io(6, 'mapped fields and source spans', 'one field review rejected')
        record_failure(MappingValidationError('record_ownership_validation',
                                               'validated_record_boundary_changed',
                                               ('sections', 0, 'records', 6)),
                       'response_model_validation', attempt=2)
        return Response()

    request = Request({'type': 'http', 'method': 'POST', 'path': '/api/v1/resume/schema', 'headers': []})
    with caplog.at_level(logging.INFO, logger=LOGGER.name):
        asyncio.run(log_resume_pipeline(request, mapping))
    formatter = ReadablePipelineFormatter(fmt='%(levelprefix)s %(message)s', use_colors=False)
    lines = [formatter.format(record) for record in caplog.records]
    assert any('Stage 6 · Evidence validation and review | In: mapped fields' in line for line in lines)
    assert any('WARNING' in line and '/sections/0/records/6' in line and
               'changed which source blocks belong' in line for line in lines)


def test_grouping_trace_shows_source_ids_and_record_roles(caplog, monkeypatch):
    from local_api.core.pipeline_logging import PipelineTrace, ReadablePipelineFormatter
    from local_api.routes.sections import log_record_groups
    from local_api.schemas.sections import ResumeSection, SectionBlock, SectionEntry, SectionResponse

    heading = SectionBlock(source_element_index=0, start=0, end=10, text='Experience', page_number=1,
                           lane='main', assignment='structural_heading', reason='heading')
    job = SectionBlock(source_element_index=1, start=0, end=8, text='Engineer', page_number=1,
                       lane='main', assignment='heading_context', reason='role')
    section = ResumeSection(category='experience', label='Experience', blocks=[heading, job],
                            entries=[SectionEntry(entry_id='job-1', block_indices=[1], lane='main',
                                                  boundary_reason='role', fields={'title': [1]})])
    monkeypatch.setenv('RESUME_LOG_VALUES', 'true')
    token = trace.set(PipelineTrace('synthetic'))
    try:
        with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
            log_record_groups(SectionResponse(status='provisional', sections=[section], needs_review=[], metadata={}, warnings=[]))
    finally:
        trace.reset(token)

    formatter = ReadablePipelineFormatter(fmt='%(message)s', use_colors=False)
    lines = [formatter.format(record) for record in caplog.records]
    assert any('experience #1' in line and 'Blocks: e1:0:8' in line for line in lines)
    assert any("e1:0:8 (page 1) | experience → group 1 (title) | Text: 'Engineer'" in line for line in lines)
    assert any('e0:0:10 (page 1) | experience → section heading' in line for line in lines)


def test_stage_two_shows_input_and_final_section_with_classification_evidence(caplog, monkeypatch):
    from local_api.core.pipeline_logging import PipelineTrace, ReadablePipelineFormatter
    from local_api.routes.sections import log_section_contents
    from local_api.schemas.sections import ResumeSection, SectionBlock, SectionResponse

    block = SectionBlock(source_element_index=3, start=0, end=23, text='BSc, Example University',
                         page_number=1, lane='main', assignment='education_boundary',
                         reason='Degree and institution form an education boundary',
                         candidate_section='skills', similarity=.61, margin=.08)
    result = SectionResponse(status='provisional', sections=[
        ResumeSection(category='education', label='Education', blocks=[block]),
    ], needs_review=[], metadata={}, warnings=[])
    monkeypatch.setenv('RESUME_LOG_VALUES', 'true')
    token = trace.set(PipelineTrace('synthetic'))
    try:
        with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
            log_section_contents(result)
    finally:
        trace.reset(token)
    formatter = ReadablePipelineFormatter(fmt='%(message)s', use_colors=False)
    output = '\n'.join(formatter.format(record) for record in caplog.records)
    assert 'Education — 1 source spans' in output
    assert "Input: 'BSc, Example University'" in output
    assert 'Assigned to: Education' in output
    assert 'model suggested skills' in output and 'education_boundary' in output
