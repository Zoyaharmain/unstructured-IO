"""Identify dated record headers using literal title grammar and source position."""
import re

ROLE_END=r'(?:Engineer|Developer|Programmer|Scientist|Specialist|Analyst|Consultant|Architect|Manager|Administrator|Officer|Director)'
JOINED=re.compile(r'^(?P<role>(?:[A-Z][\w+/#&.-]*\s+){0,5}'+ROLE_END+r'(?:\s+(?:[IVX]+|[1-6]))?(?:\s*[-–—]\s*[A-Z][A-Z0-9/+.-]*)?)\s+(?P<company>[A-Z][A-Za-z0-9&.\x27’ -]+?)\s*$')


def joined_job_header(text):
    from local_api.services.record_subfields import responsibility_fragment,is_place
    if responsibility_fragment(text) or len(text.split())>26:return {}
    parts=text.strip().split('|',1);identity=parts[0].strip();location=parts[1].strip() if len(parts)==2 else None
    match=JOINED.fullmatch(identity)
    if not match:return {}
    company=match['company']
    if len(company.split())<2 or re.match(r'^(?:Product|Project|Program|Software|Data|Business)\s+(?:Management|Development|Engineering|Analytics|Transformation)$',company):return {}
    if not (location and is_place(location)) and not re.search(r'\b(?:Limited|Ltd|Inc|LLC|Corporation|Technologies|Systems)\b',company):return {}
    return {'company':company,'role':match['role'],**({'location':location} if location else {})}


def dated_header_candidates(blocks):
    from local_api.services.record_subfields import RANGE
    from local_api.services.source_fragments import texts
    # Only the entry's opening date/header region can establish employer identity.
    opening=[b for b in blocks if b.text.strip() and b.assignment not in {'section_heading','structural_heading'}][:3]
    joined=[v for text in texts(opening) if (v:=joined_job_header(text))] if any(RANGE.fullmatch(b.text.strip()) for b in opening) else []
    split=[value for start,end,value in split_employment_headers([b for b in blocks if b.assignment not in {'section_heading','structural_heading'}][:6]) if start==0]
    return [dict(items) for items in dict.fromkeys(tuple(v.items()) for v in joined+split)]


def education_date_starts_record(blocks,index):
    from local_api.services.record_subfields import DATE
    from local_api.services.education_subfields import DEGREE
    text=blocks[index].text.strip()
    if not re.fullmatch(DATE,text,re.I):return False
    following=[b.text.strip() for b in blocks[index+1:index+4] if b.text.strip()]
    if not following:return False
    if DEGREE.search(following[0]):return True
    title=following[0].split('|',1)[0].strip()
    return ('|' in following[0] and title.isupper() and 1<=len(title.split())<=8
            and any(re.search(r'\b(?:Institute|University|College|School)\b',row,re.I) for row in following[1:]))


