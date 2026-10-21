"""Minimized source-backed regression cases; all provider calls are mocked."""
import json
from copy import deepcopy
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock,SectionRequest,SectionResponse
from local_api.services.llm_section_review import parse_decisions,review_sections,ReviewSettings,ReviewError,source_ledger,assert_coverage
from local_api.services.review_validation import allowed_split_offsets
from local_api.services.resume_sections import build_sections
from local_api.services.review_resolution import document_scope


def local(texts,cats=None):
    es=[ExtractedElement(type='NarrativeText',text=t,page_number=1,metadata={}) for t in texts]
    bs=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='main',assignment='semantic',reason='source') for i,t in enumerate(texts)]
    grouped={}
    for b,c in zip(bs,cats or ['skills']*len(bs)):grouped.setdefault(c,[]).append(b)
    return SectionRequest(elements=es),SectionResponse(status='provisional',sections=build_sections(grouped,es),needs_review=[],metadata={},warnings=[])


def rejected(pairs,lengths,texts=None,cuts=None):
    with pytest.raises(ReviewError) as exc:
        parse_decisions(json.dumps({'assignments':pairs}),len(lengths),{'skills','education','certifications'},lengths,texts,cuts)
    assert str(exc.value)=='invalid_assignments'
    return exc.value.details


def test_jewel_out_of_range_still_rejected():
    errors=rejected([['u0','skills',0,17],['u0','skills',17,24]],{'u0':22})
    assert any(e['kind']=='offset_out_of_range' for e in errors)


def test_jewel_physical_join_requires_actual_pdf_line_evidence():
    text='WORK EXPERIENCESDeveloper'
    req,response=local([text]);b=source_ledger(response)[0][0]
    req.elements[0].metadata={'pdf_source_lines':[{'start':0,'end':16,'bbox':[.1,.1,.5,.12]},{'start':16,'end':len(text),'bbox':[.1,.13,.5,.15]}]}
    cuts={'u0':allowed_split_offsets(b,req.elements)}
    assert 16 in cuts['u0']
    parse_decisions(json.dumps({'assignments':[['u0','education',0,16],['u0','skills',16,len(text)]]}),1,{'skills','education'},{'u0':len(text)},{'u0':text},cuts)
    assert any(e['kind']=='unsupported_word_boundary' for e in rejected([['u0','skills',0,16],['u0','skills',16,len(text)]],{'u0':len(text)},{'u0':text}))


def test_keerthi_missing_span_and_wrong_tuple_order_are_explicit():
    errors=rejected([['u0','skills']],{'u0':20,'u1':8})
    assert {'kind':'missing_span','id':'u1','required_length':8} in errors
    errors=rejected([['u0',0,20,'skills']],{'u0':20})
    assert errors[0]['kind']=='invalid_category_or_tuple_order'


@pytest.mark.parametrize('cut',[13,19])
def test_pradyum_combined_heading_interior_cut_rejected(cut):
    text='EDUCATION & CERTIFICATION '
    errors=rejected([['u0','education',0,cut],['u0','certifications',cut,len(text)]],{'u0':len(text)},{'u0':text})
    assert any(e['kind']=='unsupported_word_boundary' for e in errors)
    parse_decisions(json.dumps({'assignments':[['u0','education',0,12],['u0','certifications',12,len(text)]]}),1,{'education','certifications'},{'u0':len(text)},{'u0':text})


def test_rasool_absolute_offsets_and_zero_length_segment_rejected():
    assert any(e['kind']=='offset_out_of_range' for e in rejected([['u0','skills',42,135]],{'u0':93}))
    assert any(e['kind']=='empty_segment' for e in rejected([['u0','skills',0,10],['u0','skills',10,10]],{'u0':10}))


