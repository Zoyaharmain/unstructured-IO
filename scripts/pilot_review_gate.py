"""Read-only release gate: every pilot needs explicit approval/export or exclusion."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.review_pilot import catalog
from scripts.human_review_validation import validate_bundle,sha


def check_pilot_ready(review_dir,approved_gold_dir,review_catalog=None):
    decisions={};blockers=[]
    for identifier,doc in catalog(review_catalog).items():
        revisions=sorted((Path(review_dir)/identifier).glob('revision-*.json'))
        if not revisions:blockers.append(doc['file']+': no recorded human review');continue
        bundle_path=revisions[-1];bundle=json.loads(bundle_path.read_text())
        if bundle.get('decision')=='exclude':
            from pypdf import PdfReader
            pages=list(range(1,len(PdfReader(doc['pdf']).pages)+1))
            if bundle.get('draft_sha256')!=sha(doc['draft']) or bundle.get('source_pdf_sha256')!=sha(doc['pdf']) or not bundle.get('reviewer','').strip() or not bundle.get('exclusion_reason','').strip() or sorted(set(bundle.get('reviewed_pages',[])))!=pages:
                blockers.append(doc['file']+': invalid exclusion evidence');continue
            decisions[doc['file']]={'status':'excluded_by_human','pdf_sha256':sha(doc['pdf']),'review_path':str(bundle_path)};continue
        artifact=json.loads(doc['artifact'].read_text())
        issues=validate_bundle(bundle,doc['draft'],doc['pdf'],artifact['extraction']['elements'])
        if issues:blockers.append(doc['file']+': '+ '; '.join(issues[:3]));continue
        gold_path=Path(approved_gold_dir)/doc['draft'].name
        if not gold_path.exists():blockers.append(doc['file']+': approved review has not been explicitly exported');continue
        gold=json.loads(gold_path.read_text())
        comparable=lambda d:[(s['span_id'],s['source_element_index'],s['start'],s['end'],s['category'],s['text']) for s in d['spans']]
        if (gold.get('human_verified') is not True or gold.get('review_provenance',{}).get('approved_bundle_sha256')!=sha(bundle_path) or comparable(gold)!=comparable(bundle['annotation']) or gold.get('records')!=bundle['annotation'].get('records')):
            blockers.append(doc['file']+': exported correction does not match approved review');continue
        decisions[doc['file']]={'status':'gold','pdf_sha256':sha(doc['pdf']),'extraction_sha256':gold['extraction_sha256'],'annotation_path':str(gold_path),'review_path':str(bundle_path)}
    return {'ready':not blockers and len(decisions)==15,'reviewed_documents':len(decisions),'required_documents':15,'blockers':blockers,'decisions':decisions}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path)
    parser.add_argument('--review-dir',type=Path,required=True)
    parser.add_argument('--approved-gold-dir',type=Path,required=True)
    args=parser.parse_args();result=check_pilot_ready(args.review_dir,args.approved_gold_dir,args.catalog)
    print(json.dumps({k:v for k,v in result.items() if k!='decisions'},indent=2))
    raise SystemExit(0 if result['ready'] else 2)
