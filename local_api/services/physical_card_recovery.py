"""Preserve physical identity rows and explicit supplemental section boundaries."""
import re


def recover_physical_cards(result,elements):
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.source_validation import validate_result
    grouped={s.category:list(s.blocks) for s in result.sections};events=[];affected=set()
    # Typography establishes a name/title boundary even when neither contains
    # an occupation keyword. Never join different physical font-size rows.
    personal=grouped.get('personal_information',[])
    opening=min((b.source_element_index for b in personal),default=-1)
    first=[b for b in personal if b.source_element_index==opening]
    if len(first)==2:
        name,title=sorted(first,key=lambda b:b.start)
        hints=elements[opening].metadata.get('pdf_source_lines',[])
        def row(block):return next((h for h in hints if h['start']<=block.start and h['end']>=block.start+len(block.text.rstrip()) and h.get('font_size')),None)
        a,b=row(name),row(title)
        if (a and b and a['bbox'][3]<b['bbox'][1] and a['font_size']>=b['font_size']*1.3
            and 2<=len(name.text.split())<=5 and 1<=len(title.text.split())<=12
            and re.fullmatch(r"[A-Za-z .'-]+",name.text.strip())
            and re.fullmatch(r"[A-Za-z &/,.'-]+",title.text.strip())):
            replacements={name.start:'candidate_name',title.start:'professional_headline'}
            grouped['personal_information']=[x.model_copy(update={'assignment':replacements[x.start]}) if x.source_element_index==opening and x.start in replacements else x for x in personal]
            if name.assignment!='candidate_name' or title.assignment!='professional_headline':events.append('physical_identity_rows');affected.add('personal_information')
    # Explicit headings can recover from an inherited category, including a
    # tightly bounded heading transposition. Never change literal source text.
    pending=[];owner=None
    for category,block in sorted([(c,b) for c,bs in grouped.items() for b in bs],key=lambda cb:(cb[1].source_element_index,cb[1].start)):
        heading,cut=heading_boundary(block.text,ALIASES)
        work=result.metadata.get('dated_employment_scope',{})
        if block.assignment=='local_record_continuation' or category=='experience' and work.get('source_start',-1)<block.source_element_index<work.get('source_end',-1):heading=None
        if heading and cut is None and (heading!='awards' or elements[block.source_element_index].type in {'Title','Header'}):owner=heading
        if owner=='awards' and category!='awards':pending.append((category,block))
    for category,block in pending:
        grouped[category].remove(block);grouped.setdefault('awards',[]).append(block);affected.update({category,'awards'});events.append('explicit_award_section')
    if not events:return result
    old={s.category:s for s in result.sections}
    revised=result.model_copy(deep=True)
    revised.sections=[s if s.category in affected else old[s.category].model_copy(deep=True) for s in build_sections({c:sorted(bs,key=lambda b:(b.source_element_index,b.start)) for c,bs in grouped.items() if bs},elements,refine=False)]
    # Rerouting a supplemental heading must not recluster unrelated employment
    # history. Retain established entries and reindex their surviving spans.
    for section in revised.sections:
        if section.category!='experience' or section.category not in affected:continue
        key=lambda b:(b.source_element_index,b.start,b.end)
        positions={key(b):i for i,b in enumerate(section.blocks)}
        original=old[section.category];entries=[]
        for entry in original.entries:
            remap={i:positions[key(original.blocks[i])] for i in entry.block_indices if key(original.blocks[i]) in positions}
            if remap:entries.append(entry.model_copy(update={'block_indices':[remap[i] for i in entry.block_indices if i in remap],
                'fields':{field:[remap[i] for i in ids if i in remap] for field,ids in entry.fields.items()}}))
        section.entries=entries
    revised.metadata['physical_card_recovery']=sorted(set(events))
    errors=validate_result(elements,revised)
    if errors:raise ValueError('Invalid physical card source binding: '+repr(errors))
    return revised


def repair_physical_card_fields(payload,sections,fallback):
    """Keep source-established identities and award cards through field review."""
    from local_api.services.source_fragments import citations
    from local_api.services.llm_schema_mapping import local_section_payload
    repairs=[]
    for row in payload.get('sections',[]):
        if not isinstance(row,dict):continue
        category=row.get('category');parent=next((s for s in sections.sections if s.category==category),None)
        if parent is None or not isinstance(row.get('records'),list):continue
        local=local_section_payload(fallback,{category})
        if not local:continue
        if category=='personal_information' and len(row['records'])==1:
            names=[b for b in parent.blocks if b.assignment=='candidate_name']
            if len(names)==1:
                value=names[0].text.strip();record=row['records'][0];refs=citations(value,parent.blocks)
                if record.get('fields',{}).get('full_name')!=[{'value':value,'evidence':refs}]:
                    record['fields']['full_name']=[{'value':value,'evidence':refs}];record.setdefault('missing',{}).pop('full_name',None)
                    repairs.append({'code':'physical_name_restored','field':'full_name'})
        if category not in {'awards','education'}:continue
        inventory={f'e{b.source_element_index}:{b.start}:{b.end}':b for b in parent.blocks}
        for card in local[0]['records']:
            fields=card['fields'];ids=set(card['source_ids'])
            # Only established compound source cards are authoritative here.
            strong=(category=='awards' and fields.get('name') and fields.get('description')
                    or category=='education' and fields.get('degree') and fields.get('institution') and (fields.get('graduation_year') or any(e.context_fields for e in parent.entries if e.entry_id==card['record_id'])))
            if not strong:continue
            touching=[r for r in row['records'] if isinstance(r,dict) and set(r.get('source_ids',[])) & ids]
            if len(touching)!=1 or set(touching[0].get('source_ids',[]))!=ids:
                if all(set(r.get('source_ids',[]))<=ids for r in touching):
                    row['records']=[r for r in row['records'] if r not in touching]+[card]
                    repairs.append({'code':'physical_source_card_restored','category':category})
                continue
            record=touching[0]
            names=('name','description','date') if category=='awards' else ('degree','institution','start_year','graduation_year','grade_or_gpa')
            for name in names:
                if fields.get(name) and record.get('fields',{}).get(name)!=fields[name]:
                    record['fields'][name]=fields[name];record.setdefault('missing',{}).pop(name,None)
                    repairs.append({'code':'physical_source_field_restored','category':category,'field':name})
    return repairs
