"""Dated job ownership and empty artifact handling without candidate constants."""
import json
import pytest
from copy import deepcopy
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.sections import SectionResponse,SectionRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.llm_section_review import ReviewSettings,review_sections,source_ledger,assert_coverage
from local_api.services.llm_schema_mapping import local_section_payload,map_with_field_review


def test_blank_and_whitespace_elements_are_audited_without_model_review():
    elements,sections=fixture(['','  ','EXPERIENCE','Engineer | Example Ltd | Jan 2020 - Dec 2021','Built services.'],{'experience':[2,3,4]},[0,1])
    seen=[]
    def transport(settings,messages):
        spans=json.loads(messages[1]['content'])['spans'];seen.extend(spans)
        assert all(s['text'].strip() for s in spans)
        return json.dumps({'assignments':[[s['id'],s['current_category']] for s in spans]})
    out=review_sections(SectionRequest(elements=elements),sections,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert out.metadata['llm_review']['status']=='complete'
    assert not out.needs_review
    assert len(out.source_artifacts)==2 and seen
    assert not validate_result(elements,out)
    assert_coverage(elements,source_ledger(out))


def jobs_fixture():
    texts=['PROFESSIONAL EXPERIENCE',
      'Example Payments (Contract) – Senior Program Manager (TPMO - Technical Program Management Office) | London | October 2024 – Present',
      'Technology & Tools: Jira, Smartsheet, ServiceNow Strategic Portfolio Management (SPM), Confluence',
      'Key Responsibilities & Achievements:',
      'Program leadership, ensuring business strategy is integrated with delivery teams.',
      'Example Consulting – Program Manager | Paris | October 2021 – May 2023',
      'By driving data-driven digital transformation, successfully delivered scalable analytics solutions.',
      'Client: Water Utility | Program: Platform Upgrade (Fixed- Price Project) | Role: Program Manager',
      'Key Responsibilities:','Spearheaded the platform migration and maintained service continuity.',
      'Tools & Technology: SQL, Microsoft Project','Key Achievements:','Achieved outstanding customer satisfaction.',
      'EDUCATION','BSc Computer Science']
    # Simulate the reported subsection bleed and phantom employers from local/LLM placement.
    elements,sections=fixture(texts,{'experience':[0,1,2,5,6,7,8,9,10], 'awards':[3,4,11,12], 'education':[13,14]},[])
    for i in (0,3,8,11,13):elements[i].type='Title'
    return texts,elements,sections


def test_tools_results_and_project_roles_stay_with_their_dated_job():
    texts,elements,sections=jobs_fixture();before=deepcopy([e.model_dump() for e in elements])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [(j.company,j.role) for j in out.data.experience]==[
      ('Example Payments (Contract)','Senior Program Manager (TPMO - Technical Program Management Office)'),('Example Consulting','Program Manager')]
    assert 'Jira' in out.data.experience[0].technologies
    assert all(not s.startswith('Technology & Tools:') and s!='Key Responsibilities & Achievements:' for s in out.data.experience[0].responsibilities)
    assert any('Program leadership' in s for s in out.data.experience[0].responsibilities)
    assert any('By driving' in s for s in out.data.experience[1].responsibilities)
    assert any('platform migration' in s for s in out.data.experience[1].responsibilities)
    assert [e.model_dump() for e in elements]==before
    assert not validate_result(elements,SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_field_review_cannot_split_tools_into_an_extra_job():
    texts,elements,sections=jobs_fixture();req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req);payload=local_section_payload(local,{s.category for s in local.section_schemas if s.category!='needs_review'})
    row=next(r for r in payload if r['category']=='experience');first=row['records'][0];fake=deepcopy(first)
    fake['record_id']='false-tools-job';fake['source_ids']=first['source_ids'][1:];first['source_ids']=first['source_ids'][:1]
    row['records'].append(fake)
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        return json.dumps({'sections':[s for s in payload if s['category'] in categories]})
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert out.meta['field_review']['status']=='complete'
    assert len(out.data.experience)==2 and out.data.experience[0].company=='Example Payments (Contract)'


def test_incomplete_header_format_is_not_silently_folded_into_another_job():
    from local_api.services.employment_scope import recover_employment_scope
    elements,sections=fixture(['EXPERIENCE','Engineer | Alpha Ltd | Jan 2020 - Dec 2021','Engineer | Beta Ltd | Jan 2022 - Dec 2023','Engineer','Gamma Ltd','Jan 2024 - Present'],{'experience':list(range(6))},[])
    assert recover_employment_scope(sections,elements) is sections


@pytest.mark.parametrize('partial',[False,True])
def test_complete_source_ownership_does_not_allow_missing_duties_or_tools(partial):
    texts,elements,sections=jobs_fixture();req=SchemaMappingRequest(elements=elements,sections=sections)
    local=map_schema(req);payload=local_section_payload(local,{s.category for s in local.section_schemas if s.category!='needs_review'})
    row=next(s for s in payload if s['category']=='experience')
    for record in row['records']:
        for field in ('responsibilities','technologies'):
            record['fields'][field]=record['fields'][field][:1] if partial else []
            if not record['fields'][field]:record['missing'][field]='not_stated'
    def transport(settings,messages):
        categories=set(json.loads(messages[1]['content'])['registry'])
        return json.dumps({'sections':[s for s in payload if s['category'] in categories]})
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=transport)
    assert out.meta['field_review']['status']=='complete'
    assert any('Program leadership' in s for s in out.data.experience[0].responsibilities)
    assert any('By driving' in s for s in out.data.experience[1].responsibilities)
    assert 'Jira' in out.data.experience[0].technologies
    assert 'SQL' in out.data.experience[1].technologies


