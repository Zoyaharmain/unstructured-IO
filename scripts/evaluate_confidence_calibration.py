"""Offline human-label calibration. Does not modify pipeline behavior or call providers.

Input JSONL rows: document_group, task, score (raw winning margin), correct (0/1),
label_source='human_verified'. The frozen classifier must not have trained on these groups.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--task', choices=['section_content', 'section_heading'], required=True)
    p.add_argument('--model-revision', required=True)
    p.add_argument('--anchor-sha256', required=True)
    p.add_argument('--method', choices=['platt', 'isotonic'], default='platt')
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()]
    if any(r.get('label_source') != 'human_verified' for r in rows):
        p.error('Only human-verified labels are accepted; judge findings are not ground truth.')
    rows = [r for r in rows if r['task'] == args.task]
    from local_api.services.calibration_evaluation import fit_calibration
    artifact, metrics, bins = fit_calibration(rows, method=args.method)
    artifact.update(task=args.task, model_revision=args.model_revision, anchor_sha256=args.anchor_sha256,
                    dataset_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
                    target='ml_candidate_correct', label_source='human_verified', evaluation=metrics)
    artifact['version'] = hashlib.sha256(json.dumps(artifact, sort_keys=True).encode()).hexdigest()
    (args.output/'calibration.json').write_text(json.dumps(artifact, indent=2))
    (args.output/'evaluation.json').write_text(json.dumps({'metrics': metrics, 'reliability_bins': bins}, indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], '--', color='gray')
    ax.plot([b['mean_probability'] for b in bins], [b['accuracy'] for b in bins], 'o-')
    ax.set(xlabel='Predicted probability of correct ML candidate', ylabel='Observed correctness',
           title=f'{args.task}: held-out reliability')
    fig.savefig(args.output/'reliability.png', bbox_inches='tight')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
