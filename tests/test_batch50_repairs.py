"""Offline regressions: source evidence, not filenames or live provider calls."""
import json
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock
from local_api.services.review_resolution import document_scope
from local_api.services.resume_structure import word_safe_cut, entry_groups
from local_api.services.llm_section_review import parse_decisions, assignment_feedback, ReviewError


def elements(texts):
    return [ExtractedElement(type='NarrativeText',text=t,page_number=1,metadata={}) for t in texts]


@pytest.mark.parametrize('text,kind',[
 ('OMS Interview Preparation Guide\nPurpose of this document\nThis guide is meant to organise knowledge.','interview_preparation_guide'),
 ('I need two senior Angular resources as per the below defined JD.\nRequired experience: 8 years.','job_description'),
 ('Interview preparation guide\nI wrote this guide at my previous job.','candidate_or_unknown'),
 ('Senior developer\nI prepared interview questions and trained resources.','candidate_or_unknown'),
])
def test_scope_requires_document_purpose(text,kind):
    assert document_scope(elements([text]))['kind']==kind


@pytest.mark.parametrize('text,cut,expected',[
 ('PGSQL',3,5),('optimized',6,9),('frameworks',9,10),('CERTIFICATIONS',3,14),
 ('ProfessionalSummary',12,12),('TechnicalSkills',9,9),('a word',2,2),
])
def test_mechanical_cut_keeps_words(text,cut,expected):
    assert word_safe_cut(text,cut)==expected


def test_provider_word_split_rejected_without_clamping_offsets():
    response=json.dumps({'assignments':[['u0','skills',0,3],['u0','skills',3,5]]})
    with pytest.raises(ReviewError):
        parse_decisions(response,1,{'skills':'Skills'},{'u0':5},{'u0':'PGSQL'})
    with pytest.raises(ReviewError):
        parse_decisions('{"assignments":[["u0","skills",0,6]]}',1,{'skills':'Skills'},{'u0':5})


def test_retry_reports_missing_ids_and_relative_lengths_without_source_text():
    detail=json.loads(assignment_feedback('{"assignments":[["u0","skills",20,36]]}',{'u0':20,'u1':8}))
    assert detail=={'missing_ids':['u1'],'invalid_ranges':[{'id':'u0','required_length':20}]}


def block(i,text,lane):
    return SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,
                        lane=lane,assignment='llm_reviewed',reason='test',reviewed_by_llm=True)


@pytest.mark.parametrize('category',['experience','education'])
def test_same_row_dates_attach_across_lanes_without_text_changes(category):
    texts=['Example University' if category=='education' else 'Engineer, Example Systems','2020 - 2023']
    source=elements(texts)
    for e in source:e.metadata={'pdf_source_lines':[{'start':0,'end':len(e.text),'bbox':[.1,.2,.7,.22]}]}
    blocks=[block(0,texts[0],'left'),block(1,texts[1],'right')]
    before=[b.model_dump() for b in blocks]
    groups=entry_groups(blocks,category,source)
    assert len(groups)==1 and groups[0]['block_indices']==[0,1]
    assert [b.model_dump() for b in blocks]==before


def test_unlocated_date_is_not_guessed():
    source=elements(['Example University','2020 - 2023'])
    groups=entry_groups([block(0,source[0].text,'left'),block(1,source[1].text,'right')],'education',source)
    assert len(groups)==2


def test_website_critique_is_not_candidate_history():
    assert document_scope(elements(['Detailed Critique on Example website','Upon reviewing the website, I noticed these things.']))['kind']=='website_critique'


def test_pdf_recovery_retains_upstream_and_collapses_only_same_region():
    from copy import deepcopy
    from local_api.services.pdf_source_recovery import recover_pdf_source
    original=[{'text':'Repeated responsibility','metadata':{'page_number':1,'coordinates':{'points':[[0,10],[20,20]],'layout_width':100,'layout_height':100}}}]
    original.append(deepcopy(original[0]));original.append(deepcopy(original[0]))
    original[2]['metadata']['page_number']=2
    before=deepcopy(original)
    result,audit=recover_pdf_source(b'pdf',original,lines=[])
    assert original==before and len(result)==2
    assert len(result[0]['metadata']['pdf_same_region_duplicates'])==1
    assert audit['events'][0]['action']=='collapse_exact_same_region_duplicate'
    assert result[1]['text']==original[2]['text']


