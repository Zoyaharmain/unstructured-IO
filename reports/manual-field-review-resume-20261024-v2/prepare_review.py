"""Prepare a durable, unscored review session; never infer approval from predictions."""
import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'reports/manual-field-review-20261024-v1'
V1=ROOT/'ground_truth/field_level/v1'
V2=ROOT/'ground_truth/field_level/v2'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def validate_prior_evidence(reference,elements):
    for field in reference['verified_fields']:
        for q in field['source_evidence']:
            i,start,end=(q[k] for k in ('source_element_index','start','end'))
            if elements[i]['text'][start:end]!=q['quote']:
                raise ValueError('Prior expected text does not match frozen extraction')


def classify_saved_decisions(rows):
    return [{'row_number':i+1,'status':row.get('review_status'),'scorable':False}
            for i,row in enumerate(rows) if row.get('review_status') not in {None,'','pending'}]


def first_group(rows_by_doc):
    requested=[('aditya-vashisth','full_name'),('aditya-vashisth','email'),('aditya-vashisth','phone'),
               ('manjunath-murugan','email'),('manjunath-murugan','phone'),('manjunath-murugan','linkedin_url')]
    return [next(r for r in rows_by_doc[doc] if r.get('parent_section')=='personal_information' and r.get('attribute')==field and r['kind']=='field') for doc,field in requested]


def make_groups(rows_by_doc):
    groups=[];assigned=set()
    def add(rows):
        for start in range(0,len(rows),6):
            batch=rows[start:start+6];gid=f'group-{len(groups)+1:02d}'
            for row in batch:row['review_group']=gid;assigned.add(row['row_id'])
            groups.append({'group_id':gid,'rows':[r['row_id'] for r in batch],
                'context':'Contact introduction' if len(groups)==0 else 'One document/parent/record at a time'})
    add(first_group(rows_by_doc))
    parents=['personal_information','experience','education']
    parents+=list(dict.fromkeys(r.get('parent_section') for rows in rows_by_doc.values() for r in rows if r.get('parent_section') not in parents))
    for parent in parents:
        for rows in rows_by_doc.values():
            records=list(dict.fromkeys(r.get('predicted_record_id') for r in rows if r['kind']=='field' and r.get('parent_section')==parent))
            for record in records:
                add([r for r in rows if r['kind']=='field' and r.get('parent_section')==parent and r.get('predicted_record_id')==record and r['row_id'] not in assigned])
    for rows in rows_by_doc.values():
        add([r for r in rows if r['row_id'] not in assigned])
    return groups


def write_csv(path,rows):
    fields=['row_id','review_group','kind','predicted_parent','predicted_record','attribute','predicted_values',
        'source_text','decision','expected_values','expected_parent','expected_record_association','evidence','reviewer','notes']
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in rows:
            writer.writerow({'row_id':row['row_id'],'review_group':row['review_group'],'kind':row['kind'],
                'predicted_parent':row.get('parent_section',''),'predicted_record':row.get('predicted_record_id',''),
                'attribute':row.get('attribute',''),'predicted_values':json.dumps(row.get('predicted_values'),ensure_ascii=False),
                'source_text':json.dumps(row.get('source_text'),ensure_ascii=False),
                'decision':'','expected_values':'','expected_parent':'','expected_record_association':'','evidence':'','reviewer':'','notes':''})


