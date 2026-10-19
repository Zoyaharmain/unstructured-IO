import copy
import json
from pathlib import Path

import pytest
from pypdf import PdfWriter
from scripts.human_review_validation import validate_annotation,validate_bundle,sha,ATTESTATIONS
from scripts.evaluate_resume_ground_truth import extraction_hash


def sample(tmp_path):
    text='Acme Ltd Engineer 2020 - 2022'
    elements=[{'text':text}]
    span={'span_id':'s1','source_element_index':0,'start':0,'end':len(text),'text':text,'category':'experience','field_role':'content'}
    record={'record_id':'exp1','span_ids':['s1'],'employer':'Acme Ltd','title':'Engineer','dates':'2020 - 2022',
            'field_evidence':{k:['s1'] for k in ['employer','title','dates']},'human_relationship_decision':'approved'}
    annotation={'file':'fixture.pdf','extraction_sha256':extraction_hash(elements),'spans':[span],
                'records':{'work_experience':[record],'education':[]},'metadata':{'source_artifact':str(tmp_path/'artifact.json')}}
    draft=tmp_path/'fixture.json';draft.write_text(json.dumps(annotation));pdf=tmp_path/'fixture.pdf';writer=PdfWriter();writer.add_blank_page(300,300);writer.write(pdf)
    bundle={'draft_sha256':sha(draft),'source_pdf_sha256':sha(pdf),'reviewer':'Test Reviewer','decision':'approve',
            'reviewed_pages':[1],'attestations':dict.fromkeys(ATTESTATIONS,True),'pdf_issues':[],
            'span_decisions':{'s1':{'action':'approve'}},'annotation':copy.deepcopy(annotation),'recorded_at':'2026-10-19T00:00:00Z','revision':1}
    return elements,annotation,draft,pdf,bundle


def test_approval_requires_explicit_human_decisions_and_evidence(tmp_path):
    elements,annotation,draft,pdf,bundle=sample(tmp_path)
    assert validate_bundle(bundle,draft,pdf,elements)==[]
    bundle['span_decisions']={}
    assert 's1: human_decision_missing' in validate_bundle(bundle,draft,pdf,elements)


@pytest.mark.parametrize('damage',['unsupported_employer','evidence_outside_record','blank_title','wrong_membership','shared_record','changed_text'])
def test_relationship_validation_catches_wrong_associations(tmp_path,damage):
    elements,a,*_=sample(tmp_path);record=a['records']['work_experience'][0]
    if damage=='unsupported_employer':record['employer']='Another Company'
    if damage=='evidence_outside_record':record['field_evidence']['title']=['other-record-span']
    if damage=='blank_title':record['title']=''
    if damage=='wrong_membership':a['spans'][0]['category']='education'
    if damage=='shared_record':a['records']['work_experience'].append({**record,'record_id':'exp2'})
    if damage=='changed_text':a['spans'][0]['text']='invented'
    assert validate_annotation(a,elements,True,{'s1':{'action':'approve'}})


def test_education_associations_need_degree_institution_year_in_same_record(tmp_path):
    elements,a,*_=sample(tmp_path)
    text='BSc Example University 2020';elements[0]['text']=text;a['extraction_sha256']=extraction_hash(elements)
    a['spans'][0].update(text=text,end=len(text),category='education')
    a['records']={'work_experience':[],'education':[{'record_id':'edu1','span_ids':['s1'],'degree':'BSc','institution':'Example University','year':'2020',
        'field_evidence':{k:['s1'] for k in ['degree','institution','year']},'human_relationship_decision':'approved'}]}
    assert validate_annotation(a,elements,True,{'s1':{'action':'approve'}})==[]
    a['records']['education'][0]['year']='2022'
    assert any('year_unsupported_value' in x for x in validate_annotation(a,elements))


@pytest.mark.parametrize('damage',['no_approval','unchecked_pages','stale_draft','missing_pdf_text','wrong_decision'])
def test_false_zero_unassigned_does_not_enable_approval(tmp_path,damage):
    elements,a,draft,pdf,b=sample(tmp_path)
    if damage=='no_approval':b['decision']='save'
    if damage=='unchecked_pages':b['reviewed_pages']=[]
    if damage=='stale_draft':b['draft_sha256']='stale'
    if damage=='missing_pdf_text':b['pdf_issues']=[{'kind':'missing_text','status':'open'}]
    if damage=='wrong_decision':b['annotation']['spans'][0]['category']='skills'
    assert validate_bundle(b,draft,pdf,elements)