def test_retry_contains_concrete_failure_and_local_retention_is_atomic():
    req,response=local(['Python','SQL']);before=response.model_dump();messages=[]
    def provider(settings,prompt):
        messages.append(deepcopy(prompt));return '{"assignments":[["u0","skills"]]}'
    final=review_sections(req,response,settings=ReviewSettings(enabled=True,api_key='mock',model='mock'),transport=provider)
    assert len(messages)==2 and 'missing_span' in messages[1][-1]['content']
    assert any(m['role']=='assistant' for m in messages[1])
    assert final.metadata['llm_review']['status']=='failed'
    assert final.sections==response.sections and response.model_dump()==before
    assert final.metadata['quality_assessment']['review_validity']['structurally_valid'] is False


def test_unique_pdf_glyph_repair_preserves_map_and_rejects_ambiguity():
    from local_api.services.pdf_glyph_recovery import recover_pdf_glyphs
    es=[{'text':'Objec\x00ve: expertise','metadata':{'page_number':1}}];original=deepcopy(es)
    out=recover_pdf_glyphs(b'pdf',es,['Objective: expertise'])
    assert es==original and out[0]['text']=='Objective: expertise'
    mapping=out[0]['metadata']['pdf_glyph_recovery']['replacements'][0]
    assert mapping=={'original_start':5,'original_end':6,'new_start':5,'new_end':7,'source_replacement':'ti'}
    assert recover_pdf_glyphs(b'pdf',es,['Objective: expertise Objective: expertise'])[0]['text']==es[0]['text']


def test_recovery_does_not_reintroduce_damaged_glyph_source_lines():
    from local_api.services.pdf_source_recovery import recover_pdf_source
    result,audit=recover_pdf_source(b'pdf',[{'text':'Objective','metadata':{'page_number':1}}],lines=[{'text':'Objec\x00ve','page':1,'bbox':[0,.2,1,.3]}])
    assert len(result)==1 and audit['ambiguous_source_lines'][0]['reason']=='damaged_pdf_character_layer'


@pytest.mark.parametrize('texts,kind',[
 (['Website Critique Assignment Submitted by: Example','Website Reviewed: https://example.com'],'website_critique'),
 (['Hiring Manager: Example','Open Position: 4','At least 4+ year experience is mandatory.'],'job_description'),
 (['I worked with a Hiring Manager to improve our platform.','Open position reporting was my responsibility.'],'candidate_or_unknown'),
])
def test_scope_is_document_purpose_not_single_keyword(texts,kind):
    req,_=local(texts)
    assert document_scope(req.elements)['kind']==kind


def test_expanded_degree_is_one_qualification_family():
    from local_api.services.record_relationships import degree_families
    assert degree_families('Bachelor of Commerce (B.Com)')=={'bachelor'}
    assert degree_families('Master of Business Administration (MBA)')=={'master'}
    assert degree_families('B.C.A.')=={'bachelor'}
    assert degree_families('HSC and SSC')=={'higher_secondary','secondary'}


@pytest.mark.parametrize('start,end,text',[(0,9,'Python'),(-1,6,'Python'),(1,6,'ython')])
def test_source_validator_rejects_invalid_intervals(start,end,text):
    req,res=local(['Python']);res.sections[0].blocks[0]=res.sections[0].blocks[0].model_copy(update={'start':start,'end':end,'text':text})
    with pytest.raises(ReviewError):assert_coverage(req.elements,source_ledger(res))


def test_quality_keeps_semantic_accuracy_and_pdf_fidelity_unverified():
    req,res=local(['Skills Python']);final=review_sections(req,res,settings=ReviewSettings(enabled=False))
    q=final.metadata['quality_assessment']
    assert q['assignment_correctness']['verification']=='unverified'
    assert q['source_fidelity']['original_pdf_word_accuracy']=='unverified'
    assert q['review_validity']['structurally_valid'] is False


def test_short_degree_and_dated_nonbold_employment_headers_are_distinct_records():
    from local_api.services.resume_structure import entry_groups
    texts=['Worked as Gen AI Engineer at Example Technologies from Nov 2023 to Present.',
           'Worked as Senior Consultant at Example Services from Aug 2022 to Oct 2023.']
    req,res=local(texts,['experience']*2);blocks=res.sections[0].blocks
    for i,b in enumerate(blocks):
        b.reviewed_by_llm=True
        req.elements[i].metadata={'pdf_source_lines':[{'start':0,'end':len(texts[i]),'bbox':[.1,.1+i*.2,.9,.12+i*.2],'bold':False}]}
    assert [e['block_indices'] for e in entry_groups(blocks,'experience',req.elements)]==[[0],[1]]


