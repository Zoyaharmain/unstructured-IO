"""Offline structural regressions: source ownership, not resume-specific rules."""
import json
from pathlib import Path
import pytest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.resume_structure import project_source_groups, heading_boundary, heading_aliases
from local_api.services.resume_sections import ANCHORS
from local_api.services.record_subfields import employment_header_fields
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy

ROOT=Path('reports/abdul-structural-review-20261027/verified')


def test_actual_two_column_resume_record_associations_and_evidence():
    req=SchemaMappingRequest(elements=json.loads((ROOT/'extraction.json').read_text())['elements'],
                             sections=json.loads((ROOT/'sections.json').read_text()))
    before=req.model_dump()
    out=map_schema(req)
    assert out.data.contact.full_name=='ABDUL SHUKOOR'
    assert [(r.company,r.role) for r in out.data.experience]==[
        ('PARAM Info Dubai','Copilot Specialist'),
        ('Trigent Software Inc Bengaluru','Copilot Developer'),
        ('Novigo Solution Pvt. Ltd. Bengaluru','Software Engineer'),
        ('Percoyo. Pvt Ltd Bengaluru','Software Developer')]
    projects=next(s for s in req.sections.sections if s.category=='projects')
    owners={i:e.entry_id for e in projects.entries for i in e.block_indices}
    title_indices=[i for i,b in enumerate(projects.blocks) if b.text.startswith(('1. Government','2. MOBARO','COI (','SharePoint Environment'))]
    assert len(title_indices)==4
    assert len({owners[i] for i in title_indices})==4
    assert all(not r.name.startswith('Projects Worked') for r in out.data.projects if r.name)
    assert next(s.category for s in req.sections.sections for b in s.blocks if b.text=='TECHNICAL PROFILE')=='skills'
    assert req.model_dump()==before
    assert validate_result(req.elements,req.sections)==[]
    validate_hierarchy(out.section_schemas,req.sections)


@pytest.mark.parametrize('text,company,role',[
    ('I am currently working as a Platform Specialist at Example Labs from','Example Labs','Platform Specialist'),
    ('I Worked as a Software Engineer at Example Inc from','Example Inc','Software Engineer'),
    ('Worked as a Data Analyst with Example Labs','Example Labs','Data Analyst'),
])
def test_grammatical_employment_headers(text,company,role):
    assert employment_header_fields(text)=={'company':company,'role':role}


def test_responsibility_with_employer_mention_is_not_an_employment_header():
    assert employment_header_fields('Worked with Example Labs to build a data platform.')=={}


def test_technical_profile_is_a_skills_heading():
    assert heading_boundary('TECHNICAL PROFILE',heading_aliases(ANCHORS))==('skills',None)


def test_task_bullets_do_not_create_project_records():
    elements=[];blocks=[]
    for i,text in enumerate(['Built a dashboard.','Implemented a data pipeline.']):
        elements.append(ExtractedElement(type='ListItem',text=text,page_number=1,metadata={
            'pdf_source_lines':[{'start':0,'end':len(text),'bbox':[.1,.2+i*.1,.8,.22+i*.1]}]}))
        blocks.append(SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,
                                   assignment='semantic',lane='source',reason='fixture'))
    assert project_source_groups(blocks,elements)==[]


def test_numbered_projects_override_portfolio_heading_and_task_formatting():
    lines=['Projects Worked at Example Labs', '1. Search Index', 'Built a search index.',
           '2. Event Stream', 'Implemented event processing.']
    elements=[];blocks=[]
    for i,text in enumerate(lines):
        elements.append(ExtractedElement(type='ListItem' if i in {2,4} else 'Title',text=text,page_number=1,
            metadata={'pdf_source_lines':[{'start':0,'end':len(text),
                'bbox':[.1,.1+i*.05,.8,.12+i*.05],'bold':i==0}]}))
        blocks.append(SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,
                                   assignment='semantic',lane='source',reason='fixture'))
    groups=project_source_groups(blocks,elements)
    assert [g['block_indices'] for g in groups]==[[1,2],[3,4]]
