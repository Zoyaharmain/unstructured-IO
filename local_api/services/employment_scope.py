"""Dated employer/role headers own work subheadings and client project details."""
import re


def recover_employment_scope(result,elements):
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.record_subfields import employment_header_fields,RANGE,ROLE,responsibility_fragment,labelled_fields
    from local_api.schemas.sections import SectionEntry
    from local_api.services.record_relationships import annotate_relationships
    from local_api.services.source_validation import validate_result
    start=None;end=None
    for i,element in enumerate(elements):
        category,cut=heading_boundary(element.text,ALIASES)
        if category=='experience' and cut is None and len(element.text.split())<=5:start=i;break
    if start is None:return result
    for i in range(start+1,len(elements)):
        text=elements[i].text.strip();category,cut=heading_boundary(text,ALIASES)
        if category and category!='experience' and cut is None and not re.match(r'^(?:key|impact|governance|technology|tools|agile|client|responsibilit)',text,re.I):
            end=i;break
    if end is None:end=len(elements)
    anchors=[]
    for i in range(start+1,end):
        element=elements[i]
        for period in RANGE.finditer(element.text):
            offsets={0}|{h['start'] for h in element.metadata.get('pdf_source_lines',[]) if h['start']<=period.start()}
            candidates=[]
            for first in offsets:
                quote=element.text[first:period.end()]
                fields=employment_header_fields(quote)
                if '\n' in quote:
                    from types import SimpleNamespace
                    from local_api.services.dated_record_headers import split_employment_headers
                    split=split_employment_headers([SimpleNamespace(text=quote,assignment='local_employment_header',page_number=element.page_number,lane='source',source_element_index=i)])
                    if len(split)==1:fields=split[0][2]
                    else:
                        identities=[employment_header_fields(line) for line in quote.splitlines()]
                        identities=[identity for identity in identities if identity.get('company') and identity.get('role')]
                        if len(identities)==1:fields=identities[0]

                if any(re.search(r'\b(?:Client|Domain|Program|Role)\s*:',str(fields.get(key,'')),re.I) for key in ('company','role')):continue
                if fields.get('company') and fields.get('role') and not re.match(r'^(?:client|program|project)\s*:',quote,re.I):
                    candidates.append((first,fields))
            if candidates:
                first,fields=max(candidates,key=lambda c:c[0]);fields.update(start_date=period[1],end_date=period[2],duration=period.group());anchors.append((i,first,i,period.end(),fields))
            else:
                # A complete identity row can be followed by a separate date
                # row or location/date row in another extracted element.
                leading=element.text[:period.start()].strip(' |')
                if leading and not re.fullmatch(r'[A-Z][A-Za-z .,-]{1,50}',leading):continue
                for previous in range(i-1,max(start,i-3),-1):
                    text=elements[previous].text.strip()
                    if not text:continue
                    fields=employment_header_fields(text)
                    if fields.get('company') and fields.get('role') and elements[previous].page_number==element.page_number:
                        fields.update(start_date=period[1],end_date=period[2],duration=period.group())
                        if leading and not fields.get('location'):fields['location']=leading
                        anchors.append((previous,0,i,period.end(),fields));break
                    # Only a compact location row can intervene; never cross
                    # a responsibility or another unrecognized record.
                    if not re.fullmatch(r'[A-Z][A-Za-z .,-]{1,50}',text) or len(text.split())>6:break
    # A short generic tools row or undated role is never an employment anchor.
    if not anchors:return result
    # Never fold an unrecognized dated job into its neighbor merely because
    # other jobs use a more explicit header format.
    represented={(date_index,last) for _,_,date_index,last,_ in anchors}
    if any((i,period.end()) not in represented for i in range(start+1,end) for period in RANGE.finditer(elements[i].text)):
        return result
    header_elements={index for index,_,_,_,_ in anchors}
    for i in range(start+1,end):
        if i in header_elements:continue
        if (elements[i].type in {'Title','Header'} and len(elements[i].text.split())<=12
            and ROLE.search(elements[i].text) and not any(a<=i<=d for a,_,d,_,_ in anchors)):
            return result
        identity=employment_header_fields(elements[i].text)
        if identity.get('company') and identity.get('role') and not RANGE.search(elements[i].text):
            return result
    grouped={s.category:list(s.blocks) for s in result.sections}
    selected=[];affected={'experience'}
    for category,blocks in list(grouped.items()):
        remaining=[]
        for block in blocks:
            if start<=block.source_element_index<end:
                selected.append(block);affected.add(category)
            else:remaining.append(block)
        grouped[category]=remaining
    pending=[]
    for block in result.needs_review:
        in_scope=start<=block.source_element_index<end
        header=any((a,o)<=(block.source_element_index,block.start)<=(d,last) for a,o,d,last,_ in anchors)
        meaningful_body=(responsibility_fragment(block.text) or elements[block.source_element_index].type=='ListItem'
                         or labelled_fields('experience',[block])
                         or len(block.text.split())>=6 and (block.text.rstrip().endswith(('.',',',';')) or block.text[:1].islower()))
        if in_scope and (header or meaningful_body):selected.append(block)
        else:pending.append(block)
    # A recovered header can begin at a physical row inside a long paragraph.
    from local_api.services.employment_details import physical_bullet_starts
    bullet_starts=physical_bullet_starts(elements)
    pieces=[]
    for b in selected:
        cuts=[b.start]+sorted({offset for index,offset,_,_,_ in anchors if index==b.source_element_index and b.start<offset<b.end}|{last for _,_,date_index,last,_ in anchors if date_index==b.source_element_index and b.start<last<b.end}|{offset for offset in bullet_starts.get(b.source_element_index,set()) if b.start<offset<b.end})+[b.end]
        for first,last in zip(cuts,cuts[1:]):
            pieces.append(b.model_copy(update={'start':first,'end':last,'text':elements[b.source_element_index].text[first:last]}))
    pieces.sort(key=lambda b:(b.source_element_index,b.start))
    grouped['experience']=sorted(grouped.get('experience',[])+pieces,key=lambda b:(b.source_element_index,b.start))
    rebuilt=build_sections({c:bs for c,bs in grouped.items() if bs},elements,refine=False)
    section=next(s for s in rebuilt if s.category=='experience')
    cards=[]
    anchors.sort(key=lambda a:(a[0],a[1]))
    for index,offset,date_index,last,fields in anchors:
        cards.append(SectionEntry(entry_id=f'experience-{len(cards)+1}',block_indices=[],lane='source',boundary_reason='Complete literal employer/role/date header; nested work details remain with this job.'))
    for position,b in enumerate(section.blocks):
        if not start<b.source_element_index<end:continue
        owners=[i for i,a in enumerate(anchors) if (a[0],a[1])<=(b.source_element_index,b.start)]
        if not owners:continue
        label_only=bool(re.fullmatch(r'\s*(?:(?:Key\s+)?Responsibilities(?:\s*(?:&|and)\s*Achievements)?|Key Achievements|Governance\s*&\s*Agile Leadership|Agile\s*&\s*Scrum Best Practices|Impact\s*&\s*Value Delivered|Technology\s*&\s*Tools)\s*:?\s*[•▪● ]*',b.text,re.I))
        if label_only:
            section.blocks[position]=b.model_copy(update={'assignment':'structural_heading'})
            continue
        owner=owners[-1];section.blocks[position]=b.model_copy(update={'assignment':'local_employment_header' if (b.source_element_index,b.start)<(anchors[owner][2],anchors[owner][3]) else 'local_responsibility_bullet' if b.start in bullet_starts.get(b.source_element_index,set()) else 'local_record_continuation'})
        cards[owner].block_indices.append(position)
    scope_cards=[c for c in cards if c.block_indices]
    # Preserve source and established record ownership outside this chapter.
    # Sidebar/preamble corrections and later engagement recovery run afterward.
    positions={(b.source_element_index,b.start,b.end):i for i,b in enumerate(section.blocks)}
    outside=[]
    prior=next((s for s in result.sections if s.category=='experience'),None)
    if prior:
        for entry in prior.entries:
            remap={i:positions[(prior.blocks[i].source_element_index,prior.blocks[i].start,prior.blocks[i].end)] for i in entry.block_indices
                   if not start<=prior.blocks[i].source_element_index<end}
            if remap:
                identifier=entry.entry_id if entry.entry_id.endswith('-outside-scope') else entry.entry_id+'-outside-scope'
                outside.append(entry.model_copy(update={'entry_id':identifier,'block_indices':[remap[i] for i in entry.block_indices if i in remap],
                    'fields':{name:[remap[i] for i in ids if i in remap] for name,ids in entry.fields.items()}}))
    section.entries=sorted(scope_cards+outside,key=lambda entry:min(entry.block_indices))
    annotate_relationships(section)
    # Identity hints refer to the complete header region, not words in tools.
    for card,anchor in zip(scope_cards,anchors):
        header=[i for i in card.block_indices if (section.blocks[i].source_element_index,section.blocks[i].start)<(anchor[2],anchor[3])]
        from local_api.services.source_fragments import citations
        for field,name in (('employer','company'),('title','role'),('location','location')):
            refs=citations(anchor[4].get(name,''),[section.blocks[i] for i in header]) if anchor[4].get(name) else []
            ids={ref['source_id'] for ref in refs}
            if refs:card.fields[field]=[i for i in header if f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' in ids]
        card.fields['dates']=header
    old={s.category:s for s in result.sections}
    revised=result.model_copy(deep=True);revised.sections=[s if s.category in affected else old[s.category].model_copy(deep=True) for s in rebuilt];revised.needs_review=pending
    revised.metadata['dated_employment_scope']={'headers':len(anchors),'source_start':start,'source_end':end,'subheadings_do_not_create_jobs':True,'literal_records':{card.entry_id:anchor[4] for card,anchor in zip(scope_cards,anchors)}}
    errors=validate_result(elements,revised)
    if errors:raise ValueError('Invalid dated employment scope: '+repr(errors))
    return revised


def repair_dated_employment_scope(payload,sections,fallback):
    if not sections.metadata.get('dated_employment_scope'):return []
    from local_api.services.llm_schema_mapping import local_section_payload
    row=next((s for s in payload.get('sections',[]) if isinstance(s,dict) and s.get('category')=='experience'),None)
    if row is None or not isinstance(row.get('records'),list):return []
    local=local_section_payload(fallback,{'experience'})
    if not local:return []
    cards=local[0]['records']
    if not cards or not all(all(r['fields'].get(k) for k in ('company','role','start_date','end_date')) for r in cards):return []
    owners={frozenset(r['source_ids']):r for r in cards}
    current=[frozenset(r.get('source_ids',[])) for r in row['records'] if isinstance(r,dict)]
    if len(current)!=len(owners) or set(current)!=set(owners):
        row['records']=cards
        return [{'code':'dated_employment_records_restored','records':len(cards)}]
    repairs=[]
    for record in row['records']:
        source=owners[frozenset(record['source_ids'])]
        if not isinstance(record.get('fields'),dict):continue
        from local_api.services.employment_details import covered_by_values
        parent=next(s for s in sections.sections if s.category=='experience')
        allowed=[b for b in parent.blocks if f'e{b.source_element_index}:{b.start}:{b.end}' in record['source_ids']]
        for name in ('responsibilities','technologies'):
            expected=source['fields'][name]
            if expected and not covered_by_values(expected,record['fields'].get(name,[]),allowed):
                record['fields'][name]=expected;record.setdefault('missing',{}).pop(name,None)
                repairs.append({'code':'employment_source_content_restored','field':name,'record_id':record['record_id']})
        for name in ('company','role','start_date','end_date','duration','location'):
            expected=source['fields'][name]
            if expected and record['fields'].get(name)!=expected:
                record['fields'][name]=expected;record.setdefault('missing',{}).pop(name,None)
                repairs.append({'code':'dated_employment_identity_restored','field':name})
    return repairs
