"""Offline before/after disagreement, relationship and PDF-text diagnostic audit."""
import csv
import json
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.evaluate_resume_ground_truth import label_map,prediction_spans,CATEGORIES,extraction_hash,score
from scripts.human_review_validation import validate_annotation,sha


def words(text):return Counter(re.findall(r'\w+',text.casefold()))


def main():
    selected=json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text())
    gold={r['file']:r for r in map(json.loads,(ROOT/'ground_truth/gold/gold_resumes.jsonl').read_text().splitlines())}
    output=ROOT/'ground_truth/human_review/audit';output.mkdir(parents=True,exist_ok=True)
    drift=[];rows=[];relationships={};totals=Counter();old_scores=[];new_scores=[]
    for item in selected:
        file=item['file'];identifier=Path(item['artifact']).stem
        local=json.loads((ROOT/'.upstream/batch-validation'/item['artifact']).read_text())
        old_art=json.loads((ROOT/'ground_truth/reviewed/documents'/(identifier+'.json')).read_text())
        new_art=json.loads((ROOT/'ground_truth/recovery_pilot/live/documents'/(identifier+'.json')).read_text())
        elements=local['extraction']['elements'];old=old_art['reviewed_sections'];new=new_art['reviewed_sections']
        # Independently bind both predictions to the same extracted inventory.
        old_labels=label_map(elements,prediction_spans(old,elements),CATEGORIES|{'needs_review'})
        new_labels=label_map(elements,prediction_spans(new,elements),CATEGORIES|{'needs_review'})
        if gold[file]['extraction_sha256']!=extraction_hash(elements):raise ValueError('Reference extraction mismatch')
        reference=label_map(elements,gold[file]['spans'],CATEGORIES|{'ignore'})
        counts=Counter()
        for i,(element,before,after,truth) in enumerate(zip(elements,old_labels,new_labels,reference)):
            start=0
            while start<len(element['text']):
                end=start+1;signature=(before[start],after[start],truth[start])
                while end<len(element['text']) and (before[end],after[end],truth[end])==signature:end+=1
                a,b,t=signature;text=element['text'][start:end]
                if a!=b and text.strip():
                    chars=sum(not c.isspace() for c in text)
                    outcome='reference_ignored' if t=='ignore' else 'old_correct_new_wrong' if a==t else 'old_wrong_new_correct' if b==t else 'both_disagree_with_reference'
                    counts[outcome]+=chars;totals[outcome]+=chars
                    drift.append({'file':file,'source_element_index':i,'start':start,'end':end,'page':element.get('page_number'),
                        'old_category':a,'new_category':b,'reference_category':t,'outcome':outcome,'nonspace_characters':chars,'text':text})
                start=end
        old_metric=score(elements,gold[file],old);new_metric=score(elements,gold[file],new)
        old_scores.append(old_metric);new_scores.append(new_metric)
        pdf=ROOT/'ground_truth/pilot_resumes'/file
        completed=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,check=True)
        independent=completed.stdout.decode('utf-8','replace')
        (output/(identifier+'-pdftotext.txt')).write_text(independent)
        extracted='\n'.join(e['text'] for e in elements)
        missing=words(independent)-words(extracted)
        stem=Path(file).stem.replace(' ','_').replace('(','').replace(')','')
        draft=json.loads((ROOT/'ground_truth/recovery_pilot/live-review/drafts'/(stem+'.json')).read_text())
        issues=validate_annotation(draft,elements)
        relationships[file]=issues
        rows.append({'file':file,'old_reference_agreement':old_metric['character_accuracy'],
            'new_reference_agreement':new_metric['character_accuracy'],'changed_nonspace_chars':sum(counts.values()),
            **counts,'relationship_integrity_issues':len(issues),'independent_pdf_tokens':sum(words(independent).values()),
            'tokens_not_matched_in_extraction':sum(missing.values()),'parser_difference_requires_pdf_review':bool(missing),
            'missing_token_sample':'; '.join(f'{k} ({v})' for k,v in missing.most_common(15)),
            'draft_sha256':sha(ROOT/'ground_truth/recovery_pilot/live-review/drafts'/(stem+'.json')),'pdf_sha256':sha(pdf)})
    (output/'section-drift.json').write_text(json.dumps(drift,indent=2,ensure_ascii=False)+'\n')
    (output/'relationship-issues.json').write_text(json.dumps(relationships,indent=2,ensure_ascii=False)+'\n')
    with (output/'per-resume.csv').open('w',newline='') as stream:
        fields=sorted({key for row in rows for key in row});writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    total=sum(s['scored_characters'] for s in new_scores)
    summary={'resumes':len(rows),'scored_nonspace_characters':total,'old_correct':sum(s['correct_characters'] for s in old_scores),
        'new_correct':sum(s['correct_characters'] for s in new_scores),'changes':dict(totals),
        'old_exact_resumes':sum(s['entire_resume_correct'] for s in old_scores),'new_exact_resumes':sum(s['entire_resume_correct'] for s in new_scores),
        'relationship_checks_passed':sum(not issues for issues in relationships.values()),
        'relationship_checks_blocked':sum(bool(issues) for issues in relationships.values()),
        'pdf_parser_disagreements':sum(r['parser_difference_requires_pdf_review'] for r in rows),
        'original_pdf_accuracy_established':False,'reference_labels_independently_verified':False,'new_llm_calls':0}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
