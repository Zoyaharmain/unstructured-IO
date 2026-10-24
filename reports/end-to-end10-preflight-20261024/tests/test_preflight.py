import importlib.util,json
from copy import deepcopy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ten_runner',OUT/'run_ten.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
def test_exact_scope_gate():
 m=json.loads((OUT/'selection-manifest.json').read_text());m['document_count']=11
 with pytest.raises(ValueError,match='Exactly ten'):runner.verify(m)
def test_duplicate_document_rejected_before_provider_import():
 m=json.loads((OUT/'selection-manifest.json').read_text());m['selected'][1]=deepcopy(m['selected'][0])
 with pytest.raises(ValueError,match='Duplicate selected'):runner.verify(m)
def test_only_five_group02_labels_added_and_uncertainty_not_approved():
 for doc in ['aditya-vashisth','manjunath-murugan']:
  before=json.loads((ROOT/f'ground_truth/field_level/v4/{doc}.json').read_text())['verified_fields'];after=json.loads((ROOT/f'ground_truth/field_level/v5/{doc}.json').read_text())['verified_fields']
  assert after[:len(before)]==before
  assert len(after)-len(before)==(5 if doc=='aditya-vashisth' else 0)
  assert not any(r.get('decision_row_id')=='A069' for r in after)
 u=json.loads((ROOT/'ground_truth/field_level/v5/uncertainty/group02.json').read_text())['decisions'];assert len(u)==1 and u[0]['review_status']=='ambiguous' and u[0]['expected_values'] is None
def test_generalization_excludes_prior_history_and_scope_has_two_controls():
 m=json.loads((OUT/'selection-manifest.json').read_text());assert sum(r['development_control'] for r in m['selected'])==2
 assert all(not r['prior_llm_selection_hash_match'] and not r['prior_llm_selection_name_match'] for r in m['selected'][2:])
 assert len({r['normalized_text_sha256'] for r in m['selected']})==10
