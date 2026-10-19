"""Compare human-verified source-span labels to local and final LLM section output.

Never uses an LLM output as ground truth. Labels are bound to the exact extracted
source using SHA256. Scores refer to extracted-text section ownership, not OCR.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=set(json.loads((ROOT/'local_api/data/section_anchors.json').read_text()))


def extraction_hash(elements):
    return hashlib.sha256(json.dumps([e['text'] for e in elements],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def label_map(elements,spans,allowed):
    labels=[[None]*len(e['text']) for e in elements]
    for span in spans:
        index,start,end,category=(span[k] for k in ('source_element_index','start','end','category'))
        if type(index)!=int or not 0<=index<len(elements) or type(start)!=int or type(end)!=int or not 0<=start<=end<=len(labels[index]) or category not in allowed:
            raise ValueError('Invalid source interval/category')
        for offset in range(start,end):
            if labels[index][offset] is not None:raise ValueError('Overlapping labels')
            labels[index][offset]=category
    if any(any(label is None for label in row) for row in labels):raise ValueError('Incomplete source coverage')
    return labels


def prediction_spans(result,elements):
    spans=[]
    for section in result['sections']:
        for b in section['blocks']:
            spans.append({**b,'category':section['category']})
    spans.extend({**b,'category':'needs_review'} for b in result['needs_review'])
    for b in spans:
        index=b['source_element_index']
        if type(index)!=int or not 0<=index<len(elements):raise ValueError('Invalid prediction source index')
        if b['text']!=elements[index]['text'][b['start']:b['end']]:raise ValueError('Prediction changed source text')
    return spans


def score(elements,truth,prediction):
    if truth.get('human_verified') is not True:raise ValueError('Ground truth is not human verified')
    if truth.get('extraction_sha256')!=extraction_hash(elements):raise ValueError('Ground truth source hash mismatch')
    expected=label_map(elements,truth['spans'],CATEGORIES|{'ignore'})
    actual=label_map(elements,prediction_spans(prediction,elements),CATEGORIES|{'needs_review'})
    confusion=Counter();correct=total=unassigned=0
    for element,wanted,got in zip(elements,expected,actual):
        for char,a,b in zip(element['text'],wanted,got):
            if char.isspace() or a=='ignore':continue
            total+=1;correct+=a==b;unassigned+=b=='needs_review';confusion[(a,b)]+=1
    if not total:raise ValueError('No scorable human labels')
    expected_categories={a for (a,b),n in confusion.items() if n}
    predicted_categories={b for (a,b),n in confusion.items() if n and b!='needs_review'}
    exact_sections=sum(all(a==b for (a,b),n in confusion.items() if n and (a==category or b==category)) for category in expected_categories)
    return {'scored_characters':total,'correct_characters':correct,'character_accuracy':correct/total,
            'unassigned_characters':unassigned,'entire_resume_correct':correct==total,
            'expected_sections':len(expected_categories),'entirely_correct_sections':exact_sections,
            'missing_sections':sorted(expected_categories-predicted_categories),
            'extra_sections':sorted(predicted_categories-expected_categories),
            'confusion':[{'expected':a,'predicted':b,'characters':n} for (a,b),n in sorted(confusion.items())]}


def summarize_scores(scores):
    if not scores:return {'evaluated_documents':0,'accuracy':None,'entirely_correct_resumes':None,'precision_recall_f1':None}
    confusion=Counter()
    for result in scores:
        confusion.update({(r['expected'],r['predicted']):r['characters'] for r in result['confusion']})
    per_category={}
    for category in sorted(CATEGORIES):
        tp=confusion[category,category]
        fp=sum(n for (a,b),n in confusion.items() if b==category and a!=category)
        fn=sum(n for (a,b),n in confusion.items() if a==category and b!=category)
        if not tp+fp+fn:continue
        precision=tp/(tp+fp) if tp+fp else 0
        recall=tp/(tp+fn) if tp+fn else 0
        per_category[category]={'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0}
    return {'evaluated_documents':len(scores),'scored_characters':sum(r['scored_characters'] for r in scores),
            'accuracy':sum(r['correct_characters'] for r in scores)/sum(r['scored_characters'] for r in scores),
            'entirely_correct_resumes':sum(r['entire_resume_correct'] for r in scores),
            'not_entirely_correct_resumes':sum(not r['entire_resume_correct'] for r in scores),
            'entirely_correct_sections':sum(r['entirely_correct_sections'] for r in scores),
            'expected_sections':sum(r['expected_sections'] for r in scores),
            'precision_recall_f1':per_category}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--reviewed',type=Path)
    parser.add_argument('--truth',type=Path)
    parser.add_argument('--template',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    inventory=json.loads((args.source/'current-results.json').read_text())
    truth={};templates=[];rows=[];before=[];after=[];paired=[]
    if args.truth:
        for line in args.truth.read_text().splitlines():
            if not line.strip():continue
            item=json.loads(line)
            if item['file'] in truth:raise ValueError('Duplicate ground-truth filename')
            truth[item['file']]=item
    for row in inventory:
        entry={'file':row['file'],'local_evaluation':'not_evaluated','llm_evaluation':'not_evaluated'}
        if not row.get('artifact'):
            entry['local_evaluation']='no_extraction';rows.append(entry);continue
        artifact=json.loads((args.source/row['artifact']).read_text());elements=artifact['extraction']['elements']
        identifier=Path(row['artifact']).stem
        templates.append({'file':row['file'],'extraction_sha256':extraction_hash(elements),'human_verified':False,'spans':[],
                          'source_artifact':row['artifact'],'instructions':'Label every source character with a canonical category or ignore. Review against the original resume. Do not copy model assignments as ground truth.'})
        if row['file'] not in truth:
            entry['local_evaluation']='missing_ground_truth';rows.append(entry);continue
        try:
            local=score(elements,truth[row['file']],artifact['sections']);before.append(local)
            entry.update(local_evaluation='scored',local_entirely_correct=local['entire_resume_correct'],local_accuracy=local['character_accuracy'])
            candidate=args.reviewed/'documents'/(identifier+'.json') if args.reviewed else None
            if candidate and candidate.exists():
                final=json.loads(candidate.read_text())
                if final['reviewed_sections'].get('metadata',{}).get('llm_review',{}).get('status')!='complete':
                    entry['llm_evaluation']='provider_review_not_complete'
                else:
                    reviewed=score(elements,truth[row['file']],final['reviewed_sections']);after.append(reviewed);paired.append((local,reviewed))
                    entry.update(llm_evaluation='scored',llm_entirely_correct=reviewed['entire_resume_correct'],llm_accuracy=reviewed['character_accuracy'])
            else:entry['llm_evaluation']='no_live_llm_result'
        except (ValueError,KeyError,TypeError) as exc:entry['evaluation_error']=str(exc)
        rows.append(entry)
    if args.template:
        args.template.parent.mkdir(parents=True,exist_ok=True)
        args.template.write_text(''.join(json.dumps(item,ensure_ascii=False)+'\n' for item in templates))
    summary={'scope_documents':len(inventory),'ground_truth_documents_supplied':len(truth),
             'local':summarize_scores(before),'after_llm':summarize_scores(after),
             'paired_documents':len(paired),
             'improved_documents':sum(b['character_accuracy']>a['character_accuracy'] for a,b in paired),
             'regressed_documents':sum(b['character_accuracy']<a['character_accuracy'] for a,b in paired),
             'status_counts':dict(Counter(r['local_evaluation'] for r in rows)),
             'measurement':'Non-whitespace source-character section ownership, excluding human ignore labels; not OCR accuracy',
             'live_llm_calls_by_evaluator':0}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (args.output/'per-resume.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
