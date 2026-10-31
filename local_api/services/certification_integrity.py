"""Source-local credential cards: titles own adjacent IDs, dates and verification."""
import re

DETAIL = re.compile(r'^\s*(?:[•▪●*\-]\s*)?(?:(?:certification|certificate|credential|license)\s*(?:#|(?:id|number|no\.?)(?:\s*[:#=])?)|(?:issued(?:\s+(?:on|by))?|issue date|issuer|provider|issuing organization|valid\s+(?:through|until|to)|expir(?:y|ation)(?: date)?|verif(?:y|ication)(?: url)?|credential url)\s*[:#=]?\s*\S|(?:https?://|www\.)\S)',re.I)


def credential_heading(text):
    """A heading/heading fragment is never an earned credential identity."""
    from local_api.services.combined_credentials import combined_heading
    if combined_heading(text):return True
    value=re.sub(r'^\s*(?:&|/|and)\s*','',text.strip().rstrip(':'),flags=re.I)
    return bool(re.fullmatch(r'(?:certifications?|certificates?|credentials?|licen[cs]es?)',value,re.I)
                or re.fullmatch(r'(?:education|academic qualifications?)\s*(?:&|and|/)\s*(?:certifications?|certificates?|credentials?|licen[cs]es?)',value,re.I))


def credential_date_range(text):
    from local_api.services.record_subfields import RANGE
    return RANGE.fullmatch(text.strip())


def detail_row(text):
    # Separate the number marker because # is not a word boundary.
    from local_api.services.record_subfields import DATE
    return bool(re.fullmatch(DATE,text.strip(),re.I) or credential_date_range(text) or re.match(r'^\s*(?:[•▪●*\-]\s*)?(?:certification|certificate|credential|license)\s*#\s*\S',text,re.I)
                or DETAIL.match(text))


def aligned_credential_detail(previous,block,elements):
    if previous is None or previous.page_number != block.page_number:return False
    def rows(b):
        return [r for r in elements[b.source_element_index].metadata.get('pdf_source_lines',[])
                if len(r.get('bbox',[]))==4 and min(b.end,r.get('end',0))>max(b.start,r.get('start',0))]
    return any(abs(left['bbox'][1]-right['bbox'][1])<.004 and right['bbox'][0]>=left['bbox'][2]
               for left in rows(previous) for right in rows(block))


def credential_values(blocks):
    from local_api.services.source_fragments import texts
    rows=texts([b for b in blocks if b.assignment not in {'section_heading','structural_heading'}])
    candidates={}
    def add(name,value):
        value=value.strip()
        if value:candidates.setdefault(name,[]).append(value)
    from local_api.services.record_subfields import DATE,RANGE
    for text in rows:
        period=credential_date_range(text)
        if period:
            add('issue_year',period[1]);add('expiry_date',period[2])
        for match in re.finditer(r'\b(?:issued(?!\s+by\b)(?:\s+on)?|issue date)(?:\s*[:=]\s*|\s+)(' + DATE + r')(?!\d)',text,re.I):add('issue_year',match[1])
        for match in re.finditer(r'\b(?:valid\s+(?:through|until|to)|expiry(?: date)?|expiration(?: date)?)(?:\s*[:=]\s*|\s+)(' + DATE + r')(?!\d)',text,re.I):add('expiry_date',match[1])
        for match in re.finditer(r'\b(?:verify|verification(?: url)?|credential url)\s*[:=]\s*(\S+)',text,re.I):add('verification_url',match[1].rstrip('.,;'))
        for piece in re.split(r'[|\n]',text):
            piece=re.sub(r'^\s*[•▪●*]\s*','',piece).strip()
            match=re.match(r'^(?:certification|certificate|credential|license)\s*(?:#|(?:id|number|no\.?)\s*[:#=]?)\s*([A-Za-z0-9][A-Za-z0-9./_-]*)',piece,re.I)
            if match:add('credential_id',match[1]);continue
            match=re.match(r'^(?:issued by|issuer|provider|issuing organization)\s*[:=]?\s+(.+)$',piece,re.I)
            if match:add('issuer',match[1]);continue
    titles=[text.strip() for text in rows if text.strip() and not credential_heading(text) and not detail_row(text)
            and not re.fullmatch(r'\d{4}(?:-\d{2})?',text.strip())]
    if titles:
        title=re.sub(r'^\s*[•▪●*]\s*','',credential_title_text(titles[0])).rstrip(' ·•▪●;|\n\t')
        label=re.match(r'^(?:certification(?: name)?|certificate(?: name)?|credential name)\s*[:=]\s*(.+)$',title,re.I)
        if label:title=label[1]
        # Parenthesized narrative explanations are descriptions, not identity.
        inline=RANGE.search(title)
        if inline and inline.start()>0 and not title[inline.end():].strip():
            add('issue_year',inline[1]);add('expiry_date',inline[2]);title=title[:inline.start()].rstrip(' |—–-')
        title=re.split(r'\s*\((?=built to\b|designed to\b|focused on\b)',title,maxsplit=1,flags=re.I)[0].strip()
        parts=re.split(r'\s+[—–]\s+',title,maxsplit=1)
        if len(parts)==2:
            left,right=parts
            if (re.search(r'\b(?:institute|university|association|foundation|academy|council|board|school|corporation|ltd)\b',right,re.I)
                or re.search(r'\b(?:workshop|training|bootcamp)\s*$',left,re.I)):
                year=re.search(r'\s*\(((?:19|20)\d{2})\)\s*$',right)
                add('name',left);add('issuer',right[:year.start()].strip() if year else right)
                if year:add('issue_year',year[1])
            else:add('name',title)
        else:add('name',title)
    if not titles:candidates['name']=[None]
    values={};reasons=[]
    for name,items in candidates.items():
        unique=list(dict.fromkeys(items))
        if unique==[None]:values[name]=None
        elif len({v.casefold() for v in unique})==1:values[name]=unique[0]
        else:reasons.append(f'Conflicting source certification {name}; no value selected.');values[name]=None
    return values,reasons