def main():
    if V2.exists() or (OUT/'summary.json').exists():
        raise ValueError('Refuse to overwrite existing references or review sessions')
    protected=[]
    for folder in [ROOT/'reports',ROOT/'ground_truth',ROOT/'tests/fixtures',ROOT/'local_api']:
        protected.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and OUT not in p.parents)
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    save(OUT/'preservation-before.json',before)
    refs={p.stem:json.loads(p.read_text()) for p in V1.glob('*.json')}
    rows_by_doc={};audits=[];prior_checks=[]
    V2.mkdir(parents=True)
    for doc,ref in sorted(refs.items()):
        raw_path=OLD/doc/'comparison-worksheet.json';csv_path=raw_path.with_suffix('.csv')
        raw=json.loads(raw_path.read_text());rows=raw['rows'];csv_rows=list(csv.DictReader(csv_path.open()))
        assert not classify_saved_decisions(rows)
        assert all(not any(r[k].strip() for k in ['decision','expected_values','expected_parent','expected_record_association','evidence','notes']) for r in csv_rows)
        assert all(r.get('expected_values') is None and not r.get('reviewer_source_evidence') for r in rows)
        frozen=ROOT/f"reports/hierarchical-deepseek-five-20261023-225341/results/{ref['selection_index']:02d}/extraction.json"
        extraction=json.loads(frozen.read_text());validate_prior_evidence(ref,extraction['elements'])
        latest=ROOT/ref['latest_prediction_path'];prediction=json.loads(latest.read_text())
        previous_prediction=json.loads((OLD/doc/'prediction.json').read_text())
        assert all(prediction[k]==previous_prediction[k] for k in ('data','section_schemas'))
        audits.append({'document':doc,'json_rows':len(rows),'json_pending':sum(r['review_status']=='pending' for r in rows),
            'csv_rows':len(csv_rows),'csv_nonempty_decisions':sum(bool(r['decision'].strip()) for r in csv_rows),
            'accepted_new_decisions':0,'worksheet_json_sha256':sha(raw_path),'worksheet_csv_sha256':sha(csv_path),
            'latest_prediction_path':str(latest.relative_to(ROOT)),'latest_prediction_sha256':sha(latest),
            'frozen_extraction_sha256':sha(frozen),'original_pdf_available':Path(ref['source_path']).is_file()})
        new_ref=deepcopy(ref);new_ref.update(reference_version='v2',derived_from={'path':str((V1/(doc+'.json')).relative_to(ROOT)),'sha256':sha(V1/(doc+'.json'))},
            review_session={'status':'pending_explicit_field_decisions','new_approved_fields':0,'full_document_manual_signoff':False,
                'working_worksheet':str((OUT/doc/'comparison-worksheet.json').relative_to(ROOT))})
        assert new_ref['verified_fields']==ref['verified_fields'] and new_ref['provenance']==ref['provenance']
        save(V2/(doc+'.json'),new_ref)
        prior_checks.append({'document':doc,'retained_expected_fields':len(ref['verified_fields']),'unchanged_prior_provenance':True,'prior_quotes_match_frozen_source':True})
        directory=OUT/doc;directory.mkdir()
        copied=deepcopy(rows)
        prefix='A' if doc=='aditya-vashisth' else 'M'
        for i,row in enumerate(copied):
            row.update(row_id=f'{prefix}{i+1:03d}',review_group=None,reviewer='',reviewed_at=None)
        rows_by_doc[doc]=copied
    group1=first_group(rows_by_doc)
    groups=make_groups(rows_by_doc)
    for doc,rows in rows_by_doc.items():
        save(OUT/doc/'comparison-worksheet.json',{'document_key':doc,'instructions':
            'Editable working copy. Pending is unreviewed. Save explicit expected values, parent, record association and reviewer evidence; predictions/source suggestions are not approvals.', 'rows':rows})
        write_csv(OUT/doc/'comparison-worksheet.csv',rows)
    save(OUT/'group-01.json',{'review_group':'group-01','rows':[deepcopy(r) for r in group1]})
    save(OUT/'review-plan.json',groups)
    save(OUT/'decision-audit.json',audits);save(OUT/'prior-expectations-preservation.json',prior_checks)
    changed=[p for p,h in before.items() if sha(ROOT/p)!=h]
    assert not changed
    save(OUT/'summary.json',{'worksheet_rows':sum(len(r) for r in rows_by_doc.values()),'pending_rows':230,
        'new_verified_decisions':0,'retained_prior_manjunath_expectations':6,'aditya_verified_fields':0,
        'new_accuracy_evaluation_run':False,'api_calls':0,'mapping_runs':0,'pdf_extraction_runs':0,
        'existing_files_checked':len(before),'existing_files_changed':changed,'source_pdf_accessibility':'Original paths unavailable; frozen extracted source used for evidence validation.'})
    (V2/'README.md').write_text('# Field references v2 — review pending\n\nNo new reviewer decisions have been saved. Aditya has zero verified fields. Manjunath retains exactly the six v1 prior user-supplied expectations, with unchanged per-field provenance; these are not new manual PDF-review approvals. Predictions were not copied into expected labels. All 230 worksheet rows remain unreviewed. No new accuracy score was generated. Original PDF paths are unavailable here; prior quotes were checked against the frozen extraction only.\n\nThe editable review session is in `reports/manual-field-review-resume-20261024-v2`. Preserve these references until explicit field decisions are supplied.\n')
    print(json.dumps(audits,indent=2))

if __name__=='__main__':main()
