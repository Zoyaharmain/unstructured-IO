"""Re-run local sections against existing, immutable human-verified source labels.

Existing gold is previously used data. This evaluator never calls it unseen and
never derives labels from predictions. Record metrics require separate labels.
"""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truth', type=Path, default=ROOT/'ground_truth/gold/gold_resumes.jsonl')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output must be new')
    from scripts.batch_check_resumes import initialize_worker
    from scripts.evaluate_resume_ground_truth import score, summarize_scores
    from local_api.schemas.sections import SectionRequest
    from local_api.services.resume_sections import detect_sections
    from local_api.services.section_recovery import recover_sections
    from local_api.services.source_ownership import finalize_ownership
    initialize_worker()
    rows, scores = [], []
    for line in args.truth.read_text().splitlines():
        if not line.strip():
            continue
        truth = json.loads(line)
        source = Path(truth['source_artifact'])
        if not source.is_file():
            rows.append({'file':truth['file'], 'status':'source_unavailable'})
            continue
        artifact = json.loads(source.read_text())
        elements = artifact['extraction']['elements']
        request = SectionRequest(elements=elements)
        status, error_type = 'scored', None
        try:
            sections = finalize_ownership(request.elements, recover_sections(request, detect_sections(request)))
            prediction = sections.model_dump()
        except Exception as exc:
            # A failed parser contributes abstentions, not an omitted easy-only
            # denominator. This is an evaluation representation, not a parser result.
            status, error_type = 'pipeline_failed', type(exc).__name__
            prediction = {'sections':[], 'needs_review':[{'source_element_index':i,'start':0,
                'end':len(e['text']),'text':e['text']} for i,e in enumerate(elements)]}
        result = score(elements, truth, prediction)
        scores.append(result)
        rows.append({'file':truth['file'], 'status':status, 'error_type':error_type, **result})
        print(json.dumps({'completed':len(rows), 'status':status}), flush=True)
    summary = summarize_scores(scores)
    category_scores = summary['precision_recall_f1'] or {}
    summary.update(section_macro_f1=sum(s['f1'] for s in category_scores.values())/len(category_scores) if category_scores else None,
                   pipeline_failures=sum(row['status']=='pipeline_failed' for row in rows),
                   source_unavailable_documents=sum(row['status']=='source_unavailable' for row in rows),
                   record_boundary_f1=None, responsibility_ownership_accuracy=None, cross_record_leakage=None,
                   scope='Existing previously used gold corpus; not unseen held-out evidence', provider_calls=0,
                   production_quality_established=False)
    args.output.mkdir(parents=True, mode=0o700)
    (args.output/'summary.json').write_text(json.dumps(summary, indent=2))
    (args.output/'per-resume.json').write_text(json.dumps(rows, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
