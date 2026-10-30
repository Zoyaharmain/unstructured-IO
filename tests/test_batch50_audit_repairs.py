from datetime import datetime, timezone
import pytest
from local_api.services.standardization.dates import parse_date_string
from local_api.services.standardization.skills import canonicalize_skill_name
from scripts.audit_saved_resume_outputs import audit_one


@pytest.mark.parametrize('raw,expected',[('June, 2003','2003-06'),('April, 2003','2003-04'),('March, 2001','2001-03'),('OCT2022','2022-10'),('May 201 8','2018-05'),('201 7','2017')])
def test_date_forms_found_in_batch_are_parsed_without_rewriting_raw(raw,expected):
    assert parse_date_string(raw,reference_date=datetime(2026,10,29,tzinfo=timezone.utc))[0]==expected


def test_onwards_is_current_but_certificate_validity_range_is_not_an_issue_year():
    assert parse_date_string('onwards')[2]
    iso,precision,current,warnings=parse_date_string('2026–2029')
    assert iso is None and not current and warnings


def test_ambiguous_alm_does_not_invent_a_product_vendor():
    value,warning=canonicalize_skill_name('ALM')
    assert value=='ALM'
    assert warning.warning_type=='ambiguous_skill_alias'
    assert not warning.applied
    assert canonicalize_skill_name('HP ALM')[0]=='HP ALM'


def test_absent_saved_inventory_is_unavailable_not_failed_validation(tmp_path):
    source=tmp_path/'test.docx'
    from docx import Document
    doc=Document();doc.add_paragraph('Example Candidate');doc.save(source)
    mapping={'data':{'contact':{'full_name':'Example Candidate','email':'','phone':''}},'meta':{},'section_schemas':[]}
    result,*_=audit_one(mapping,source)
    assert not result['citation_inventory_available']
    assert result['structural_issues']==[]


def test_local_fallback_does_not_count_responsibilities_without_a_job_identity():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock, SectionEntry, ResumeSection, SectionResponse
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    text='Supported delivery and coordinated stakeholders.'
    element=ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={})
    block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='source',assignment='semantic',reason='fixture')
    entry=SectionEntry(entry_id='unknown',block_indices=[0],lane='source',boundary_reason='fixture',fields={'responsibilities':[0]})
    sections=SectionResponse(status='provisional',warnings=[],metadata={},needs_review=[],sections=[ResumeSection(category='experience',label='Experience',text=text,blocks=[block],entries=[entry])])
    result=__import__('local_api.services.schema_mapping',fromlist=['map_schema']).map_schema(SchemaMappingRequest(elements=[element],sections=sections))
    assert result.data.experience==[]
    assert result.section_schemas[0].residual_blocks[0].quote==text
    assert result.meta['record_reviews'][0]['review_reasons']


def test_wrapped_acronym_expansion_is_one_qualification_not_two_records():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock
    from local_api.services.resume_structure import reviewed_education_groups
    texts=['PGDB (Post','Graduate Diploma in Banking from Example University 2013-2014)',
           'MBA (Master of Business Administration-2011-2013)']
    elements=[];blocks=[]
    for i,(text,top) in enumerate(zip(texts,[.1,.12,.3])):
        hint={'start':0,'end':len(text),'bbox':[.1,top,.3,top+.005],'font_size':10}
        elements.append(ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={'pdf_source_lines':[hint]}))
        blocks.append(SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='left',assignment='heading_context',reason='fixture'))
    groups=reviewed_education_groups(blocks,elements)
    assert [g['block_indices'] for g in groups]==[[0,1],[2]]


def test_degree_expansion_is_not_used_as_subject_and_real_second_degree_stays_ambiguous():
    from local_api.schemas.sections import SectionBlock
    from local_api.services.education_subfields import refine_education
    def refine(text):
        block=SectionBlock(source_element_index=0,start=0,end=len(text),text=text,page_number=1,lane='left',assignment='semantic',reason='fixture')
        return refine_education({'degree':None,'institution':None,'field_of_study':None,'start_year':None,'graduation_year':None,'grade_or_gpa':None},[block])
    values,reasons=refine('MBA (Master of Business Administration-2011-2013)')
    assert values['degree']=='MBA' and values['field_of_study'] is None
    values,reasons=refine('MBA and Bachelor of Science')
    assert values['degree'] is None and reasons


def test_pdf_column_interleaving_is_not_reported_as_a_missing_literal(tmp_path,monkeypatch):
    import scripts.audit_saved_resume_outputs as audit
    from types import SimpleNamespace
    source=tmp_path/'example.pdf';source.write_bytes(b'fixture')
    monkeypatch.setattr(audit,'original_text',lambda p:'Program adjacent-column-text Governance')
    monkeypatch.setattr(audit.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='Program Governance'))
    mapping={'data':{'contact':{'full_name':'Program Governance','email':'','phone':''}},'meta':{},'section_schemas':[]}
    result,*_=audit.audit_one(mapping,source)
    assert result['literal_checks']==1
    assert not result['source_presence_not_confirmed']


def test_job_responsibilities_and_achievements_heading_does_not_start_awards():
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionRequest
    from local_api.services.resume_sections import get_engine
    texts=['Professional Experience','Jan 2020 – Dec 2022: Example Ltd., as Analyst',
           'Key Responsibilities & Achievements:','Delivered platform improvements.',
           'Technology & Tools: Python, SQL','Education','Bachelor of Science']
    result=get_engine().detect(SectionRequest(elements=[ExtractedElement(type='NarrativeText',text=t,page_number=1,metadata={}) for t in texts]))
    for index in [2,3,4]:
        assert any(b.source_element_index==index for s in result.sections if s.category=='experience' for b in s.blocks)
    assert not any(b.source_element_index in {2,3,4} for s in result.sections if s.category=='awards' for b in s.blocks)
