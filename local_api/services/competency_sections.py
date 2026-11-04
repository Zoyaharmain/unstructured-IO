"""Source-bound competency names and profile descriptions under explicit headings."""
import re

LABEL=re.compile(r'(?:^|(?<=[.!?])\s+|(?<=[•▪●])\s*)([A-Z][A-Za-z0-9 &/()\-]{1,90}):\s*')
CAPABILITY=re.compile(r'\b(?:management|leadership|strategy|planning|transformation|engineering|development|architecture|analytics|analysis|security|governance|compliance|design|delivery|operations|migration|optimization|improvement|expansion|engagement|expertise|finance|accounting|sales|marketing)\b',re.I)


def expertise_heading(text):
    from local_api.services.resume_structure import normalized_heading
    value=normalized_heading(text)
    return bool(re.fullmatch(r'(?:areas?|fields?) of (?:expertise|speciali[sz]ation|competenc(?:e|y|ies))(?: (?:and|/) (?:interests?|skills?|capabilities))?',value))


def recover_competency_sections(result,elements):
    from local_api.services.review_resolution import document_scope
    if document_scope(elements)['candidate_resume'] is False:return result
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.source_validation import validate_result
    from local_api.services.standardization.dictionaries import TECH_ALIASES
    windows=[]
    for start,e in enumerate(elements):
        if not expertise_heading(e.text):continue
        end=len(elements)
        for i in range(start+1,len(elements)):
            category,cut=heading_boundary(elements[i].text,ALIASES)
            text=elements[i].text.strip()
            if category and cut is None or elements[i].type in {'Title','Header'} and text.isupper() and len(text.split())<=8 and ':' not in text:
                end=i;break
        windows.append((start,end))
    if not windows:return result
    all_blocks=[b for s in result.sections for b in s.blocks]+list(result.needs_review)
    owners={(b.source_element_index,b.start,b.end):s.category for s in result.sections for b in s.blocks}
    replacements={};records=[]
    for start,end in windows:
        active=None
        for index in range(start,end):
            existing=sorted([b for b in all_blocks if b.source_element_index==index],key=lambda b:b.start)
            if not existing or not elements[index].text.strip():continue
            text=elements[index].text
            if index==start:
                replacements[index]=[(b.model_copy(update={'assignment':'structural_heading','reason':'Explicit professional expertise heading.'}),'skills') for b in existing]
                continue
            labels=list(LABEL.finditer(text))
            if labels and any(not (CAPABILITY.search(m[1]) or m[1].casefold() in TECH_ALIASES) for m in labels):
                active=None;continue
            if not labels:
                if active is None:continue
                parts=[(0,len(text),'summary','local_competency_description')]
            else:
                parts=[]
                if labels[0].start()>0:
                    prefix=text[:labels[0].start()]
                    parts.append((0,labels[0].start(),'summary' if active and any(c.isalnum() for c in prefix) else 'skills','local_competency_description' if active and any(c.isalnum() for c in prefix) else 'structural_heading'))
                for number,match in enumerate(labels):
                    stop=labels[number+1].start() if number+1<len(labels) else len(text)
                    name_start,name_end=match.span(1);active=match[1]
                    if match.start()<name_start:parts.append((match.start(),name_start,'skills','structural_heading'))
                    parts.append((name_start,match.end(),'skills','local_competency_name'))
                    if match.end()<stop:parts.append((match.end(),stop,'summary','local_competency_description'))
                    records.append({'name':active,'source_element_index':index,'name_start':name_start,'name_end':name_end,'description_start':match.end(),'description_end':stop})
            output=[]
            for first,last,category,assignment in parts:
                if first==last:continue
                template=next((b for b in existing if b.start<=first<b.end),existing[0])
                output.append((template.model_copy(update={'start':first,'end':last,'text':text[first:last],
                    'assignment':assignment,'reason':'Source-labeled professional capability and its career-wide explanation; no employer/date association inferred.',
                    'llm_action':'source_backed_recovery' if template.reviewed_by_llm else None}),category))
            replacements[index]=output
    if not replacements:return result
    # Repeated recovery is a no-op when all literal intervals already agree.
    desired={(b.source_element_index,b.start,b.end):(category,b.assignment) for pairs in replacements.values() for b,category in pairs}
    if all(owners.get(key)==category and next((b.assignment for b in all_blocks if (b.source_element_index,b.start,b.end)==key),None)==assignment for key,(category,assignment) in desired.items()) and sum(b.source_element_index in replacements for b in all_blocks)==len(desired):return result
    affected={s.category for s in result.sections if any(b.source_element_index in replacements for b in s.blocks)}|{'skills','summary'}
    grouped={s.category:[b for b in s.blocks if b.source_element_index not in replacements] for s in result.sections}
    for pairs in replacements.values():
        for block,category in pairs:grouped.setdefault(category,[]).append(block)
    old={s.category:s for s in result.sections};revised=result.model_copy(deep=True)
    revised.sections=[s if s.category in affected else old[s.category].model_copy(deep=True) for s in build_sections({c:sorted(bs,key=lambda b:(b.source_element_index,b.start)) for c,bs in grouped.items() if bs},elements,refine=False)]
    # Removing preamble fragments must not recluster unrelated dated records.
    for section in revised.sections:
        if section.category in {'skills','summary'} or section.category not in old:continue
        positions={(b.source_element_index,b.start,b.end):i for i,b in enumerate(section.blocks)};original=old[section.category];entries=[]
        for entry in original.entries:
            remap={i:positions[(original.blocks[i].source_element_index,original.blocks[i].start,original.blocks[i].end)] for i in entry.block_indices if (original.blocks[i].source_element_index,original.blocks[i].start,original.blocks[i].end) in positions}
            if remap:entries.append(entry.model_copy(update={'block_indices':[remap[i] for i in entry.block_indices if i in remap], 'fields':{f:[remap[i] for i in ids if i in remap] for f,ids in entry.fields.items()}}))
        section.entries=entries
    revised.needs_review=[b for b in result.needs_review if b.source_element_index not in replacements]
    # Reconstructed elements include their separators; do not retain an old
    # whitespace artifact for the same interval as a duplicate source claim.
    revised.source_artifacts=[b for b in result.source_artifacts if b.source_element_index not in replacements]
    revised.metadata['competency_section_recovery']={'records':records,'policy':'Literal competency names -> skills; career-wide explanations -> summary; source intervals preserved.'}
    errors=validate_result(elements,revised)
    if errors:raise ValueError('Invalid competency source coverage: '+repr(errors))
    return revised


