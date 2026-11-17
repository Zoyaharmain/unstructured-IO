"""Headingless education needs both institution evidence and an aligned date."""
def education_pairs(elements):
    from local_api.services.record_relationships import field_kinds
    from local_api.services.record_subfields import RANGE, employment_header_fields, responsibility_fragment
    institutions=[]; dates=[]
    for i,e in enumerate(elements):
        text=e.get('text','') if isinstance(e,dict) else e.text
        metadata=e.get('metadata',{}) if isinstance(e,dict) else e.metadata
        page=e.get('page_number',metadata.get('page_number')) if isinstance(e,dict) else e.page_number
        if len(text.split())>16:
            continue
        lines=[h for h in metadata.get('pdf_source_lines',[]) if len(h.get('bbox',[]))==4]
        if 'institution' in field_kinds(text,'education') and not employment_header_fields(text) and not responsibility_fragment(text):
            institutions.extend((i,page,h['bbox']) for h in lines)
        elif RANGE.match(text.strip()):
            dates.extend((i,page,h['bbox']) for h in lines)
    pairs={}
    for i,page,box in dates:
        peers={j for j,p,b in institutions if p==page and abs(box[1]-b[1])<.008
               and (box[2]<=b[0]+.02 or b[2]<=box[0]+.02)}
        if len(peers)==1:
            pairs[i]=next(iter(peers))
    return {date:institution for date,institution in pairs.items() if list(pairs.values()).count(institution)==1}


def aligned_education_elements(elements):
    pairs=education_pairs(elements)
    return set(pairs)|set(pairs.values())


def recover_aligned_education(result, elements):
    """Keep positive physical relations coherent after optional model review."""
    selected=aligned_education_elements(elements)
    moved=[b for s in result.sections if s.category!='education' for b in s.blocks if b.source_element_index in selected]
    moved += [b for b in result.needs_review if b.source_element_index in selected]
    if not moved:
        return result
    from local_api.services.resume_sections import build_sections
    grouped={s.category:[b for b in s.blocks if b.source_element_index not in selected] for s in result.sections}
    grouped.setdefault('education',[])
    grouped['education'].extend(b for s in result.sections if s.category=='education' for b in s.blocks if b.source_element_index in selected)
    grouped['education'].extend(b.model_copy(update={'assignment':'education_relation',
        'reason':'Unique aligned date and institution evidence; employment assignment contradicted by source layout.'}) for b in moved)
    grouped={k:sorted(v,key=lambda b:(b.source_element_index,b.start)) for k,v in grouped.items() if v}
    out=result.model_copy(deep=True)
    rebuilt=build_sections(grouped,elements,refine=False)
    affected={'education'}|{s.category for s in result.sections if any(b.source_element_index in selected for b in s.blocks)}
    original={s.category:s for s in result.sections}
    out.sections=[s if s.category in affected else original[s.category].model_copy(deep=True) for s in rebuilt]
    out.needs_review=[b for b in out.needs_review if b.source_element_index not in selected]
    out.metadata['headingless_education_recovery']={'moved_spans':len(moved)}
    return out
