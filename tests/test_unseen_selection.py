import json
import pytest
from scripts.select_unseen_resumes import prior_selections,choose

def item(name,digest):return {'file':name,'sha256':digest*64,'pages':1,'two_col':False,'coverage':90}

def test_exclusion_unions_nested_runs_and_fails_on_corrupt_history(tmp_path):
 for name,rows in [('first',[item('one.pdf','a')]),('nested/second',[item('two.pdf','b')])]:
  path=tmp_path/name;path.mkdir(parents=True);(path/'manifest.json').write_text(json.dumps({'selected':rows}))
 hashes,names,sources=prior_selections(tmp_path)
 assert hashes=={'a'*64,'b'*64} and names=={'one.pdf','two.pdf'} and len(sources)==2
 (tmp_path/'first/manifest.json').write_text('{broken')
 with pytest.raises(ValueError):prior_selections(tmp_path)

def test_renamed_pdf_and_changed_file_name_are_both_excluded():
 pool=[item('renamed.pdf','a'),item('previous.pdf','b'),item('new.pdf','c'),item('alias.pdf','c'),item('other.pdf','d')]
 selected=choose(pool,2,42,{'a'*64},{'previous.pdf'})
 assert len({i['sha256'] for i in selected})==2
 assert {i['sha256'] for i in selected}=={'c'*64,'d'*64}
 assert selected==choose(pool,2,42,{'a'*64},{'previous.pdf'})
 with pytest.raises(ValueError,match='Insufficient'):choose(pool,3,42,{'a'*64},{'previous.pdf'})

def test_no_history_and_invalid_hash_fail_closed(tmp_path):
 with pytest.raises(ValueError,match='No previous'):prior_selections(tmp_path)
 (tmp_path/'manifest.json').write_text(json.dumps({'selected':[{'file':'x','sha256':'broken'}]}))
 with pytest.raises(ValueError,match='Invalid exclusion'):prior_selections(tmp_path)
 with pytest.raises(ValueError,match='positive'):choose([],0,42,set(),set())

def test_report_separates_out_of_scope_unknown_text():
 from scripts.report_pilot50_review import pending_by_scope
 rows=[{'document_scope':{'candidate_resume':False},'final_unassigned_meaningful':413},
       {'document_scope':{'candidate_resume':True},'final_unassigned_meaningful':3},
       {'document_scope':{'candidate_resume':None},'final_unassigned_meaningful':1}]
 counts=pending_by_scope(rows)
 assert counts['out_of_scope_meaningful_unassigned']==413
 assert counts['candidate_or_unknown_meaningful_unassigned']==4
 assert counts['candidate_or_unknown_documents']==2
