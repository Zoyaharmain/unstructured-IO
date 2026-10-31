"""Local recovery must improve actual mappings without widening evidence scope."""
from copy import deepcopy
import json
import re
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, SectionResponse, SectionEntry
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import build_sections, SectionEngine
from local_api.services.local_completion import recover_local_content
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.llm_section_review import ReviewSettings
from local_api.schemas.subschema_spec import SUBSCHEMAS


def fixture(texts, assigned, pending, lanes=None):
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in texts]
    def block(i):
        return SectionBlock(source_element_index=i,start=0,end=len(texts[i]),text=texts[i],page_number=1,
            lane=lanes[i] if lanes else 'main',assignment='semantic',reason='low semantic separation')
    sections = build_sections({category:[block(i) for i in indices] for category,indices in assigned.items()}, elements)
    result = SectionResponse(status='needs_review',sections=sections,needs_review=[block(i) for i in pending],metadata={},warnings=[])
    return elements, result


def test_duties_recovered_into_the_original_job_and_mapped_not_just_retained():
    elements, result = fixture(['Engineer | Example Ltd | Jan 2020 - Dec 2021',
        'Built the original service.', 'Integrate internal platforms with external systems using validated source APIs.'],
        {'experience':[0,1]},[2])
    before=deepcopy(result.model_dump())
    original_id=result.sections[0].entries[0].entry_id
    repaired=recover_local_content(result,elements)
    assert not repaired.needs_review
    assert repaired.sections[0].entries[0].entry_id == original_id
    assert not validate_result(elements,repaired)
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert elements[2].text in mapped.data.experience[0].responsibilities
    assert result.model_dump()==before
    assert mapped.meta['reviewed_sections']


def test_separate_column_duties_are_not_attached_to_an_unrelated_job():
    elements,result=fixture(['Engineer | Example Ltd | Jan 2020 - Dec 2021','Built unrelated services for a separate project.'],
        {'experience':[0]},[1],['left','right'])
    assert recover_local_content(result,elements) is result


def test_an_intervening_uncertain_job_header_prevents_ownership_guess():
    elements,result=fixture(['Engineer | Example Ltd | Jan 2020 - Dec 2021',
        'Analyst | Another Ltd | Jan 2022 - Dec 2023','Managed a separate business operation.'],{'experience':[0]},[1,2])
    repaired=recover_local_content(result,elements)
    assert any(b.source_element_index==2 for b in repaired.needs_review)


@pytest.mark.parametrize('text,category,field,value',[
    ('Project Name: Atlas','projects','name','Atlas'),
    ('Certification: Cloud Credential','certifications','name','Cloud Credential'),
    ('University: Example University','education','institution','Example University'),
])
def test_explicit_unassigned_labels_reach_real_schema_fields(text,category,field,value):
    elements,result=fixture([text],{},[0])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert getattr(getattr(mapped.data,category)[0],field)==value
    assert not mapped.meta['needs_review']


def test_inline_bullet_segmentation_keeps_complete_items_and_exact_text():
    class Encoder:
        def tokenizer(self,text,**kwargs):
            return {'offset_mapping':[(m.start(),m.end()) for m in re.finditer(r'\S+',text)]}
    engine=SectionEngine.__new__(SectionEngine);engine.encoder=Encoder()
    text='Built APIs using date range 2020-2021. • Maintained end-to-end services. • Reduced cost by 30%.'
    elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={})]
    units,_=engine.units(elements)
    assert ''.join(u.text for u in units)==text
    assert len(units)==3
    assert '2020-2021' in units[0].text and 'end-to-end' in units[1].text


def test_certificate_detail_rows_attach_to_the_correct_card():
    texts=['Certifications','Certification: Credential A','Issued By: Org A','Credential ID: A-123',
           'Certification: Credential B','Issued By: Org B','Expiry Date: 2027-01']
    elements,result=fixture(texts,{'certifications':list(range(len(texts)))},[])
    assert len(result.sections[0].entries)==2
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert [(c.name,c.issuer) for c in mapped.data.certifications]==[('Credential A','Org A'),('Credential B','Org B')]
    assert mapped.data.certifications[0].credential_id=='A-123'
    assert mapped.data.certifications[1].expiry_date=='2027-01'