def test_pdf_recovery_adds_actual_missing_line_and_keeps_partial_overlap_uncertain():
    from local_api.services.pdf_source_recovery import recover_pdf_source
    original=[{'text':'Existing line','metadata':{'page_number':1}}]
    lines=[{'text':'Existing line','page':1,'bbox':[0,.1,.8,.12]},
           {'text':'Achievements','page':1,'bbox':[0,.2,.8,.22]},
           {'text':'Existing line extra','page':1,'bbox':[0,.3,.8,.32]}]
    result,audit=recover_pdf_source(b'pdf',original,lines=lines)
    assert [e['text'] for e in result]==['Existing line','Achievements']
    assert len(audit['ambiguous_source_lines'])==1
    assert audit['requires_fresh_block_detection'] and not audit['human_verified']


def test_employment_geometry_keeps_each_employer_with_dates_and_responsibilities():
    texts=['Engineer, Alpha Systems','Jan 2020 - Dec 2021','Built service A.',
           'Senior Engineer, Beta Corporation','Jan 2022 - Present','Built service B.']
    source=elements(texts);blocks=[]
    for i,e in enumerate(source):
        top=[.1,.1,.15,.4,.4,.45][i]
        e.metadata={'pdf_source_lines':[{'start':0,'end':len(e.text),'bbox':[.1,top,.8,top+.01],'bold':i in (0,3)}]}
        blocks.append(block(i,e.text,['left','right','wide'][i%3]))
    groups=entry_groups(blocks,'experience',source)
    assert [g['block_indices'] for g in groups]==[[0,1,2],[3,4,5]]


def test_employer_title_on_adjacent_rows_belong_to_one_job():
    texts=['Alpha Systems','Business Analyst','2020 - 2023','Responsibilities include analysis.']
    source=elements(texts);blocks=[]
    for i,e in enumerate(source):
        top=[.1,.12,.12,.15][i]
        e.metadata={'pdf_source_lines':[{'start':0,'end':len(e.text),'bbox':[.1,top,.8,top+.01],'bold':i in (0,1)}]}
        blocks.append(block(i,e.text,'right' if i==2 else 'left'))
    assert [g['block_indices'] for g in entry_groups(blocks,'experience',source)]==[[0,1,2,3]]


def test_education_degree_institution_year_grade_use_source_rows():
    texts=['Example University','Master of Science','2023','CGPA 8.5',
           'Another College','Bachelor of Science','2020','Grade A']
    source=elements(texts);blocks=[]
    for i,e in enumerate(source):
        top=[.1,.12,.1,.14,.3,.32,.3,.34][i]
        e.metadata={'pdf_source_lines':[{'start':0,'end':len(e.text),'bbox':[.1,top,.8,top+.01]}]}
        blocks.append(block(i,e.text,'right' if i in (2,6) else 'left'))
    groups=entry_groups(blocks,'education',source)
    assert [g['block_indices'] for g in groups]==[[0,1,2,3],[4,5,6,7]]


def test_repeated_pdf_title_uses_its_own_source_region():
    from io import BytesIO
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    from local_api.services.pdf_section_layout import annotate_pdf_lines
    writer=PdfWriter();page=writer.add_blank_page(600,800)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 40 700 Td (Analyst) Tj 0 -200 Td (Analyst) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(stream)
    output=BytesIO();writer.write(output)
    raw=[{'text':'Analyst','metadata':{'page_number':1,'coordinates':{'points':[[40,289],[100,303]],'layout_width':600,'layout_height':800}}}]
    annotate_pdf_lines(output.getvalue(),raw)
    hints=raw[0]['metadata']['pdf_source_lines']
    assert len(hints)==1 and .35<hints[0]['bbox'][1]<.40


def test_camel_case_skill_is_not_mistaken_for_joined_heading():
    assert word_safe_cut('PostgreSQL',7)==10
    assert word_safe_cut('TechnicalSkills',9)==9


def test_frontend_readable_groups_use_same_reviewed_records_as_json_entries():
    from local_api.services.resume_sections import build_sections
    texts=['Engineer, Alpha Systems','2020 - 2023','Built a service.']
    source=elements(texts);blocks=[]
    for i,e in enumerate(source):
        top=[.1,.1,.15][i]
        e.metadata={'pdf_source_lines':[{'start':0,'end':len(e.text),'bbox':[.1,top,.8,top+.01],'bold':i==0}]}
        blocks.append(block(i,e.text,'right' if i==1 else 'left'))
    section=build_sections({'experience':blocks},source)[0]
    assert [g.block_indices for g in section.readable_blocks]==[e.block_indices for e in section.entries]
    assert sorted(i for g in section.readable_blocks for i in g.block_indices)==[0,1,2]
