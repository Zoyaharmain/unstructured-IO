"""Human verification and gold-standard promotion workflow for resume annotations.

Validates exact extraction hash, 100% character coverage, non-overlapping intervals,
applies human reviewer corrections, and explicitly promotes verified files to gold/.
Never marks an automated annotation as human-verified without explicit approval.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_resume_ground_truth import extraction_hash, label_map, CATEGORIES


def apply_corrections(draft, corrections):
    """Apply human reviewer corrections to a draft annotation.

    Corrections can include:
    - span_updates: list of dicts with {span_id: ..., category: ..., reason: ...}
    - splits: list of dicts with {span_id: ..., segments: [{start: ..., end: ..., category: ...}]}
    - merges: list of dicts with {span_ids: [...], category: ...}
    - record_updates: {work_experience: [...], education: [...]}
    - notes: reviewer notes
    """
    spans_by_id = {s['span_id']: s for s in draft['spans']}
    applied = []

    # 1. Direct span category corrections
    for update in corrections.get('span_updates', []):
        sid = update['span_id']
        new_cat = update['category']
        if sid not in spans_by_id:
            raise KeyError(f"Correction references unknown span_id: {sid}")
        if new_cat not in CATEGORIES and new_cat != 'ignore':
            raise ValueError(f"Invalid category in correction: {new_cat}")
        old_cat = spans_by_id[sid]['category']
        spans_by_id[sid]['category'] = new_cat
        spans_by_id[sid]['uncertainty_flag'] = False
        spans_by_id[sid]['uncertainty_reason'] = None
        spans_by_id[sid]['human_corrected'] = True
        spans_by_id[sid]['correction_note'] = update.get('note', f"Changed from {old_cat} to {new_cat}")
        applied.append(f"Updated span {sid}: {old_cat} -> {new_cat}")

    # 2. Record updates
    if 'record_updates' in corrections:
        rec_updates = corrections['record_updates']
        if 'work_experience' in rec_updates:
            draft['records']['work_experience'] = rec_updates['work_experience']
            applied.append("Updated work_experience records")
        if 'education' in rec_updates:
            draft['records']['education'] = rec_updates['education']
            applied.append("Updated education records")

    draft['corrections_applied'] = applied
    draft['reviewer_notes'] = corrections.get('notes', 'Reviewed and approved.')
    return draft


def validate_gold_invariants(data, elements):
    """Strictly assert all invariants required for gold ground truth."""
    if data['extraction_sha256'] != extraction_hash(elements):
        raise ValueError("Extraction SHA256 does not match authoritative source elements")

    # Full character coverage & non-overlapping intervals check
    allowed = CATEGORIES | {'ignore'}
    labels = label_map(elements, data['spans'], allowed)

    # Ensure no unresolved needs_review categories
    for s in data['spans']:
        if s['category'] not in allowed:
            raise ValueError(f"Span {s.get('span_id')} has invalid category: {s.get('category')}")

    return True


def promote_to_gold(draft_path, corrections_path, gold_dir, gold_jsonl_path, reviewer=None, approved_review_path=None):
    """Export one explicitly approved review to a new gold version; never auto-approve."""
    import copy
    from scripts.human_review_validation import validate_bundle,sha
    if approved_review_path is None:
        raise ValueError('Explicit approved human review bundle required; draft predictions are not approval')
    original=json.loads(Path(draft_path).read_text())
    bundle=json.loads(Path(approved_review_path).read_text())
    artifact=json.loads((ROOT/original['metadata']['source_artifact']).read_text())
    pdf=ROOT/'ground_truth/pilot_resumes'/original['file']
    issues=validate_bundle(bundle,draft_path,pdf,artifact['extraction']['elements'])
    if issues:raise ValueError('Human approval requirements failed: '+ '; '.join(issues))
    if reviewer and reviewer!=bundle['reviewer']:raise ValueError('Reviewer does not match approved bundle')
    old_gold=(ROOT/'ground_truth/gold').resolve()
    for target in (Path(gold_dir).resolve(),Path(gold_jsonl_path).resolve()):
        if target==old_gold or old_gold in target.parents:raise ValueError('Existing gold is preserved; export to a new version directory')
    gold=copy.deepcopy(bundle['annotation'])
    gold.update(human_verified=True,status='gold_approved',reviewer=bundle['reviewer'],reviewed_at=bundle['recorded_at'],
        human_decisions=bundle['span_decisions'],
        review_provenance={'approved_bundle_sha256':sha(approved_review_path),'original_draft_sha256':bundle['draft_sha256'],
            'source_pdf_sha256':bundle['source_pdf_sha256'],'approval_revision':bundle['revision'],'attestations':bundle['attestations'],
            'reviewed_pages':bundle['reviewed_pages']})
    for span in gold['spans']:
        span['uncertainty_flag']=False;span['uncertainty_reason']=None
    gold['uncertainty_summary']={**gold.get('uncertainty_summary',{}),'uncertain_spans':0,'uncertainty_rate':0.0}
    gold_dir=Path(gold_dir);gold_dir.mkdir(parents=True,exist_ok=True)
    destination=gold_dir/Path(draft_path).name
    manifest=Path(gold_jsonl_path)
    if manifest.exists():
        entries=[json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
        if any(e['file']==gold['file'] for e in entries):raise ValueError('Approved correction already exists; choose a new dataset version')
    with destination.open('x') as stream:json.dump(gold,stream,indent=2,ensure_ascii=False)
    entry={'file':gold['file'],'extraction_sha256':gold['extraction_sha256'],'human_verified':True,
        'spans':[{k:span[k] for k in ('source_element_index','start','end','category')} for span in gold['spans']],
        'source_artifact':gold['metadata']['source_artifact'],'review_provenance':gold['review_provenance']}
    return destination,entry


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft',type=Path,required=True)
    parser.add_argument('--approved-review',type=Path,required=True)
    parser.add_argument('--gold-dir',type=Path,default=ROOT/'ground_truth/approved_gold_v2')
    parser.add_argument('--gold-jsonl',type=Path,default=ROOT/'ground_truth/approved_gold_v2/gold_resumes.jsonl')
    args=parser.parse_args()
    path,entry=promote_to_gold(args.draft,None,args.gold_dir,args.gold_jsonl,approved_review_path=args.approved_review)
    args.gold_jsonl.parent.mkdir(parents=True,exist_ok=True)
    with args.gold_jsonl.open('a') as stream:stream.write(json.dumps(entry,ensure_ascii=False)+'\n')
    print('Explicitly approved annotation exported to '+str(path))


if __name__=='__main__':main()
