"""Import explicit group decisions offline; never infer labels or overwrite versions."""
import csv
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
PREVIOUS=ROOT/'reports/manual-field-review-resume-20261024-v2'
V2=ROOT/'ground_truth/field_level/v2'
V3=ROOT/'ground_truth/field_level/v3'
INPUT=Path('/mnt/c/Users/Gopi Gedar/Downloads/group-01-reviewed-2026-10-24T09-54-57.555Z.json')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def validate_payload(payload, group, inventory, specification):
    if payload.get('review_group')!='group-01' or not isinstance(payload.get('decisions'),list):raise ValueError('Wrong review group or missing decisions')
    known={r['row_id']:r for r in group};seen=set();approved=[];uncertain=[];pending=[]
    for decision in payload['decisions']:
        rid=decision.get('row_id')
        if rid not in known or rid in seen:raise ValueError('Unknown or duplicate review row')
        seen.add(rid);row=known[rid]
        if decision.get('document_key')!=row['document_key'] or decision.get('attribute')!=row['attribute']:raise ValueError('Document or field mismatch')
        status=decision.get('review_status')
        if status=='pending':pending.append(rid);continue
        if not isinstance(decision.get('reviewer'),str) or not decision['reviewer'].strip():raise ValueError('Explicit reviewer required')
        time=datetime.fromisoformat(str(decision.get('reviewed_at','')).replace('Z','+00:00'))
        if time.tzinfo is None:raise ValueError('Review timestamp requires timezone')
        if status=='ambiguous':
            if not decision.get('reviewer_notes','').strip():raise ValueError('Ambiguity requires notes')
            uncertain.append(deepcopy(decision));continue
        if status not in {'correct','corrected'}:raise ValueError('Unsupported decision; absence requires a separate explicit scope')
        expected=decision.get('expected_values');parent=decision.get('expected_parent_section');field=decision['attribute']
        if parent not in specification or field not in specification[parent]:raise ValueError('Undefined parent/field')
        rule=specification[parent][field]
        if not isinstance(expected,list) or not expected or (not rule['multiple'] and len(expected)>1):raise ValueError('Explicit expected values required')
        for value in expected:
            if rule['type']=='string' and (not isinstance(value,str) or not value.strip()):raise ValueError('Wrong expected type')
            if rule['type']=='number' and (type(value) not in (int,float)):raise ValueError('Wrong expected type')
        selector=decision.get('expected_record_association')
        if not isinstance(selector,dict) or selector.get('kind') not in {'record_id','attribute','singleton'}:raise ValueError('Explicit record association required')
        if selector['kind']=='record_id' and not selector.get('value'):raise ValueError('Empty record ID')
        if selector['kind']=='attribute' and (not selector.get('attribute') or 'value' not in selector):raise ValueError('Incomplete record selector')
        evidence=decision.get('reviewer_source_evidence')
        if not isinstance(evidence,list) or not evidence:raise ValueError('Reviewer evidence required')
        sources=inventory[decision['document_key']]
        for q in evidence:
            if not isinstance(q,dict) or q.get('source_id') not in sources:raise ValueError('Foreign source block')
            if not isinstance(q.get('quote'),str) or not q['quote'].strip() or q['quote'] not in sources[q['source_id']]:raise ValueError('Quote does not occur in cited source')
        if any(not any(str(value) in q['quote'] for q in evidence) for value in expected):raise ValueError('Value unsupported by reviewer evidence')
        if status=='correct' and (expected!=row['predicted_values'] or parent!=row['parent_section'] or selector!={'kind':'record_id','value':row['predicted_record_id']} or evidence!=row['predicted_evidence']):
            raise ValueError('Correct decision differs from displayed tuple; use corrected')
        approved.append(deepcopy(decision))
    if payload.get('pending_rows_omitted')!=len(known)-len(seen):raise ValueError('Omitted-row count mismatch')
    return approved,uncertain,pending


