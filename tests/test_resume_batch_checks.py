"""Expected-answer comparison must never certify unreviewed model output."""
from scripts.check_resume_batch import compare, evaluate


def test_partial_objects_and_unordered_records_have_exact_counts():
    assert compare({'experience':[{'company':'B'},{'company':'A'}]},
                   {'experience':[{'company':'A','role':'Engineer'},{'company':'B'}]})==[]
    assert compare([{'company':'A'}],[{'company':'A'},{'company':'B'}])==['data:count']
    assert compare({'contact':{'full_name':'Correct'}},{'contact':{'full_name':'Wrong'}})==['data.contact.full_name']


def test_partial_record_matching_does_not_greedily_consume_specific_match():
    assert compare([{}, {'company':'A'}],[{'company':'A'},{'company':'B'}])==[]
    assert compare([{'company':'A'},{'company':'A'}],[{'company':'A'},{'company':'B'}])


def test_review_and_source_hash_are_required_and_empty_truth_is_invalid():
    row={'sha256':'source'}
    assert evaluate(None,row,{})==('not_reviewed',[])
    assert evaluate({'human_reviewed':False,'expected_data':{'name':'A'}},row,{})[0]=='not_reviewed'
    assert evaluate({'human_reviewed':True,'sha256':'old'},row,{})[0]=='stale_expectations'
    assert evaluate({'human_reviewed':True,'sha256':'source','expected_data':{}},row,{})[0]=='invalid_expectations'
    truth={'human_reviewed':True,'sha256':'source','expected_data':{'name':'A'}}
    assert evaluate(truth,row,{'name':'A'})==('pass',[])
    assert evaluate(truth,row,{'name':'B'})==('fail',['data.name'])