def test_true_same_region_duplicate_and_legitimate_printed_repetition():
    from local_api.services.pdf_source_recovery import recover_pdf_source
    def source(y):return {'text':'Keeping the applications up 24/7 and resolving incidents','metadata':{'page_number':3,'coordinates':{'points':[[10,y],[90,y+10]],'layout_width':100,'layout_height':100}}}
    first=source(10);same=deepcopy(first);printed_again=source(50)
    result,audit=recover_pdf_source(b'pdf',[first,same,printed_again],lines=[])
    assert len(result)==2 and len(audit['events'])==1
    assert len(result[0]['metadata']['pdf_same_region_duplicates'])==1


def test_missing_physical_label_is_not_blocked_by_similar_word_elsewhere():
    from local_api.services.pdf_source_recovery import recover_pdf_source
    original=[{'text':'core','metadata':{'page_number':4,'pdf_source_lines':[{'start':0,'end':4,'bbox':[.1,.1,.3,.12]}]}}]
    result,audit=recover_pdf_source(b'pdf',original,lines=[{'text':'Score','page':4,'bbox':[.7,.4,.8,.42]}])
    assert [e['text'] for e in result]==['core','Score']


def test_field_references_cannot_point_to_another_entry():
    from scripts.batch_check_resumes import validate_result
    req,res=local(['Python'])
    from local_api.schemas.sections import SectionEntry
    res.sections[0].entries=[SectionEntry(entry_id='test-1',block_indices=[0],lane='main',boundary_reason='test',fields={'dates':[1]})]
    assert 'invalid_field_entry_reference' in validate_result(req.elements,res)


def test_empty_ocr_reference_is_not_pdf_accuracy_proof():
    req,res=local(['Recognized OCR text']);req.elements[0].metadata['ocr_verification_required']=True
    final=review_sections(req,res,settings=ReviewSettings(enabled=False))
    assert final.metadata['quality_assessment']['source_fidelity']['ocr_reference_needed']
    assert final.metadata['quality_assessment']['source_fidelity']['original_pdf_word_accuracy']=='unverified'


def test_failed_followup_retains_valid_first_review_and_records_precise_cause():
    req,res=local(['Python']);responses=iter(['{"assignments":[["u0","needs_review"]]}','{"assignments":[["u0","skills",0,99]]}'])
    final=review_sections(req,res,settings=ReviewSettings(enabled=True,api_key='mock',model='mock'),transport=lambda *a:next(responses))
    state=final.metadata['llm_review']
    assert state['status']=='complete' and state['recovery_status']=='failed'
    assert final.needs_review[0].text=='Python'
    assert state['recovery_validation_failures'][0]['details'][0]['kind']=='offset_out_of_range'


def test_shared_accomplishments_are_not_invented_as_last_employer_duties():
    from local_api.services.resume_structure import entry_groups
    texts=['Analyst, Alpha Systems | 2018 - 2020','Analyst, Beta Systems | 2020 - 2024','Accomplishments:','Built reusable processes across several companies.']
    req,res=local(texts,['experience']*4);bs=res.sections[0].blocks
    for i,b in enumerate(bs):
        b.reviewed_by_llm=True;req.elements[i].metadata={'pdf_source_lines':[{'start':0,'end':len(texts[i]),'bbox':[.1,.1+i*.1,.9,.12+i*.1],'bold':i<2}]}
    assert [g['block_indices'] for g in entry_groups(bs,'experience',req.elements)]==[[0],[1]]
    rebuilt=build_sections({'experience':bs},req.elements)[0]
    assert [g.block_indices for g in rebuilt.readable_blocks][-1]==[2,3]
