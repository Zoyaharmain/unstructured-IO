"""Capture a private, single-resume pipeline trace without changing processing rules.

Use --review to send the document through the configured DeepSeek stages.
Output includes resume text: keep the trace private. Existing runs are never overwritten.
"""
import argparse
import asyncio
import functools
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--review', action='store_true', help='Enable real configured DeepSeek review.')
    args = parser.parse_args()
    payload = args.file.read_bytes()
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    for key, value in {'HF_HOME': str(ROOT / '.venv/model-cache'), 'OMP_NUM_THREADS': '1',
                       'OPENBLAS_NUM_THREADS': '1', 'HF_HUB_OFFLINE': '1',
                       'TRANSFORMERS_OFFLINE': '1', 'DO_NOT_TRACK': 'true',
                       'MPLCONFIGDIR': '/tmp/resume-inspector-mpl'}.items():
        os.environ.setdefault(key, value)
    lock = threading.RLock()
    sequence = 0
    calls = 0

    def save(name, data):
        if hasattr(data, 'model_dump'):
            data = data.model_dump(mode='json')
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n')

    def event(kind, **data):
        nonlocal sequence
        with lock:
            sequence += 1
            with (args.output / 'events.jsonl').open('a') as stream:
                stream.write(json.dumps({'event': sequence, 'kind': kind, **data}, ensure_ascii=False, default=str) + '\n')
            return sequence

    save('manifest.json', {'file': str(args.file.resolve()), 'document_sha256': hashlib.sha256(payload).hexdigest(),
         'document_format': args.file.suffix.lower(),
         'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
         'working_tree': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
         'python': sys.executable, 'review_requested': args.review})

    def instrument(module_name, names):
        module = importlib.import_module('local_api.services.' + module_name)
        for name in names:
            original = getattr(module, name)
            def wrap(fn, label):
                @functools.wraps(fn)
                def traced(*a, **kw):
                    number = event('enter', function=label, file=fn.__code__.co_filename,
                                   line=fn.__code__.co_firstlineno)
                    source = next((x for x in a if type(x).__name__ == 'SectionResponse'), None)
                    if source is not None:
                        save(f'{number:04d}-{label}-input.json', source)
                    trace_group = label == 'resume_structure.entry_groups' and a[1] == 'certifications'
                    previous_trace = sys.gettrace()
                    if trace_group:
                        sys.settrace(branch_trace)
                    try:
                        result = fn(*a, **kw)
                    except Exception as exc:
                        event('error', function=label, error_type=type(exc).__name__)
                        raise
                    finally:
                        if trace_group:
                            sys.settrace(previous_trace)
                    if hasattr(result, 'model_dump'):
                        save(f'{number:04d}-{label}-output.json', result)
                    elif label == 'resume_structure.entry_groups':
                        blocks = a[0]
                        event('record_groups', function=label, category=a[1], records=result,
                              blocks=[b.model_dump(mode='json') for b in blocks])
                    event('return', function=label, call_event=number)
                    return result
                return traced
            setattr(module, name, wrap(original, module_name + '.' + name))

    targets = {
        'resume_structure': ['entry_groups'],
        'resume_sections': ['detect_sections', 'build_sections'],
        'section_recovery': ['recover_sections'],
        'local_completion': ['recover_local_content'],
        'employment_scope': ['recover_employment_scope'],
        'dated_record_headers': ['recover_split_employment_headers'],
        'employment_integrity': ['repair_employment_entries'],
        'physical_card_recovery': ['recover_physical_cards'],
        'combined_credentials': ['recover_combined_credentials'],
        'project_section_recovery': ['recover_project_sections'],
        'source_rows': ['refine_rows'],
        'certification_integrity': ['recover_certification_cards'],
        'llm_section_review': ['review_sections'],
        'source_ownership': ['finalize_ownership', 'materialize'],
        'schema_mapping': ['map_schema'],
        'llm_schema_mapping': ['map_with_field_review', 'parse_review', 'commit_review'],
    }
    for module, names in targets.items():
        instrument(module, names)

    # Log actual certification branch decisions, with current source line numbers.
    import local_api.services.resume_structure as structure
    fn = inspect.unwrap(structure.entry_groups)
    lines, start = inspect.getsourcelines(fn)
    decision_lines = {start + i for i, line in enumerate(lines) if line.strip() == 'if starts_new:'}
    def branch_trace(frame, kind, value):
        if frame.f_code is not fn.__code__:
            return None
        if frame.f_code is fn.__code__ and kind == 'line' and frame.f_lineno in decision_lines:
            values = frame.f_locals
            if values.get('category') == 'certifications':
                block = values['b']
                event('certification_boundary', file=frame.f_code.co_filename, line=frame.f_lineno,
                      source_id=f'e{block.source_element_index}:{block.start}:{block.end}', text=block.text,
                      flags={k: values.get(k) for k in ['starts_new', 'is_continuation', 'bullet_seen',
                             'prev_ends_continuation', 'is_bold_heading_start', 'is_cap_title',
                             'credential_noun_wrap', 'detail', 'card_has_colon_heading']})
        return branch_trace

    import local_api.services.llm_section_review as llm
    from local_api.core.provider_env import load_provider_env
    load_provider_env(ROOT / '.env')
    if not args.review:
        os.environ['DEEPSEEK_REVIEW_ENABLED'] = 'false'
    elif not llm.ReviewSettings.from_env().enabled or not llm.ReviewSettings.from_env().api_key:
        parser.error('--review requires enabled DeepSeek credentials; no simulated calls are substituted.')
    original_provider = llm.provider_json
    def provider(settings, path, body=None):
        nonlocal calls
        if body is None:
            return original_provider(settings, path, body)
        with lock:
            calls += 1
            number = calls
        save(f'provider-{number:03d}-request.json', body)
        event('provider_request', call=number)
        try:
            response = original_provider(settings, path, body)
            save(f'provider-{number:03d}-response.json', response)
            event('provider_response', call=number)
            return response
        except Exception as exc:
            event('provider_error', call=number, error_type=type(exc).__name__)
            raise
    llm.provider_json = provider

    async def run():
        from local_api.services.text_extraction_service import extract_text
        from local_api.schemas.sections import SectionRequest
        from local_api.schemas.mapping import ReviewedSchemaMappingRequest
        from local_api.routes.sections import resume_sections, local_resume_sections
        from local_api.routes.schema_mapping import map_existing_sections
        extraction = extract_text(payload, args.file.name, 'auto', True)
        save('extraction.json', extraction)
        request = SectionRequest(elements=extraction.elements)
        sections = await (resume_sections(request) if args.review else local_resume_sections(request))
        save('sections.json', sections)
        mapped = await map_existing_sections(ReviewedSchemaMappingRequest(
            elements=request.elements, sections=sections, source=args.file.name, review_fields=args.review))
        save('final.json', mapped)
        save('summary.json', {'provider_calls': calls, 'llm_review': sections.metadata.get('llm_review'),
             'structure_review': sections.metadata.get('structure_review'), 'field_review': mapped.meta.get('field_review'),
             'certifications': [c.model_dump(mode='json') for c in mapped.data.certifications]})
        print(f'Trace saved to {args.output}; provider calls: {calls}', flush=True)
    asyncio.run(run())


if __name__ == '__main__':
    main()
