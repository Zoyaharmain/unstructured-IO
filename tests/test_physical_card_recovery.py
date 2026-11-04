"""Source card repairs are independent of candidate and employer names."""
import json
from copy import deepcopy
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.llm_schema_mapping import local_section_payload,map_with_field_review
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.standardization.mapping import mapping_input
from local_api.services.standardization.service import standardize_resume_data


def row(start,end,y,size=11,bold=False,x=.1):
    return {'start':start,'end':end,'bbox':[x,y,x+.4,y+.012],'font_size':size,'bold':bold}


def test_different_sized_header_rows_are_name_and_literal_title():
    name='EXAMPLE CANDIDATE';title='CAPITAL MARKETS OPERATIONS';text=name+' '+title
    elements,sections=fixture([text,'example@example.org','PROFILE','Experienced finance professional specializing in market operations and reliable controls for institutional customers across multiple business teams.'],{'personal_information':[0,1],'summary':[2,3]},[])
    elements[0].type='Header';elements[0].metadata={'pdf_source_lines':[row(0,len(name),.03,20,True),row(len(name)+1,len(text),.06,12,True)]}
    # Source refinement finds the two typography rows, as it does for PDF uploads.
    from local_api.services.resume_sections import build_sections
    sections.sections=build_sections({s.category:s.blocks for s in sections.sections},elements)
    before=deepcopy([e.model_dump() for e in elements]);out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.contact.full_name==name and out.data.professional_title==title
    assert [e.model_dump() for e in elements]==before


def test_bullet_separated_header_owns_right_aligned_dates():
    texts=['EXPERIENCE','Example Trust - Middle Office Settlement Operations • Senior Financial Analyst','Wellington, NZ Jan 2025 – Present','Managed daily trade confirmations.']
    elements,sections=fixture(texts,{'experience':[0,1,2,3]},[])
    elements[1].metadata={'pdf_source_lines':[row(0,50,.1,11,True),row(53,len(texts[1]),.12,11,True)]}
    cut=texts[2].index('Jan');elements[2].metadata={'pdf_source_lines':[row(0,cut-1,.1,x=.7),row(cut,len(texts[2]),.12,x=.7)]}
    from local_api.services.resume_sections import build_sections
    sections.sections=build_sections({'experience':sections.sections[0].blocks},elements)
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(out.data.experience)==1
    job=out.data.experience[0]
    assert job.company=='Example Trust' and job.role=='Senior Financial Analyst'
    assert job.start_date=='Jan 2025' and job.end_date=='Present'


def test_misspelled_heading_routes_title_result_and_date_to_one_award():
    texts=['EDUCATION','ACADEMIC ACHEIVEMENTS','Sustainable Design Competition','Won third place for a recycled textile business model.','August 2021']
    elements,sections=fixture(texts,{'education':list(range(5))},[])
    elements[1].type=elements[2].type=elements[4].type='Title';elements[3].type='ListItem'
    req=SchemaMappingRequest(elements=elements,sections=sections);out=map_schema(req)
    awards=next(s for s in out.section_schemas if s.category=='awards')
    assert len(awards.records)==1
    values={a.name:[v.value for v in a.items] for a in awards.records[0].attributes}
    assert values['name']==[texts[2]] and values['description']==[texts[3]] and values['date']==[texts[4]]
    assert not validate_result(elements,SectionResponse.model_validate(out.meta['reviewed_sections']))
    payload=local_section_payload(out,{s.category for s in out.section_schemas if s.category!='needs_review'})
    ar=next(s for s in payload if s['category']=='awards');card=ar['records'][0]
    duplicate=deepcopy(card);duplicate['record_id']='wrong-result';duplicate['source_ids']=card['source_ids'][1:]
    card['source_ids']=card['source_ids'][:1];ar['records'].append(duplicate)
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        return json.dumps({'sections':[s for s in payload if s['category'] in categories]})
    reviewed=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert reviewed.meta['field_review']['status']=='complete'
    assert len(next(s for s in reviewed.section_schemas if s.category=='awards').records)==1


