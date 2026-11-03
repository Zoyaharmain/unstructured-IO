"""Verify LinkedIn URL recovery, 3-entry education with grades, and experience responsibilities on Deeksha Yadu resume."""
import json
from pathlib import Path
from local_api.schemas.extraction import ExtractedElement
from local_api.services.resume_sections import detect_sections
from local_api.schemas.sections import SectionRequest
from local_api.services.schema_mapping import map_schema
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.standardization.service import standardize_resume_data


def test_deeksha_resume_mapping_and_standardization():
    cache_path = Path('scratch/deeksha_elements.json')
    if not cache_path.exists():
        pdf_path = Path('scratch/DeekshaYadu.pdf')
        if not pdf_path.exists():
            return
        from local_api.services.text_extraction_service import extract_text
        resp = extract_text(pdf_path.read_bytes(), 'DeekshaYadu.pdf')
        raw_elements = [el.model_dump() for el in resp.elements]
    else:
        raw_elements = json.loads(cache_path.read_text())

    elements = [ExtractedElement(**el) for el in raw_elements]
    req = SectionRequest(elements=elements)
    sections = detect_sections(req)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=sections))
    std, meta, status, warns = standardize_resume_data(mapped.data.model_dump())

    # 1. LinkedIn URL recovery
    assert mapped.data.contact.linkedin_url == 'linkedin.com/in/deekshayadu'
    assert std.contact.linkedin_url == 'https://linkedin.com/in/deekshayadu'

    # 2. Education: 3 distinct qualifications with grades
    assert len(std.education) == 3
    degrees = [e.degree for e in std.education]
    assert 'B.Tech' in degrees
    assert 'Higher Secondary Certificate (CBSE)' in degrees
    assert 'Secondary School Certificate (CBSE)' in degrees

    btech = next(e for e in std.education if e.degree == 'B.Tech')
    assert btech.grade_or_gpa == '8.44/10'
    assert btech.start_year_iso == '2016' and btech.graduation_year_iso == '2020'

    hsc = next(e for e in std.education if e.degree == 'Higher Secondary Certificate (CBSE)')
    assert hsc.grade_or_gpa == '85.4%'
    assert hsc.start_year_iso == '2015' and hsc.graduation_year_iso == '2016'

    ssc = next(e for e in std.education if e.degree == 'Secondary School Certificate (CBSE)')
    assert ssc.grade_or_gpa == '8.8/10'
    assert ssc.start_year_iso == '2013' and ssc.graduation_year_iso == '2014'

    # 3. Experience: 2 jobs with responsibilities and technologies
    assert len(std.experience) == 2
    nielsen = next(e for e in std.experience if 'nielsen' in e.company.lower())
    assert nielsen.role == 'Software Engineer 1'
    assert len(nielsen.responsibilities) >= 4
    assert len(nielsen.technologies) >= 5
    assert 'SCALA' in nielsen.technologies or 'Spark' in nielsen.technologies

    cognizant = next(e for e in std.experience if 'cognizant' in e.company.lower())
    assert cognizant.role == 'Associate Software Engineer'
    assert len(cognizant.responsibilities) >= 4
    assert len(cognizant.technologies) >= 5
    assert 'Python' in cognizant.technologies or 'Pyspark' in cognizant.technologies

