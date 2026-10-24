"""Offline revalidation of an already imported decision file. No mapping or API calls."""
import csv
import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
OLD=ROOT/'reports/manual-field-review-group01-import-20261024-v3'
V3=ROOT/'ground_truth/field_level/v3'
V4=ROOT/'ground_truth/field_level/v4'
INPUT=Path('/mnt/c/Users/Gopi Gedar/Downloads/group-01-reviewed-2026-10-24T09-54-57.555Z.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def module():
    spec=importlib.util.spec_from_file_location('prior_import',OLD/'import_group.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def validate_record(d,schema,inventory):
    sections=[s for s in schema['section_schemas'] if s['category']==d['expected_parent_section']]
    records=[r for s in sections for r in s['records'] if r['record_id']==d['expected_record_association']['value']]
    if len(records)!=1:raise ValueError('Parent/record association does not identify one saved record')
    record=records[0]
    attrs=[a for a in record['attributes'] if a['name']==d['attribute']]
    if len(attrs)!=1:raise ValueError('Field is not defined on selected record')
    if [i['value'] for i in attrs[0]['items']]!=d['expected_values']:raise ValueError('Saved mapped values differ from correct decision')
    for q in d['reviewer_source_evidence']:
        if q['source_id'] not in record['source_ids']:raise ValueError('Evidence block does not belong to selected record')
        if q['quote'] not in inventory[q['source_id']]:raise ValueError('Evidence quote does not occur in block')
    return True

def main():
    if V4.exists() or (OUT/'summary.json').exists():raise ValueError('Refuse to overwrite previous reference/report')
    from local_api.schemas.subschema_spec import SUBSCHEMAS
    from local_api.schemas.sections import SectionResponse
    from local_api.schemas.extraction import ExtractedElement
    from local_api.services.source_validation import validate_result
    refs={p.stem:json.loads(p.read_text()) for p in V3.glob('*.json')}
    protected=[INPUT]
    for folder in [ROOT/'ground_truth',OLD,ROOT/'reports/manual-field-review-resume-20261024-v2',ROOT/'local_api',ROOT/'tests/fixtures']:
        protected.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    inventories={};schemas={};bindings={}
    for doc,ref in refs.items():
        ext=ROOT/f"reports/hierarchical-deepseek-five-20261023-225341/results/{ref['selection_index']:02d}/extraction.json"
        pred=ROOT/ref['latest_prediction_path'];sec=pred.with_name('sections.json')
        protected.extend([ext,pred,sec]);raw=json.loads(ext.read_text());parsed=SectionResponse.model_validate_json(sec.read_text())
        errors=validate_result([ExtractedElement.model_validate(e) for e in raw['elements']],parsed)
        if errors:raise ValueError(f'Source interval validation failed: {doc}')
        blocks=[b for s in parsed.sections for b in s.blocks]+parsed.needs_review
        inventories[doc]={f'e{b.source_element_index}:{b.start}:{b.end}':b.text for b in blocks}
        schemas[doc]=json.loads(pred.read_text())
        bindings[doc]={'extraction':str(ext.relative_to(ROOT)),'extraction_sha256':sha(ext),'sections':str(sec.relative_to(ROOT)),'sections_sha256':sha(sec),'prediction':str(pred.relative_to(ROOT)),'prediction_sha256':sha(pred),'source_pdf_sha256_declared':ref['source_sha256'],'original_pdf_available':Path(ref['source_path']).is_file(),'interval_validation':'passed'}
    before={str(p):sha(p) for p in protected};save(OUT/'preservation-before.json',before)
    payload=json.loads(INPUT.read_text())
    group=json.loads((ROOT/'reports/manual-field-review-resume-20261024-v2/group-01.json').read_text())['rows']
    for r in group:r['document_key']='aditya-vashisth' if r['row_id'].startswith('A') else 'manjunath-murugan'
    approved,uncertain,pending=module().validate_payload(payload,group,inventories,SUBSCHEMAS)
    audit=[]
    for d in approved:
        validate_record(d,schemas[d['document_key']],inventories[d['document_key']])
        matches=[f for f in refs[d['document_key']]['verified_fields'] if f.get('decision_row_id')==d['row_id']]
        if len(matches)!=1:raise ValueError('Previously imported row missing or duplicated')
        f=matches[0]
        for a,b in [('expected_values','expected_values'),('expected_parent_section','parent_section'),('expected_record_association','record_selector'),('reviewer_source_evidence','source_evidence'),('reviewer','reviewer'),('reviewed_at','reviewed_at')]:
            if d[a]!=f[b]:raise ValueError(f'Prior reference conflicts with submitted decision: {d["row_id"]}')
        if f['decision_file_sha256']!=sha(INPUT):raise ValueError('Decision file provenance mismatch')
        audit.append(dict(deepcopy(d),validation_status='accepted_already_imported',reason='Explicit decision and exact quote/value/parent/record verified; retained once from v3, not appended again.',checks={'source_interval_integrity':True,'exact_quote_in_cited_block':True,'expected_value_in_quote':True,'defined_parent_and_field':True,'record_exists_under_parent':True,'evidence_owned_by_record':True,'current_saved_prediction_matches_correct_decision':True,'prior_reference_matches':True},original_pdf_rechecked=False))
    (OUT/'received-group-01.json').write_bytes(INPUT.read_bytes())
    save(OUT/'validation-results.json',{'accepted':audit,'rejected':[],'uncertain':uncertain,'explicit_pending_rows':pending,'reviewer_identity':'Self-declared; not independently authenticated','source_bindings':bindings})
    with (OUT/'validation-results.csv').open('w',newline='') as stream:
        cols=['row_id','document_key','reviewer','review_status','expected_values','expected_parent_section','expected_record_association','reviewer_source_evidence','validation_status','reason']
        w=csv.DictWriter(stream,fieldnames=cols,extrasaction='ignore');w.writeheader()
        for row in audit:w.writerow({k:json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k) for k in cols})
    allrows={};pending_count=0
    for doc in refs:
        folder=OUT/doc;folder.mkdir(exist_ok=True)
        worksheet=json.loads((OLD/doc/'comparison-worksheet.json').read_text())
        save(folder/'comparison-worksheet.json',worksheet)
        (folder/'comparison-worksheet.csv').write_bytes((OLD/doc/'comparison-worksheet.csv').read_bytes())
        for row in worksheet['rows']:
            allrows[row['row_id']]=dict(deepcopy(row),document_key=doc,source_pdf_sha256=refs[doc]['source_sha256'])
            if row['review_status']=='pending':
                assert row['expected_values'] is None and row['expected_parent_section'] is None and row['expected_record_association'] is None and not row.get('reviewer_source_evidence',[])
                pending_count+=1
    groupids=['A064','A065','A066','A067','A068','A069']
    rows=[allrows[rid] for rid in groupids]
    for row in rows:
        assert row['review_status']=='pending'
        row['previous_review_group']=row['review_group'];row['review_group']='group-02'
        for source in row['source_text']:assert inventories[row['document_key']][source['source_id']]==source['text']
    save(OUT/'group-02.json',{'review_group':'group-02','review_session':OUT.name,'scope':'employment: Aditya, Persistent Systems, experience-1; six header fields; all pending','supersedes_navigation_only':'Earlier Group 02 personal-information page is preserved; use this employment session for the requested next group.','rows':rows})
    V4.mkdir()
    for doc,ref in refs.items():
        updated=deepcopy(ref);updated['reference_version']='v4'
        updated['derived_from']={'path':str((V3/(doc+'.json')).relative_to(ROOT)),'sha256':sha(V3/(doc+'.json'))}
        updated['revalidation']={'report':str((OUT/'validation-results.json').relative_to(ROOT)),'decision_file_sha256':sha(INPUT),'new_labels_added':0,'same_decisions_already_in_v3':True}
        updated['review_session']['working_worksheet']=str((OUT/doc/'comparison-worksheet.json').relative_to(ROOT))
        updated['review_session']['new_approved_fields']=0
        assert updated['verified_fields']==ref['verified_fields']
        save(V4/(doc+'.json'),updated)
    summary={'reference_version':'v4','reviewer':'Aditya Vashisth','decision_file_sha256':sha(INPUT),'accepted_revalidated':len(audit),'rejected':0,'uncertain':len(uncertain),'new_labels_added':0,'duplicate_labels_added':0,'pending_rows_unreviewed':pending_count,'reference_field_counts':{doc:len(ref['verified_fields']) for doc,ref in refs.items()},'prior_expected_fields_retained_with_original_provenance':6,'group02_rows':groupids,'api_calls':0,'mapping_runs':0,'accuracy_score_generated':False}
    changed=[p for p,h in before.items() if sha(Path(p))!=h]
    assert not changed
    summary.update(protected_files_checked=len(before),protected_files_changed=changed)
    save(OUT/'summary.json',summary);save(OUT/'source-bindings.json',bindings)
    (V4/'README.md').write_text('# Field references v4\n\nRevalidated the six explicit Group 01 decisions by reviewer Aditya Vashisth. The identical file was already incorporated in v3; no duplicate or new labels were appended. Verified field objects and provenance are unchanged from v3: Aditya 3, Manjunath 9 (including six prior expectations with their narrower provenance). The 224 pending worksheet rows remain unreviewed. Exact quotes were checked against saved extracted blocks and record ownership; original PDFs were unavailable, so this is not fresh visual verification or whole-document approval. No accuracy score, API call or production change.\n\nValidation and the new employment Group 02: reports/manual-field-review-employment-20261024-v4.\n')
    table='\n'.join('| '+ ' | '.join([d['row_id'],d['document_key'],d['attribute'],', '.join(d['expected_values']),'; '.join(q['source_id']+': '+q['quote'] for q in d['reviewer_source_evidence'])])+' |' for d in audit)
    (OUT/'report.md').write_text('''# Group 01 revalidation and employment Group 02

Six explicit `correct` decisions accepted; zero rejected; zero uncertain in the submitted file. Reviewer name on every row: **Aditya Vashisth** (self-declared). Review timestamps are preserved exactly in validation-results.json. The file is the same one already imported into v3, so v4 retains these labels once and adds zero labels. Previous references and reports remain unchanged.

| Row | Resume | Field | Explicit expected value | Exact cited source |
|---|---|---|---|---|
'''+table+'''

All six decisions explicitly name parent `personal_information` and record association `{"kind":"record_id","value":"personal_information"}`. Each parent/attribute is defined, the record exists under that parent in the saved current hierarchy, each citation belongs to that record, each quote occurs exactly in the cited block and contains its expected value. The six correct decisions match the saved mapped tuples and prior v3 references. No citation was inherited or inferred. JSON and CSV validation files record each decision and the reason for acceptance.

Validation is against the frozen extracted text and saved section intervals, which passed integrity checks. Original PDF paths are unavailable here; no fresh visual PDF verification or identity authentication was performed. Declared PDF hashes are provenance, not freshly checked PDF hashes. Presence of text and record membership supports these submitted personal fields, not correctness of unreviewed records.

v4 contains 12 reference fields: Aditya 3 and Manjunath 9. Six of Manjunath's fields retain their earlier explicit-user-expectation provenance unchanged; they are not newly approved PDF decisions. All 224 pending rows retain null expected values/parents/associations and empty reviewer evidence. No new accuracy score or whole-resume approval is implied.

## Next manual review: Group 02 employment

Open **group-02.html** in this directory. Review Aditya's Persistent Systems record (`experience-1`, parent `experience`) in six rows: A064 company, A065 role, A066 start date, A067 end date, A068 duration, A069 location. This keeps one employment record together. Saved header source `e12:647:706` reads:

> Engineering Lead | Persistent Systems | Apr 2022 - Present

Current values are Persistent Systems, Engineering Lead, Apr 2022, Present, Apr 2022 - Present, and an unresolved empty location. The page shows full saved record text, proposed field-specific evidence, current parent/record, and controls for corrections or uncertainty. These are predictions, not approvals. Do not infer a location from a different job or personal address, or interpret “Present” as a newly verified current-employment claim. The older personal-information Group 02 page remains preserved; this new session is specifically the requested employment review.

Every row starts pending. Enter your reviewer name, explicitly confirm/correct individual rows or mark uncertainty with notes, then download JSON (preferred) or CSV. Verified absence requires checking the original PDF and recording scope; an empty model field alone does not establish absence. Downloads are durable separate files; browser selections alone are not saved. Share the downloaded file path for validation. Session-specific filenames distinguish this Group 02 from the previous personal-field page. No labels from Group 02 are incorporated until you review and submit them.

No DeepSeek/API calls, production mapping changes, extraction/block detection, or previous 350-resume experiment were run. Work stops here for manual review.
''')
    (OUT/'README.md').write_text('# Manual review continuation\n\nRead report.md and open group-02.html for six employment fields. Download decisions after reviewing and keep the file. Submit its saved path; pending or omitted rows remain unreviewed. No automatic ground-truth update occurs from the page.\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