def test_dates_in_separate_elements_establish_complete_jobs():
    elements,sections=fixture(['EXPERIENCE','Example Payments – Senior Program Manager (Technical - Delivery Office)',
      'London | October 2024 – Present','Program leadership across product and engineering teams.',
      'Example Consulting – Delivery Manager','Paris | October 2021 – May 2023','Led cloud migration and delivery governance.'],{'experience':list(range(7))},[])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [(j.company,j.role) for j in out.data.experience]==[
      ('Example Payments','Senior Program Manager (Technical - Delivery Office)'),('Example Consulting','Delivery Manager')]
    assert any('Program leadership' in s for s in out.data.experience[0].responsibilities)
    assert out.data.experience[0].start_date=='October 2024'


def test_source_paragraphs_join_wrapped_fragments_without_duplicates():
    elements,sections=fixture(['EXPERIENCE','Example Ltd – Engineer | Jan 2020 – Dec 2021',
      'Managed enterprise programs across business and','', 'engineering teams to deliver measurable benefits.',
      'Other Ltd – Engineer | Jan 2022 – Present','Delivered reliable services.'],{'experience':[0,1,2,4,5,6]},[3])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.experience[0].responsibilities==['Managed enterprise programs across business and\nengineering teams to deliver measurable benefits.']
    assert not validate_result(elements,SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_one_dated_job_does_not_require_a_second_job_to_map_its_body():
    elements,sections=fixture(['EXPERIENCE','Example Ltd – Engineer | Jan 2020 – Present','Program leadership and delivery governance across business and engineering.'],{'experience':[0,1]},[2])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(out.data.experience)==1
    assert out.data.experience[0].responsibilities==[elements[2].text]


def test_large_quote_cannot_hide_missing_responsibility_words():
    from local_api.services.employment_details import covered_by_values
    elements,sections=fixture(['Led delivery and managed budgets.'],{'experience':[0]},[])
    blocks=sections.sections[0].blocks;sid=f'e0:0:{len(elements[0].text)}'
    expected=[{'value':elements[0].text,'evidence':[{'source_id':sid,'quote':elements[0].text}]}]
    incomplete=[{'value':'Led delivery','evidence':[{'source_id':sid,'quote':elements[0].text}]}]
    assert not covered_by_values(expected,incomplete,blocks)
    complete=[{'value':'Led delivery and'},{'value':'managed budgets.'}]
    assert covered_by_values(expected,complete,blocks)


def test_blank_marker_geometry_preserves_two_bullets_in_one_source_paragraph():
    first='Led platform delivery.';second='Managed program budgets.';body=first+' '+second
    elements,sections=fixture(['EXPERIENCE','Example Ltd – Engineer | Jan 2020 – Present',body,''],{'experience':[0,1,2]},[3])
    elements[2].metadata={'pdf_source_lines':[
      {'start':0,'end':len(first),'bbox':[.1,.20,.6,.21]},
      {'start':len(first)+1,'end':len(body),'bbox':[.1,.25,.6,.26]}]}
    elements[3].type='ListItem';elements[3].metadata={'coordinates':{'points':[[80,250],[85,260]],'layout_width':1000,'layout_height':1000}}
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.experience[0].responsibilities==[first,second]
    revised=SectionResponse.model_validate(out.meta['reviewed_sections'])
    assert len(revised.source_artifacts)==1 and not revised.needs_review
    assert not validate_result(elements,revised)
