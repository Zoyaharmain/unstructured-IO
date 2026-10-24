import importlib.util,json
from copy import deepcopy
from pathlib import Path
import pytest
from local_api.schemas.subschema_spec import SUBSCHEMAS

OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('import_review_group',OUT/'import_group.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def fixture():
    payload=json.loads((OUT/'received-group-01.json').read_text())
    group=json.loads((ROOT/'reports/manual-field-review-resume-20261024-v2/group-01.json').read_text())['rows']
    inventories={}
    for row in group:
        row['document_key']='aditya-vashisth' if row['row_id'].startswith('A') else 'manjunath-murugan'
        inventories.setdefault(row['document_key'],{}).update({b['source_id']:b.get('text',b.get('quote')) for b in row['source_text']})
    return payload,group,inventories


def test_saved_six_decisions_validate_without_modifying_inputs():
    payload,group,inventory=fixture();before=deepcopy(payload)
    approved,uncertain,pending=module.validate_payload(payload,group,inventory,SUBSCHEMAS)
    assert len(approved)==6 and not uncertain and not pending and payload==before


@pytest.mark.parametrize('mutation',['duplicate','foreign_row','wrong_document','missing_reviewer','bad_quote','foreign_source','unsupported_value','wrong_confirmation','omitted_count','missing_timestamp'])
def test_invalid_decisions_are_rejected(mutation):
    payload,group,inventory=fixture();d=payload['decisions'][0]
    if mutation=='duplicate':payload['decisions'].append(deepcopy(d))
    if mutation=='foreign_row':d['row_id']='A099'
    if mutation=='wrong_document':d['document_key']='manjunath-murugan'
    if mutation=='missing_reviewer':d['reviewer']=''
    if mutation=='bad_quote':d['reviewer_source_evidence'][0]['quote']='Fake quote'
    if mutation=='foreign_source':d['reviewer_source_evidence'][0]['source_id']='e999:0:9'
    if mutation=='unsupported_value':d['expected_values']=['Invented name']
    if mutation=='wrong_confirmation':d['expected_record_association']['value']='another-record'
    if mutation=='omitted_count':payload['pending_rows_omitted']=4
    if mutation=='missing_timestamp':d['reviewed_at']=''
    with pytest.raises(ValueError):module.validate_payload(payload,group,inventory,SUBSCHEMAS)


def test_omitted_and_pending_rows_do_not_become_labels():
    payload,group,inventory=fixture();payload['decisions']=payload['decisions'][:1];payload['pending_rows_omitted']=5
    approved,_,_=module.validate_payload(payload,group,inventory,SUBSCHEMAS);assert len(approved)==1
    payload['decisions'][0]['review_status']='pending'
    approved,_,pending=module.validate_payload(payload,group,inventory,SUBSCHEMAS)
    assert not approved and pending==['A001']


def test_versions_and_working_copies_preserve_unreviewed_scope():
    previous=ROOT/'ground_truth/field_level/v2';current=ROOT/'ground_truth/field_level/v3'
    for doc,old_count,new_count in [('aditya-vashisth',0,3),('manjunath-murugan',6,9)]:
        old=json.loads((previous/(doc+'.json')).read_text());new=json.loads((current/(doc+'.json')).read_text())
        assert len(new['verified_fields'])==new_count
        assert new['verified_fields'][:old_count]==old['verified_fields']
    rows=[r for doc in ['aditya-vashisth','manjunath-murugan'] for r in json.loads((OUT/doc/'comparison-worksheet.json').read_text())['rows']]
    assert len(rows)==230 and sum(r['review_status']=='pending' for r in rows)==224
    assert all(r.get('expected_values') is None for r in rows if r['review_status']=='pending')
    assert all(r['review_status']=='pending' for r in json.loads((OUT/'group-02.json').read_text())['rows'])
