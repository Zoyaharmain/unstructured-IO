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