def test_completeness_checks_actual_values_not_broad_evidence_quotes():
    elements,result=fixture(['Award Name: Prize; unassigned original outcome of 40%.'],{'awards':[0]},[])
    from local_api.services.mapping_completeness import mapping_completeness
    from local_api.schemas.subschemas import SectionSchema,SubschemaRecord,Attribute,AttributeValue,SourceQuote
    sid=f'e0:0:{len(elements[0].text)}'
    hierarchy=[SectionSchema(category='awards',label='Awards',records=[SubschemaRecord(record_id='award-1',source_ids=[sid],
        attributes=[Attribute(name=k,status='mapped' if k=='name' else 'not_stated',items=[AttributeValue(value='Prize',
            evidence=[SourceQuote(source_id=sid,quote=elements[0].text)])] if k=='name' else []) for k in SUBSCHEMAS['awards']])])]
    ledger=mapping_completeness(elements,result,hierarchy)
    assert any('40%' in item['text'] for item in ledger['unmapped'])
    assert ledger['all_meaningful_content_accounted_for'] and not ledger['all_meaningful_content_mapped']


def test_direct_field_review_first_classifies_unassigned_original_text():
    elements,result=fixture(['Won the regional innovation prize.'],{},[0])
    req=SchemaMappingRequest(elements=elements,sections=result)
    calls=[]
    def provider(settings,messages):
        payload=json.loads(messages[1]['content']);calls.append(payload)
        if 'spans' in payload:
            assert payload['source_elements'][0]['text']==elements[0].text
            return json.dumps({'assignments':[[s['id'],'awards'] for s in payload['spans']]})
        sid=f'e0:0:{len(elements[0].text)}'
        fields={k:[] for k in SUBSCHEMAS['awards']}
        fields['name']=[{'value':elements[0].text,'evidence':[{'source_id':sid,'quote':elements[0].text}]}]
        return json.dumps({'sections':[{'category':'awards','records':[{'record_id':'award-1','source_ids':[sid],
            'fields':fields,'missing':{k:'not_stated' for k,v in fields.items() if not v}}]}]})
    out=map_with_field_review(req,settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=provider)
    assert len(calls)==2
    assert out.meta['field_review']['status']=='complete'
    assert out.section_schemas[0].records[0].attributes[0].items[0].value==elements[0].text
    assert out.meta['unassigned_section_review']['provider_calls']==1
    assert out.meta['provider_call_summary']['total_this_mapping_request']==2
    assert out.meta['completeness_check']['all_meaningful_content_mapped']


def test_unclassifiable_source_retains_an_explicit_completeness_reason():
    elements,result=fixture(['Unclear original fragment without an established meaning.'],{},[0])
    out=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    ledger=out.meta['completeness_check']
    assert ledger['unassigned_source_fragments']==1
    assert ledger['unmapped'][0]['reason']=='section_unassigned'
    assert ledger['unmapped'][0]['text']==elements[0].text


def test_labelled_responsibility_does_not_drop_first_last_or_split_prose_commas():
    from test_record_subfields import request
    req=request('experience', [['Employer: Example Ltd','Role: Engineer',
        'Built the first service.', 'Responsibilities: Managed APIs, releases, and deployments; maintained reliability.',
        'Delivered the final migration.']])
    out=map_schema(req)
    assert out.data.experience[0].responsibilities == ['Built the first service.',
        'Managed APIs, releases, and deployments; maintained reliability.', 'Delivered the final migration.']


def test_project_description_does_not_duplicate_identity_and_keeps_continuation():
    from test_record_subfields import request
    req=request('projects', [['Project Name: Atlas','Description: Built a search service.',
        'Reduced query latency by 30%.','Tech Stack: Python, SQL']])
    out=map_schema(req)
    project=out.data.projects[0]
    assert project.name=='Atlas'
    assert project.description=='Built a search service.\nReduced query latency by 30%.'
    assert project.technologies==['Python','SQL']
    assert not out.meta['completeness_check']['conflicting_field_overlaps']


@pytest.mark.parametrize('start,end',[('2020-09-15','2021-02-20'),('15 Sep 2020','20 Feb 2021'),('09/2020','02/2021')])
def test_complete_source_date_ranges_reach_the_job_fields(start,end):
    from test_record_subfields import request
    out=map_schema(request('experience', [['Employer: Example Ltd','Role: Engineer',f'Period: {start} - {end}']]))
    assert out.data.experience[0].start_date==start
    assert out.data.experience[0].end_date==end


