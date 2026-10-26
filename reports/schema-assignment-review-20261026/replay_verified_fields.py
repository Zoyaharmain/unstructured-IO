"""Replay partial references against frozen extraction; no original PDF claim."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result


def values(record, name):
    return [i.value for a in record.attributes if a.name == name for i in a.items]


def main():
    out = Path(__file__).parent / 'verified-fields'
    out.mkdir(exist_ok=True)
    results = []
    for path in sorted((ROOT / 'ground_truth/field_level/v5').glob('*.json')):
        reference = json.loads(path.read_text())
        frozen = ROOT / 'reports/hierarchical-deepseek-five-20261023-225341/results' / f"{reference['selection_index']:02}"
        elements = [ExtractedElement.model_validate(e) for e in json.loads((frozen / 'extraction.json').read_text())['elements']]
        for field in reference['verified_fields']:
            for quote in field['source_evidence']:
                if 'source_id' in quote:
                    index, start, end = map(int, quote['source_id'].removeprefix('e').split(':'))
                    assert quote['quote'] in elements[index].text[start:end]
                else:
                    assert elements[quote['source_element_index']].text[quote['start']:quote['end']] == quote['quote']
        sections = SectionResponse.model_validate(json.loads((frozen / 'sections.json').read_text()))
        sections.sections = build_sections({s.category: s.blocks for s in sections.sections}, elements)
        assert not validate_result(elements, sections)
        mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections))
        rows = []
        for field in reference['verified_fields']:
            records = [r for s in mapped.section_schemas if s.category == field['parent_section'] for r in s.records]
            selector = field['record_selector']
            if selector['kind'] == 'record_id':
                records = [r for r in records if r.record_id == selector['value']]
            elif selector['kind'] == 'attribute':
                records = [r for r in records if values(r, selector['attribute']) == [selector['value']]]
            elif selector['kind'] != 'singleton':
                raise ValueError('Unsupported selector')
            actual = values(records[0], field['attribute']) if len(records) == 1 else []
            rows.append({'parent': field['parent_section'], 'attribute': field['attribute'],
                         'selector': selector, 'expected': field['expected_values'], 'actual': actual,
                         'exact_match': len(records) == 1 and actual == field['expected_values']})
        results.append({'document': reference['document_key'], 'fields': rows})
    summary = {'measurement': '17 partial human field references replayed against frozen extracted source; original PDF paths unavailable, no fresh PDF verification',
               'provider_calls': 0, 'verified_field_count': sum(len(r['fields']) for r in results),
               'exact_matches': sum(f['exact_match'] for r in results for f in r['fields']), 'documents': results}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print({k: v for k, v in summary.items() if k != 'documents'})


if __name__ == '__main__':
    main()
