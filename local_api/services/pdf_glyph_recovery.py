"""Resolve damaged glyph placeholders only through a unique PDF text-layer match.

Non-placeholder characters must match the Poppler source exactly within a
unique full-element match or a bounded surrounding context after compaction. Preserve the original and every replacement's source map.
This never predicts a missing character from a dictionary or language model.
"""
from copy import deepcopy
import re,subprocess
from local_api.services.pdf_section_layout import compact


def local_glyph_matches(key,offsets,reference):
    replacements=[]
    for index,char in enumerate(key):
        if char not in '\x00\ufffd':continue
        left=max(0,index-32);right=min(len(key),index+33);window=key[left:right]
        if sum(c not in '\x00\ufffd' for c in window)<16:continue
        damaged=[i for i,c in enumerate(window) if c in '\x00\ufffd']
        pattern=''.join('([A-Za-z]{1,3})' if c in '\x00\ufffd' else re.escape(c) for c in window)
        matches=list(re.finditer(pattern,reference))
        if len(matches)==1:
            replacements.append((offsets[index],matches[0].groups()[damaged.index(index-left)]))
    return replacements


def recover_pdf_glyphs(payload,elements,reference_pages=None):
    result=deepcopy(elements)
    if not any('\x00' in e.get('text','') or '\ufffd' in e.get('text','') for e in result):return result
    if reference_pages is None:
        reference=subprocess.run(['pdftotext','-layout','-','-'],input=payload,capture_output=True,timeout=45,check=True)
        reference_pages=reference.stdout.decode('utf-8','replace').split('\f')
    for e in result:
        original=e.get('text','')
        if '\x00' not in original and '\ufffd' not in original:continue
        page=e.get('metadata',{}).get('page_number')
        if not isinstance(page,int) or not 1<=page<=len(reference_pages):continue
        key,offsets=compact(original);reference,_=compact(reference_pages[page-1])
        pattern=''.join('([A-Za-z]{1,3})' if c in '\x00\ufffd' else re.escape(c) for c in key)
        if len(key)>20000:continue
        matches=list(re.finditer(pattern,reference))
        positions=[offsets[i] for i,c in enumerate(key) if c in '\x00\ufffd']
        replacements=list(zip(positions,matches[0].groups())) if len(matches)==1 else local_glyph_matches(key,offsets,reference)
        if not replacements:
            e.setdefault('metadata',{})['pdf_glyph_uncertainty']='No unique source-layer match for damaged glyphs';continue
        pieces=[];mapping=[];cursor=0;new_cursor=0
        for position,replacement in replacements:
            pieces.append(original[cursor:position]);new_cursor+=position-cursor
            mapping.append({'original_start':position,'original_end':position+1,'new_start':new_cursor,'new_end':new_cursor+len(replacement),'source_replacement':replacement})
            pieces.append(replacement);new_cursor+=len(replacement);cursor=position+1
        pieces.append(original[cursor:]);e['text']=''.join(pieces)
        meta=e.setdefault('metadata',{})
        previous=deepcopy(meta.get('pdf_glyph_recovery'))
        meta['pdf_glyph_recovery']={'method':'unique Poppler PDF text-layer match','original_text':original,'replacements':mapping,'human_verified':False}
        if previous:meta['pdf_glyph_recovery']['previous_recovery']=previous
        if '\x00' not in e['text'] and '\ufffd' not in e['text']:meta.pop('pdf_glyph_uncertainty',None)
        # Prior line offsets refer to the damaged representation.
        meta.pop('pdf_source_lines',None)
    return result
