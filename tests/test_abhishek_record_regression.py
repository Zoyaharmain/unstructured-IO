"""Regression against the specific reported Abhishek extraction; no API calls."""
import json
from pathlib import Path
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy

ROOT=Path('reports/abhishek-record-recovery-20261027')


def request():
    elements=json.loads((ROOT/'extraction.json').read_text())['elements']
    sections=SectionResponse.model_validate(json.loads((ROOT/'sections.json').read_text()))
    req=SchemaMappingRequest(elements=elements,sections=sections)
    sections.sections=build_sections({s.category:s.blocks for s in sections.sections},req.elements)
    return req


def test_actual_resume_has_three_correct_employers_roles_and_date_ranges():
    req=request();before=req.model_dump()
    out=map_schema(req)
    assert [(r.company,r.role,r.start_date,r.end_date) for r in out.data.experience]==[
        ('SLK Software','Team Leader','01/2025','Present'),
        ('Impetus Technologies','SRE/Devops Engineer','06/2021','12/2024'),
        ('Cavisson Systems','Software Engineer','10/2018','05/2021')]
    assert [(r.start_year,r.graduation_year) for r in out.data.education]==[('2014','2018')]
    assert req.model_dump()==before
    revised=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert validate_result(req.elements,revised)==[]
    validate_hierarchy(out.section_schemas,revised)


def test_date_is_not_moved_when_degree_row_is_not_physically_aligned():
    req=request()
    for section in req.sections.sections:
        if section.category=='education':
            for block in section.blocks:
                req.elements[block.source_element_index].metadata={}
    from local_api.services.education_date_recovery import recover_education_dates
    assert recover_education_dates(req.sections,req.elements) is req.sections
