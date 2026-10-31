"""Retain separately dated, source-supported records through provisional review."""

def repair_dated_records(payload,source_sections,fallback):
    from local_api.services.llm_schema_mapping import local_section_payload
    repairs=[]
    for category,required in (('experience',('company','role','start_date','end_date')),('education',('degree','institution','graduation_year'))):
        local=local_section_payload(fallback,{category})
        row=next((r for r in payload.get('sections',[]) if isinstance(r,dict) and r.get('category')==category),None)
        if not local or row is None or not isinstance(row.get('records'),list):continue
        cards=local[0]['records']
        if len(cards)<2 or not all(all(c['fields'].get(name) for name in required) for c in cards):continue
        # A dated source header is evidence; arbitrary local keyword guesses are not.
        parent=next((s for s in source_sections.sections if s.category==category),None)
        if parent is None:continue
        if category=='experience':
            from local_api.services.dated_record_headers import dated_header_candidates
            if not all(dated_header_candidates([parent.blocks[i] for i in e.block_indices]) for e in parent.entries):continue
        old=row['records'];sets=[set(r.get('source_ids',[])) for r in old if isinstance(r,dict)]
        expected=[set(r['source_ids']) for r in cards]
        if len(sets)!=len(expected) or any(owner not in sets for owner in expected):
            row['records']=cards
            repairs.append({'code':'source_dated_records_restored','category':category,'records':len(cards)})
    return repairs