def credential_list_spans(text):
    depth=0;ends=[]
    for match in re.finditer(r'[()\[\]{}]|[·•▪●;|]+\s*',text):
        token=match[0][0]
        if token in '([{':depth+=1
        elif token in ')]}':depth=max(0,depth-1)
        elif not depth:ends.append(match.end())
    bounds=[0]+ends+[len(text)]
    return list(zip(bounds,bounds[1:]))


def credential_title_text(text):
    spans=credential_list_spans(text)
    return text[spans[0][0]:spans[0][1]].strip(' ·•▪●;|\n\t') if spans else text.strip()


def inline_credential_cuts(text):
    """Top-level list separators in a credential section, never name punctuation.

    Metadata segments remain attached to their preceding title. Commas, dashes,
    slashes and ampersands are intentionally not list boundaries.
    """
    cuts=[];seen_title=False
    for first,last in credential_list_spans(text):
        value=text[first:last].strip(' ·•▪●;|\n\t')
        if not value:continue
        from types import SimpleNamespace
        from local_api.services.record_subfields import labelled_fields
        labels=labelled_fields('certifications',[SimpleNamespace(text=value,assignment='semantic')])
        if detail_row(value) or labels and 'name' not in labels:continue
        if re.search(r'\b(?:institute|university|association|foundation|academy|council|board|school|corporation|ltd)\b',value,re.I):continue
        if len(value.split())==1 and value.isalpha():return []
        # Only short title-like fragments qualify. A narrative list is not an
        # inventory of earned credentials even within a certification section.
        if (not any(c.isalpha() for c in value) or len(value.split())>24
            or credential_heading(value) or re.search(r'\b(?:including|such as|earned|completed|pursuing|preparing|working|responsible|covering)\b',value,re.I)):
            return []
        if seen_title:cuts.append(first)
        seen_title=True
    return cuts


def recover_certification_cards(result,elements):
    from local_api.services.resume_structure import entry_groups
    from local_api.schemas.sections import SectionEntry
    from local_api.services.source_validation import validate_result
    section=next((s for s in result.sections if s.category=='certifications'),None)
    if section is None:return result
    revised=section.model_copy(deep=True);parts=[]
    for block in revised.blocks:
        if credential_heading(block.text):
            block=block.model_copy(update={'assignment':'structural_heading','reason':'Certification section heading or combined-heading fragment; not a credential record.'})
        if not block.text:
            parts.append(block);continue
        # Split explicit inline lists at top-level separators. Metadata segments
        # (Issued/Valid/ID/Verify) stay with the preceding credential.
        cuts=[0]+inline_credential_cuts(block.text)+[len(block.text)]
        for first,last in zip(cuts,cuts[1:]):
            if first<last:parts.append(block.model_copy(update={'start':block.start+first,'end':block.start+last,'text':block.text[first:last],'assignment':'inline_certification_title' if len(cuts)>2 else block.assignment}))
    revised.blocks=parts
    revised.entries=[SectionEntry(**entry) for entry in entry_groups(parts,'certifications',elements)]
    if [b.model_dump() for b in parts]==[b.model_dump() for b in section.blocks] and [e.block_indices for e in revised.entries]==[e.block_indices for e in section.entries]:return result
    updated=result.model_copy(deep=True);updated.sections=[revised if s.category=='certifications' else s for s in updated.sections]
    updated.metadata['certification_card_recovery']={'cards':len(revised.entries),'source_spans':len(parts)}
    errors=validate_result(elements,updated)
    if errors:raise ValueError('Invalid source binding after credential card recovery: '+repr(errors))
    return updated


