"""Re-run local section detection against source-hash-bound human labels.

Field completion is reported separately; it is not field accuracy.
No provider calls and no changes to source or ground truth.
"""
import argparse
import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_resume_ground_truth import score, summarize_scores
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import get_engine
from local_api.services.schema_mapping import map_schema


def evaluate(source, truth_path):
    truth_rows = [json.loads(line) for line in truth_path.read_text().splitlines() if line.strip()]
    truth = {row['file']: row for row in truth_rows}
    if len(truth) != len(truth_rows):
        raise ValueError('Duplicate ground-truth filename')
    inventory = json.loads((source / 'current-results.json').read_text())
    engine = get_engine()
    scores, rows, fields = [], [], Counter()
    for row in inventory:
        if row['file'] not in truth or not row.get('artifact'):
            continue
        artifact = json.loads((source / row['artifact']).read_text())
        request = SectionRequest(elements=artifact['extraction']['elements'], extraction_verified=True)
        sections = engine.detect(request)
        result = score(artifact['extraction']['elements'], truth[row['file']], sections.model_dump())
        mapped = map_schema(SchemaMappingRequest(elements=request.elements, sections=sections))
        scores.append(result)
        for parent in mapped.section_schemas:
            for record in parent.records:
                for attr in record.attributes:
                    fields[parent.category + '.' + attr.name + '.' + attr.status] += 1
        rows.append({'file': row['file'], **result})
    if not scores:
        raise ValueError('No source-hash-matched human labels were evaluated')
    return {'measurement': 'Human-labeled non-whitespace section ownership; not OCR or subfield accuracy',
            'sections': summarize_scores(scores), 'per_document': rows,
            'missing_truth_documents': sorted(set(truth) - {r['file'] for r in rows}),
            'field_completion_counts_not_accuracy': dict(sorted(fields.items())), 'provider_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--truth', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.source, args.truth)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result['sections'], indent=2))


if __name__ == '__main__':
    main()
