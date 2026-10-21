"""Conservative PDF text-layer recovery with retained upstream provenance.

No OCR or LLM. Existing text is never rewritten. Missing lines come from actual
PDF character objects; only exact same-region duplicates are collapsed. This is
not independent proof of PDF fidelity (images and ambiguous overlaps still need
review). Old element offsets/cached classifications must not be reused afterward.
"""
from copy import deepcopy
from hashlib import sha256
from difflib import SequenceMatcher
from io import BytesIO

from local_api.services.pdf_section_layout import compact

VERSION = 'pdf-source-recovery-v1'


def source_lines(payload):
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTContainer, LTTextLine, LTChar, LAParams
    def walk(item):
        if isinstance(item, LTTextLine):
            yield item
        elif isinstance(item, LTContainer):
            for child in item:
                yield from walk(child)
    for page_number,page in enumerate(extract_pages(BytesIO(payload),laparams=LAParams(all_texts=True)),1):
        for line in walk(page):
            if not any(isinstance(c,LTChar) for c in line):continue
            text=line.get_text().strip()
            if sum(c.isalnum() for c in text)<3:continue
            x0,y0,x1,y1=line.bbox
            yield {'text':text,'page':page_number,'bbox':[x0/page.width,1-y1/page.height,x1/page.width,1-y0/page.height]}


def element_top(element):
    meta=element.get('metadata',{})
    coords=meta.get('coordinates',{})
    try:
        return min(p[1] for p in coords['points'])/coords['layout_height']
    except (KeyError,TypeError,ValueError,ZeroDivisionError):
        hints=meta.get('pdf_source_lines',[])
        return min((h['bbox'][1] for h in hints if len(h.get('bbox',[]))==4),default=None)


def recover_pdf_source(payload, original, lines=None):
    """Return fresh elements and an audit ledger; never mutate upstream objects."""
    elements=[];seen={};events=[]
    for index,raw in enumerate(original):
        e=deepcopy(raw);meta=e.setdefault('metadata',{})
        coords=meta.get('coordinates',{})
        points=coords.get('points')
        key=(meta.get('page_number'),e.get('text'),repr(points),coords.get('layout_width'),coords.get('layout_height'))
        # A repeated paragraph without identical location is not a duplicate.
        if points and e.get('text','').strip() and key in seen:
            kept=elements[seen[key]]
            kept['metadata'].setdefault('pdf_same_region_duplicates',[]).append({'original_index':index,'element':e})
            events.append({'action':'collapse_exact_same_region_duplicate','original_index':index,'kept_original_index':kept['metadata']['upstream_element_index']})
            continue
        meta['upstream_element_index']=index
        seen[key]=len(elements);elements.append(e)
    records=list(source_lines(payload) if lines is None else lines)
    by_page={}
    for e in elements:
        by_page.setdefault(e['metadata'].get('page_number'),[]).append(e)
    additions=[];ambiguous=[]
    for record in records:
        page=record['page'];text=record['text'];key,_=compact(text)
        page_elements=by_page.get(page,[])
        page_key=''.join(compact(e.get('text',''))[0] for e in page_elements)
        if not key or key in page_key:continue
        if '\x00' in text or '\ufffd' in text:
            ambiguous.append({**record,'reason':'damaged_pdf_character_layer'});continue
        # Partial overlaps can mean a spacing/order issue or a partly missing
        # line. Preserve uncertainty rather than adding duplicate fragments.
        overlap=max((SequenceMatcher(None,key,compact(e.get('text',''))[0],autojunk=False).find_longest_match().size for e in page_elements),default=0)
        if overlap/max(1,len(key))>.6:
            located=[h['bbox'] for e in page_elements for h in e.get('metadata',{}).get('pdf_source_lines',[]) if len(h.get('bbox',[]))==4]
            box=record['bbox']
            represented=any(min(b[3],box[3])>max(b[1],box[1]) and min(b[2],box[2])-max(b[0],box[0])>.3*max(.001,box[2]-box[0]) for b in located)
            # Shared words elsewhere (Software Engineer, Score, delivering)
            # cannot prove this physical line was represented. Only recover
            # with located evidence and no existing line covering this region.
            if not located or represented:
                ambiguous.append(record);continue
        if any(a['page']==page and compact(a['text'])[0]==key and a['bbox']==record['bbox'] for a in additions):continue
        additions.append(record)
    for record in sorted(additions,key=lambda r:(r['page'],r['bbox'][1],r['bbox'][0])):
        identity=sha256(repr((record['page'],record['bbox'],record['text'])).encode()).hexdigest()
        recovered={'type':'UncategorizedText','element_id':identity,'text':record['text'],'metadata':{
            'page_number':record['page'],'pdf_source_recovery':{'version':VERSION,'method':'PDF character objects; missing complete physical line','bbox':record['bbox'],'independently_verified':False},
            'pdf_source_lines':[{'start':0,'end':len(record['text']),'bbox':record['bbox'],'heading_style':False}]}}
        position=len(elements)
        for i,e in enumerate(elements):
            page=e['metadata'].get('page_number');top=element_top(e)
            if isinstance(page,int) and (page>record['page'] or (page==record['page'] and top is not None and top>record['bbox'][1]+.002)):
                position=i;break
        elements.insert(position,recovered)
        events.append({'action':'recover_pdf_character_line',**record,'element_id':identity})
    audit={'version':VERSION,'source_sha256':sha256(payload).hexdigest(),'events':events,'ambiguous_source_lines':ambiguous,'original_elements':len(original),'final_elements':len(elements),'requires_fresh_block_detection':bool(events),'human_verified':False}
    if elements:elements[0]['metadata']['pdf_source_recovery_audit']=audit
    return elements,audit
