"""Execution provenance and meaningful-content guards use production functions."""
import json,subprocess,sys
from pathlib import Path
import pytest
from scripts.report_pilot50_review import execution_context
from local_api.services.review_validation import inspect_assignments
from local_api.services.source_accounting import artifact_reason
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock


def test_replay_does_not_attribute_historical_calls_to_new_run():
    context=execution_context({'run_kind':'offline_replay','source_run':'prior'}, {'classification_api_calls':111,'historical_classification_api_calls':111})
    assert context['live_api_calls']==0 and context['historical_api_calls']==111
    assert not context['fresh_local_processing']
    live=execution_context({}, {'classification_api_calls':111})
    assert live['live_api_calls']==111 and live['fresh_local_processing']


@pytest.mark.parametrize('script',['reproduce_100_fixed_offline.py','reproduce_structural_fix_offline.py'])
def test_replay_refuses_to_delete_existing_results(tmp_path,script):
    destination=tmp_path/'existing';destination.mkdir();marker=destination/'gold.json';marker.write_text('approved')
    run=subprocess.run([sys.executable,'-B',str(Path('scripts')/script),'--output',str(destination)],capture_output=True,text=True)
    assert run.returncode!=0 and 'already exists' in run.stderr
    assert marker.read_text()=='approved'


def test_optional_provider_type_is_only_the_documented_constant():
    args=(1,{'skills'},{'u0':6})
    assert not inspect_assignments('{"type":"json_object","assignments":[["u0","skills"]]}',*args)[1]
    assert inspect_assignments('{"type":"anything","assignments":[["u0","skills"]]}',*args)[1][0]['kind']=='invalid_schema'


@pytest.mark.parametrize('text,kind,bottom,expected',[
 ('1 | P a g e','Footer',False,True),
 ('2 | P a g e','UncategorizedText',True,True),
 ('2 | P a g e','NarrativeText',False,False),
 (' • ','Footer',False,True),
 ('ADDITIONAL INFORMATION','Footer',True,False),
 ('C#','Footer',True,False),
 ('2024','Footer',True,False),
 ('Member, IEEE','NarrativeText',True,False),
])
def test_artifacts_require_specific_source_evidence(text,kind,bottom,expected):
    metadata={'pdf_source_lines':[{'start':0,'end':len(text),'bbox':[.1,.95,.8,.97]}]} if bottom else {}
    element=ExtractedElement(type=kind,text=text,page_number=1,metadata=metadata)
    block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='needs_review',reason='source')
    assert bool(artifact_reason(element,block)) is expected
