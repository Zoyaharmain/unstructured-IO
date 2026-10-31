"""Identical text at a different physical location is distinct source evidence."""
from copy import deepcopy
from local_api.services.pdf_source_recovery import recover_pdf_source


def element(text,y,x=.1):
    return {'type':'Title','text':text,'metadata':{'page_number':1,'pdf_source_lines':[
        {'start':0,'end':len(text),'bbox':[x,y,x+.4,y+.02]}]}}


def line(text,y,x=.1):
    return {'text':text,'page':1,'bbox':[x,y,x+.4,y+.02]}


def test_missing_repeated_employer_is_recovered_at_second_location():
    name='Example Services Limited'
    original=[element(name,.1),element('Senior Software Engineer',.13),element('Associate Software Engineer',.53)]
    before=deepcopy(original)
    out,audit=recover_pdf_source(b'pdf',original,lines=[line(name,.1),line(name,.5)])
    assert original==before
    assert [e['text'] for e in out].count(name)==2
    recovered=next(e for e in out if 'pdf_source_recovery' in e['metadata'])
    assert recovered['metadata']['pdf_source_lines'][0]['bbox']==[.1,.5,.5,.52]
    assert out.index(recovered)<next(i for i,e in enumerate(out) if e['text']=='Associate Software Engineer')
    assert audit['requires_fresh_block_detection']
    again,second=recover_pdf_source(b'pdf',out,lines=[line(name,.1),line(name,.5)])
    assert len(again)==len(out) and not second['events']


def test_both_printed_occurrences_already_present_are_not_duplicated():
    text='Example Services Limited'
    out,audit=recover_pdf_source(b'pdf',[element(text,.1),element(text,.5)],lines=[line(text,.1),line(text,.5)])
    assert len(out)==2 and not audit['events']


def test_repeated_source_without_location_evidence_is_not_guessed():
    text='Example Services Limited'
    out,audit=recover_pdf_source(b'pdf',[{'text':text,'metadata':{'page_number':1}}],lines=[line(text,.1),line(text,.5)])
    assert len(out)==1


def test_same_height_different_columns_are_distinct_occurrences():
    text='Professional Certificate'
    out,audit=recover_pdf_source(b'pdf',[element(text,.1,x=.05)],lines=[line(text,.1,x=.05),line(text,.1,x=.6)])
    assert len(out)==2 and len(audit['events'])==1