def repair_competency_fields(payload,sections):
    from local_api.services.source_fragments import citations,texts
    from local_api.services.employment_details import covered_by_values
    repairs=[]
    for category in ('skills','summary'):
        parent=next((s for s in sections.sections if s.category==category),None)
        row=next((r for r in payload.get('sections',[]) if isinstance(r,dict) and r.get('category')==category),None)
        if parent is None or row is None or len(row.get('records',[]))!=1:continue
        record=row['records'][0]
        if not isinstance(record.get('fields'),dict) or not isinstance(record.get('source_ids'),list):continue
        blocks=[b for b in parent.blocks if b.assignment not in {'section_heading','structural_heading'}]
        def add_sources(refs):
            record['source_ids'].extend(r['source_id'] for r in refs if r['source_id'] not in record['source_ids'])
        if category=='skills':
            known={str(item.get('value','')).casefold() for items in record['fields'].values() if isinstance(items,list) for item in items if isinstance(item,dict)}
            for block in blocks:
                if block.assignment!='local_competency_name':continue
                value=block.text.strip().removesuffix(':').rstrip();refs=citations(value,blocks)
                if value.casefold() in known or not refs:continue
                record['fields'].setdefault('domain_and_functional',[]).append({'value':value,'evidence':refs})
                record.setdefault('missing',{}).pop('domain_and_functional',None);add_sources(refs);known.add(value.casefold())
                repairs.append({'code':'literal_competency_name_restored','field':'domain_and_functional'})
        else:
            descriptions=[{'value':b.text.strip(),'evidence':citations(b.text.strip(),blocks)} for b in blocks if b.assignment=='local_competency_description' and b.text.strip()]
            if descriptions and not covered_by_values(descriptions,record['fields'].get('statements',[]),blocks):
                complete=[{'value':value.strip(),'evidence':citations(value.strip(),blocks)} for value in texts(blocks) if value.strip()]
                record['fields']['statements']=[item for item in complete if item['evidence']]
                record.setdefault('missing',{}).pop('statements',None)
                for item in record['fields']['statements']:add_sources(item['evidence'])
                repairs.append({'code':'competency_explanations_source_coverage_restored','field':'statements'})
    return repairs
