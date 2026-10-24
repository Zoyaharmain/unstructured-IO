"""Red regressions for proposed repairs. Expected to fail until approved production fixes."""
import sys
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from local_api.services.record_relationships import field_kinds
from scripts.single_resume_pipeline import fingerprint
from local_api.schemas.sections import SectionResponse

def test_responsibility_continuation_is_not_company_evidence():
    text='delivering high-integrity data feeds to downstream Fund accounting systems.'
    kinds=field_kinds(text,'experience')
    assert 'responsibilities' in kinds and 'employer' not in kinds

def test_hierarchy_only_progress_changes_feedback_fingerprint():
    sections=SectionResponse(status='provisional',sections=[],needs_review=[],metadata={},warnings=[])
    before={'data':{},'section_schemas':[{'category':'experience','records':[]}]}
    after=deepcopy(before);after['section_schemas'][0]['records']=[{'record_id':'experience-1','attributes':[]}]
    assert fingerprint(sections,before)!=fingerprint(sections,after)
