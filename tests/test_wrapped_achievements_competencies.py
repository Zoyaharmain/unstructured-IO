from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, ResumeSection, SectionEntry
from local_api.services.resume_structure import entry_groups
from local_api.services.list_fields import skill_candidates


def block(index,start,text,lane):
    return SectionBlock(source_element_index=index,start=start,end=start+len(text),text=text,
                        page_number=1,lane=lane,assignment='heading_context',reason='fixture')


def test_achievement_list_items_keep_wrapped_rows_in_same_record():
    from local_api.services.section_subschemas import build_subschemas
    from local_api.schemas.sections import SectionResponse
    from local_api.vendor.handoff_schema.models import ResumeSchema, ContactInfo
    values=['Delivered a global program across multiple regions.', 'Reduced support incidents through platform improvements.']
    elements=[ExtractedElement(type='ListItem',text=t,page_number=1,metadata={}) for t in values]
    blocks=[]
    for i,text in enumerate(values):
        cut=text.index(' ',20)+1
        blocks.extend([block(i,0,text[:cut],'wide'),block(i,cut,text[cut:],'left')])
    entries=entry_groups(blocks,'awards',elements)
    assert [e['block_indices'] for e in entries]==[[0,1],[2,3]]
    section=ResumeSection(category='awards',label='Awards',blocks=blocks,
                          entries=[SectionEntry.model_validate(e) for e in entries])
    sections=SectionResponse(status='provisional',warnings=[],metadata={},sections=[section],needs_review=[])
    data=ResumeSchema(contact=ContactInfo(full_name='',email='',phone=''))
    mapped=build_subschemas(sections,data,{'candidate_resume':True})
    names=[next(a for a in r.attributes if a.name=='name').items[0] for r in mapped[0].records]
    assert [item.value for item in names]==values
    assert all(len(item.evidence)==2 for item in names)
    assert all(not a.items for r in mapped[0].records for a in r.attributes if a.name in {'issuer','date'})


def test_middle_dot_competencies_are_completed_across_source_lines():
    pieces=['Leadership: Enterprise Program Management · Steering ',
            'Committee Reporting · Benefits Realization']
    blocks=[block(0,0,pieces[0],'wide'),block(0,len(pieces[0]),pieces[1],'left')]
    assert skill_candidates(blocks)==['Enterprise Program Management','Steering Committee Reporting','Benefits Realization']


def test_separate_physical_skill_rows_without_delimiters_are_not_joined():
    pieces=['Working Capital Finance ', 'Supply Chain Finance']
    blocks=[block(0,0,pieces[0],'wide'),block(0,len(pieces[0]),pieces[1],'left')]
    assert skill_candidates(blocks)==['Working Capital Finance','Supply Chain Finance']


def test_inline_heading_with_value_is_not_discarded_as_heading_only():
    from local_api.services.resume_sections import build_sections
    text='Languages: English, Hindi'
    elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={})]
    sections=build_sections({'languages':[block(0,0,text,'left')]},elements)
    assert sections[0].blocks[0].assignment not in {'section_heading','structural_heading'}
    assert sections[0].logical_blocks[0]['text']==text


def test_experience_location_and_action_clauses_do_not_fragment_jobs():
    from local_api.services.record_subfields import employment_header_fields, is_place
    assert is_place('Bengaluru, India')
    assert is_place('Chennai, India')
    assert not is_place('Standard Chartered Global Business Services')
    assert not is_place('Singtel Global India Pvt. Ltd.')
    
    # Action sentences must never be parsed as employer/role
    pmo = 'Established PMO governance, SLA management, risk/dependency tracking, and executive reporting'
    assert employment_header_fields(pmo) == {}
    
    # Multi-component headers with division and location must cleanly resolve
    sc_header = 'IAM Project Manager | Information & Cybersecurity Services | Standard Chartered Global Business Services, Bengaluru, India'
    parsed = employment_header_fields(sc_header)
    assert parsed.get('role') == 'IAM Project Manager'
    assert parsed.get('company') == 'Standard Chartered Global Business Services'
    assert parsed.get('location') == 'Bengaluru, India'


def test_suresh_resume_experience_and_awards_mapping():
    import json
    from pathlib import Path
    from local_api.services.resume_sections import detect_sections
    from local_api.schemas.sections import SectionRequest
    from local_api.services.schema_mapping import map_schema
    from local_api.schemas.mapping import SchemaMappingRequest

    path = Path('reports/suresh-section-review-20261028/after/extraction.json')
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)

    req = SectionRequest(elements=data['elements'])
    res = detect_sections(req)
    mapped = map_schema(SchemaMappingRequest(elements=req.elements, sections=res))

    # Experience must have exactly 3 genuine jobs without fake action/location fragments
    assert len(mapped.data.experience) == 3
    assert 'Standard Chartered' in mapped.data.experience[0].company
    assert mapped.data.experience[0].role == 'IAM Project Manager'
    assert 'Singtel' in mapped.data.experience[1].company
    assert mapped.data.experience[1].role == 'Technical Delivery Manager'
    assert 'Tata Teleservices' in mapped.data.experience[2].company

    # Awards and achievements must contain both Key Achievements (4) and Awards & Recognition (2) = 6 records
    awards_schema = next(s for s in mapped.section_schemas if s.category == 'awards')
    assert len(awards_schema.records) == 6
    names = [r.attributes[0].items[0].value for r in awards_schema.records if r.attributes and r.attributes[0].items]
    assert any('Best Performer Award' in n for n in names)
    assert any('Security Champion Award' in n for n in names)
    assert any('USD 8.7M+' in n for n in names)
    assert any('USD 825K' in n for n in names)
