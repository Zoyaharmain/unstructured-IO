"""Run a hash-bound, sequential DeepSeek section-and-schema pilot.

This command makes paid provider calls.  It is intentionally limited to a
pre-frozen manifest of 5--10 PDFs, shares one request budget across the whole
run, and stops after the first incomplete document by default.
"""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_scope(path, *, single_file=None):
    data = json.loads(path.read_text())
    selected = data.get('selected')
    if not isinstance(selected, list):
        raise ValueError('Selection manifest must contain a selected-resumes list')
    if single_file is not None:
        if Path(single_file).name != single_file or not single_file.lower().endswith('.pdf'):
            raise ValueError('Single-file selection must be a PDF filename only')
        matches = [row for row in selected if isinstance(row, dict) and row.get('file') == single_file]
        if not matches:
            raise ValueError('Single-file selection was not found in the frozen manifest: ' + single_file)
        if len(matches) != 1:
            raise ValueError('Single-file selection matched multiple manifest entries: ' + single_file)
        selected = matches
    elif not 5 <= len(selected) <= 10:
        raise ValueError('Selection manifest must contain exactly 5--10 selected resumes')
    scope = []
    seen_hashes, seen_files = set(), set()
    for row in selected:
        if not isinstance(row, dict):
            raise ValueError('Invalid selection row')
        name, digest = row.get('file'), str(row.get('sha256', '')).lower()
        if (not isinstance(name, str) or Path(name).name != name or not name.lower().endswith('.pdf')
                or len(digest) != 64 or any(char not in '0123456789abcdef' for char in digest)
                or name in seen_files or digest in seen_hashes):
            raise ValueError('Selection must contain unique PDF filenames and SHA256 hashes')
        seen_files.add(name); seen_hashes.add(digest); scope.append({'file': name, 'sha256': digest})
    if data.get('disjoint_confirmed') is not True:
        raise ValueError('Manifest must explicitly confirm disjoint prior selection hashes')
    return scope


def verify_scope_sources(scope, folder):
    """Fail before provider setup when a frozen source no longer matches."""
    verified = {}
    for item in scope:
        source = folder / item['file']
        if not source.is_file() or sha256(source) != item['sha256']:
            raise ValueError('Missing or changed source PDF: ' + item['file'])
        verified[item['file']] = item['sha256']
    return verified


def ensure_new_output(output):
    if output.exists():
        raise ValueError('Use a new output directory; pilot artifacts are immutable')


def settings_from_args(args):
    from local_api.services.llm_section_review import ReviewSettings
    settings = replace(ReviewSettings.from_env(), enabled=True,
                       recovery_attempts=args.recovery_attempts,
                       max_total_requests=args.request_cap,
                       max_document_requests=args.document_request_cap,
                       max_pass_requests=args.pass_request_cap)
    settings.validate()
    if not settings.api_key:
        raise ValueError('DEEPSEEK_API_KEY is required in .env or the environment')
    return settings


