"""Separate education and certification rows under a shared explicit heading."""
import re


def combined_heading(text):
    value=text.strip().rstrip(':').casefold()
    pieces=re.split(r'\s*(?:&|/|\band\b)\s*',value)
    education={'education','academic qualifications','qualifications'}
    credentials={'certification','certifications','certificates','credentials','licenses','licences'}
    return len(pieces)==2 and ((pieces[0] in education and pieces[1] in credentials) or (pieces[1] in education and pieces[0] in credentials))


def recover_combined_credentials(result,elements):
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.education_subfields import DEGREE
    from local_api.services.certification_integrity import credential_date_range
    from local_api.services.source_validation import validate_result
    starts=[i for i,e in enumerate(elements) if combined_heading(e.text)]
    if not starts:return result
    scope=set();headings=set(starts)
    for start in starts:
        for i in range(start,min(len(elements),start+50)):
            if i>start and heading_boundary(elements[i].text,ALIASES)[0]:break
            if elements[start].page_number and elements[i].page_number and elements[i].page_number-elements[start].page_number>2:break
            scope.add(i)
    original=[(s.category,b) for s in result.sections for b in s.blocks]+[(None,b) for b in result.needs_review]
    pieces=[]
    for category,block in original:
        if block.source_element_index not in scope:
            pieces.append((category,block));continue
        lines=elements[block.source_element_index].metadata.get('pdf_source_lines',[])
        cuts=sorted({block.start,block.end}|{r['start'] for r in lines if block.start<r.get('start',0)<block.end})
        if not block.text:pieces.append((category,block));continue
        for a,z in zip(cuts,cuts[1:]):
            pieces.append((category,block.model_copy(update={'start':a,'end':z,'text':elements[block.source_element_index].text[a:z]})))
    def rows(block):
        return [r for r in elements[block.source_element_index].metadata.get('pdf_source_lines',[])
                if len(r.get('bbox',[]))==4 and min(block.end,r.get('end',0))>max(block.start,r.get('start',0))]
    owners={}
    for j,(category,block) in enumerate(pieces):
        if block.source_element_index not in scope or block.source_element_index in headings:continue
        if DEGREE.search(block.text):owners[j]='education'
        elif re.search(r'\b(?:certified|certification|certificate|licen[cs]e|workshop|bootcamp)\b',block.text,re.I):owners[j]='certifications'
    for j,(category,block) in enumerate(pieces):
        if block.source_element_index not in scope or not credential_date_range(block.text):continue
        aligned={owner for k,owner in owners.items() if pieces[k][1].page_number==block.page_number
                 for left in rows(pieces[k][1]) for right in rows(block)
                 if abs(left['bbox'][1]-right['bbox'][1])<.004 and right['bbox'][0]>=left['bbox'][2]}
        if len(aligned)==1:owners[j]=next(iter(aligned))
    grouped={};pending=[]
    for j,(category,block) in enumerate(pieces):
        chosen=owners.get(j,category)
        if block.source_element_index in headings:
            chosen=category or 'education'
            block=block.model_copy(update={'assignment':'structural_heading','reason':'Shared education/certification heading; not a qualification or credential.'})
        elif j in owners:
            block=block.model_copy(update={'assignment':'combined_credential_source_row','reason':'Literal degree/certificate identity or uniquely aligned source date in a shared section.'})
        if chosen:grouped.setdefault(chosen,[]).append(block)
        else:pending.append(block)
    for blocks in grouped.values():blocks.sort(key=lambda b:(b.source_element_index,b.start))
    rebuilt=build_sections(grouped,elements,refine=False)
    updated=result.model_copy(deep=True);old={s.category:s for s in result.sections}
    affected={c for c,b in original if b.source_element_index in scope and c}|{'education','certifications'}
    updated.sections=[s if s.category in affected else old[s.category].model_copy(deep=True) for s in rebuilt]
    updated.needs_review=pending
    updated.metadata['combined_credential_recovery']={'source_heading_elements':starts,'classified_source_rows':len(owners)}
    if validate_result(elements,updated):raise ValueError('Invalid source binding after combined credential recovery')
    return updated if updated.model_dump()!=result.model_dump() else result
