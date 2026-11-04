"""Literal source paragraphs and field coverage for established employment cards."""
import re
from local_api.services.source_fragments import runs,citations


def duties_from_source(blocks):
    from local_api.services.record_subfields import ALIASES
    labels=[key for key,field in ALIASES['experience'].items() if field=='technologies']+['technologies']
    tool=re.compile(r'(?<!\w)(?:'+ '|'.join(re.escape(key) for key in sorted(labels,key=len,reverse=True))+r')\s*:\s*',re.I)
    body=[b for b in blocks if b.assignment in {'local_record_continuation','local_responsibility_bullet'}]
    groups=[]
    for run in runs(body):
        for block in run:
            if not groups or block is run[0] or block.assignment=='local_responsibility_bullet':groups.append([])
            groups[-1].append(block)
    paragraphs=[]
    responsibility_label=re.compile(r'(?:Key\s+)?Responsibilities(?:\s*(?:&|and)\s*Achievements)?\s*:\s*[•▪● ]*',re.I)
    for run in groups:
        raw=''.join(b.text for b in run);remaining=raw;segments=[]
        while True:
            match=tool.search(remaining)
            if not match:segments.append(remaining);break
            segments.append(remaining[:match.start()].rstrip(' |;'))
            following=responsibility_label.search(remaining,match.end())
            if not following:break
            remaining=remaining[following.end():]
        for segment in segments:
            new_bullet=(run[0].assignment=='local_responsibility_bullet' or bool(re.match(r'^\s*[•▪●*]',segment)))
            value=re.sub(r'^\s*(?:[•▪●*]\s*|-\s+)','',segment).strip()
            value=re.sub(r'^\s*(?:(?:Key\s+)?Responsibilities(?:\s*(?:&|and)\s*Achievements)?|Impact\s*&\s*Value Delivered)\s*:\s*[•▪● ]*','',value,flags=re.I).strip()
            if not any(c.isalnum() for c in value):continue
            # Join only literal wrapped continuations; an explicit bullet is
            # always a new item, even if the previous line lacks punctuation.
            if not new_bullet and paragraphs and not paragraphs[-1].rstrip().endswith(('.', '!', '?', ':')) and (
                value[:1].islower() or re.search(r'\b(?:and|in|with|for|of|across|including|the|to|on)\s*$',paragraphs[-1],re.I)):
                joined=paragraphs[-1]+'\n'+value
                if citations(joined,body):paragraphs[-1]=joined;continue
            paragraphs.append(value)
    return list(dict.fromkeys(paragraphs))


def covered_by_values(expected,items,blocks):
    """Measure literal value coverage, never an overbroad evidence quotation."""
    inventory={f'e{b.source_element_index}:{b.start}:{b.end}':b.text for b in blocks}
    masks={sid:[False]*len(text) for sid,text in inventory.items()}
    for item in items:
        value=item.get('value') if isinstance(item,dict) else None
        if not isinstance(value,str):continue
        for ref in citations(value,blocks,flexible_whitespace=True):
            text=inventory[ref['source_id']]
            for match in re.finditer(re.escape(ref['quote']),text):
                masks[ref['source_id']][match.start():match.end()]=[True]*(match.end()-match.start())
    for item in expected:
        value=item.get('value')
        refs=citations(value,blocks,flexible_whitespace=True)
        if not refs:return False
        for ref in refs:
            text=inventory[ref['source_id']];start=text.find(ref['quote'])
            if any(c.isalnum() and not masks[ref['source_id']][start+i] for i,c in enumerate(ref['quote'])):return False
    return True


def physical_bullet_starts(elements):
    """Use retained list-marker geometry; blank markers remain audit artifacts."""
    markers=[];starts={}
    for index,element in enumerate(elements):
        text=element.text.strip()
        if element.type=='ListItem' and text:starts.setdefault(index,set()).add(0)
        if not (element.type=='ListItem' and not text or re.fullmatch(r'[•▪●\uf0b7]',text)):continue
        coords=element.metadata.get('coordinates',{})
        try:
            points=coords['points'];width=coords['layout_width'];height=coords['layout_height']
            left=min(p[0] for p in points)/width;right=max(p[0] for p in points)/width
            top=min(p[1] for p in points)/height;bottom=max(p[1] for p in points)/height
        except (KeyError,TypeError,ValueError,ZeroDivisionError):continue
        if right-left<.025 and bottom-top<.04:markers.append((element.page_number,right,top))
    for index,element in enumerate(elements):
        for row in element.metadata.get('pdf_source_lines',[]):
            box=row.get('bbox',[])
            if len(box)!=4:continue
            if any(page==element.page_number and 0<=box[0]-x<.08 and abs(box[1]-y)<.003 for page,x,y in markers):
                offset=row['start'];starts.setdefault(index,set()).add(offset)
    return starts
