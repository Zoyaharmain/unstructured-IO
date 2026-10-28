"""Offline extraction, schema and reviewed-answer checks for a resume sample."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def compare(expected, actual, path='data'):
    """Compare declared fields only; record lists have exact counts, any order."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict): return [path]
        return [issue for key, value in expected.items()
                for issue in compare(value, actual.get(key), f'{path}.{key}')]
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual): return [path + ':count']
        # Bipartite matching avoids greedy errors with partial expected records.
        options = [[j for j, item in enumerate(actual) if not compare(value, item)] for value in expected]
        matched = {}
        def assign(i, seen):
            for j in options[i]:
                if j in seen: continue
                seen.add(j)
                if j not in matched or assign(matched[j], seen):
                    matched[j] = i
                    return True
            return False
        return [] if all(assign(i, set()) for i in range(len(expected))) else [path + ':records']
    return [] if type(expected) is type(actual) and expected == actual else [path]


def evaluate(truth, row, data):
    if not truth or truth.get('human_reviewed') is not True:
        return 'not_reviewed', []
    if truth.get('sha256') != row['sha256']:
        return 'stale_expectations', ['source_hash']
    expected = truth.get('expected_data')
    if not isinstance(expected, dict) or not expected:
        return 'invalid_expectations', ['expected_data']
    failures = compare(expected, data)
    return ('fail' if failures else 'pass'), failures


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def document_report(output, row):
    key = Path(row.get('artifact', 'documents/' + str(len(row.get('file', '')))))
    target = key.with_suffix('.report.md')
    lines = ['# Resume check', '', 'File: ' + row['file'], '',
             'Source/schema checks: ' + row['checks'], 'Accuracy: ' + row['accuracy'],
             'Review required: ' + str(row['review_required']), 'Provider calls: 0', '',
             '## Diagnostics', '', '```json', json.dumps(row, indent=2, ensure_ascii=False), '```']
    (output/target).write_text('\n'.join(lines) + '\n')
    row['report_artifact'] = str(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--expected', type=Path, help='Human-reviewed expected-results JSON from an earlier run')
    args = parser.parse_args()
    if not args.folder.is_dir() or args.limit < 1 or args.timeout < 1:
        parser.error('Supply an existing folder and positive limit/timeout')
    if args.output.exists(): parser.error('Use a new output directory; existing results are preserved')
    truth = json.loads(args.expected.read_text()) if args.expected else {}
    if not isinstance(truth, dict): parser.error('Expected-results JSON must be an object keyed by relative filename')
    from scripts.batch_check_resumes import initialize_worker, process_document, SUPPORTED
    initialize_worker()  # Model loaded once; provider disabled and Python network blocked.
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.schemas.sections import SectionResponse
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    from local_api.services.subschema_validation import validate_hierarchy
    files = sorted((p for p in args.folder.rglob('*') if p.is_file() and
                    p.suffix.lower() in SUPPORTED and not p.name.startswith('~$')), key=lambda p: str(p.relative_to(args.folder)).casefold())[:args.limit]
    if not files: parser.error('No supported resumes found')
    args.output.mkdir(parents=True, mode=0o700)
    (args.output/'documents').mkdir(mode=0o700)
    rows=[]; template={}; started=time.monotonic()
    for number, file in enumerate(files, 1):
        relative=str(file.relative_to(args.folder))
        row=process_document(file, relative, args.output, args.timeout, True, 'fresh_batch')
        row['accuracy']='not_evaluated'
        if row['status']=='processed':
            try:
                artifact=json.loads((args.output/row['artifact']).read_text())
                request=SchemaMappingRequest(elements=artifact['extraction']['elements'], sections=artifact['sections'])
                mapped=map_schema(request)
                revised=SectionResponse.model_validate(mapped.meta.get('reviewed_sections', artifact['sections']))
                errors=validate_result(request.elements,revised)
                if errors: raise ValueError('Source coverage validation failed')
                validate_hierarchy(mapped.section_schemas,revised)
                schema_path=Path(row['artifact']).with_suffix('.schema.json')
                save(args.output/schema_path,mapped.model_dump(mode='json'))
                row['schema_artifact']=str(schema_path)
                row['missing_required_fields']=mapped.meta.get('missing_required_fields',[])
                row['unresolved_attributes']=sum(not a.items for s in mapped.section_schemas for r in s.records for a in r.attributes)
                row['review_records']=sum(bool(r.review_reasons) for s in mapped.section_schemas for r in s.records)
                row['accuracy'],row['mismatch_paths']=evaluate(truth.get(relative),row,mapped.data.model_dump(mode='json'))
                row['checks']='pass'
            except Exception as exc:
                row.update(status='mapping_failure',checks='fail',error_type=type(exc).__name__)
                from local_api.services.schema_diagnostics import diagnose
                row['diagnostic']=diagnose(exc, 'subschema_validation')
        else: row['checks']='fail'
        row['review_required']=row['checks']!='pass' or bool(row.get('flags') or row.get('missing_required_fields') or row.get('unresolved_attributes') or row.get('review_records'))
        template[relative]={'sha256':row.get('sha256'),'human_reviewed':False,'expected_data':None}
        # A stable document key also exists for extraction failures.
        if not row.get('artifact'):
            import hashlib
            row['artifact']='documents/'+hashlib.sha256(relative.encode()).hexdigest()[:20]+'.json'
            save(args.output/row['artifact'], {'file':relative,'failure':row})
        document_report(args.output,row)
        rows.append(row)
        save(args.output/'results.json',rows)
        print(f"{number}/{len(files)}: checks={row['checks']}; accuracy={row['accuracy']}",flush=True)
    save(args.output/'expected.template.json',template)
    summary={'documents':len(rows),'checks_passed':sum(r['checks']=='pass' for r in rows),
             'review_required':sum(r['review_required'] for r in rows),
             'accuracy_passed':sum(r['accuracy']=='pass' for r in rows),
             'accuracy_evaluated':sum(r['accuracy'] in {'pass','fail'} for r in rows),
             'provider_calls':0,'llm_review_exercised':False,'seconds':round(time.monotonic()-started,2)}
    save(args.output/'summary.json',summary)
    def cell(value): return str(value).replace('|','\\|').replace('\n',' ')
    report=['# Offline resume batch check','',
            f"Documents: {len(rows)} · Checks passed: {summary['checks_passed']} · Human-answer comparisons: {summary['accuracy_evaluated']} · Provider calls: 0",'',
            'Checks passing establishes source/schema consistency, not semantic accuracy. Unreviewed results have no accuracy verdict. Comparisons cover only declared expected fields; PDF/OCR accuracy still requires source review.','',
            '| Resume | Checks | Accuracy | Review needed | Details |','|---|---|---|---|---|']
    for r in rows:
        detail=r.get('report_artifact',r.get('artifact',''))
        report.append(f"| {cell(r['file'])} | {r['checks']} | {r['accuracy']} | {r['review_required']} | {cell(detail or r.get('error_type',''))} |")
    report.extend(['','Copy expected.template.json outside the run directory. For each reviewed source, fill expected_data with selected fields from schema.json data and set human_reviewed to true. Preserve sha256. Run again with --expected pointing to that file. Lists require exact record counts and compare without ordering. Missing optional fields can be omitted from expected objects. Existing artifacts are never overwritten.'])
    (args.output/'report.md').write_text('\n'.join(report)+'\n')
    print(f"Report: {args.output/'report.md'}")
    return int(any(r['checks']=='fail' or r['accuracy'] in {'fail','stale_expectations','invalid_expectations'} for r in rows))


if __name__=='__main__':
    raise SystemExit(main())
