"""Reconcile the exact 15 pilot annotations with cached source-preserving LLM output.

No live provider calls, no gold changes, no uncertainty suppression. Produces
new unverified drafts plus independent per-resume accounting and review reports.
"""
import json
import argparse
from pathlib import Path
import sys
import html
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.generate_ground_truth_drafts import generate_draft,generate_html_review
from local_api.schemas.extraction import ExtractionResponse
from local_api.schemas.sections import SectionResponse
from local_api.services.source_accounting import account_source


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir',type=Path,default=ROOT/'ground_truth/cache/llm_reviews')
    parser.add_argument('--output',type=Path,default=ROOT/'ground_truth/recovery_pilot')
    args=parser.parse_args()
    selected=json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text())
    output=args.output;(output/'drafts').mkdir(parents=True,exist_ok=True)
    rows=[]
    for item in selected:
        name=item['file'];stem=Path(name).stem.replace(' ','_').replace('(','').replace(')','')
        before=json.loads((ROOT/'ground_truth/drafts'/(stem+'.json')).read_text())
        path=ROOT/'.upstream/batch-validation'/item['artifact']
        art=json.loads(path.read_text());extraction=ExtractionResponse.model_validate(art['extraction'])
        local=SectionResponse.model_validate(art['sections'])
        local_accounting=account_source(extraction.elements,local)
        try:
            after=generate_draft(name,path,args.cache_dir,cached_only=True)
            (output/'drafts'/(stem+'.json')).write_text(json.dumps(after,indent=2,ensure_ascii=False)+'\n')
            generate_html_review(after,output/'drafts'/(stem+'_review.html'))
            state=after['llm_review'];accounting=state['source_accounting']
            row={'file':name,'cache_used':state.get('cache_used',False),'new_provider_calls':0,
                 'provider_status_from_cache':state.get('status'),'local_unassigned_spans':len(local.needs_review),
                 'local_meaningful_unassigned':local_accounting['unresolved_meaningful_spans'],
                 'reviewed_spans':accounting['total_spans'],'final_unassigned_spans':after['uncertainty_summary']['unassigned_spans'],
                 'final_meaningful_unassigned':accounting['unresolved_meaningful_spans'],
                 'before_uncertain_spans':before['uncertainty_summary']['uncertain_spans'],
                 'after_uncertain_spans':after['uncertainty_summary']['uncertain_spans'],
                 'disagreements_for_human_review':after['uncertainty_summary']['disagreement_spans'],
                 'assignments_changed_in_cached_review':state.get('changed_units'),
                 'artifacts':accounting['non_content_artifacts'],'source_coverage_exact':accounting['all_source_text_preserved'],
                 'duplicates_excluded':accounting['duplicates_excluded'],'warnings':[],
                 'review_file':'drafts/'+stem+'_review.html'}
        except Exception as exc:row={'file':name,'error':type(exc).__name__,'new_provider_calls':0}
        rows.append(row)
    (output/'results.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    headings=['Resume','Local unassigned (meaningful)','After cached LLM (meaningful)','Disagreements for human review','Artifacts','Cached provider status','Review']
    body=[]
    for r in rows:
        cells=[r['file'],r.get('local_meaningful_unassigned','error'),r.get('final_meaningful_unassigned','error'),r.get('disagreements_for_human_review','error'),r.get('artifacts',''),r.get('provider_status_from_cache','error')]
        body.append('<tr>'+''.join('<td>'+html.escape(str(c))+'</td>' for c in cells)+('<td><a href="'+html.escape(r['review_file'],quote=True)+'">Inspect spans and records</a></td>' if r.get('review_file') else '<td>Error</td>')+'</tr>')
    page='<!doctype html><meta charset="utf-8"><title>Pilot recovery accounting</title><style>body{font:16px system-ui;margin:24px}td,th{padding:10px;border:1px solid #ddd;text-align:left}table{border-collapse:collapse}</style><h1>Pilot recovery accounting — 15 resumes</h1><p>Saved DeepSeek decisions replayed; no new provider calls. All drafts remain unverified. Disagreements are human-review items, not missing assignments. Complete means valid provider output, not correct classification.</p><table><tr>'+''.join('<th>'+h+'</th>' for h in headings)+'</tr>'+''.join(body)+'</table>'
    (output/'index.html').write_text(page)
    print(json.dumps({'resumes':len(rows),'errors':sum('error' in r for r in rows),'meaningful_unassigned_before':sum(r.get('local_meaningful_unassigned',0) for r in rows),'meaningful_unassigned_after':sum(r.get('final_meaningful_unassigned',0) for r in rows),'human_review_disagreements':sum(r.get('disagreements_for_human_review',0) for r in rows),'new_provider_calls':0},indent=2))


if __name__=='__main__':main()
