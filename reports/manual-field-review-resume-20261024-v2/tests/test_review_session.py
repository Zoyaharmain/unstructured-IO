import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import pytest

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('prepare_review_session',OUT/'prepare_review.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_predictions_cannot_turn_pending_into_approval():
    rows=[{'review_status':'pending','predicted_values':['Correct-looking value'],'expected_values':None}]
    assert module.classify_saved_decisions(rows)==[]
    assert module.classify_saved_decisions([dict(rows[0],review_status='verified')])[0]['scorable'] is False


def test_invalid_prior_evidence_is_rejected():
    reference={'verified_fields':[{'source_evidence':[{'source_element_index':0,'start':0,'end':4,'quote':'Fake'}]}]}
    with pytest.raises(ValueError):module.validate_prior_evidence(reference,[{'text':'Real'}])


def test_v2_preserves_six_prior_fields_and_zero_new_approvals():
    for doc,count in [('aditya-vashisth',0),('manjunath-murugan',6)]:
        old=json.loads((ROOT/'ground_truth/field_level/v1'/f'{doc}.json').read_text())
        new=json.loads((ROOT/'ground_truth/field_level/v2'/f'{doc}.json').read_text())
        assert new['verified_fields']==old['verified_fields'] and len(new['verified_fields'])==count
        assert new['provenance']==old['provenance']
        assert new['review_session']['new_approved_fields']==0


def test_working_rows_are_unique_pending_and_not_scored():
    rows=[]
    for name in ['aditya-vashisth','manjunath-murugan']:
        rows+=json.loads((OUT/name/'comparison-worksheet.json').read_text())['rows']
    assert len(rows)==230 and len({r['row_id'] for r in rows})==230
    assert all(r['review_status']=='pending' and r['expected_values'] is None for r in rows)
    first=json.loads((OUT/'group-01.json').read_text())['rows']
    assert [r['row_id'] for r in first]==['A001','A002','A003','M002','M003','M005']
    assert all(r['review_group']=='group-01' for r in first)
    plan=json.loads((OUT/'review-plan.json').read_text())
    assert all(len(g['rows'])<=6 for g in plan)
    assert len({row for g in plan for row in g['rows']})==230
    summary=json.loads((OUT/'summary.json').read_text())
    assert summary['new_accuracy_evaluation_run'] is False
