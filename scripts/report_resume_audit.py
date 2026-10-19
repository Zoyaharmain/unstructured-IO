"""Produce a private searchable HTML/CSV review queue and an aggregate Markdown report."""
import argparse
from collections import Counter
import csv
import html
import json
from pathlib import Path
import statistics


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--report',type=Path,default=Path('reports/resume-corpus-audit.md'))
    args=parser.parse_args();root=args.output
    summary=json.loads((root/'summary.json').read_text())
    rows=json.loads((root/'current-results.json').read_text())
    categories=json.loads((Path(__file__).resolve().parents[1]/'local_api/data/section_anchors.json').read_text())
    section_rows=[]
    detected_counts=Counter()
    columns=['file','extension','status','block_detection_status','section_count','detected_sections','assigned_source_spans','flags','review_characters','review_units','assigned_text_percent','words','reference_parser_token_recall','seconds','error_type','artifact']
    table=[]
    review_reasons=Counter()
    (root/'views').mkdir(exist_ok=True)
    for row in rows:
        row.update(block_detection_status='not_evaluated',section_count=0,detected_sections='',assigned_source_spans=0)
        link=html.escape(row.get('artifact',''),quote=True)
        if row.get('artifact'):
            artifact=json.loads((root/row['artifact']).read_text())
            result=artifact['sections']
            detected={section['category'] for section in result['sections']}
            detected_counts.update(detected)
            row.update(section_count=len(detected),
                       detected_sections='; '.join(section['label'] for section in result['sections']),
                       assigned_source_spans=sum(len(section['blocks']) for section in result['sections']),
                       block_detection_status=('detected_with_unassigned_text' if result['needs_review'] else 'detected_no_unassigned_text') if detected else 'no_sections_detected')
            for category in categories:
                row[category+'_detected']='yes' if category in detected else 'not_detected'
            for section in result['sections']:
                section_rows.append({'file':row['file'],'section':section['label'],
                    'source_heading':section.get('source_heading') or '',
                    'source_spans':len(section['blocks']),'words':len(section['text'].split()),
                    'entries':len(section.get('entries',[])),
                    'pages':'; '.join(str(n) for n in sorted({b['page_number'] for b in section['blocks'] if b.get('page_number') is not None})),
                    'correctness':'unverified','text_preview':section['text'][:200]})
            row['review_characters']=sum(len(b['text'].strip()) for b in result['needs_review'])
            review_reasons.update(b['reason'] for b in result['needs_review'])
            sections=''.join('<h2>'+html.escape(section['label'])+' — detected</h2><p>'+str(len(section['blocks']))+' source spans · '+str(len(section['text'].split()))+' words · correctness unverified</p><p>Original heading: '+html.escape(section.get('source_heading') or 'No explicit heading recovered')+'</p><pre>'+html.escape(section['text'])+'</pre>' for section in result['sections'])
            unknown=''.join('<pre>'+html.escape(block['text'])+'</pre>' for block in result['needs_review'])
            title=html.escape(row['file'])
            view='<!doctype html><html lang="en"><meta charset="utf-8"><title>'+title+'</title><style>body{font:15px system-ui;margin:24px;color:#183044}main{display:grid;grid-template-columns:1fr 1fr;gap:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f8;padding:16px}h2{margin-top:28px}.unknown pre{background:#fff3df}@media(max-width:800px){main{display:block}}</style><a href="../index.html">← Audit table</a><h1>'+title+'</h1><p>Detected sections: '+html.escape(row['detected_sections'])+'. Local provisional assignments; no DeepSeek validation. Compare against the original document to judge accuracy.</p><main><section><h2>Extracted source text</h2><pre>'+html.escape(artifact['extraction']['text'])+'</pre></section><section>'+sections+'<div class="unknown"><h2>Needs review</h2>'+(unknown or '<p>None. This does not establish semantic accuracy.</p>')+'</div></section></main></html>'
            view_path=Path('views')/(Path(row['artifact']).stem+'.html')
            (root/view_path).write_text(view)
            link=html.escape(str(view_path),quote=True)
        cells=[html.escape(str(row.get(c,''))) for c in columns[:-1]]
        table.append('<tr>'+''.join('<td>'+c+'</td>' for c in cells)+(f'<td><a href="{link}">Compare source and section blocks</a></td>' if link else '<td></td>')+'</tr>')
    with (root/'review-queue.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore');writer.writeheader()
        for row in sorted(rows,key=lambda r:(r['status']=='processed',not bool(r['flags']),r.get('assigned_text_percent',0),-(r.get('review_characters') or 0))):
            writer.writerow({**row,'flags':'; '.join(row['flags'])})
    matrix_columns=['file','block_detection_status','section_count','assigned_source_spans','review_units']+[key+'_detected' for key in categories]+['correctness']
    with (root/'block-detection.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=matrix_columns,extrasaction='ignore');writer.writeheader()
        for row in rows:
            writer.writerow({**{key+'_detected':'not_evaluated' for key in categories},**row,'correctness':'unverified'})
    with (root/'section-blocks.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['file','section','source_heading','source_spans','words','entries','pages','correctness','text_preview']);writer.writeheader();writer.writerows(section_rows)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Offline resume audit</title>
<style>body{font:15px system-ui;margin:24px;color:#183044}input{padding:10px;width:70%;margin:12px 0}table{border-collapse:collapse;width:100%}th,td{padding:8px;border:1px solid #ddd;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#edf3f6}td:first-child{overflow-wrap:anywhere;max-width:280px}.scroll{overflow:auto}</style>
<h1>Resume block detection audit</h1><p>Each row shows detected canonical sections and assigned source spans. A section marked not detected may be absent from the original resume; it is not automatically a missed section.</p><p><a href="block-detection.csv">Download block detection matrix</a> · <a href="section-blocks.csv">Download per-section details</a></p><p>Local extraction → BERT/K-means → local recovery. No API or DeepSeek calls.</p>
<p>Processing success and full assignment do not establish semantic accuracy. Flags are a human review queue.</p>
<input id="search" aria-label="Search files, flags or statuses" placeholder="Search filename, unassigned_text, error, parser_token_disagreement…"><p id="count"></p><div class="scroll"><table><thead><tr>'''
    page+=''.join('<th>'+html.escape(c)+'</th>' for c in columns)+'</tr></thead><tbody>'+''.join(table)+'''</tbody></table></div>
<script>const rows=[...document.querySelectorAll('tbody tr')];const input=document.querySelector('input');function filter(){let n=0;for(const row of rows){row.hidden=!row.textContent.toLowerCase().includes(input.value.toLowerCase());if(!row.hidden)n++}document.querySelector('#count').textContent=n+' / '+rows.length+' documents'}input.addEventListener('input',filter);filter();</script></html>'''
    (root/'index.html').write_text(page)
    by_format={}
    for ext in sorted({r['extension'] for r in rows}):
        subset=[r for r in rows if r['extension']==ext]
        by_format[ext]={'total':len(subset),'statuses':dict(Counter(r['status'] for r in subset)),
                        'with_unassigned':sum(bool(r.get('review_units')) for r in subset)}
    assigned=[r['assigned_text_percent'] for r in rows if r.get('assigned_text_percent') is not None]
    aggregate={**summary,'by_format':by_format,'median_assigned_text_percent':statistics.median(assigned) if assigned else None,
               'documents_below_95pct_local_assignment':sum(value<95 for value in assigned),
               'unique_document_hashes':len({r['sha256'] for r in rows if r.get('sha256')}),
               'extraction_strategies':dict(Counter(r['strategy'] for r in rows if r.get('strategy'))),
               'review_reasons':dict(review_reasons),'detected_sections':dict(detected_counts),
               'block_detection_statuses':dict(Counter(r['block_detection_status'] for r in rows))}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.with_suffix('.json').write_text(json.dumps(aggregate,indent=2)+'\n')
    lines=['# Offline resume corpus audit','',f"Completed **{len(rows)} / {summary['files_discovered']}** resumes. API calls: **0**.",'',
           'The run invokes production extraction, Sentence-BERT/K-means grouping and local boundary recovery directly. DeepSeek is disabled; the batch container has no network. Input files are read-only.',
           '', '| Format | Files | Processed | Errors/timeouts/empty | With unassigned text |','|---|---:|---:|---:|---:|']
    for ext,s in by_format.items():
        good=s['statuses'].get('processed',0)
        lines.append(f"| {ext} | {s['total']} | {good} | {s['total']-good} | {s['with_unassigned']} |")
    lines+=['','## Results','',f"- Status counts: `{json.dumps(summary['statuses'],sort_keys=True)}`.",
            f"- Source/reference invariant failures: **{summary['invariant_failure_documents']}**.",
            f"- All spans assigned locally: **{summary['all_assigned_documents']}** documents.",
            f"- Documents with unassigned text: **{summary['documents_with_unassigned_text']}**.",
            f"- Median locally assigned text: **{aggregate['median_assigned_text_percent']}%** (coverage, not accuracy).",
            f"- Documents below 95% local assignment coverage: **{aggregate['documents_below_95pct_local_assignment']}**.",
            f"- Triage flags (may overlap): `{json.dumps(summary['flags'],sort_keys=True)}`.",'',
            '## What was checked','',
            'Exact source-span coverage and text reconstruction; canonical section uniqueness and reconstruction; highlight offset validity; entry references; empty extraction; unresolved spans; unusually sparse output; and token overlap with a separate PDF parser. Parser disagreement is a diagnostic, not a missing-word accuracy score.',
            '', '## Limits and review queue','',
            'This corpus has no manually labeled ground-truth sections or original transcriptions. Semantic section accuracy, precision/recall and word accuracy were **not measured**. A processed document can contain incorrect assignments, even if every span was assigned. The DeepSeek validation/recovery layer was intentionally not tested. Unsupported/corrupt/encrypted documents are reported rather than silently counted as passes.',
            '', 'Private filenames, extracted text and section results are kept in the ignored audit directory. Open `index.html` for a searchable per-file table, `review-queue.csv` for triage, and `documents/*.json` for exact extraction and assigned/unassigned spans. No private resume text is copied into this aggregate report.',
            '', '## Reproduce','', 'See `docs/BATCH_RESUME_AUDIT.md`. Rerunning the same command resumes unchanged inputs; changed production code or file metadata invalidates the cached result.', '']
    retained=sum(bool(r.get('retained_from_prior_revision')) for r in rows)
    if retained:
        lines += ['## Incremental repair verification', '',
                  f'{retained} successful corpus results were retained from an earlier code revision using --retry-failed. Failed files were rerun. This is not a fresh full-corpus run of the later revision; use a new output directory to test changed behavior across every file.', '']
    preflight=root/'input-preflight.json'
    if preflight.exists():
        inspection=json.loads(preflight.read_text())
        counts=dict(Counter(item['kind'] for item in inspection['issues']))
        lines += ['## Input preflight', '',
                  f"Independent package inspection covered {inspection['files']} files; issues: `{json.dumps(counts,sort_keys=True)}`.", '']
    lines+=['## Detected resume blocks', '', '| Section | Documents with a detected block |','|---|---:|']
    for key,value in categories.items():lines.append(f"| {value['label']} | {detected_counts[key]} |")
    lines+=['', 'A detected block means the local pipeline assigned text to that category. It does not verify correct ownership or completeness. A category not detected may simply be absent from the original resume. Canonical sections and their source spans are counted separately.', '',
            'Open `block-detection.csv` for a yes/not_detected/not_evaluated matrix per resume, `section-blocks.csv` for heading, source-span, word, entry and page details per detected section, and the HTML table for normal block-by-block text.', '']
    if summary.get('stopped_by_user'):
        lines.insert(2,f"**Partial audit stopped by request: {summary.get('files_untested',summary['files_discovered']-len(rows))} files have no completed batch result. No model tests were resumed to generate this report.**")
        page_path=root/'index.html'
        page_path.write_text(page_path.read_text().replace('<h1>Resume block detection audit</h1>', '<h1>Partial resume block detection audit</h1><p>Stopped by request: '+str(len(rows))+' batch results; '+str(summary.get('files_untested',0))+' not completed.</p>',1))
    args.report.write_text('\n'.join(lines));print(json.dumps(aggregate,indent=2))


if __name__=='__main__':main()
