"""Repair only source-established prose splits; never infer a new employer."""
import re


def repair_employment_entries(result, elements):
    from local_api.services.record_subfields import responsibility_fragment, employment_header_fields, RANGE
    from local_api.services.record_relationships import annotate_relationships
    section = next((s for s in result.sections if s.category == 'experience'), None)
    if section is None: return result
    repaired = section.model_copy(deep=True); entries=[];events=[]
    for entry in repaired.entries:
        parts=[repaired.blocks[i] for i in entry.block_indices if re.search(r'\w',repaired.blocks[i].text)]
        if not parts or not entries:
            entries.append(entry);continue
        first=parts[0]; source=elements[first.source_element_index].text
        source_prose=elements[first.source_element_index].type == 'ListItem' and responsibility_fragment(source) and not employment_header_fields(source)
        prose=responsibility_fragment(first.text) or source_prose
        prior=entries[-1]; previous=[repaired.blocks[i] for i in prior.block_indices]
        adjacent=previous and first.page_number==previous[-1].page_number and 0 <= first.source_element_index-previous[-1].source_element_index <= 1
        compatible=previous and (first.lane==previous[-1].lane or 'wide' in {first.lane,previous[-1].lane})
        own_header=any(not (elements[b.source_element_index].type == 'ListItem' and responsibility_fragment(elements[b.source_element_index].text) and not employment_header_fields(elements[b.source_element_index].text))
                       and employment_header_fields(b.text) for b in parts)
        anchored=any(RANGE.search(b.text) and not responsibility_fragment(b.text) for b in previous)
        if not (prose and adjacent and compatible and anchored and not own_header):
            entries.append(entry);continue
        for i in entry.block_indices:
            repaired.blocks[i]=repaired.blocks[i].model_copy(update={'assignment':'local_record_continuation',
                'reason':'Action-led source paragraph continues the adjacent dated employment entry; no independent employment header.'})
        prior.block_indices.extend(entry.block_indices)
        events.append({'removed_entry_id':entry.entry_id,'owning_entry_id':prior.entry_id,
                       'source_element_indices':sorted({b.source_element_index for b in parts})})
    if not events:return result
    repaired.entries=entries;annotate_relationships(repaired)
    updated=result.model_copy(deep=True)
    updated.sections=[repaired if s.category=='experience' else s for s in updated.sections]
    updated.metadata['employment_prose_repairs']=events
    return updated


def repair_review_employment(payload, source_sections):
    """Repair supported truncations/prose splits in provisional provider records."""
    from local_api.services.record_subfields import responsibility_fragment, refine_record
    from local_api.services.source_fragments import citations, texts
    from local_api.schemas.subschema_spec import SUBSCHEMAS
    section=next((s for s in source_sections.sections if s.category=='experience'),None)
    row=next((r for r in payload.get('sections',[]) if isinstance(r,dict) and r.get('category')=='experience'),None)
    if section is None or row is None or not isinstance(row.get('records'),list):return []
    inventory={f'e{b.source_element_index}:{b.start}:{b.end}':b for b in section.blocks}
    owners={entry.entry_id:{f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' for i in entry.block_indices} for entry in section.entries}
    records=[];repairs=[]
    for record in row['records']:
        if not isinstance(record,dict) or not isinstance(record.get('fields'),dict) or not isinstance(record.get('source_ids'),list):
            records.append(record);continue
        ids=record['source_ids'];blocks=[b for sid,b in inventory.items() if sid in ids]
        company=record['fields'].get('company')
        company=company[0].get('value') if isinstance(company,list) and len(company)==1 and isinstance(company[0],dict) else None
        owner=[key for key,values in owners.items() if ids and set(ids)<=values]
        previous=records[-1] if records and isinstance(records[-1],dict) else None
        previous_ids=previous.get('source_ids',[]) if previous else []
        same_owner=bool(len(owner)==1 and previous_ids and set(previous_ids)<=owners[owner[0]])
        if (isinstance(company,str) and responsibility_fragment(company) and blocks and previous
            and same_owner and not set(ids)&set(previous_ids)
            and isinstance(previous.get('fields'),dict) and isinstance(previous['fields'].get('responsibilities'),list)
            and min(list(inventory).index(sid) for sid in ids) > max(list(inventory).index(sid) for sid in previous_ids)):
            old=previous['fields']['responsibilities']
            for paragraph in texts(blocks):
                value=paragraph.strip();refs=citations(value,blocks)
                if not refs:continue
                old=[item for item in old if not (isinstance(item,dict) and isinstance(item.get('value'),str) and item['value'] in value)]
                old.append({'value':value,'evidence':refs})
            previous['fields']['responsibilities']=old
            previous.setdefault('missing',{}).pop('responsibilities',None)
            previous['source_ids']=[sid for sid in inventory if sid in set(previous_ids)|set(ids)]
            repairs.append({'code':'prose_record_restored_to_source_owner','removed_record_id':record.get('record_id'),'owning_record_id':previous.get('record_id')})
            continue
        empty={name:[] if spec['multiple'] else None for name,spec in SUBSCHEMAS['experience'].items()}
        explicit,_=refine_record('experience',empty,blocks)
        from local_api.services.dated_record_headers import dated_header_candidates
        dated_headers=dated_header_candidates(blocks)
        if len(dated_headers)==1:
            for name,value in dated_headers[0].items():
                refs=citations(value,blocks)
                existing=record['fields'].get(name)
                if refs and (not existing or len(existing)==1 and existing[0].get('value')!=value):
                    record['fields'][name]=[{'value':value,'evidence':refs}]
                    record.setdefault('missing',{}).pop(name,None)
                    repairs.append({'code':'dated_identity_header_restored','field':name,'normalized_value':value})
        independent=explicit.get('role') or ''
        if (re.match(r'^(?:independent|freelance|self[- ]employed)\s+',independent,re.I)
            and explicit.get('company') is None and company and company in independent):
            record['fields']['company']=[]
            record.setdefault('missing',{})['company']='not_stated'
            refs=citations(independent,blocks)
            if refs:
                record['fields']['role']=[{'value':independent,'evidence':refs}]
                record['missing'].pop('role',None)
            repairs.append({'code':'independent_practice_not_employer','original_value':company,'normalized_value':None})
        for name in ('start_date','end_date','role'):
            items=record['fields'].get(name)
            old=items[0].get('value') if isinstance(items,list) and len(items)==1 and isinstance(items[0],dict) else None
            new=explicit.get(name)
            if not isinstance(old,str) or not isinstance(new,str) or old==new:continue
            richer_date=name.endswith('_date') and re.fullmatch(r'(?:19|20)\d{2}',old.strip()) and re.search(r'\b'+re.escape(old.strip())+r'\b',new) and len(new)>4
            glued_month=name=='role' and old.startswith(new) and re.fullmatch(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)',old[len(new):].strip(),re.I)
            refs=citations(new,blocks)
            if (richer_date or glued_month) and refs:
                record['fields'][name]=[{'value':new,'evidence':refs}]
                repairs.append({'code':'source_header_field_restored','field':name,'original_value':old,'normalized_value':new})
        records.append(record)
    row['records']=records
    return repairs
