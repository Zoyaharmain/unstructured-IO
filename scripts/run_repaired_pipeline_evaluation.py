"""Evaluate repaired extraction, recovery, schema mapping and ledger across 15 gold resumes and key edge-case fixtures.
"""
import json
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from local_api.services.resume_sections import detect_sections
from local_api.services.section_recovery import recover_sections
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.schemas.extraction import ExtractedElement
from scripts.evaluate_resume_ground_truth import extraction_hash, score, summarize_scores, prediction_spans


def evaluate_15_gold(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = json.loads((ROOT / 'ground_truth/selected_15_resumes.json').read_text())
    gold = {r['file']: r for r in map(json.loads, (ROOT / 'ground_truth/gold/gold_resumes.jsonl').read_text().splitlines())}

    results = []
    gold_scores = []

    print(f"Evaluating {len(selected)} gold resumes...")
    t0_all = time.perf_counter()

    for item in selected:
        file_name = item['file']
        art_path = ROOT / '.upstream/batch-validation' / item['artifact']
        art = json.loads(art_path.read_text())
        raw_elements = art['extraction']['elements']
        elements = [ExtractedElement(**e) for e in raw_elements]

        t0 = time.perf_counter()
        sec_req = SectionRequest(elements=elements)
        sec_resp = detect_sections(sec_req)
        sec_recovered = recover_sections(sec_req, sec_resp)
        mapping_req = SchemaMappingRequest(elements=elements, sections=sec_recovered, source=file_name)
        mapped = map_schema(mapping_req)
        duration = round(time.perf_counter() - t0, 3)

        # Ground truth section scoring
        pred_dict = {
            'sections': [s.model_dump() for s in sec_recovered.sections],
            'needs_review': [b.model_dump() for b in sec_recovered.needs_review]
        }
        gt_score = score(raw_elements, gold[file_name], pred_dict)
        gold_scores.append(gt_score)

        ledger = mapped.meta.get('source_coverage_ledger', {})
        status_counts = ledger.get('status_counts', {})

        row = {
            'file': file_name,
            'pages': item.get('pages', 1),
            'character_accuracy': round(gt_score['character_accuracy'] * 100, 2),
            'scored_characters': gt_score['scored_characters'],
            'correct_characters': gt_score['correct_characters'],
            'unassigned_characters': gt_score['unassigned_characters'],
            'expected_sections': gt_score['expected_sections'],
            'entirely_correct_sections': gt_score['entirely_correct_sections'],
            'missing_sections': gt_score['missing_sections'],
            'extra_sections': gt_score['extra_sections'],
            'candidate_name': mapped.data.contact.full_name,
            'email': mapped.data.contact.email,
            'phone': mapped.data.contact.phone,
            'experience_records': len(mapped.data.experience),
            'education_records': len(mapped.data.education),
            'skills_count': len(mapped.data.skills.all_skills),
            'missing_required_fields': mapped.meta.get('missing_required_fields', []),
            'ledger_statuses': status_counts,
            'duration_seconds': duration,
        }
        results.append(row)
        print(f"  {file_name:30} -> Acc: {row['character_accuracy']}% | Name: {row['candidate_name']:20} | Exp: {row['experience_records']:2} | Edu: {row['education_records']:2} | {duration}s")

    total_time = round(time.perf_counter() - t0_all, 2)
    summary = summarize_scores(gold_scores)

    evaluation_report = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total_evaluated': len(results),
        'total_duration_seconds': total_time,
        'overall_character_accuracy': round(summary['accuracy'] * 100, 2),
        'total_scored_characters': summary['scored_characters'],
        'entirely_correct_resumes': summary['entirely_correct_resumes'],
        'per_resume_results': results,
        'category_metrics': summary['precision_recall_f1'],
    }

    (output_dir / 'gold_15_evaluation.json').write_text(json.dumps(evaluation_report, indent=2))
    print(f"\nOverall Gold Accuracy: {evaluation_report['overall_character_accuracy']}% in {total_time}s")
    return evaluation_report


if __name__ == '__main__':
    out = ROOT / 'reports/pipeline-repairs-20261025-104500'
    evaluate_15_gold(out)

