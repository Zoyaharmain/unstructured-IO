import socket,contextlib,pytest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
def prohibited(*a,**k):raise AssertionError('Network prohibited in offline mapper regression suite')
socket.socket.connect=prohibited
files=['test_saved_hierarchical_defects.py','test_record_subfields.py','test_schema_mapping.py','test_section_subschemas.py','test_resume_sections.py','test_hierarchical_schema.py','test_schema_field_index.py','test_structural_grouping.py','test_section_layout_recovery.py','test_resume_ground_truth.py','test_llm_section_review.py','test_single_resume_check.py','test_report_source_binding.py','test_pipeline200_root_causes.py','test_existing350_repairs.py','test_batch50_repairs.py','test_flagged_review_resolution.py','test_ground_truth_workflow.py','test_hierarchical_five_runner.py']
log=Path('reports/hierarchical-defect-replay-20261023-231542/regression-tests.txt')
with log.open('w') as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
 result=pytest.main(['-q',*['tests/'+f for f in files]])
print(log.read_text()[-3500:]);raise SystemExit(result)
