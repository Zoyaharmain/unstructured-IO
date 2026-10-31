"""Distinguish an introductory professional headline from employment records."""
import re


def recover_professional_headline(result,elements):
    from local_api.services.record_subfields import ROLE,RANGE,employment_header_fields
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.source_validation import validate_result
    # Sidebar skills/contact can precede the main-column introduction. Real
    # work, qualifications and projects establish the end of the preamble.
    end=min((i for i,e in enumerate(elements) if heading_boundary(e.text,ALIASES)[0]
             in {'experience','education','projects','certifications','references'}),default=min(len(elements),20))
    all_blocks=sorted([b for s in result.sections for b in s.blocks]+list(result.needs_review),key=lambda b:(b.source_element_index,b.start))
    candidates=[]
    for block in all_blocks:
        index=block.source_element_index;text=block.text.strip()
        if index>=end or not 2<=len(text.split())<=18 or not ROLE.search(text) or RANGE.search(text):continue
        if re.search(r'\b(?:target|desired|seeking|preferred)\b',text,re.I):continue
        if employment_header_fields(text).get('company'):continue
        neighbors=elements[max(0,index-1):min(len(elements),index+3)]
        if any(RANGE.search(e.text) or re.match(r'^\s*(?:company|employer)\s*[:=]',e.text,re.I) for e in neighbors):continue
        el=elements[index]
        strong_style=(el.type=='Title' or any(r.get('bold') and r['start']<=block.start and r['end']>=block.end-1 for r in el.metadata.get('word_source_runs',[])))
        if not strong_style:continue
        following=[b for b in all_blocks if index<b.source_element_index<=index+2 and b.source_element_index<end and b.text.strip()]
        prose=next((b for b in following if len(b.text.split())>=15 and not RANGE.search(b.text)
                    and re.search(r'\b(?:speciali[sz]ing|proven track record|experienced|experience|expertise|professional|career|I am|I have)\b',b.text,re.I)),None)
        if prose:candidates.append((block,prose))
    if len(candidates)!=1:return result
    headline,summary=candidates[0];key=lambda b:(b.source_element_index,b.start,b.end)
    moving={key(headline):('personal_information','professional_headline'),key(summary):('summary','professional_summary_context')}
    owners={key(b):s.category for s in result.sections for b in s.blocks}
    if owners.get(key(headline))=='personal_information' and owners.get(key(summary))=='summary' and headline.assignment=='professional_headline':return result
    grouped={s.category:[b for b in s.blocks if key(b) not in moving] for s in result.sections}
    for block in (headline,summary):
        category,assignment=moving[key(block)]
        grouped.setdefault(category,[]).append(block.model_copy(update={'assignment':assignment,
            'reason':'Styled role headline and adjacent career-summary prose before actual history; no independent employment evidence.'}))
    grouped={c:sorted(bs,key=key) for c,bs in grouped.items() if bs}
    updated=result.model_copy(deep=True);old={s.category:s for s in result.sections}
    affected={owners[k] for k in moving if k in owners}|{'personal_information','summary'}
    updated.sections=[s if s.category in affected else old[s.category].model_copy(deep=True) for s in build_sections(grouped,elements,refine=False)]
    updated.needs_review=[b for b in result.needs_review if key(b) not in moving]
    updated.metadata['professional_headline_recovery']={'headline_source_element_index':headline.source_element_index,'summary_source_element_index':summary.source_element_index}
    if validate_result(elements,updated):raise ValueError('Invalid source binding after professional headline recovery')
    return updated