def test_icon_prefixed_contacts_and_unheaded_career_summary_are_classified():
    from local_api.services.preamble_recovery import recover_summary_preamble
    texts=['Experienced software engineer with six years building reliable services.',
        'Delivered scalable platforms and improved availability across multiple regions.',
        '\ue001 person@example.org','Work Experience','Engineer | Example Ltd | Jan 2020 - Dec 2021']
    elements,result=fixture(texts,{'experience':[3,4]},[0,1,2])
    before=deepcopy(result.model_dump())
    repaired=recover_summary_preamble(result,elements)
    assert not repaired.needs_review
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert mapped.data.contact.email=='person@example.org'
    assert mapped.data.summary=='\n'.join(texts[:2])
    assert result.model_dump()==before
    assert not validate_result(elements,repaired)


def test_prominent_name_fragments_are_classified_without_losing_the_surname():
    from local_api.services.contact_sections import recover_contact_sections
    text='Jane Doe Senior Engineer'
    elements=[ExtractedElement(type='Title',text=text,page_number=1,metadata={'pdf_source_lines':[
        {'start':0,'end':9,'font_size':24,'bbox':[.1,.04,.4,.08]},
        {'start':9,'end':len(text),'font_size':12,'bbox':[.1,.09,.5,.12]}]}),
        ExtractedElement(type='NarrativeText',text='person@example.org',page_number=1,metadata={'pdf_source_lines':[
        {'start':0,'end':18,'font_size':10,'bbox':[.1,.13,.5,.15]}]})]
    def block(i,start,end):return SectionBlock(source_element_index=i,start=start,end=end,text=elements[i].text[start:end],
        page_number=1,lane='left',assignment='needs_review',reason='preamble uncertainty')
    result=SectionResponse(status='needs_review',sections=[],needs_review=[block(0,0,5),block(0,5,9),block(0,9,len(text)),
        block(1,0,len(elements[1].text))],metadata={},warnings=[])
    repaired=recover_contact_sections(result,elements)
    assert not repaired.needs_review
    out=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert out.data.contact.full_name=='Jane Doe'


def test_long_paragraph_prefers_whole_sentences_within_encoder_windows():
    class Encoder:
        def tokenizer(self,text,**kwargs):
            return {'offset_mapping':[(m.start(),m.end()) for m in re.finditer(r'\S+',text)]}
    engine=SectionEngine.__new__(SectionEngine);engine.encoder=Encoder()
    sentences=['Built '+' '.join(['reliable']*148)+' services.',
               'Managed '+' '.join(['scalable']*148)+' platforms.',
               'Delivered '+' '.join(['secure']*148)+' applications.']
    text=' '.join(sentences)
    units,_=engine.units([ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={})])
    assert [u.text.strip() for u in units]==sentences
    assert ''.join(u.text for u in units)==text


def test_unassigned_leading_duties_in_a_uniquely_owned_paragraph_get_a_section_not_an_invented_employer():
    text='Design and implement secure services. Integrate systems with enterprise tools.'
    elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={})]
    cut=text.index('enterprise')
    def block(start,end,assignment):return SectionBlock(source_element_index=0,start=start,end=end,text=text[start:end],
        page_number=1,lane='wide',assignment=assignment,reason='existing source heading context')
    sections=build_sections({'experience':[block(cut,len(text),'heading_context')]},elements)
    # No employer/role has been established. Classification must not invent one.
    for s in sections:s.entries=[]
    result=SectionResponse(status='needs_review',sections=sections,needs_review=[block(0,cut,'needs_review')],metadata={},warnings=[])
    recovered=recover_local_content(result,elements)
    assert not recovered.needs_review
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=recovered))
    assert mapped.data.experience==[]
    assert mapped.meta['completeness_check']['meaningful_unmapped_fragments']


def test_field_review_can_correct_an_assigned_but_misclassified_block():
    elements,result=fixture(['Technical Skills: Python, SQL'],{'summary':[0]},[])
    calls=[]
    def provider(settings,messages):
        payload=json.loads(messages[1]['content']);calls.append(payload)
        if 'spans' in payload:
            assert payload['spans'][0]['current_category']=='summary'
            return json.dumps({'assignments':[['u0','skills']]})
        sid=f'e0:0:{len(elements[0].text)}'
        fields={k:[] for k in SUBSCHEMAS['skills']}
        fields['technical_skills']=[{'value':v,'evidence':[{'source_id':sid,'quote':v}]} for v in ('Python','SQL')]
        return json.dumps({'sections':[{'category':'skills','records':[{'record_id':'skills','source_ids':[sid],
            'fields':fields,'missing':{k:'not_stated' for k,v in fields.items() if not v}}]}]})
    out=map_with_field_review(SchemaMappingRequest(elements=elements,sections=result),
        settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=provider)
    assert len(calls)==2
    assert out.data.skills.technical_skills==['Python','SQL']
    assert out.data.summary is None
    assert out.meta['classification_preflight']['suspected_misclassifications']==1


