"""Attach exact Word run/relationship evidence without rewriting visible text."""
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlsplit


def annotate_word_source(payload,elements):
    w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    r='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    with ZipFile(BytesIO(payload)) as archive:
        root=ET.fromstring(archive.read('word/document.xml'))
        rels=ET.fromstring(archive.read('word/_rels/document.xml.rels')) if 'word/_rels/document.xml.rels' in archive.namelist() else []
    targets={x.get('Id'):x.get('Target') for x in rels if x.get('Type','').endswith('/hyperlink') and x.get('TargetMode')=='External'}
    paragraphs={}
    for index,p in enumerate(root.iter(w+'p')):
        text=''.join(t.text or '' for t in p.iter(w+'t'))
        if text.strip():paragraphs.setdefault(' '.join(text.split()),[]).append((index,p))
    out=[]
    for element in elements:
        out.append(element)
        matches=paragraphs.get(' '.join(element.get('text','').split()),[])
        if len(matches)!=1:continue
        index,p=matches[0];cursor=0;runs=[]
        text=element['text']
        for run in p.iter(w+'r'):
            value=''.join(t.text or '' for t in run.iter(w+'t')).strip()
            if not value:continue
            match=re.compile(r'\s+'.join(re.escape(v) for v in value.split())).search(text,cursor)
            if not match:continue
            runs.append({'start':match.start(),'end':match.end(),'bold':run.find(w+'rPr/'+w+'b') is not None})
            cursor=match.end()
        metadata=element.setdefault('metadata',{});metadata['word_source_paragraph_index']=index;metadata['word_source_runs']=runs
        links=[]
        for link in p.iter(w+'hyperlink'):
            rid=link.get(r+'id');target=targets.get(rid);display=''.join(t.text or '' for t in link.iter(w+'t'))
            if not target:continue
            links.append({'relationship_id':rid,'target':target,'display_text':display,'part':'word/document.xml'})
            try:parts=urlsplit(target)
            except ValueError:continue
            # A labelled/icon link has a real document URL even when its target
            # is not printed. Keep it as separate, explicitly sourced evidence.
            if (parts.scheme in {'http','https'} and parts.hostname and '.' in parts.hostname and parts.path.strip('/')
                and not re.search(r'https?://|www\.',display,re.I) and not re.search(r'https?://',text,re.I)):
                out.append({'type':'Link','text':target,'metadata':{'word_hyperlink_evidence':{'relationship_id':rid,'paragraph_index':index,'part':'word/document.xml','display_text':display},'page_number':metadata.get('page_number')}})
        if links:metadata['word_source_hyperlinks']=links
    elements[:]=out
