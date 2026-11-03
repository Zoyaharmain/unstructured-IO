"""General source grammar regressions; no candidate names or file-specific logic."""
import pytest
from local_api.services.record_subfields import employment_header_fields,RANGE
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock
from local_api.services.resume_structure import entry_groups,heading_boundary
from local_api.services.resume_sections import ALIASES
from local_api.services.project_fields import project_fields


@pytest.mark.parametrize('prefix,employer,role',[
 ('Having currently working in','Example Labs','FullStack devlopper'),
 ('Having Experience in','Another Organization','Platform Specialist'),
 ('Currently working in','Northern Systems','Developer'),
])
def test_explicit_organization_and_post_labels_generalize(prefix,employer,role):
 text=f'⮚ {prefix} {employer} post of {role} start 17-06-2022 to till 02-12-2022.'
 assert employment_header_fields(text)=={'company':employer,'role':role}
 assert RANGE.search(text).group(1,2)==('17-06-2022','02-12-2022')


def test_payroll_employer_is_not_replaced_by_client_organization():
 text='Having Experience in Client Organization postof Sr Software Engineer payroll was Staffing Organization pvt ltd. Start 25-03-2019 to 20-09-2019.'
 assert employment_header_fields(text)=={'company':'Staffing Organization pvt ltd','role':'Sr Software Engineer'}


def test_internship_is_literal_but_general_experience_prose_is_not_a_job():
 assert employment_header_fields('Having Experience in 6 months internship in Example Labs.')=={'company':'Example Labs','role':'internship'}
 assert employment_header_fields('Having experience of Python, machine learning and data science.')=={}


def test_wrapped_day_month_year_and_repeated_current_connector_keep_literal_offsets():
 text='05-12- 2022 to till till now'
 match=RANGE.fullmatch(text)
 assert match and match.group(1,2)==('05-12- 2022','now')


def block(text,index,heading=False):
 return SectionBlock(source_element_index=index,start=0,end=len(text),text=text,page_number=1,lane='left' if index%2 else 'wide',assignment='structural_heading' if heading else 'semantic',reason='fixture')


def test_numbered_project_markers_outrank_subfield_font_and_lane_boundaries():
 texts=['Project # 9: First Platform','Environment: Python','Description','Built APIs.',
        'Project #2',': Second Platform','Role: Team member',
        'Academic Project#1',':','Learning Portal','Role: Developer']
 elements=[ExtractedElement(type='Title',text=t,page_number=1,metadata={}) for t in texts]
 blocks=[block(t,i,i==4) for i,t in enumerate(texts)]
 groups=entry_groups(blocks,'projects',elements)
 assert [g['block_indices'] for g in groups]==[[0,1,2,3],[5,6],[7,8,9,10]]
 names=[project_fields([blocks[i] for i in g['block_indices']],elements)[0] for g in groups]
 assert names==['First Platform','Second Platform','Learning Portal']


def test_educational_qualification_singular_is_an_education_heading():
 assert heading_boundary('Educational Qualification:',ALIASES)==('education',None)


def test_wrapped_labelled_statement_keeps_full_source_dates_and_company_suffix():
 from local_api.services.record_subfields import refine_record
 pieces=['Having Experience in Client Platform postof Software Engineer payroll was Example Staffing pvt',
         'ltd. Start 25-03-2019 to 20-09-2019.']
 values,reasons=refine_record('experience',{'company':None,'role':None,'start_date':None,'end_date':None,'duration':None,'location':None},[block(t,i) for i,t in enumerate(pieces)])
 assert values['company']=='Example Staffing pvt\nltd'
 assert values['start_date']=='25-03-2019' and values['end_date']=='20-09-2019'


def test_wrapped_numeric_source_range_does_not_degrade_to_year_only():
 from local_api.services.record_subfields import refine_record
 pieces=['Having currently working in Example Labs post of Developer start 05-12-',
         '2022 to till till now.']
 values,reasons=refine_record('experience',{'company':None,'role':None,'start_date':None,'end_date':None,'duration':None,'location':None},[block(t,i) for i,t in enumerate(pieces)])
 assert values['start_date']=='05-12-\n2022'
 assert values['end_date']=='now'


def test_parenthetical_institution_candidate_is_not_declared_as_a_subject():
 from local_api.services.education_subfields import refine_education
 text='MCA (EXAMPLE North Campus) GGPA: 7.04'
 values,reasons=refine_education({'degree':None,'institution':None,'field_of_study':None,'grade_or_gpa':None},[block(text,0)])
 assert values['degree']=='MCA' and values['field_of_study'] is None
 assert values['institution'] is None and reasons
 assert values['grade_or_gpa']=='7.04'
