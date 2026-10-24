"""Offline evidence/invariant checks; no extraction, mapping replay or provider calls."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));RUN=ROOT/'reports/end-to-end10-preflight-20261024/execution'
from local_api.schemas.sections import SectionBlock
from local_api.services.education_subfields import refine_education
from local_api.services.record_relationships import field_kinds

def test_abbreviated_year_is_explicitly_uncertain_not_invented():
    text='Guru Gobind Singh Indraprastha University, Delhi | 2018 - 21'
    block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='heading_context',reason='fixture')
    values,reasons=refine_education({'degree':'','institution':'','field_of_study':None,'start_year':None,'graduation_year':None,'grade_or_gpa':None},[block])
    assert values['start_year']=='2018' and values['graduation_year'] is None
    assert any('no century inferred' in r for r in reasons)

def test_true_company_header_remains_employer_evidence():
    assert 'employer' in field_kinds('Persistent Systems','experience')

def test_all_saved_passes_terminated_and_accounting_valid():
    d=json.loads((ROOT/'reports/ten-resume-repair-plan-20261024/investigation.json').read_text())
    assert len(d['recovery_validation'])==10
    for row in d['recovery_validation']:
        assert row['within_two_pass_limit']
        assert all(p['interval_validation']=='passed' and p['hierarchy_validation']=='passed' for p in row['passes'])

def test_e24_retained_as_residual_not_lost_from_source():
    schema=json.loads((RUN/'02/schema.json').read_text())
    residual=[q for s in schema['section_schemas'] for q in s['residual_blocks'] if q['source_id']=='e24:0:75']
    assert len(residual)==1 and residual[0]['quote']=='delivering high-integrity data feeds to downstream Fund accounting systems.'

def test_limits_are_prompt_characters_not_unit_count_for_two_failures():
    d=json.loads((ROOT/'reports/ten-resume-repair-plan-20261024/investigation.json').read_text())
    rows=[r for r in d['limits'] if r['file'] in ['Siva Mari.pdf','Vikrant Roy.pdf']]
    assert len(rows)==2
    assert all(r['initial_review_units']<r['max_units'] and r['section_prompt_characters']>r['max_prompt_characters'] for r in rows)
