"""Offline diagnostics for the confirmed production run; no provider calls.

Structural/evidence checks and user-example regressions are not semantic accuracy.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_api.schemas.mapping import SchemaMappingResponse
from local_api.schemas.sections import SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def text_hash(elements):
    return hashlib.sha256(json.dumps([e['text'] for e in elements], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def fields(schema):
    result = defaultdict(list)
    for parent in schema.get('section_schemas', []):
        for record in parent['records']:
            for attr in record['attributes']:
                result[parent['category'] + '.' + attr['name']].extend(i['value'] for i in attr['items'])
    return dict(result)


def evaluate(manifest_path):
    manifest = json.loads(manifest_path.read_text())
    root = manifest_path.parent
    results = Path(manifest['execution']['results_directory'])
    execution = json.loads((results / 'execution-summary.json').read_text())
    calls = json.loads((results / 'calls.json').read_text())
    rows, changes = [], []
    for selected in manifest['selected']:
        directory = results / ('%02d' % selected['index'])
        row = {'file': selected['file'], 'document_id': selected['document_id'], 'sha256': selected['sha256'],
               'semantic_accuracy': None, 'semantic_accuracy_status': 'unscorable_no_verified_field_reference'}
        own_calls = [c for c in calls if c['document_id'] == selected['document_id']]
        usage = Counter()
        for c in own_calls:
            usage.update({k: v for k, v in c.get('usage', {}).items() if type(v) is int})
        row.update(provider_requests=len(own_calls), usage=dict(usage),
                   provider_latency_seconds=round(sum(c.get('latency_seconds', 0) for c in own_calls), 3),
                   calls_by_stage=dict(Counter(c['stage'] for c in own_calls)),
                   request_failures=[c for c in own_calls if c['status'] == 'failed'])
        if not (directory / 'schema.json').is_file():
            row['status'] = 'no_final_mapping'; rows.append(row); continue
        schema = json.loads((directory / 'schema.json').read_text())
        sections = SectionResponse.model_validate(json.loads((directory / 'sections.json').read_text()))
        extraction = json.loads((directory / 'extraction.json').read_text())
        elements = [ExtractedElement.model_validate(e) for e in extraction['elements']]
        baseline = json.loads(Path(selected['baseline_mapping']).read_text())
        original = json.loads(Path(selected['baseline_source']).read_text())
        problems = []
        try:
            SchemaMappingResponse.model_validate(schema)
            row['schema_valid'] = True
        except Exception as exc:
            row['schema_valid'] = False; problems.append({'type': 'schema_invalid', 'error': str(exc)[:500]})
        source_errors = validate_result(elements, sections)
        row['source_interval_validation_errors'] = source_errors
        try:
            validate_hierarchy(schema['section_schemas'], sections)
            row['hierarchy_and_record_local_evidence_valid'] = True
        except Exception as exc:
            row['hierarchy_and_record_local_evidence_valid'] = False
            problems.append({'type': 'hierarchy_or_evidence_invalid', 'error': str(exc)[:500]})
        same = text_hash(extraction['elements']) == text_hash(original['extraction']['elements'])
        row['same_extracted_element_text_as_baseline'] = same
        stats, record_counts = Counter(), Counter()
        reviews, parent_stats = [], {}
        for parent in schema['section_schemas']:
            own = Counter(); record_signatures = {}
            record_counts[parent['category']] = len(parent['records'])
            for record in parent['records']:
                record_values = {a['name']: [i['value'] for i in a['items']] for a in record['attributes']}
                signature = json.dumps(record_values, sort_keys=True, ensure_ascii=False)
                if any(record_values.values()) and signature in record_signatures:
                    problems.append({'type': 'duplicate_record_candidate', 'parent': parent['category'],
                                     'record_ids': [record_signatures[signature], record['record_id']]})
                record_signatures[signature] = record['record_id']
                if record['review_reasons']:
                    reviews.append({'parent': parent['category'], 'record_id': record['record_id'], 'reasons': record['review_reasons']})
                for attr in record['attributes']:
                    own[attr['status'] + '_attributes'] += 1
                    seen = set()
                    for item in attr['items']:
                        own['populated_items'] += 1
                        own['evidence_quotes'] += len(item['evidence'])
                        own[item['status'] + '_items'] += 1
                        marker = str(item['value']).casefold()
                        if marker in seen:
                            problems.append({'type': 'duplicate_attribute_item', 'parent': parent['category'],
                                'record_id': record['record_id'], 'attribute': attr['name'], 'value': item['value']})
                        seen.add(marker)
            own['residual_blocks'] = len(parent['residual_blocks'])
            parent_stats[parent['category']] = dict(own); stats.update(own)
        row.update(status='evaluated', structural_diagnostic_counts=dict(stats), counts_are_accuracy=False,
                   parent_diagnostics=parent_stats, record_counts=dict(record_counts),
                   relationship_review_records=reviews, diagnostics=problems,
                   missing_required_fields=schema['meta']['missing_required_fields'],
                   section_review=sections.metadata.get('llm_review', {}),
                   audit=json.loads((directory / 'schema-audit.json').read_text()),
                   feedback=json.loads((directory / 'pipeline.json').read_text()))
        before, after = fields(baseline), fields(schema)
        diff = []
        for key in sorted(set(before) | set(after)):
            if before.get(key, []) != after.get(key, []):
                diff.append({'field': key, 'before': before.get(key, []), 'after': after.get(key, [])})
        changes.append({'file': selected['file'], 'same_extracted_text': same,
                        'note': 'Value-list differences are not proof of corrected associations or semantic improvement.',
                        'changes': diff})
        if selected['file'] == '_ManjunathMurugan.pdf':
            expected = {'personal_information.full_name': 'Manjunath MURUGAN',
                        'personal_information.location': 'Noisy-le-Grand, France'}
            checks = [{'field': key, 'expected': value, 'before': before.get(key, []),
                       'after': after.get(key, []), 'passes': value in after.get(key, [])} for key, value in expected.items()]
            for language, proficiency in [('English', 'Full Professional Proficiency (C1)'),
                                          ('Fran\u00e7ais', 'D\u00e9butant (cours intensif en cours)')]:
                pairs = [{a['name']: [i['value'] for i in a['items']] for a in r['attributes']}
                         for p in schema['section_schemas'] if p['category'] == 'languages' for r in p['records']]
                checks.append({'language': language, 'expected_proficiency': proficiency,
                    'passes': any(language in p.get('language', []) and proficiency in p.get('proficiency', []) for p in pairs),
                    'actual_language_records': pairs})
            row['user_reported_regression_checks'] = checks
        rows.append(row)
    summary = {'selected_documents': 5, 'documents_with_final_schema': sum(r.get('status') == 'evaluated' for r in rows),
               'schema_valid_documents': sum(r.get('schema_valid', False) for r in rows),
               'hierarchy_and_evidence_valid_documents': sum(r.get('hierarchy_and_record_local_evidence_valid', False) for r in rows),
               'semantic_metrics': {'precision': None, 'recall': None, 'f1': None, 'exact_match_accuracy': None,
                                    'reason': 'No exhaustive human-verified field-level references'},
               'execution': execution, 'documents': rows}
    save(root / 'evaluation.json', summary)
    save(root / 'before-after.json', changes)
    print(json.dumps({'documents': len(rows), 'schema_valid': summary['schema_valid_documents'],
                      'evidence_valid': summary['hierarchy_and_evidence_valid_documents'],
                      'provider_requests': execution['provider_requests'], 'usage': execution['usage']}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    evaluate(parser.parse_args().manifest)


if __name__ == '__main__':
    main()