def split_employment_headers(blocks):
    """Find compact role/employer/date headers across literal source rows."""
    from local_api.services.record_subfields import ROLE,RANGE,responsibility_fragment,is_place,COMPANY_KEYWORD
    rows=[(i,line.strip()) for i,b in enumerate(blocks)
          if b.assignment not in {'section_heading','structural_heading'}
          for line in b.text.splitlines() if line.strip()]
    found=[]
    def title(value):
        return (bool(ROLE.search(value)) and len(value.split())<=12 and not RANGE.search(value)
                and not responsibility_fragment(value) and not COMPANY_KEYWORD.search(value)
                and not re.match(r'^(?:client|project|responsibilit)',value,re.I))
    for position in range(len(rows)-2):
        first,second=rows[position:position+2]
        if title(first[1]) and not title(second[1]):role,employer=first[1],second[1]
        elif title(second[1]) and not title(first[1]):role,employer=second[1],first[1]
        else:continue
        if (len(employer.split())>12 or not re.match(r'^[A-Z0-9]',employer)
            or responsibility_fragment(employer) or RANGE.search(employer)
            or re.match(r'^(?:client|project|location|team|department)\s*:',employer,re.I)):
            continue
        date=None
        for index,value in rows[position+2:position+5]:
            if RANGE.fullmatch(value):date=index;break
            if not re.match(r'^Client\s*[:=]',value,re.I):break
        if date is None:continue
        indices=list(range(first[0],date+1));parts=[blocks[i] for i in indices]
        if any(b.page_number!=parts[0].page_number or b.lane not in {parts[0].lane,'wide'} and parts[0].lane!='wide' for b in parts):continue
        if any(b.source_element_index-a.source_element_index>1 for a,b in zip(parts,parts[1:])):continue
        components=re.split(r'\s+[–—-]\s+|\s*\|\s*',employer)
        if len(components)>2:continue
        company=components[0].strip();values={'company':company,'role':role}
        if len(components)==2:
            suffix=components[1].strip()
            # The compact header position provides location context without
            # adding candidate cities to a fixed place-name list. Department/
            # practice labels remain ambiguous and are not recast as places.
            place_shape=bool(re.fullmatch(r'[A-Z][A-Za-z.\'-]*(?:[ ,]+[A-Z][A-Za-z.\'-]*){0,4}',suffix))
            if not (is_place(suffix) or place_shape) or re.search(r'\b(?:team|department|division|operations|engineering|services|solutions|platform|products|practice|business|unit|group)\b',suffix,re.I):continue
            values['location']=suffix
        if not company or ':' in company or not any(c.isalpha() for c in company):continue
        found.append((first[0],date,values))
    return found


def recover_split_employment_headers(result,elements):
    """Join a split header/date entry only when source adjacency establishes it."""
    from local_api.schemas.sections import SectionEntry
    from local_api.services.record_relationships import annotate_relationships
    from local_api.services.source_validation import validate_result
    section=next((s for s in result.sections if s.category=='experience'),None)
    if section is None:return result
    revised=section.model_copy(deep=True);events=[]
    candidates=split_employment_headers(revised.blocks)
    # A detector may have appended the next role/employer to the preceding
    # date-led record. Partition at proven header starts before rejoining dates.
    starts={start for start,end,values in candidates}
    partitioned=[]
    for entry in revised.entries:
        chunks=[]
        for index in entry.block_indices:
            if not chunks or index in starts:chunks.append([])
            chunks[-1].append(index)
        for number,indices in enumerate(chunks):
            partitioned.append(entry.model_copy(update={'entry_id':entry.entry_id+(f'-header-{number}' if number else ''),'block_indices':indices,'fields':{}}) if len(chunks)>1 else entry)
    revised.entries=partitioned
    for start,end,values in candidates:
        span=set(range(start,end+1))
        touching=[e for e in revised.entries if span.intersection(e.block_indices)]
        if not touching or any(min(e.block_indices)<start for e in touching):continue
        indices=sorted(span.union(*(set(e.block_indices) for e in touching)))
        if len(touching)==1 and indices==touching[0].block_indices:continue
        entry=SectionEntry(entry_id=touching[0].entry_id,block_indices=indices,lane=revised.blocks[start].lane,
                           boundary_reason='Adjacent role, employer and date rows form one source-backed employment header.')
        revised.entries=[e for e in revised.entries if e not in touching]+[entry]
        revised.entries.sort(key=lambda e:min(e.block_indices))
        events.append({'source_block_indices':list(range(start,end+1)),'joined_entries':len(touching)})
    if not events:return result
    annotate_relationships(revised)
    updated=result.model_copy(deep=True);updated.sections=[revised if s.category=='experience' else s for s in updated.sections]
    updated.metadata['split_employment_header_recovery']=events
    errors=validate_result(elements,updated)
    if errors:raise ValueError('Invalid source binding after split employment header recovery: '+repr(errors))
    return updated