def test_page_artifacts_do_not_become_unresolved_candidate_information():
    from local_api.services.standardization.mapping import mapping_input
    from local_api.services.schema_diagnostics import mapping_result
    elements,result=fixture(['Full Name: Example Person','Email: person@example.org','Phone: +1 234 567 8901','Page 1 of 1'],
        {'personal_information':[0,1,2]},[3])
    elements[3].type='Footer'
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert mapped.meta['needs_review']==[]
    assert mapped.meta['layout_artifacts']
    assert not mapping_input(mapped)['additional_sections']
    assert mapped.meta['completeness_check']['all_meaningful_content_mapped']
    assert not mapping_result(mapped)['requires_review']


def test_skill_casing_does_not_create_false_source_omissions():
    elements,result=fixture(['Technical Skills: python, sql'],{'skills':[0]},[])
    mapped=map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert mapped.meta['completeness_check']['all_meaningful_content_mapped']


def test_preflight_and_field_mapping_share_one_request_budget():
    elements,result=fixture(['Won the regional innovation prize.'],{},[0]);calls=[]
    def provider(settings,messages):
        payload=json.loads(messages[1]['content']);calls.append(payload)
        assert 'spans' in payload  # No budget remains for a second field call.
        return json.dumps({'assignments':[['u0','awards']]})
    mapped=map_with_field_review(SchemaMappingRequest(elements=elements,sections=result),
        settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0,max_total_requests=1),transport=provider)
    assert len(calls)==1
    assert mapped.meta['provider_call_summary']['total_this_mapping_request']==1
    assert mapped.meta['field_review']['status']=='failed'
    assert mapped.meta['mapping_result']['requires_review']


def test_reviewed_abstentions_do_not_trigger_another_classification_call():
    elements,result=fixture(['Unknown original fragment.'],{},[0])
    result.metadata['llm_review']={'status':'complete','provider_calls':1}
    def forbidden(*args):pytest.fail('Repeated provider call for an already reviewed abstention')
    mapped=map_with_field_review(SchemaMappingRequest(elements=elements,sections=result),
        settings=ReviewSettings(enabled=True,api_key='mock',recovery_attempts=0),transport=forbidden)
    assert mapped.meta['provider_call_summary']['total_this_mapping_request']==0
    assert mapped.meta['field_review']['status']=='not_applicable'
    assert mapped.meta['field_review']['reason']=='no_classified_sections'
    assert mapped.meta['completeness_check']['unassigned_source_fragments']==1


def test_explicit_freelance_role_can_anchor_duties_without_an_invented_employer():
    from test_record_subfields import request
    mapped=map_schema(request('experience',[['Role: Freelance Engineer','Engagement Type: Freelance',
        'Built a production service for clients.','Managed releases and deployments.']]))
    assert len(mapped.data.experience)==1
    assert mapped.data.experience[0].company==''
    assert mapped.data.experience[0].role=='Freelance Engineer'
    assert mapped.data.experience[0].responsibilities==['Built a production service for clients.','Managed releases and deployments.']


def test_target_role_section_maps_four_spans_to_preferences_with_source_evidence():
    texts = ['TARGET ROLES',
             'Senior Program Manager | Business Transformation Manager | ',
             'Continuous Improvement Manager | Assistant Director – Operations — India | UAE & ',
             'Middle East | UK | Europe | Remote / Global']
    elements, result = fixture(texts, {}, [0,1,2,3], ['left','wide','wide','left'])
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=result))
    assert not mapped.data.experience and not mapped.data.education
    assert mapped.data.professional_title is None
    assert mapped.data.contact.location is None
    assert mapped.data.contact.target_role == texts[1] + '\n' + texts[2].split(' — ')[0]
    assert mapped.data.contact.work_preferences == 'India | UAE & \n' + texts[3]
    personal = next(s for s in mapped.section_schemas if s.category == 'personal_information')
    attrs = {a.name:a for a in personal.records[0].attributes}
    assert attrs['target_role'].items and attrs['work_preferences'].items
    assert not mapped.meta['needs_review']
    assert not validate_result(elements, type(result).model_validate(mapped.meta['reviewed_sections']))