def main():
    from scripts.check_pilot_fallback import DEFAULT_FOLDER, load_provider_env
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection-manifest', type=Path, required=True)
    parser.add_argument('--single-file', help='Run exactly one PDF already present in the frozen manifest')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--folder', type=Path, default=DEFAULT_FOLDER)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--request-cap', type=int, required=True)
    parser.add_argument('--document-request-cap', type=int, default=12)
    parser.add_argument('--pass-request-cap', type=int, default=12)
    parser.add_argument('--recovery-attempts', choices=range(4), type=int, default=0)
    parser.add_argument('--stop-on-first-incomplete', action='store_true')
    args = parser.parse_args()
    if args.workers != 1:
        parser.error('Only --workers 1 is allowed so the shared request cap is deterministic')
    if min(args.request_cap, args.document_request_cap, args.pass_request_cap) < 1:
        parser.error('Request caps must be positive')
    try:
        ensure_new_output(args.output)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        scope = load_scope(args.selection_manifest, single_file=args.single_file)
        verified_hashes = verify_scope_sources(scope, args.folder)
    except ValueError as exc:
        parser.error(str(exc))

    load_provider_env(ROOT / '.env')
    try:
        settings = settings_from_args(args)
    except ValueError as exc:
        parser.error(str(exc))

    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.schemas.sections import SectionRequest
    from local_api.services.llm_section_review import ReviewError, call_deepseek, check_connection
    from local_api.services.resume_sections import detect_sections
    from local_api.services.review_chunking import binding, new_budget, run_schema_audit
    from local_api.services.schema_mapping import map_schema
    from local_api.services.section_recovery import recover_sections
    from local_api.services.source_validation import validate_result
    from local_api.services.text_extraction_service import extract_text
    from scripts.single_resume_pipeline import run_feedback

    connection = check_connection()
    if connection.get('status') != 'ready':
        parser.error('Provider preflight failed: ' + connection.get('error_code', 'not_ready'))

    args.output.mkdir(parents=True, mode=0o700)
    (args.output / 'documents').mkdir(mode=0o700)
    (args.output / 'selected-pdfs').mkdir(mode=0o700)
    write(args.output / 'manifest.json', {
        'created_utc': datetime.now(timezone.utc).isoformat(), 'scope': scope,
        'selection_manifest': str(args.selection_manifest.resolve()),
        'single_file': args.single_file,
        'selected_filename': scope[0]['file'] if args.single_file else None,
        'verified_source_sha256': scope[0]['sha256'] if args.single_file else None,
        'verified_source_hashes': verified_hashes,
        'provider_model': settings.model, 'request_caps': {
            'global': args.request_cap, 'per_document': args.document_request_cap,
            'per_pass': args.pass_request_cap}, 'recovery_attempts': args.recovery_attempts,
        'stop_on_first_incomplete': args.stop_on_first_incomplete,
        'semantic_accuracy_certified': False,
    })
    for item in scope:
        shutil.copy2(args.folder / item['file'], args.output / 'selected-pdfs' / item['file'])

    budget = new_budget(settings)
    rows, stopped = [], None
    for index, item in enumerate(scope, 1):
        name = item['file']; document_dir = args.output / 'documents' / f'{index:02d}'
        document_dir.mkdir(mode=0o700)
        payload = (args.output / 'selected-pdfs' / name).read_bytes()
        calls = []
        def transport(config, messages):
            call_number = len(calls) + 1
            calls.append({'call': call_number, 'status': 'attempted'})
            write(document_dir / f'provider-request-{call_number}.json',
                  {'model': config.model, 'messages': messages})
            try:
                content = call_deepseek(config, messages)
                calls[-1]['status'] = 'complete'
                write(document_dir / f'provider-response-{call_number}.json', {'content': content})
                return content
            except Exception:
                calls[-1]['status'] = 'failed'
                raise
            finally:
                write(document_dir / 'provider-calls.json', calls)
        try:
            extraction = extract_text(payload, name, 'auto')
            write(document_dir / 'extraction.json', extraction.model_dump(mode='json'))
            request = SectionRequest(elements=extraction.elements)
            local = recover_sections(request, detect_sections(request))
            write(document_dir / 'local-sections.json', local.model_dump(mode='json'))
            errors = validate_result(request.elements, local)
            if errors:
                raise ValueError('local_source_validation_failed')
            document_hash = hashlib.sha256(payload).hexdigest()
            def audit(sections, schema):
                inventory_hash = binding(request.elements)['source_inventory_sha256']
                pass_id = max((pass_no for doc, pass_no in budget.passes if doc == inventory_hash), default=0)
                return run_schema_audit(request.elements, sections, schema, settings, transport,
                                        budget=budget, pass_id=pass_id, document_sha256=document_hash)
            def save_pass(number, sections, schema, audit_result, feedback):
                target = document_dir / f'pass-{number:02d}'; target.mkdir(mode=0o700)
                write(target / 'sections.json', sections.model_dump(mode='json'))
                write(target / 'schema.json', schema); write(target / 'schema-audit.json', audit_result)
                write(target / 'feedback.json', feedback)
            sections, schema, audit, pipeline = run_feedback(
                request, local, settings, name, transport, audit, save_pass,
                request_budget=budget, document_sha256=document_hash)
            write(document_dir / 'sections.json', sections.model_dump(mode='json'))
            write(document_dir / 'schema.json', schema); write(document_dir / 'schema-audit.json', audit)
            write(document_dir / 'pipeline.json', pipeline)
            complete = pipeline['provider_coverage_status'] == 'complete'
            row = {'file': name, 'sha256': document_hash, 'status': 'complete' if complete else 'incomplete',
                   'provider_calls': len(calls), 'pipeline_stop_reason': pipeline['stop_reason'],
                   'provider_coverage_status': pipeline['provider_coverage_status'],
                   'section_status': sections.metadata.get('llm_review', {}).get('status'),
                   'schema_audit_status': audit['status'], 'source_validation_errors': [],
                   'semantic_accuracy_verified': False}
        except Exception as exc:
            row = {'file': name, 'sha256': hashlib.sha256(payload).hexdigest(), 'status': 'failed',
                   'provider_calls': len(calls), 'error_type': type(exc).__name__,
                   'semantic_accuracy_verified': False}
        rows.append(row); write(args.output / 'current-results.json', rows)
        if row['status'] != 'complete' and args.stop_on_first_incomplete:
            stopped = row['file']; break
    write(args.output / 'summary.json', {
        'selected_documents': len(scope), 'attempted_documents': len(rows), 'rows': rows,
        'request_budget_events': budget.events, 'requests_used': budget.total,
        'request_cap': args.request_cap, 'stopped_on': stopped,
        'complete': len(rows) == len(scope) and all(row['status'] == 'complete' for row in rows),
        'semantic_accuracy_verified': False,
    })
    print(json.dumps({'attempted': len(rows), 'selected': len(scope), 'requests_used': budget.total,
                      'request_cap': args.request_cap, 'stopped_on': stopped}, indent=2))


if __name__ == '__main__':
    main()
