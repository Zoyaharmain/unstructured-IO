"""Section ownership precision, recall, and F1 across the 15 gold documents.

Evaluates:
1. Section-level span classification (Precision, Recall, F1 per category, Micro/Macro averages).
2. Structured schema field completion counts (not field-value accuracy).
3. Coverage ledger status distribution across all 15 documents.
4. Detailed analysis of lowest-scoring documents (S Abhinav.pdf, Java Aws backend.pdf, PUPPYKUMARI.pdf).
"""
import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionRequest
from local_api.services.resume_sections import detect_sections
from local_api.services.section_recovery import recover_sections
from local_api.services.schema_mapping import map_schema
from scripts.evaluate_resume_ground_truth import score, summarize_scores, prediction_spans, label_map, CATEGORIES


def run_evaluation(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = json.loads((ROOT / 'ground_truth/selected_15_resumes.json').read_text())
    gold = {r['file']: r for r in map(json.loads, (ROOT / 'ground_truth/gold/gold_resumes.jsonl').read_text().splitlines())}

    doc_results = []
    category_confusion = Counter()
    field_coverage_summary = Counter()

    print(f"Running field-level evaluation on {len(selected)} gold resumes...")
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

        pred_dict = {
            'sections': [s.model_dump() for s in sec_recovered.sections],
            'needs_review': [b.model_dump() for b in sec_recovered.needs_review]
        }

        gold_truth = dict(gold[file_name])
        s = score(raw_elements, gold_truth, pred_dict)

        for c in s['confusion']:
            category_confusion[(c['expected'], c['predicted'])] += c['characters']

        # Ledger status counts
        statuses = mapped.meta.get('source_coverage_ledger', {}).get('field_statuses', {})
        for f, st in statuses.items():
            field_coverage_summary[st] += 1

        doc_data = {
            'file': file_name,
            'character_accuracy': round(s['character_accuracy'], 4),
            'scored_characters': s['scored_characters'],
            'correct_characters': s['correct_characters'],
            'unassigned_characters': s['unassigned_characters'],
            'duration_seconds': duration,
            'candidate_name': mapped.data.contact.full_name,
            'email': mapped.data.contact.email,
            'phone': mapped.data.contact.phone,
            'experience_records': len(mapped.data.experience),
            'education_records': len(mapped.data.education),
            'skills_count': len(mapped.data.skills.all_skills),
            'ledger_statuses': mapped.meta.get('source_coverage_ledger', {}).get('status_counts', {})
        }
        doc_data['candidate_resume'] = mapped.meta['document_scope'].get('candidate_resume')
        doc_data['confusion'] = s['confusion']
        artifact_dir = output_dir / 'documents'
        artifact_dir.mkdir(exist_ok=True)
        (artifact_dir / (file_name + '.json')).write_text(json.dumps({
            'sections': sec_recovered.model_dump(), 'mapping': mapped.model_dump(),
        }, indent=2, ensure_ascii=False) + '\n')
        doc_results.append(doc_data)
        print(f"  {file_name:<30} -> Acc: {s['character_accuracy']*100:5.2f}% | Name: {mapped.data.contact.full_name:<20} | Exp: {len(mapped.data.experience):2d} | Edu: {len(mapped.data.education):2d} | {duration:.3f}s")

    total_time = round(time.perf_counter() - t0_all, 2)

    # Compute Category-Level Precision, Recall, F1
    all_categories = sorted(CATEGORIES)
    category_metrics = {}
    total_tp = total_fp = total_fn = 0

    for cat in all_categories:
        tp = category_confusion[(cat, cat)]
        fp = sum(n for (expected, pred), n in category_confusion.items() if pred == cat and expected != cat)
        fn = sum(n for (expected, pred), n in category_confusion.items() if expected == cat and pred != cat)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        category_metrics[cat] = {
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
        }
        total_tp += tp
        total_fp += fp
        total_fn += fn

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2 * micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0.0

    valid_cats = [m for m in category_metrics.values() if (m['tp'] + m['fn']) > 0]
    macro_precision = sum(m['precision'] for m in valid_cats) / len(valid_cats) if valid_cats else 0.0
    macro_recall = sum(m['recall'] for m in valid_cats) / len(valid_cats) if valid_cats else 0.0
    macro_f1 = sum(m['f1'] for m in valid_cats) / len(valid_cats) if valid_cats else 0.0

    total_chars = sum(d['scored_characters'] for d in doc_results)
    total_correct = sum(d['correct_characters'] for d in doc_results)
    overall_char_acc = total_correct / total_chars if total_chars else 0.0

    report = {
        'measurement': 'Non-whitespace source-character section ownership; not OCR or field-value accuracy',
        'provider_calls': 0,
        'total_documents': len(doc_results),
        'total_duration_seconds': total_time,
        'overall_character_accuracy': round(overall_char_acc, 4),
        'micro_averages': {
            'precision': round(micro_precision, 4),
            'recall': round(micro_recall, 4),
            'f1': round(micro_f1, 4),
        },
        'macro_averages': {
            'precision': round(macro_precision, 4),
            'recall': round(macro_recall, 4),
            'f1': round(macro_f1, 4),
        },
        'per_category_metrics': category_metrics,
        'coverage_ledger_summary': dict(field_coverage_summary),
        'per_document_results': doc_results,
    }
    candidates = [d for d in doc_results if d['candidate_resume'] is not False]
    report['candidate_documents'] = {
        'count': len(candidates),
        'character_accuracy': round(sum(d['correct_characters'] for d in candidates) /
                                    max(1, sum(d['scored_characters'] for d in candidates)), 4),
    }

    out_file = output_dir / 'field_level_evaluation.json'
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f"\nSaved evaluation metrics to {out_file}")
    print(f"Overall Accuracy: {overall_char_acc*100:.2f}% | Micro F1: {micro_f1*100:.2f}% | Macro F1: {macro_f1*100:.2f}%")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reports/pipeline-recovery-and-accuracy-current')
    args = parser.parse_args()
    run_evaluation(args.output_dir)