def main():
    if V3.exists() or (OUT/'summary.json').exists():raise ValueError('Refuse to overwrite reference versions or reports')
    from local_api.schemas.subschema_spec import SUBSCHEMAS
    from local_api.schemas.sections import SectionResponse
    from local_api.schemas.extraction import ExtractedElement
    from local_api.services.source_validation import validate_result
    group=json.loads((PREVIOUS/'group-01.json').read_text())['rows']
    for row in group:row['document_key']='aditya-vashisth' if row['row_id'].startswith('A') else 'manjunath-murugan'
    protected=[INPUT]
    for folder in [ROOT/'ground_truth',PREVIOUS,ROOT/'local_api',ROOT/'tests/fixtures']:
        protected.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    references={p.stem:json.loads(p.read_text()) for p in V2.glob('*.json')}
    inventory={};bindings={}
    for doc,ref in references.items():
        frozen=ROOT/f"reports/hierarchical-deepseek-five-20261023-225341/results/{ref['selection_index']:02d}/extraction.json"
        prediction=ROOT/ref['latest_prediction_path'];sections=prediction.with_name('sections.json')
        protected.extend([frozen,prediction,sections])
        ext=json.loads(frozen.read_text());raw=json.loads(sections.read_text());parsed=SectionResponse.model_validate(raw)
        assert not validate_result([ExtractedElement.model_validate(e) for e in ext['elements']],parsed)
        blocks=[b for s in parsed.sections for b in s.blocks]+parsed.needs_review
        inventory[doc]={f'e{b.source_element_index}:{b.start}:{b.end}':b.text for b in blocks}
        bindings[doc]={'extraction':str(frozen.relative_to(ROOT)),'extraction_sha256':sha(frozen),
            'sections':str(sections.relative_to(ROOT)),'sections_sha256':sha(sections),
            'source_pdf_sha256_declared':ref['source_sha256'],'original_pdf_available':Path(ref['source_path']).is_file()}
    before={str(p):sha(p) for p in protected};save(OUT/'preservation-before.json',before)
    payload=json.loads(INPUT.read_text());approved,uncertain,pending=validate_payload(payload,group,inventory,SUBSCHEMAS)
    (OUT/'received-group-01.json').write_bytes(INPUT.read_bytes())
    V3.mkdir(parents=True)
    rows_by_doc={};decisions={d['row_id']:d for d in approved+uncertain}
    for doc,ref in references.items():
        updated=deepcopy(ref);updated['reference_version']='v3'
        updated['derived_from']={'path':str((V2/(doc+'.json')).relative_to(ROOT)),'sha256':sha(V2/(doc+'.json'))}
        additions=[d for d in approved if d['document_key']==doc]
        existing={f['field_id'] for f in ref['verified_fields']}
        for d in additions:
            fid=f"{d['expected_parent_section']}.{d['attribute']}"
            if fid in existing:raise ValueError('New decision conflicts with retained reference; manual resolution required')
            existing.add(fid)
            updated['verified_fields'].append({'field_id':fid,'parent_section':d['expected_parent_section'],
                'attribute':d['attribute'],'expected_values':d['expected_values'],'record_selector':d['expected_record_association'],
                'source_evidence':d['reviewer_source_evidence'],'verification_basis':'explicit_saved_group01_reviewer_decision',
                'review_decision':d['review_status'],'reviewer':d['reviewer'],'reviewed_at':d['reviewed_at'],
                'reviewer_notes':d.get('reviewer_notes',''),'decision_row_id':d['row_id'],
                'decision_file':str((OUT/'received-group-01.json').relative_to(ROOT)),
                'decision_file_sha256':sha(INPUT),'source_binding':bindings[doc],
                'reviewer_identity_status':'self_declared; not independently authenticated',
                'original_pdf_rechecked_by_importer':False})
        assert updated['verified_fields'][:len(ref['verified_fields'])]==ref['verified_fields']
        updated['coverage']='partial_explicit_field_decisions_not_exhaustive'
        updated['provenance']={'prior_version_provenance':deepcopy(ref['provenance']),
            'group01_explicit_decisions_recorded':len(additions),'full_document_approval':False}
        updated['review_session']={'status':'group01_imported_more_fields_pending','new_approved_fields':len(additions),
            'full_document_manual_signoff':False,'working_worksheet':str((OUT/doc/'comparison-worksheet.json').relative_to(ROOT))}
        save(V3/(doc+'.json'),updated)
        folder=OUT/doc;folder.mkdir()
        worksheet=json.loads((PREVIOUS/doc/'comparison-worksheet.json').read_text())
        for row in worksheet['rows']:
            if row['row_id'] in decisions:
                d=decisions[row['row_id']]
                for key in ['review_status','reviewer','reviewed_at','reviewer_notes','expected_values','expected_parent_section','expected_record_association','reviewer_source_evidence']:
                    row[key]=deepcopy(d[key])
        rows_by_doc[doc]=worksheet['rows'];save(folder/'comparison-worksheet.json',worksheet)
        columns=['row_id','review_group','kind','parent_section','predicted_record_id','attribute','predicted_values','source_text',
            'review_status','expected_values','expected_parent_section','expected_record_association','reviewer_source_evidence','reviewer','reviewed_at','reviewer_notes']
        with (folder/'comparison-worksheet.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore');writer.writeheader()
            for row in worksheet['rows']:
                writer.writerow({k:json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k) for k in columns})
    plan=json.loads((PREVIOUS/'review-plan.json').read_text());group2=next(g for g in plan if g['group_id']=='group-02')
    allrows={r['row_id']:dict(r,document_key=doc,source_pdf_sha256=references[doc]['source_sha256']) for doc,rows in rows_by_doc.items() for r in rows}
    save(OUT/'group-02.json',{'review_group':'group-02','rows':[allrows[rid] for rid in group2['rows']]})
    save(OUT/'review-plan.json',plan)
    changed=[p for p,h in before.items() if sha(Path(p))!=h];assert not changed
    summary={'validated_file':str(INPUT),'decision_file_sha256':sha(INPUT),'accepted_explicit_fields':len(approved),
        'uncertain_decisions':len(uncertain),'pending_rows_unreviewed':sum(r['review_status']=='pending' for rows in rows_by_doc.values() for r in rows),
        'inherited_expectations_preserved':sum(len(r['verified_fields']) for r in references.values()),
        'total_reference_fields':sum(len(r['verified_fields']) for r in references.values())+len(approved),
        'reference_version':'v3','next_group':'group-02','next_group_rows':group2['rows'],
        'api_calls':0,'mapping_runs':0,'accuracy_evaluation_run':False,'protected_files_checked':len(before),'protected_files_changed':changed}
    save(OUT/'summary.json',summary);save(OUT/'source-bindings.json',bindings)
    (V3/'README.md').write_text('# Field references v3\n\nImported six explicit Group 01 decisions from the user-provided downloaded file. Aditya has three newly verified fields; Manjunath has three new fields plus six unchanged prior expectations. The prior six retain their original, narrower provenance. All other worksheet rows remain unreviewed. This is partial field review, not whole-document approval. Reviewer identity is self-declared. Quotes were validated against frozen source text; original PDF paths remain unavailable to the importer. No API call, mapping change or new accuracy score was generated.\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
