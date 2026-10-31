"""General Word layouts: undelimited headers, date-first degrees and broken URLs."""
from copy import deepcopy
from io import BytesIO
import json
import pytest
from docx import Document
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from test_block_completion import fixture
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.contacts import normalize_url
from local_api.services.llm_schema_mapping import map_with_field_review,local_section_payload
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.source_fragments import citations


def job_fixture():
    texts=['EXPERIENCE','January 2023 - Present',
           'Lead Data Scientist Example Systems Limited | Hyderabad, India',
           'With a strong background in application design, I specialize in building reliable systems.',
           'March 2019 - August 2022','Application Programmer IV - AI/ML Example Research | Hyderabad, India',
           'I have worked with Python and data platforms.']
    return fixture(texts,{'experience':list(range(len(texts)))},[])


def test_dated_headers_win_over_first_person_responsibility_prose():
    elements,sections=job_fixture();before=deepcopy(sections.model_dump())
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert [(j.company,j.role) for j in out.data.experience]==[
        ('Example Systems Limited','Lead Data Scientist'),('Example Research','Application Programmer IV - AI/ML')]
    assert elements[3].text in out.data.experience[0].responsibilities
    assert elements[6].text in out.data.experience[1].responsibilities
    assert sections.model_dump()==before


def test_three_date_first_qualifications_are_three_populated_records():
    texts=['EDUCATION','May 2022','PG Certificate Program | Visual Design (UX) Example Institute of Technology',
           'September 2012','Bachelor of Science - BS | Computing','Example University',
           'December 1996','INFORMATION TECHNOLOGY | Digital Publishing','Example Institute of Publishing']
    elements,sections=fixture(texts,{'education':list(range(len(texts)))},[])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert len(out.data.education)==3
    assert [e.graduation_year for e in out.data.education]==['May 2022','September 2012','December 1996']
    assert all(e.degree and e.institution for e in out.data.education)
    assert out.data.education[0].degree=='PG Certificate Program'
    assert out.data.education[2].degree=='INFORMATION TECHNOLOGY'


def test_visible_wrapped_urls_are_cited_before_safe_normalization():
    texts=['Example Person','https://www.linkedin.com  /in/example-', 'a123456/',
           'https://www.example.i o/person','SKILLS','GitHub Actions']
    elements,sections=fixture(texts,{'personal_information':[0,1],'skills':[3,4,5]},[2])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    std,meta,status,warnings=standardize_resume_data(out.data)
    assert std.contact.linkedin_url=='https://www.linkedin.com/in/example-a123456/'
    assert std.contact.portfolio_url=='https://www.example.io/person'
    assert std.contact.github_url is None
    assert sum(w.warning_type=='url_whitespace_repaired' and w.applied for w in warnings)==2
    attrs={a.name:a for s in out.section_schemas if s.category=='personal_information' for r in s.records for a in r.attributes}
    assert attrs['linkedin_url'].items and attrs['portfolio_url'].items


@pytest.mark.parametrize('value',['https://example.com/a b','https://bad example.com/person','Portfolio'])
def test_prose_spaces_and_bare_labels_are_not_guessed_as_urls(value):
    assert normalize_url(value,'portfolio_url')[0] is None


def test_embedded_label_link_is_preserved_as_explicit_relationship_evidence():
    from local_api.services.text_extraction_service import extract_text
    doc=Document();p=doc.add_paragraph();link=OxmlElement('w:hyperlink')
    from docx.oxml.ns import qn
    rid=p.part.relate_to('https://example.org/person',RT.HYPERLINK,is_external=True)
    link.set(qn('r:id'),rid);run=OxmlElement('w:r');t=OxmlElement('w:t');t.text='Portfolio';run.append(t);link.append(run);p._p.append(link)
    data=BytesIO();doc.save(data)
    ex=extract_text(data.getvalue(),'example.docx')
    assert any(e.text=='https://example.org/person' and e.metadata.get('word_hyperlink_evidence') for e in ex.elements)


def test_review_cannot_replace_source_headers_with_narrative_identities():
    elements,sections=job_fixture();req=SchemaMappingRequest(elements=elements,sections=sections);local=map_schema(req)
    payload=local_section_payload(local,{'experience'})
    record=payload[0]['records'][0]
    value='With a strong background in application design'
    record['fields']['company']=[{'value':value,'evidence':citations(value,sections.sections[0].blocks)}]
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=lambda *_:json.dumps({'sections':payload}))
    assert out.meta['field_review']['status']=='complete'
    assert out.data.experience[0].company=='Example Systems Limited'


def test_word_bold_project_names_are_boundaries_but_bold_actions_are_not():
    from local_api.services.resume_structure import entry_groups
    elements,sections=fixture(['First Portal','Built a reliable service.','Second Portal','Designed another service.'],{'projects':[0,1,2,3]},[])
    for e in elements:e.metadata['word_source_runs']=[{'start':0,'end':len(e.text),'bold':True}]
    groups=entry_groups(sections.sections[0].blocks,'projects',elements)
    assert [g['block_indices'] for g in groups]==[[0,1],[2,3]]


def test_first_person_prose_is_rejected_when_no_real_source_header_supports_employer():
    from local_api.services.llm_schema_mapping import parse_review
    elements,sections=fixture(['With an extensive background in application development, I specialize in software design.'],{'experience':[0]},[])
    from local_api.schemas.subschema_spec import SUBSCHEMAS
    block=sections.sections[0].blocks[0];sid=f'e0:0:{len(block.text)}'
    fields={name:[] for name in SUBSCHEMAS['experience']}
    fields['company']=[{'value':'With an extensive background in application development','evidence':[{'source_id':sid,'quote':block.text}]}]
    payload={'sections':[{'category':'experience','records':[{'record_id':'fake','source_ids':[sid],'fields':fields,'missing':{name:'unmapped' for name,value in fields.items() if not value}}]}]}
    with pytest.raises(ValueError):parse_review(json.dumps(payload),sections)


def test_linked_portfolio_label_does_not_become_a_body_section_boundary():
    elements,sections=fixture(['Example Person','Portfolio','https://example.org/person','EDUCATION','Degree: BSc'],
                              {'personal_information':[0],'projects':[1,2],'education':[3,4]},[])
    elements[1].metadata['word_source_hyperlinks']=[{'target':'https://example.org/person','display_text':'Portfolio'}]
    out=map_schema(SchemaMappingRequest(elements=elements,sections=sections))
    assert out.data.contact.portfolio_url=='https://example.org/person'
