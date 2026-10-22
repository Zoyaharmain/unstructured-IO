from copy import deepcopy
from local_api.services.pdf_glyph_recovery import recover_pdf_glyphs


def test_unique_local_window_repairs_word_despite_unrelated_missing_suffix():
 original='prefix not represented in PDF '+'A'*36+' con\x00nuous learning and staying current '+ 'B'*36+' suffix not represented in PDF'
 reference='A'*36+' continuous learning and staying current '+'B'*36
 elements=[{'text':original,'metadata':{'page_number':1}}]
 before=deepcopy(elements);out=recover_pdf_glyphs(b'',elements,[reference])
 assert 'continuous learning' in out[0]['text']
 assert elements==before
 assert out[0]['metadata']['pdf_glyph_recovery']['replacements'][0]['source_replacement']=='ti'


def test_local_window_requires_unique_match_and_sufficient_context():
 text='A'*36+' con\x00nuous learning and staying current '+'B'*36
 reference='A'*36+' continuous learning and staying current '+'B'*36
 elements=[{'text':text,'metadata':{'page_number':1}}]
 assert recover_pdf_glyphs(b'',elements,[reference+' '+reference])[0]['text']==text
 tiny=[{'text':'\x00','metadata':{'page_number':1}}]
 assert recover_pdf_glyphs(b'',tiny,['lots of words here'])[0]['text']=='\x00'
