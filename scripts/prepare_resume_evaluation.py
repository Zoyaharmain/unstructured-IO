"""Audit prior use and freeze disjoint development/validation/held-out manifests."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_api.services.evaluation_datasets import inventory, audit_usage, make_splits, validate_splits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', default='resume-ownership-v1')
    parser.add_argument('--history', type=Path, nargs='+', default=[ROOT/p for p in ('reports','ground_truth','manifests','tests','scripts','.upstream','docs','local_api/data')])
    args = parser.parse_args()
    if args.output.exists() or not args.folder.is_dir():
        parser.error('Use an existing source folder and a new output directory')
    documents = inventory(args.folder)
    audited = audit_usage(documents, args.history)
    splits = make_splits(audited, seed=args.seed)
    validate_splits(splits)
    args.output.mkdir(parents=True, mode=0o700)
    for name, rows in splits.items():
        (args.output/(name+'.jsonl')).write_text(''.join(json.dumps(row)+'\n' for row in rows))
    summary = {'unique_source_documents':len(documents),'split_counts':{k:len(v) for k,v in splits.items()},
               'seed':args.seed,'history_roots':[str(p) for p in args.history],
               'previously_exposed_documents':sum(bool(d['historical_evidence']) for d in audited),
               'independently_labeled_held_out_documents':0,'unseen_resume_accuracy':'not_established',
               'training_use':'Not documented per resume; external pretraining and untracked use cannot be audited here.',
               'reservation_policy':'Prior exposure always goes to development. Unmatched documents require independence attestation before held-out use.',
               'empty_split_policy':'Never relabel used data as unseen to fill empty validation or test splits.'}
    (args.output/'audit-summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
