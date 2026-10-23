"""Offline two-resume field-reference evaluation; no inferred reviewer approvals."""
import argparse
import csv
import hashlib
import html
import json
import socket
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def values(record, field):
    return [v['value'] for a in record['attributes'] if a['name'] == field for v in a['items']]


def evaluate(reference, prediction):
    rows = []
    all_records = [(p['category'], r) for p in prediction['section_schemas'] for r in p['records']]
    for field in reference['verified_fields']:
        selector = field['record_selector']
        candidates = [r for parent, r in all_records if parent == field['parent_section']]
        if selector['kind'] == 'attribute':
            candidates = [r for r in candidates if values(r, selector['attribute']) == [selector['value']]]
        elif selector['kind'] != 'singleton':
            raise ValueError('Unsupported association selector')
        actual = values(candidates[0], field['attribute']) if len(candidates) == 1 else []
        expected = field['expected_values']
        status = 'exact_match' if len(candidates) == 1 and actual == expected else 'ambiguous' if len(candidates) > 1 else 'missing' if not actual else 'incorrect'
        if status in {'missing', 'incorrect'}:
            elsewhere = [(p, r['record_id']) for p, r in all_records if r not in candidates and values(r, field['attribute']) == expected]
            if elsewhere:
                status = 'incorrectly_associated' if any(p == field['parent_section'] for p, _ in elsewhere) else 'incorrectly_grouped'
        rows.append({**field, 'actual_values': actual, 'classification': status, 'matching_record_count': len(candidates)})
    n = len(rows)
    matched = sum(r['classification'] == 'exact_match' for r in rows)
    return {'verified_field_count': n, 'exact_matches': matched, 'exact_match_rate': matched / n if n else None,
            'precision': None, 'recall': None, 'f1': None,
            'metric_scope': 'Only explicit user-supplied field expectations; not exhaustive PDF review or population accuracy.',
            'results': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--references', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refuse to overwrite an existing run')
    references = [json.loads(p.read_text()) for p in sorted(args.references.glob('*.json'))]
    if len(references) != 2 or {r['selection_index'] for r in references} != {2, 3}:
        raise ValueError('Exactly the two specified references required')
    def prohibited(*a, **k):
        raise AssertionError('Network/provider calls prohibited')
    socket.socket.connect = prohibited
    from local_api.services import llm_section_review as llm
    llm.provider_json = prohibited
    llm.call_deepseek = prohibited
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionResponse
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.resume_sections import build_sections
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    from local_api.services.subschema_validation import validate_hierarchy
    protected = []
    for name in ('hierarchical-deepseek-five-20261023-225341', 'deepseek-schema-full350-20261022',
                 'hierarchical-defect-replay-20261023-231542', 'project-url-fix-20261024'):
        protected.extend(p for p in (ROOT / 'reports' / name).rglob('*') if p.is_file())
    protected.extend(p for p in args.references.rglob('*') if p.is_file())
    protected.extend(ROOT / r['source_path'] for r in references)
    protected.extend(ROOT / f'tests/fixtures/hierarchical_defects/{i:02}.json' for i in (2, 3))
    before = {str(p): sha(p) for p in protected}
    args.output.mkdir(parents=True, mode=0o700)
    save(args.output / 'preservation-before.json', before)
    summary = []
    for ref in references:
        index = ref['selection_index']
        source = Path(ref['source_path'])
        if sha(source) != ref['source_sha256']:
            raise ValueError('PDF hash mismatch')
        directory = args.output / ref['document_key']
        directory.mkdir(mode=0o700)
        frozen = ROOT / f'reports/hierarchical-deepseek-five-20261023-225341/results/{index:02}'
        extraction = json.loads((frozen / 'extraction.json').read_text())
        elements = [ExtractedElement.model_validate(e) for e in extraction['elements']]
        for field in ref['verified_fields']:
            for q in field['source_evidence']:
                if elements[q['source_element_index']].text[q['start']:q['end']] != q['quote']:
                    raise ValueError('Reference source quote mismatch')
        sections = SectionResponse.model_validate(json.loads((frozen / 'sections.json').read_text()))
        if validate_result(elements, sections):
            raise ValueError('Invalid frozen source inventory')
        sections.metadata['offline_replay'] = {'provider_calls': 0, 'fresh_llm_review': False}
        historical = sections.metadata.pop('llm_review', None)
        sections.metadata['offline_replay']['historical_review'] = historical
        sections.sections = build_sections({s.category: s.blocks for s in sections.sections}, elements)
        if validate_result(elements, sections):
            raise ValueError('Invalid replayed source inventory')
        mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections, source=source.name))
        validate_hierarchy(mapped.section_schemas, sections)
        output = mapped.model_dump(mode='json')
        save(directory / 'prediction.json', output)
        save(directory / 'sections.json', sections.model_dump(mode='json'))
        latest_path = ROOT / ref['latest_prediction_path']
        latest = json.loads(latest_path.read_text())
        unchanged = all(latest[k] == output[k] for k in ('data', 'section_schemas'))
        evaluation = evaluate(ref, output)
        evaluation.update({'document_key': ref['document_key'], 'same_as_latest_post_fix_fields': unchanged,
                           'schema_valid': True, 'source_evidence_valid': True, 'provider_calls': 0})
        save(directory / 'evaluation.json', evaluation)
        block_text = {f'e{b.source_element_index}:{b.start}:{b.end}': b.text for s in sections.sections for b in s.blocks}
        block_text.update({f'e{b.source_element_index}:{b.start}:{b.end}': b.text for b in sections.needs_review})
        worksheet = []
        for parent in output['section_schemas']:
            for record in parent['records']:
                context = [{k: values(record, k)} for k in ('name', 'company', 'role', 'degree', 'institution', 'language') if values(record, k)]
                for attr in record['attributes']:
                    worksheet.append({'kind': 'field', 'parent_section': parent['category'], 'predicted_record_id': record['record_id'],
                        'predicted_record_context': context, 'attribute': attr['name'],
                        'predicted_values': [v['value'] for v in attr['items']],
                        'predicted_evidence': [q for v in attr['items'] for q in v['evidence']],
                        'source_text': [{ 'source_id': sid, 'text': block_text[sid]} for sid in record['source_ids']],
                        'review_status': 'pending', 'expected_values': None, 'expected_parent_section': None,
                        'expected_record_association': None, 'reviewer_source_evidence': [], 'reviewer_notes': ''})
            for q in parent['residual_blocks']:
                worksheet.append({'kind': 'residual_source', 'parent_section': parent['category'],
                    'source_text': [q], 'review_status': 'pending', 'expected_values': None,
                    'expected_parent_section': None, 'expected_record_association': None, 'reviewer_notes': ''})
        for b in sections.needs_review:
            worksheet.append({'kind': 'unassigned_source', 'source_text': [b.model_dump(mode='json')], 'review_status': 'pending',
                              'expected_values': None, 'expected_parent_section': None, 'expected_record_association': None, 'reviewer_notes': ''})
        # Predictions stay in the worksheet; they are never promoted to verified references.
        save(directory / 'comparison-worksheet.json', {'document_key': ref['document_key'], 'instructions':
            'Fill expected values, parent, record association and exact source evidence. Pending rows are unscored. Explicitly record missing fields, merged/split records and absent values. No approval is inferred from an empty decision.', 'rows': worksheet})
        with (directory / 'comparison-worksheet.csv').open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['kind','predicted_parent','predicted_record','attribute','predicted_values','source_text','decision','expected_values','expected_parent','expected_record_association','evidence','notes'])
            for row in worksheet:
                writer.writerow([row['kind'],row.get('parent_section',''),row.get('predicted_record_id',''),row.get('attribute',''),
                    json.dumps(row.get('predicted_values'),ensure_ascii=False),json.dumps(row['source_text'],ensure_ascii=False),'','','','','',''])
        headings = ['Parent / record / field','System output (unverified)','Source record text','Your decision / expected value / correct association']
        table = []
        for row in worksheet:
            label = ' / '.join(str(row.get(k,'')) for k in ('parent_section','predicted_record_id','attribute')) or row['kind']
            text = '\n'.join(q.get('text',q.get('quote','')) for q in row['source_text'])
            table.append('<tr><td>'+html.escape(label)+'</td><td>'+html.escape(json.dumps(row.get('predicted_values'),ensure_ascii=False))+'</td><td><pre>'+html.escape(text)+'</pre></td><td contenteditable="true"></td></tr>')
        (directory / 'comparison-worksheet.html').write_text('<!doctype html><meta charset="utf-8"><title>Field review</title><style>body{font:14px sans-serif}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:8px;vertical-align:top}pre{white-space:pre-wrap}td:last-child{min-width:250px}</style><h1>'+html.escape(source.name)+'</h1><p>All system outputs below are unverified suggestions. Enter decisions in JSON/CSV for a durable record. Browser edits are temporary; save or print before closing. Empty source fields require a PDF decision, not an inferred negative label.</p><table><tr>'+''.join('<th>'+x+'</th>' for x in headings)+'</tr>'+''.join(table)+'</table>')
        (directory / 'source-text.txt').write_text('\n\n'.join(f"Element {i}, page {e.page_number}\n{e.text}" for i,e in enumerate(elements)))
        summary.append({k:v for k,v in evaluation.items() if k != 'results'} | {'worksheet_rows':len(worksheet)})
    changed = [p for p,h in before.items() if not Path(p).exists() or sha(Path(p)) != h]
    save(args.output / 'summary.json', {'documents': summary, 'provider_calls': 0,
        'protected_file_count': len(before), 'protected_files_changed': changed,
        'precision_recall_f1': None, 'metric_limit': 'Incomplete labels; no exhaustive coverage or population accuracy claims.'})
    if changed:
        raise ValueError('Protected input changed')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
