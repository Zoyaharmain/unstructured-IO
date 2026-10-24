"""Run one source through the existing pipeline and optional DeepSeek audits."""
import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def parse_audit(content, evidence_ids):
    """Provider findings are advisory and must cite existing source intervals."""
    result = json.loads(content)
    if not isinstance(result, dict) or set(result) != {'findings'} or not isinstance(result['findings'], list):
        raise ValueError('Invalid audit envelope')
    for finding in result['findings']:
        if not isinstance(finding, dict) or set(finding) != {'field', 'issue', 'source_ids'}:
            raise ValueError('Invalid audit finding')
        if not all(isinstance(finding[k], str) and finding[k].strip() for k in ('field', 'issue')):
            raise ValueError('Invalid audit text')
        ids = finding['source_ids']
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in evidence_ids for i in ids):
            raise ValueError('Audit finding lacks source evidence')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--strategy', choices=['auto', 'fast', 'hi_res', 'ocr_only'], default='auto')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--llm-review', action='store_true', help='Send this document text and schema to configured DeepSeek')
    mode.add_argument('--local-only', action='store_true', help='Explicitly disable all DeepSeek calls')
    parser.add_argument('--recovery-attempts', type=int, choices=range(4), default=1)
    args = parser.parse_args()
    args.file = args.file.expanduser()
    try:
        payload = args.file.read_bytes()
    except OSError as exc:
        parser.error(
            f"Cannot read resume file: {args.file} ({exc.strerror}). "
            "Supply the actual document path; resume.pdf in the guide is an example. "
            "Existing local example: --file 'tests/fixtures/Jayesh Yadav-CV.pdf'"
        )
    if not payload:
        parser.error('The resume file is empty; choose a non-empty document')
    if not args.llm_review and not args.local_only:
        parser.error('Choose --llm-review for DeepSeek verification and feedback retries, or --local-only to explicitly skip DeepSeek')
    if args.output.exists():
        parser.error('Use a new output directory; existing artifacts are preserved')
    # A prior explicit refusal persists for this document.
    if args.llm_review and args.file.name.casefold() == 'jewel bijoy.pdf':
        parser.error('JEWEL BIJOY is reserved for local review; omit --llm-review')
    os.environ.setdefault('HF_HOME', str(ROOT / '.venv/model-cache'))
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    from scripts.check_pilot_fallback import load_provider_env
    from local_api.schemas.sections import SectionRequest
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.text_extraction_service import extract_text
    from local_api.services.resume_sections import detect_sections
    from local_api.services.section_recovery import recover_sections
    from local_api.services.llm_section_review import ReviewSettings, review_sections, call_deepseek
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    if args.llm_review:
        load_provider_env(ROOT / '.env')
    settings = replace(ReviewSettings.from_env(), enabled=args.llm_review, recovery_attempts=args.recovery_attempts)
    if args.llm_review:
        settings.validate()
        if not settings.api_key:
            parser.error('DEEPSEEK_API_KEY is required for --llm-review')
    args.output.mkdir(parents=True, mode=0o700)
    save(args.output / 'manifest.json', {'file': str(args.file.resolve()), 'sha256': hashlib.sha256(payload).hexdigest(),
         'strategy': args.strategy, 'llm_requested': args.llm_review, 'recovery_attempts': args.recovery_attempts,
         'semantic_accuracy_certified': False, 'pipeline': 'bounded_section_schema_feedback'})
    extraction = extract_text(payload, args.file.name, args.strategy)
    save(args.output / 'extraction.json', extraction.model_dump(mode='json'))
    request = SectionRequest(elements=extraction.elements)
    local = recover_sections(request, detect_sections(request))
    save(args.output / 'local-sections.json', local.model_dump(mode='json'))
    errors = validate_result(request.elements, local)
    if errors:
        save(args.output / 'validation-errors.json', errors)
        raise ValueError('Local source validation failed; see validation-errors.json')
    provider_calls = []

    def recorded_transport(config, messages):
        number = len(provider_calls) + 1
        provider_calls.append({'call': number, 'status': 'attempted'})
        save(args.output / f'provider-request-{number}.json', {'messages': messages, 'model': config.model})
        try:
            content = call_deepseek(config, messages)
            provider_calls[-1]['status'] = 'complete'
            save(args.output / f'provider-response-{number}.json', {'content': content})
            return content
        except Exception:
            provider_calls[-1]['status'] = 'failed'
            raise
        finally:
            save(args.output / 'provider-calls.json', provider_calls)

    from local_api.services.review_chunking import new_budget, run_schema_audit, binding
    request_budget = new_budget(settings)
    document_hash = hashlib.sha256(payload).hexdigest()

    def audit_schema(sections, schema):
        key = binding(request.elements)['source_inventory_sha256']
        pass_id = max((pid for doc, pid in request_budget.passes if doc == key), default=0)
        return run_schema_audit(request.elements, sections, schema, settings, recorded_transport,
                                budget=request_budget, pass_id=pass_id, document_sha256=document_hash)

    def save_pass(number, sections, schema, audit, row):
        directory = args.output / f'pass-{number:02d}'
        directory.mkdir(mode=0o700)
        for name, data in [('sections', sections.model_dump(mode='json')), ('schema', schema),
                           ('schema-audit', audit), ('feedback', row)]:
            save(directory / (name + '.json'), data)

    from scripts.single_resume_pipeline import run_feedback
    sections, schema, audit, pipeline = run_feedback(
        request, local, settings, args.file.name, recorded_transport, audit_schema, save_pass,
        request_budget=request_budget, document_sha256=document_hash)
    save(args.output / 'sections.json', sections.model_dump(mode='json'))
    save(args.output / 'schema.json', schema)
    save(args.output / 'schema-audit.json', audit)
    save(args.output / 'pipeline.json', pipeline)
    review = sections.metadata.get('llm_review', {})
    report = f'''# Individual resume check

Source: {args.file.name}

- Extraction: {args.strategy}; {len(extraction.elements)} elements.
- Sentence-BERT / K-means and local recovery: completed.
- Exact extracted-source interval validation: passed.
- LLM section review: {review.get('status', 'disabled')}; provider calls: {review.get('provider_calls', 0)}.
- Schema contract and source binding: passed.
- Separate LLM schema audit: {audit['status']}; findings: {len(audit['findings'])}.
- Missing required fields: {len(schema['meta']['missing_required_fields'])}.
- Feedback passes: {len(pipeline['passes'])}; stop reason: {pipeline['stop_reason']}.
- Total DeepSeek calls (sections and schema audits): {len(provider_calls)}.

**Overall: needs review.** No human source approval or original-PDF word accuracy certification is implied.

Inspect extraction.json against the original PDF; sections.json for block placement and record ownership; schema.json for final values, field_evidence, missing_required_fields, unmapped_blocks and record_reviews; schema-audit.json for advisory LLM findings.

In LLM mode, unresolved meaningful spans, missing schema fields and schema-audit findings re-enter local recovery, LLM section review, schema mapping and schema audit. The configured budget is shared with invalid-placement retries. See pass directories and pipeline.json. Unchanged source/mapping output stops further retries. Invalid responses retain validated output. Missing source words require correcting extraction (try a new run with --strategy ocr_only for scanned PDFs), then running the entire pipeline on that extraction. Missing schema fields and relationship findings require source inspection and a mapping/grouping fix; repeating identical input does not establish correctness. The schema audit never silently changes values. Preserve this run and use a new output directory after repairs.
'''
    (args.output / 'report.md').write_text(report)
    print(f'Completed: {args.output / "report.md"} (needs_review)')


if __name__ == '__main__':
    main()
