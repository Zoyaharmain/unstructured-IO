"""Explicit institution context for sibling qualifications in one source element."""
import re


def recover_education_context(result):
    section=next((s for s in result.sections if s.category=='education'),None)
    if section is None:return result
    from local_api.services.record_relationships import field_kinds
    revised=section.model_copy(deep=True);changed=False
    for entry in revised.entries:
        qualification=[revised.blocks[i] for i in entry.block_indices if re.search(r'\bClass\s+(?:10th|12th|XII|X)(?!\w)',revised.blocks[i].text,re.I)]
        if len(qualification)!=1 or entry.fields.get('institution'):continue
        source=qualification[0].source_element_index
        siblings=[e for e in revised.entries if e is not entry and any(revised.blocks[i].source_element_index==source and re.search(r'\bClass\s+',revised.blocks[i].text,re.I) for i in e.block_indices)]
        schools={i for sibling in siblings for i in sibling.fields.get('institution',[])
                 if 'institution' in field_kinds(revised.blocks[i].text,'education')
                 and 'qualification' not in field_kinds(revised.blocks[i].text,'education')
                 and revised.blocks[i].page_number==qualification[0].page_number
                 and 0<=source-revised.blocks[i].source_element_index<=2}
        if len(schools)==1:
            context={'institution':sorted(schools)}
            if entry.context_fields!=context:entry.context_fields=context;changed=True
    if not changed:return result
    updated=result.model_copy(deep=True);updated.sections=[revised if s.category=='education' else s for s in updated.sections]
    updated.metadata['shared_education_context']={'policy':'Institution only, sibling qualifications in the same original source element; no dates or grades inherited.'}
    return updated


def valid_institution_context(section,entry,index):
    from local_api.services.record_relationships import field_kinds
    school=section.blocks[index]
    if 'institution' not in field_kinds(school.text,'education') or 'qualification' in field_kinds(school.text,'education'):return False
    qualifications=[section.blocks[i] for i in entry.block_indices if re.search(r'\bClass\s+(?:10th|12th|XII|X)(?!\w)',section.blocks[i].text,re.I)]
    return any(school.page_number==b.page_number and 0<=b.source_element_index-school.source_element_index<=2
               and any(index in sibling.block_indices and any(section.blocks[i].source_element_index==b.source_element_index
                   and re.search(r'\bClass\s+',section.blocks[i].text,re.I) for i in sibling.block_indices)
                   for sibling in section.entries if sibling.entry_id!=entry.entry_id)
               for b in qualifications)