def test_plural_bachelor_month_range_and_grade_map_without_inference():
    from local_api.services.education_subfields import refine_education
    texts=['Example College of Arts and Commerce','Bachelors in Commerce - Honors in Costing Major','July 2019 – May 2022','CGPA - 9.8']
    elements,sections=fixture(texts,{'education':list(range(4))},[])
    fields,_=refine_education({'institution':None,'degree':None,'field_of_study':None,'start_year':None,'graduation_year':None,'grade_or_gpa':None},sections.sections[0].blocks)
    assert fields['degree']=='Bachelors in Commerce'
    assert fields['start_year']=='July 2019' and fields['graduation_year']=='May 2022'


def test_department_narrative_is_not_an_employer_header():
    from local_api.services.record_subfields import employment_header_fields
    assert not employment_header_fields('Worked with a team - improving settlement operations across the company.')


def shared_school_fixture():
    from local_api.schemas.sections import SectionEntry
    first='Class 12th - 90.6%';second='Class 10th - 10 CGPA';combined=first+' • '+second
    elements,sections=fixture(['EDUCATION','Example Secondary School',combined,'May 2019'],{'education':[0,1,2,3]},[])
    section=sections.sections[0]
    original=next(b for b in section.blocks if b.source_element_index==2 and b.start==0)
    # Use the full original element as the authority for all three exact spans.
    template=original.model_copy(update={'start':0,'end':len(combined),'text':combined})
    heading=next(b for b in section.blocks if b.source_element_index==0)
    institution=next(b for b in section.blocks if b.source_element_index==1)
    date=next(b for b in section.blocks if b.source_element_index==3)
    def part(start,end):return template.model_copy(update={'start':start,'end':end,'text':combined[start:end]})
    section.blocks=[heading,institution,part(0,len(first)),part(len(first),len(first)+3),part(len(first)+3,len(combined)),date]
    section.text='EDUCATION\nExample Secondary School\n'+combined+'\nMay 2019'
    section.entries=[SectionEntry(entry_id='school-12',block_indices=[1,2,5],lane='main',boundary_reason='source',fields={'institution':[1],'qualification':[2],'grade':[2],'dates':[5]}),
                     SectionEntry(entry_id='school-10',block_indices=[4],lane='main',boundary_reason='source',fields={'qualification':[4],'grade':[4]})]
    return elements,sections


def test_school_context_shares_only_institution_and_keeps_evidence_disjoint():
    elements,sections=shared_school_fixture();req=SchemaMappingRequest(elements=elements,sections=sections)
    out=map_schema(req)
    assert len(out.data.education)==2
    assert [e.institution for e in out.data.education]==['Example Secondary School']*2
    assert out.data.education[0].graduation_year=='May 2019'
    assert out.data.education[1].graduation_year is None
    assert out.data.education[1].grade_or_gpa=='10 CGPA'
    revised=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert not validate_result(elements,revised)
    hierarchy=next(s for s in out.section_schemas if s.category=='education')
    assert not set(hierarchy.records[0].source_ids)&set(hierarchy.records[1].source_ids)
    second=next(a for a in hierarchy.records[1].attributes if a.name=='institution')
    assert second.items[0].evidence[0].source_id not in hierarchy.records[1].source_ids
    payload=local_section_payload(out,{'education'})
    payload[0]['records'][1]['fields']['institution']=[];payload[0]['records'][1]['missing']['institution']='unmapped'
    reviewed=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert reviewed.meta['field_review']['status']=='complete'
    assert reviewed.data.education[1].institution=='Example Secondary School'
    assert reviewed.data.education[1].graduation_year is None


def test_shared_context_cannot_authorize_dates_or_an_unrelated_source():
    elements,sections=shared_school_fixture()
    second=sections.sections[0].entries[1]
    second.context_fields={'graduation_year':[5]}
    assert 'invalid_record_context' in validate_result(elements,sections)
    second.context_fields={'institution':[5]}
    assert 'invalid_record_context' in validate_result(elements,sections)
