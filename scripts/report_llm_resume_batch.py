"""Offline comparison of an approved LLM batch with its local baseline."""
import argparse
from collections import Counter
import json
from pathlib import Path


def employer_matches(expected, records):
    def norm(text): return ''.join(c for c in text.casefold() if c.isalnum())
    options=[[j for j,r in enumerate(records) if norm(name) in norm(r.get('company',''))] for name in expected]
    matched={}
    def assign(i, seen):
        for j in options[i]:
            if j in seen: continue
            seen.add(j)
            if j not in matched or assign(matched[j], seen):
                matched[j]=i
                return True
        return False
    for i in range(len(expected)): assign(i,set())
    return len(matched)


def summarize(source, output):
    baseline=json.loads((source/'results.json').read_text())
    rows=[]
    spot_path=output/'source-employer-checks.json'
    spots=json.loads(spot_path.read_text())['expected'] if spot_path.exists() else {}
    def norm(value): return ''.join(c for c in value.casefold() if c.isalnum())
    for i,local in enumerate(baseline,1):
        directory=output/f'resume-{i:02d}'
        row={'file':local['file'],'checks':'not_completed','local_unresolved':local.get('unresolved_attributes'),
             'section_review':'not_completed','field_review':'not_completed','provider_calls':0}
        calls=directory/'provider-calls.json'
        if calls.exists():row['provider_calls']=len(json.loads(calls.read_text()))
        if (directory/'schema.json').exists():
            schema=json.loads((directory/'schema.json').read_text())
            sections=json.loads((directory/'sections.json').read_text())
            extraction=json.loads((directory/'extraction.json').read_text())
            import sys
            sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
            from local_api.schemas.mapping import SchemaMappingRequest
            from local_api.schemas.subschemas import SectionSchema
            from local_api.schemas.sections import SectionResponse
            from local_api.services.source_validation import validate_result
            from local_api.services.subschema_validation import validate_hierarchy
            try:
                req=SchemaMappingRequest(elements=extraction['elements'],sections=sections)
                revised=SectionResponse.model_validate(schema['meta'].get('reviewed_sections',sections))
                errors=validate_result(req.elements,revised)
                if errors:raise ValueError('source_coverage')
                validate_hierarchy([SectionSchema.model_validate(s) for s in schema['section_schemas']],revised)
                row['checks']='pass'
            except Exception as exc:row.update(checks='fail',exception_type=type(exc).__name__)
            old=json.loads((source/local['schema_artifact']).read_text())
            old_extraction=json.loads((source/local['artifact']).read_text())['extraction']
            row['identical_extracted_inventory']=([e['text'] for e in old_extraction['elements']]==[e['text'] for e in extraction['elements']])
            meta=schema['meta'];field=meta.get('field_review',{})
            if local['file'] in spots:
                expected=spots[local['file']]
                row['employer_spot_check']={'expected':len(expected),'local_recovered':employer_matches(expected,old['data'].get('experience',[])),
                    'llm_recovered':employer_matches(expected,schema['data'].get('experience',[])),
                    'source_available':sum(norm(name) in norm(' '.join(e['text'] for e in extraction['elements'])) for name in expected),
                    'missing_from_extraction':[name for name in expected if norm(name) not in norm(' '.join(e['text'] for e in extraction['elements']))]}
            row.update(section_review=sections.get('metadata',{}).get('llm_review',{}).get('status','unavailable'),
                       field_review=field.get('status','unavailable'),
                       mapping_result=meta.get('mapping_result'),field_diagnostics=field,
                       llm_unresolved=sum(not a['items'] for s in schema['section_schemas'] for r in s['records'] for a in r['attributes']),
                       missing_required_fields=meta.get('missing_required_fields',[]),
                       changed_categories=[k for k,v in schema['data'].items() if old['data'].get(k)!=v],
                       record_counts={key:{'local':len(old['data'].get(key,[])),'llm':len(schema['data'].get(key,[]))}
                                      for key in ['experience','education','projects','certifications']},
                       accuracy='not_ground_truth_evaluated')
            if (directory/'schema-audit.json').exists():
                audit=json.loads((directory/'schema-audit.json').read_text())
                row.update(audit_status=audit.get('status'),audit_reason=audit.get('reason'),audit_findings=len(audit.get('findings',[])))
            if (directory/'pipeline.json').exists():
                pipeline=json.loads((directory/'pipeline.json').read_text())
                row.update(feedback_passes=len(pipeline.get('passes',[])),stop_reason=pipeline.get('stop_reason'))
        rows.append(row)
    hashes=Counter(r.get('sha256') for r in baseline)
    summary={'scope':len(rows),'completed':sum(r['checks']!='not_completed' for r in rows),
             'source_schema_checks':dict(Counter(r['checks'] for r in rows)),
             'section_review_statuses':dict(Counter(r['section_review'] for r in rows)),
             'field_review_statuses':dict(Counter(r['field_review'] for r in rows)),
             'audit_statuses':dict(Counter(r.get('audit_status','not_completed') for r in rows)),
             'audit_failure_reasons':dict(Counter(r['audit_reason'] for r in rows if r.get('audit_reason'))),
             'mapping_statuses':dict(Counter((r.get('mapping_result') or {}).get('status','not_completed') for r in rows)),
             'provider_calls':sum(r['provider_calls'] for r in rows),
             'local_unresolved':sum(r.get('local_unresolved',0) for r in rows),
             'llm_unresolved_completed':sum(r.get('llm_unresolved',0) for r in rows),
             'accuracy_percentage':None,'reason':'No independently reviewed complete ground truth',
             'unique_source_hashes':len(hashes)}
    observed=[r['employer_spot_check'] for r in rows if 'employer_spot_check' in r]
    summary['employer_spot_check']={key:sum(r[key] for r in observed) for key in ['expected','source_available','local_recovered','llm_recovered']}
    (output/'comparison.json').write_text(json.dumps({'summary':summary,'documents':rows},indent=2)+'\n')
    def cell(value):return str(value).replace('|','\\|').replace('\n',' ')
    report=['# Ten-resume LLM comparison','', '```json',json.dumps(summary,indent=2),'```','',
            'Source/schema checks measure coverage, ownership, types and citations; they do not prove semantic correctness. Unresolved attributes include genuinely absent optional values. Fewer unresolved fields is not an accuracy score. Provider calls include section placement, field mapping, audits and bounded feedback retries.','',
            '| Resume | Source/schema | Section review | Field review | Mapping result | Unresolved local → LLM | Calls |','|---|---|---|---|---|---|---|']
    for r in rows:
        report.append('| '+' | '.join(cell(v) for v in [r['file'],r['checks'],r['section_review'],r['field_review'],(r.get('mapping_result') or {}).get('status','pending'),f"{r['local_unresolved']} → {r.get('llm_unresolved','pending')}",r['provider_calls']])+' |')
    report+=['','## Employer source spot-check','',
        'The employer subset was independently inspected in original DOCX XML and PDF text. This is an assistant spot-check, not human-approved comprehensive ground truth. It matches employer cores to distinct company fields, ignoring punctuation/case and tolerating city suffixes; it does not score roles, dates, responsibilities, exact boundaries, invented extra records or other fields.', '',
        '| Resume | Checked employers | In extraction | Local recovered | LLM recovered |', '|---|---|---|---|---|']
    for row in rows:
        if 'employer_spot_check' in row:
            check=row['employer_spot_check']
            report.append('| '+' | '.join(cell(v) for v in [row['file'],check['expected'],check['source_available'],check['local_recovered'],check['llm_recovered']])+' |')
    report+=['','Detailed sanitized statuses, mapping diagnostics, audit findings counts and record counts are in comparison.json. Each resume-NN folder preserves source extraction, review requests/responses, final schema, pass history and advisory findings. No additional API calls are made by this report.']
    (output/'report.md').write_text('\n'.join(report)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();print(json.dumps(summarize(args.source,args.output)))