def test_promotion_cannot_auto_approve_or_overwrite(tmp_path,monkeypatch):
    import scripts.verify_ground_truth as verify
    elements,a,draft,pdf,b=sample(tmp_path)
    root=tmp_path/'repo';(root/'ground_truth/pilot_resumes').mkdir(parents=True)
    (root/'ground_truth/pilot_resumes/fixture.pdf').write_bytes(pdf.read_bytes())
    (tmp_path/'artifact.json').write_text(json.dumps({'extraction':{'elements':elements}}))
    monkeypatch.setattr(verify,'ROOT',root)
    destination=root/'ground_truth/approved_v2';manifest=destination/'gold.jsonl';original=draft.read_bytes()
    with pytest.raises(ValueError,match='Explicit approved'):verify.promote_to_gold(draft,None,destination,manifest)
    approval=tmp_path/'approved.json';approval.write_text(json.dumps(b))
    path,entry=verify.promote_to_gold(draft,None,destination,manifest,approved_review_path=approval)
    assert entry['human_verified'] and json.loads(path.read_text())['human_decisions']==b['span_decisions']
    assert draft.read_bytes()==original
    with pytest.raises(FileExistsError):verify.promote_to_gold(draft,None,destination,manifest,approved_review_path=approval)


def test_bulk_gate_stops_before_provider_or_candidate_generation(tmp_path,monkeypatch):
    import scripts.pilot_review_gate as gate
    import scripts.scale_ground_truth as scale
    monkeypatch.setattr(gate,'check_pilot_ready',lambda *a:{'ready':False,'blockers':['not reviewed'],'decisions':{}})
    monkeypatch.setattr(scale,'load_env',lambda:pytest.fail('Must not load provider configuration before gate'))
    with pytest.raises(ValueError,match='gate is not complete'):
        scale.scale_corpus(tmp_path,tmp_path/'output',approved_gold_dir=tmp_path/'gold',pilot_review_dir=tmp_path/'reviews')
    assert not (tmp_path/'output').exists()


def test_bulk_skips_and_preserves_approved_corrections(tmp_path,monkeypatch):
    import scripts.pilot_review_gate as gate
    import scripts.scale_ground_truth as scale
    elements,a,*_=sample(tmp_path)
    source=tmp_path/'source';source.mkdir();(source/'artifact.json').write_text(json.dumps({'extraction':{'elements':elements}}))
    (source/'results.jsonl').write_text(json.dumps({'file':'fixture.pdf','extension':'.pdf','artifact':'artifact.json','sha256':'pdf-hash'})+'\n')
    approved=tmp_path/'approved.json';approved.write_text('immutable human corrections')
    decision={'status':'gold','pdf_sha256':'pdf-hash','extraction_sha256':extraction_hash(elements),'annotation_path':str(approved)}
    monkeypatch.setattr(gate,'check_pilot_ready',lambda *a:{'ready':True,'decisions':{'fixture.pdf':decision},'blockers':[]})
    monkeypatch.setattr(scale,'load_env',lambda:None)
    monkeypatch.setattr(scale,'generate_draft',lambda *a,**k:pytest.fail('Human correction must not be sent back to candidate generator'))
    scale.scale_corpus(source,tmp_path/'candidates',approved_gold_dir=tmp_path/'gold',pilot_review_dir=tmp_path/'reviews')
    assert approved.read_text()=='immutable human corrections'
    assert json.loads((tmp_path/'candidates/manifest.json').read_text())['records'][0]['annotation_path']==str(approved)


def test_equal_entry_counts_do_not_prove_employer_title_date_associations():
    from scripts.human_review_validation import score_record_relationships
    reference={'human_verified':True,'review_provenance':{'approved_bundle_sha256':'explicit-approval'},'extraction_sha256':'source',
        'records':{'work_experience':[{'employer':'Alpha','title':'Engineer','dates':'2020-2021'}, {'employer':'Beta','title':'Manager','dates':'2022-2023'}],'education':[]}}
    predicted=copy.deepcopy(reference)
    predicted['records']['work_experience'][0]['title']='Manager'
    predicted['records']['work_experience'][1]['title']='Engineer'
    score=score_record_relationships(predicted,reference)['work_experience']
    assert score['complete_predicted_records']==score['reference_records']==2
    assert score['exact_relationship_matches']==0 and score['recall']==0


def test_legacy_human_verified_flag_does_not_establish_relationship_ground_truth():
    from scripts.human_review_validation import score_record_relationships
    with pytest.raises(ValueError,match='provenance'):
        score_record_relationships({'extraction_sha256':'source'},{'human_verified':True,'extraction_sha256':'source'})
