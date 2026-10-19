"""Score source-bound field relationships only against explicit human-approved gold."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.human_review_validation import score_record_relationships


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predicted-dir',type=Path,required=True)
    parser.add_argument('--reference-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();rows=[]
    for prediction in sorted(args.predicted_dir.glob('*.json')):
        predicted=json.loads(prediction.read_text());reference=args.reference_dir/prediction.name
        row={'file':predicted['file'],'status':'missing_explicit_human_reference','metrics':None}
        if reference.exists():
            try:
                row['metrics']=score_record_relationships(predicted,json.loads(reference.read_text()));row['status']='scored'
            except ValueError as exc:row.update(status='invalid_reference_or_source',reason=str(exc))
        rows.append(row)
    summary={'candidate_documents':len(rows),'evaluated_documents':sum(r['status']=='scored' for r in rows),
             'relationship_accuracy_established':False,'new_api_calls':0,
             'note':'Exact relationship tuple precision/recall/F1 are reported only for explicit source-bound human references. Entry counts are not accuracy.'}
    summary['relationship_accuracy_established']=summary['evaluated_documents']>0
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'per-resume.json').write_text(json.dumps(rows,indent=2)+'\n')
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
