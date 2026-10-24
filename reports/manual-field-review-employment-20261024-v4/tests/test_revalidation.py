import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/manual-field-review-employment-20261024-v4'
spec=importlib.util.spec_from_file_location('revalidation',OUT/'revalidate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test_references_are_idempotent_and_prior_fields_unchanged():
    for doc in ['aditya-vashisth','manjunath-murugan']:
        old=json.loads((ROOT/f'ground_truth/field_level/v3/{doc}.json').read_text());new=json.loads((ROOT/f'ground_truth/field_level/v4/{doc}.json').read_text())
        assert new['verified_fields']==old['verified_fields']
        ids=[f.get('decision_row_id') for f in new['verified_fields'] if f.get('decision_row_id')]
        assert len(ids)==len(set(ids))
def test_pending_rows_stay_unreviewed():
    rows=[r for doc in ['aditya-vashisth','manjunath-murugan'] for r in json.loads((OUT/doc/'comparison-worksheet.json').read_text())['rows']]
    pending=[r for r in rows if r['review_status']=='pending'];assert len(pending)==224
    assert all(r['expected_values'] is None and r['expected_record_association'] is None and not r.get('reviewer_source_evidence') for r in pending)
def test_record_validation_rejects_wrong_parent_and_foreign_evidence():
    d=json.loads((OUT/'received-group-01.json').read_text())['decisions'][0]
    schema=json.loads((ROOT/'reports/project-url-fix-20261024/offline-replay/03/schema.json').read_text())
    sources={q['source_id']:q['quote'] for q in d['reviewer_source_evidence']}
    assert mod.validate_record(d,schema,sources)
    bad=deepcopy(d);bad['expected_parent_section']='experience'
    with pytest.raises(ValueError,match='Parent/record'):mod.validate_record(bad,schema,sources)
    bad=deepcopy(d);bad['reviewer_source_evidence'][0]['source_id']='foreign'
    with pytest.raises(ValueError,match='does not belong'):mod.validate_record(bad,schema,sources)
def test_protected_files_remain_unchanged():
    snapshot=json.loads((OUT/'preservation-before.json').read_text())
    assert all(mod.sha(Path(p))==h for p,h in snapshot.items())
