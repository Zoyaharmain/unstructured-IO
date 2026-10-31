"""Explicit project/program headings establish their own source section scope."""


def recover_project_sections(result,elements):
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary,normalized_heading
    from local_api.services.source_validation import validate_result
    blocks=sorted([b for s in result.sections for b in s.blocks]+list(result.needs_review),key=lambda b:(b.source_element_index,b.start))
    moved={};active=None
    for block in blocks:
        category,cut=heading_boundary(block.text,ALIASES)
        if category and cut is None:
            active=block if category=='projects' and normalized_heading(block.text) in ALIASES and set(normalized_heading(block.text).split()) & {'programs','initiatives'} else None
        if active is None:continue
        if block.source_element_index-active.source_element_index>100 or (active.page_number and block.page_number and block.page_number-active.page_number>2):
            active=None;continue
        key=(block.source_element_index,block.start,block.end)
        moved[key]=block.model_copy(update={'assignment':'structural_heading' if block is active else block.assignment,
            'reason':'Explicit project/program heading establishes source section ownership.'})
    if not moved:return result
    categories={key:s.category for s in result.sections for b in s.blocks for key in [(b.source_element_index,b.start,b.end)]}
    assignments={(b.source_element_index,b.start,b.end):b.assignment for b in blocks}
    if all(categories.get(key)=='projects' and b.assignment==assignments[key] for key,b in moved.items()):return result
    grouped={s.category:[b for b in s.blocks if (b.source_element_index,b.start,b.end) not in moved] for s in result.sections}
    grouped.setdefault('projects',[]).extend(moved.values())
    grouped={c:sorted(bs,key=lambda b:(b.source_element_index,b.start)) for c,bs in grouped.items() if bs}
    affected={categories[key] for key in moved if key in categories}|{'projects'}
    original={s.category:s for s in result.sections}
    updated=result.model_copy(deep=True)
    updated.sections=[s if s.category in affected else original[s.category].model_copy(deep=True) for s in build_sections(grouped,elements,refine=False)]
    updated.needs_review=[b for b in result.needs_review if (b.source_element_index,b.start,b.end) not in moved]
    updated.metadata['project_section_recovery']={'source_spans':len(moved)}
    assigned=sum(len(b.text.strip()) for s in updated.sections for b in s.blocks)
    total=assigned+sum(len(b.text.strip()) for b in updated.needs_review)
    updated.metadata.update(assigned_units=sum(len(s.blocks) for s in updated.sections),review_units=len(updated.needs_review),assigned_text_percent=round(100*assigned/max(1,total),1))
    updated.status='needs_review' if updated.needs_review else 'provisional'
    if validate_result(elements,updated):raise ValueError('Invalid source binding after project heading recovery')
    return updated


def repair_review_programs(payload,source_sections,fallback):
    """Preserve separately titled, dated program cards if review merges/omits them."""
    import re
    from local_api.services.llm_schema_mapping import local_section_payload
    local=local_section_payload(fallback,{'projects'})
    row=next((r for r in payload.get('sections',[]) if isinstance(r,dict) and r.get('category')=='projects'),None)
    if not local or row is None or not isinstance(row.get('records'),list):return []
    cards=local[0]['records']
    if len(cards)<2:return []
    if not all(len(r['fields']['name'])==1 and re.search(r'\b(?:program|project|initiative)\s*$',r['fields']['name'][0]['value'],re.I)
        and r['fields']['start_date'] and r['fields']['end_date'] and r['fields']['description'] for r in cards):return []
    old=row['records'];by_ids={frozenset(r['source_ids']):r for r in old if isinstance(r,dict) and isinstance(r.get('source_ids'),list) and all(isinstance(s,str) for s in r['source_ids'])}
    repairs=[];recovered=[]
    for card in cards:
        existing=by_ids.get(frozenset(card['source_ids']))
        if existing is None:
            recovered.append(card);repairs.append({'code':'dated_source_program_record_recovered','record_id':card['record_id']});continue
        for name in ('name','description','start_date','end_date'):
            if not isinstance(existing.get('fields'),dict):break
            if existing['fields'].get(name)!=card['fields'][name]:
                existing['fields'][name]=card['fields'][name]
                existing.setdefault('missing',{}).pop(name,None)
                repairs.append({'code':'complete_source_program_field_recovered','field':name,'record_id':existing.get('record_id')})
        recovered.append(existing)
    if repairs:row['records']=recovered
    return repairs
