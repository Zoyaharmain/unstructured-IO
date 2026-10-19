"""Independent scoring examples: full assignment must not masquerade as accuracy."""
import pytest
from scripts.evaluate_resume_ground_truth import extraction_hash,score,summarize_scores


def document():
    elements=[{'text':'Python SQL'},{'text':'Acme engineer'}]
    spans=[{'source_element_index':i,'start':0,'end':len(e['text']),'category':cat} for i,(e,cat) in enumerate(zip(elements,['skills','experience']))]
    truth={'human_verified':True,'extraction_sha256':extraction_hash(elements),'spans':spans}
    return elements,truth


def prediction(elements,categories):
    sections=[];unknown=[]
    for i,(element,category) in enumerate(zip(elements,categories)):
        block={'source_element_index':i,'start':0,'end':len(element['text']),'text':element['text']}
        if category=='needs_review':unknown.append(block)
        else:sections.append({'category':category,'blocks':[block]})
    return {'sections':sections,'needs_review':unknown}


def test_all_assigned_but_wrong_category_is_not_entirely_correct():
    elements,truth=document();result=score(elements,truth,prediction(elements,['skills','skills']))
    assert not result['entire_resume_correct']
    assert result['unassigned_characters']==0
    assert result['missing_sections']==['experience']
    assert result['character_accuracy']<1


def test_ground_truth_measures_review_improvement_and_exact_sections():
    elements,truth=document()
    local=score(elements,truth,prediction(elements,['skills','needs_review']))
    reviewed=score(elements,truth,prediction(elements,['skills','experience']))
    assert reviewed['entire_resume_correct'] and reviewed['entirely_correct_sections']==2
    assert reviewed['character_accuracy']>local['character_accuracy']
    assert summarize_scores([reviewed])['entirely_correct_resumes']==1


@pytest.mark.parametrize('damage',['unverified','source_changed','gap','overlap'])
def test_invalid_or_unverified_ground_truth_is_not_scored(damage):
    elements,truth=document()
    if damage=='unverified':truth['human_verified']=False
    if damage=='source_changed':truth['extraction_sha256']='bad'
    if damage=='gap':truth['spans'][0]['end']-=1
    if damage=='overlap':truth['spans'].append(truth['spans'][0].copy())
    with pytest.raises(ValueError):score(elements,truth,prediction(elements,['skills','experience']))


def test_no_ground_truth_does_not_return_zero_or_fake_accuracy():
    summary=summarize_scores([])
    assert summary['accuracy'] is None
    assert summary['entirely_correct_resumes'] is None
