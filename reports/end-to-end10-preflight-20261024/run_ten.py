"""Guarded telemetry wrapper around the existing production single-resume pipeline.

Default mode only verifies the frozen selection. --execute makes paid requests;
use it only after the user confirms the displayed selection and command.
"""
import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


def verify(manifest):
    selected = manifest['selected']
    if len(selected) != 10 or manifest['document_count'] != 10:
        raise ValueError('Exactly ten documents required')
    for key in ('sha256', 'document_id', 'source_path'):
        if len({row[key] for row in selected}) != 10:
            raise ValueError('Duplicate selected ' + key)
    for row in selected:
        if sha(row['source_path']) != row['sha256']:
            raise ValueError('Selected source hash changed: ' + row['file'])
        for key in ('baseline_source', 'baseline_mapping'):
            if sha(row[key]) != row[key + '_sha256']:
                raise ValueError('Baseline changed: ' + row[key])
        if not row['development_control'] and (row['prior_llm_selection_name_match'] or row['prior_llm_selection_hash_match']):
            raise ValueError('Selection overlaps recorded LLM history')
    for source in manifest['history_sources']:
        if sha(source['path']) != source['sha256']:
            raise ValueError('Historical selection changed: ' + source['path'])
    for path, digest in manifest['code_sha256'].items():
        if sha(path) != digest:
            raise ValueError('Reviewed implementation changed: ' + path)
    for path, digest in manifest.get('evaluation_code_sha256', {}).items():
        if sha(path) != digest:
            raise ValueError('Evaluation implementation changed: ' + path)
    prior = json.loads(Path(manifest['prior350_preservation_file']).read_text())
    if any(sha(path) != digest for path, digest in prior.items()):
        raise ValueError('Previous full350 artifact changed')
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Make paid calls after user confirmation')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    selected = verify(manifest)
    from scripts.check_pilot_fallback import load_provider_env
    from local_api.services import llm_section_review as llm
    load_provider_env(ROOT / '.env')
    config = llm.ReviewSettings.from_env()
    config.validate()
    if not config.enabled or not config.api_key:
        raise ValueError('Configured DeepSeek review must be enabled')
    for name in ('model', 'base_url', 'thinking', 'max_tokens', 'max_units', 'max_input_chars'):
        if getattr(config, name) != manifest['provider'][name]:
            raise ValueError('Provider setting changed: ' + name)
    if not args.execute:
        print(json.dumps({'status': 'verified_no_calls', 'documents': [r['file'] for r in selected],
                          'model': config.model, 'provider_calls': 0}, indent=2))
        return
    if manifest['provider_budget']['maximum_requests'] != 40 or manifest['provider_budget']['recovery_attempts'] != 1:
        raise ValueError('Unreviewed execution budget')
    results = Path(manifest['execution']['results_directory'])
    results.mkdir(mode=0o700)  # Never overwrite or automatically resume paid runs.
    calls, documents = [], []
    active = None
    old_transport = llm.call_deepseek
    old_argv = sys.argv[:]
    started = time.monotonic()

    def transport(settings, messages):
        if active is None or active not in selected:
            raise ValueError('Provider call outside frozen ten-document scope')
        if sha(active['source_path']) != active['sha256']:
            raise ValueError('Source changed before provider request')
        own = [c for c in calls if c['document_id'] == active['document_id']]
        if len(calls) >= 40 or len(own) >= 4:
            raise ValueError('Frozen provider request budget exceeded')
        stage = 'schema_audit' if messages[0]['content'].startswith('Audit resume schema') else 'section_review'
        event = {'number': len(calls) + 1, 'document_id': active['document_id'], 'file': active['file'],
                 'stage': stage, 'attempt_for_stage': 1 + sum(c['stage'] == stage for c in own),
                 'status': 'attempted', 'model': settings.model}
        calls.append(event)
        save(results / 'calls.json', calls)
        payload = {'model': settings.model, 'messages': messages, 'stream': False,
                   'response_format': {'type': 'json_object'}, 'thinking': {'type': settings.thinking},
                   'max_tokens': settings.max_tokens}
        tick = time.monotonic()
        try:
            envelope = llm.provider_json(settings, '/chat/completions', payload)
            save(results / ('provider-envelope-%02d.json' % event['number']), envelope)
            event['usage'] = envelope.get('usage', {})
            choice = envelope['choices'][0]
            event['finish_reason'] = choice.get('finish_reason')
            if choice.get('finish_reason') != 'stop':
                raise llm.ReviewError('incomplete_response')
            content = choice['message']['content']
            if not isinstance(content, str):
                raise llm.ReviewError('invalid_response')
            event['status'] = 'response_received'
            return content
        except Exception as exc:
            event.update(status='failed', error=str(exc) if isinstance(exc, llm.ReviewError) else type(exc).__name__)
            raise
        finally:
            event['latency_seconds'] = round(time.monotonic() - tick, 3)
            save(results / 'calls.json', calls)

    # Runtime telemetry only: production implementations are unchanged.
    from local_api.services import resume_sections as detection, section_recovery as recovery
    from local_api.services.source_accounting import account_source
    old_detect, old_recover = detection.detect_sections, recovery.recover_sections
    traces = []
    def trace(stage, request, before, after):
        traces.append({'document_id': active['document_id'], 'stage': stage,
            'original_elements': len(request.elements),
            'before': account_source(request.elements, before) if before is not None else None,
            'after': account_source(request.elements, after)})
        save(results / 'stage-traces.json', traces)
    def detected(request):
        result = old_detect(request); trace('initial_detection', request, None, result); return result
    def recovered(request, result):
        before = result.model_copy(deep=True)
        repaired = old_recover(request, result)
        trace('local_recovery_invocation', request, before, repaired); return repaired
    detection.detect_sections, recovery.recover_sections = detected, recovered
    llm.call_deepseek = transport
    try:
        from scripts.check_single_resume import main as run_single
        for active in selected:
            tick = time.monotonic()
            destination = results / ('%02d' % active['index'])
            row = {'file': active['file'], 'document_id': active['document_id'], 'output': str(destination)}
            try:
                sys.argv = ['scripts/check_single_resume.py', '--file', active['source_path'],
                    '--output', str(destination), '--strategy', 'auto', '--llm-review', '--recovery-attempts', '1']
                run_single()
                sections = json.loads((destination / 'sections.json').read_text())
                audit = json.loads((destination / 'schema-audit.json').read_text())
                row.update(status='pipeline_completed', section_review=sections['metadata'].get('llm_review'),
                           audit_status=audit['status'], audit_findings=len(audit.get('findings', [])))
            except (Exception, SystemExit) as exc:
                row.update(status='pipeline_failed', error_type=type(exc).__name__)
            row['seconds'] = round(time.monotonic() - tick, 3)
            documents.append(row)
            save(results / 'documents.json', documents)
            if any(c.get('error') in {'authentication_failed', 'insufficient_balance', 'provider_forbidden', 'model_unavailable'} for c in calls):
                break
    finally:
        detection.detect_sections, recovery.recover_sections = old_detect, old_recover
        llm.call_deepseek = old_transport
        sys.argv = old_argv
        usage = Counter()
        for call in calls:
            usage.update({k: v for k, v in call.get('usage', {}).items() if type(v) is int})
        preserved = True
        try:
            verify(manifest)
        except Exception:
            preserved = False
        save(results / 'execution-summary.json', {'documents_attempted': len(documents), 'selected_documents': 10,
            'provider_requests': len(calls), 'distinct_documents_sent_to_provider': len({c['document_id'] for c in calls}),
            'usage': dict(usage), 'seconds': round(time.monotonic() - started, 3),
            'inputs_baselines_code_and_prior_artifacts_unchanged': preserved,
            'cost_usd': None, 'cost_reason': 'No current price assumed; inspect recorded provider usage/cost fields.',
            'semantic_accuracy': None, 'semantic_accuracy_reason': 'Partial references for two controls only; evaluate separately by provenance',
            'documents': documents})
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('evaluate_ten', Path(__file__).with_name('evaluate_run.py'))
    evaluation = module_from_spec(spec); spec.loader.exec_module(evaluation)
    evaluation.evaluate(manifest, results)
    print('Execution artifacts:', results)


if __name__ == '__main__':
    main()
