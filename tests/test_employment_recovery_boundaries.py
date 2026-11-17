"""Recovery cannot undo positive section evidence or consume new sections."""
import pytest
from test_block_completion import fixture
from local_api.services.employment_scope import recover_employment_scope
from local_api.services.record_subfields import employment_header_fields
from local_api.services.source_validation import validate_result


@pytest.mark.parametrize('marker',['➢','➤','•',''])
def test_stated_employment_with_separated_from_date_preserves_employer(marker):
    parsed=employment_header_fields(f'{marker} Working as Platform Developer at Nebula Systems — From March 2023 to Till now')
    assert parsed=={'role':'Platform Developer','company':'Nebula Systems'}


def test_unfamiliar_title_and_education_fragments_terminate_employment_recovery():
    texts=['WORK EXPERIENCE','➢ Working as Platform Developer at Nebula Systems — From March 2023 to Till now',
           'STUDY HISTORY','B.Tech from North Coast College, Harbor — 2022','TECHNICAL SKILLS','Python']
    elements,result=fixture(texts,{'experience':[0,1,2],'education':[3],'skills':[4,5]},[])
    elements[2].type='Title'
    education=next(s for s in result.sections if s.category=='education')
    b=education.blocks[0];cut=b.text.index('Harbor')
    education.blocks=[b.model_copy(update={'end':cut,'text':b.text[:cut],'assignment':'education_boundary'}),
                      b.model_copy(update={'start':cut,'text':b.text[cut:],'assignment':'heading_context'})]
    education.entries[0].block_indices=[0,1]
    education.text=texts[3]
    out=recover_employment_scope(result,elements)
    exp=next(s for s in out.sections if s.category=='experience')
    assert {b.source_element_index for b in exp.blocks if b.assignment=='local_employment_header'}=={1}
    assert all(b.source_element_index!=3 for b in exp.blocks)
    edu=next(s for s in out.sections if s.category=='education')
    assert ''.join(b.text for b in edu.blocks)==texts[3]
    assert len(edu.entries)==1 and edu.entries[0].block_indices==[0,1]
    assert not validate_result(elements,out)


def test_positive_education_is_protected_even_without_a_title_before_it():
    texts=['WORK EXPERIENCE','Working as Engineer at Orbit Ltd From January 2020 to December 2022',
           'B.Tech from North Coast College — 2019','SKILLS','SQL']
    elements,result=fixture(texts,{'experience':[0,1],'education':[2],'skills':[3,4]},[])
    next(s for s in result.sections if s.category=='education').blocks[0].assignment='education_boundary'
    out=recover_employment_scope(result,elements)
    assert all(b.source_element_index!=2 for s in out.sections if s.category=='experience' for b in s.blocks)
    assert not validate_result(elements,out)


def test_empty_project_boundary_placeholder_cannot_become_an_exported_record(monkeypatch):
    from local_api.services import resume_sections
    from local_api.schemas.sections import SectionBlock
    elements,_=fixture(['PROJECTS','Project Name: Atlas'],{'projects':[0,1]},[])
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(e.text),text=e.text,page_number=1,
                        lane='main',assignment='structural_heading' if i==0 else 'semantic',reason='fixture')
            for i,e in enumerate(elements)]
    monkeypatch.setattr(resume_sections,'entry_groups',lambda *_:[
        {'entry_id':'placeholder','block_indices':[],'lane':'main','boundary_reason':'heading only'},
        {'entry_id':'actual','block_indices':[1],'lane':'main','boundary_reason':'source project name'}])
    sections=resume_sections.build_sections({'projects':blocks},elements)
    assert [e.entry_id for e in sections[0].entries]==['actual']


def test_unfamiliar_title_with_unreliable_style_and_following_education_is_pending():
    from local_api.services.resume_sections import SectionEngine,Unit
    from local_api.schemas.sections import SectionRequest
    from local_api.schemas.extraction import ExtractedElement
    texts=['EXPERIENCE','Learning Journey','B.Tech from North Coast College — 2022']
    elements=[ExtractedElement(type='Title' if i==1 else 'NarrativeText',text=t,page_number=1,metadata={}) for i,t in enumerate(texts)]
    engine=object.__new__(SectionEngine)
    engine.units=lambda _:([Unit(i,0,len(t),t,'main',False) for i,t in enumerate(texts)],False)
    engine.encode_texts=lambda _: [[0]]*3
    class Scores:
        purity=1
        def score(self,*args,**kwargs):return [('summary',0,.1,.01)]*3
    engine.headings=Scores();engine.content=Scores()
    out=engine._detect(SectionRequest(elements=elements))
    assert any(b.source_element_index==1 and b.boundary_candidate for b in out.needs_review)
    assert any(b.source_element_index==2 for s in out.sections if s.category=='education' for b in s.blocks)