def repair_review_certifications(payload,source_sections,fallback=None):
    from local_api.services.source_fragments import citations
    section=next((s for s in source_sections.sections if s.category=='certifications'),None)
    row=next((r for r in payload.get('sections',[]) if isinstance(r,dict) and r.get('category')=='certifications'),None)
    if section is None or row is None or not isinstance(row.get('records'),list):return []
    inventory={f'e{b.source_element_index}:{b.start}:{b.end}':b for b in section.blocks}
    owners=[{f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' for i in e.block_indices} for e in section.entries]
    records=[];repairs=[]
    # An explicit inline source list is a record boundary even if field review
    # returns one combined name. Restore only affected cards, not unrelated ones.
    if fallback is not None:
        from local_api.services.llm_schema_mapping import local_section_payload
        local=local_section_payload(fallback,{'certifications'})
        inline_ids={sid for sid,b in inventory.items() if b.assignment=='inline_certification_title'}
        cards=[r for r in (local[0]['records'] if local else []) if set(r['source_ids']) & inline_ids]
        expected=[set(r['source_ids']) for r in cards]
        affected=set().union(*expected) if expected else set()
        touching=[r for r in row['records'] if isinstance(r,dict) and set(r.get('source_ids',[])) & affected]
        if cards and {frozenset(r.get('source_ids',[])) for r in touching}!={frozenset(ids) for ids in expected}:
            # Never overwrite a record that also claims unrelated source cards.
            if all(set(r.get('source_ids',[]))<=affected for r in touching):
                row['records']=[r for r in row['records'] if r not in touching]+cards
                row['records'].sort(key=lambda r:min((list(inventory).index(sid) for sid in r.get('source_ids',[]) if sid in inventory),default=len(inventory)))
                repairs.append({'code':'inline_credential_records_restored','records':len(cards)})
    for record in row['records']:
        if not isinstance(record,dict) or not isinstance(record.get('fields'),dict) or not isinstance(record.get('source_ids'),list):records.append(record);continue
        ids=record['source_ids'];blocks=[b for sid,b in inventory.items() if sid in ids]
        if blocks and all(b.assignment in {'section_heading','structural_heading'} or credential_heading(b.text) for b in blocks):
            repairs.append({'code':'section_heading_not_certificate','removed_record_id':record.get('record_id')})
            continue
        name=record['fields'].get('name',[])
        name=name[0].get('value') if isinstance(name,list) and len(name)==1 and isinstance(name[0],dict) else None
        previous=records[-1] if records else None
        same=previous and any(set(ids)<=owner and set(previous['source_ids'])<=owner for owner in owners)
        if same and isinstance(name,str) and detail_row(name) and not set(ids)&set(previous['source_ids']):
            previous['source_ids']=[sid for sid in inventory if sid in set(ids)|set(previous['source_ids'])]
            repairs.append({'code':'credential_details_restored_to_named_certificate','removed_record_id':record.get('record_id'),'owning_record_id':previous.get('record_id')})
        else:records.append(record)
    for record in records:
        if not isinstance(record,dict) or not isinstance(record.get('fields'),dict):continue
        blocks=[b for sid,b in inventory.items() if sid in record.get('source_ids',[])]
        values,reasons=credential_values(blocks)
        for name,value in values.items():
            if not value or reasons:continue
            evidence=citations(value,blocks)
            if not evidence:continue
            existing=record['fields'].get(name)
            if existing and (not isinstance(existing,list) or len(existing)!=1):continue
            if existing and len(existing)==1 and existing[0].get('value')==value:continue
            record['fields'][name]=[{'value':value,'evidence':evidence}];record.setdefault('missing',{}).pop(name,None)
            repairs.append({'code':'literal_credential_field_recovered','field':name,'normalized_value':value})
    row['records']=records
    return repairs