def test_target_section_reclassifies_wrong_education_without_touching_real_degree():
    elements, result = fixture(['BSc | Example University | 2018', 'TARGET ROLES',
                               'Engineering Manager | Program Manager — Remote / Global'],
                              {'education':[0,1,2]}, [], ['left','left','wide'])
    repaired = recover_local_content(result,elements)
    assert [b.source_element_index for s in repaired.sections if s.category == 'education' for b in s.blocks] == [0]
    assert [b.source_element_index for s in repaired.sections if s.category == 'personal_information' for b in s.blocks] == [1,2]
    assert not validate_result(elements,repaired)


def test_target_preference_context_stops_at_next_heading():
    elements,result = fixture(['DESIRED POSITIONS','Engineering Manager','WORK EXPERIENCE',
                              'Engineer | Example Ltd | Jan 2020 - Dec 2021'],{},[0,1,2,3])
    repaired = recover_local_content(result,elements)
    personal = next(s for s in repaired.sections if s.category == 'personal_information')
    assert [b.source_element_index for b in personal.blocks] == [0,1]


def test_small_repeated_and_singleton_sections_share_one_grounded_review_call():
    from local_api.schemas.mapping import ReviewedSchemaMappingRequest
    from local_api.services.llm_schema_mapping import local_section_payload
    elements, sections = fixture(['Example Person', 'Email: person@example.org',
        'Engineer | Example Ltd | Jan 2020 - Dec 2021', 'Built reliable services.'],
        {'personal_information':[0,1], 'experience':[2,3]}, [])
    sections.metadata['llm_review']={'status':'complete'}
    request=ReviewedSchemaMappingRequest(elements=elements,sections=sections,review_fields=True)
    local=map_schema(request)
    calls=[]
    def transport(settings,messages):
        document=json.loads(messages[-1]['content'])
        categories={s['category'] for s in document['sections']}
        calls.append(categories)
        return json.dumps({'sections':local_section_payload(local,categories)})
    mapped=map_with_field_review(request, settings=ReviewSettings(enabled=True,api_key='test',recovery_attempts=0),transport=transport)
    assert calls == [{'personal_information','experience'}]
    assert mapped.meta['field_review']['status']=='complete'
    assert mapped.meta['field_review']['provider_calls']==1
    assert mapped.data.experience[0].company=='Example Ltd'


def test_target_scope_does_not_make_open_to_location_into_residence():
    elements, result = fixture(['Example Person', 'Open to: India | Remote / Global',
                               'TARGET ROLES', 'Program Manager — India | Remote / Global'],
                               {'personal_information':[0,1]}, [2,3])
    mapped = map_schema(SchemaMappingRequest(elements=elements,sections=result))
    assert mapped.data.contact.location is None
    assert mapped.data.contact.work_preferences == 'India | Remote / Global'


def test_field_review_cannot_truncate_explicit_target_list_to_first_title():
    from local_api.schemas.mapping import ReviewedSchemaMappingRequest
    from local_api.services.llm_schema_mapping import local_section_payload
    from local_api.services.source_fragments import citations
    texts=['Example Person','TARGET ROLES','Senior Program Manager | Business Transformation Manager | ',
           'Operations Transformation Manager | Change Management Lead | Continuous Improvement Manager | ',
           'Governance, Risk & Controls Manager | AVP / Assistant Director – Operations — India | UAE & ',
           'Middle East | UK | Europe | Remote / Global']
    elements,sections=fixture(texts,{'personal_information':[0]},[1,2,3,4,5])
    request=ReviewedSchemaMappingRequest(elements=elements,sections=sections,review_fields=True)
    local=map_schema(request)
    original=type(sections).model_validate(local.meta['reviewed_sections'])
    request=request.model_copy(update={'sections':original})
    expected=local.data.contact.target_role
    def transport(settings,messages):
        payload=local_section_payload(local,{'personal_information'})
        fields=payload[0]['records'][0]['fields']
        fields['target_role']=[{'value':'Senior Program Manager',
            'evidence':citations('Senior Program Manager',original.sections[0].blocks)}]
        return json.dumps({'sections':payload})
    mapped=map_with_field_review(request,settings=ReviewSettings(enabled=True,api_key='test',recovery_attempts=0),transport=transport)
    assert mapped.meta['field_review']['status']=='complete'
    assert mapped.data.contact.target_role==expected
    assert 'Business Transformation Manager' in expected and 'AVP / Assistant Director' in expected
    attrs={a.name:a for s in mapped.section_schemas for r in s.records for a in r.attributes}
    assert attrs['target_role'].items[0].value==expected
    assert mapped.data.contact.work_preferences=='India | UAE & \nMiddle East | UK | Europe | Remote / Global'
    assert any(r['code']=='complete_explicit_target_list_recovered' for r in mapped.meta['field_review']['evidence_repairs'])
