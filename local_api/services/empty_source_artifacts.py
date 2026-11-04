"""Blank source spans are auditable artifacts, never human review work."""


def separate_empty_source(result,elements):
    blanks=[b for s in result.sections for b in s.blocks if not b.text.strip()]+[b for b in result.needs_review if not b.text.strip()]
    if not blanks:return result
    revised=result.model_copy(deep=True)
    known={(b.source_element_index,b.start,b.end) for b in revised.source_artifacts}
    revised.source_artifacts.extend(b.model_copy(update={'assignment':'source_artifact','reason':'Empty or whitespace-only source span; no classification or human review required.'}) for b in blanks if (b.source_element_index,b.start,b.end) not in known)
    revised.needs_review=[b for b in revised.needs_review if b.text.strip()]
    sections=[]
    for section in revised.sections:
        positions={i:new for new,i in enumerate(i for i,b in enumerate(section.blocks) if b.text.strip())}
        if len(positions)==len(section.blocks):sections.append(section);continue
        section.blocks=[b for b in section.blocks if b.text.strip()]
        if not section.blocks:continue
        entries=[]
        for entry in section.entries:
            owned=[positions[i] for i in entry.block_indices if i in positions]
            if not owned:continue
            entry.block_indices=owned
            entry.fields={f:[positions[i] for i in ids if i in positions] for f,ids in entry.fields.items()}
            entry.context_fields={f:[positions[i] for i in ids if i in positions] for f,ids in entry.context_fields.items()}
            entries.append(entry)
        section.entries=entries
        text='';previous=None
        for b in section.blocks:
            if previous and not (previous.source_element_index==b.source_element_index and previous.end==b.start):text+='\n'
            text+=b.text;previous=b
        section.text=text;section.highlights=[]
        def readable(group):
            return group.model_copy(update={'block_indices':[positions[i] for i in group.block_indices if i in positions],
                                            'children':[readable(child) for child in group.children]})
        section.readable_blocks=[readable(group) for group in section.readable_blocks]
        sections.append(section)
    revised.sections=sections
    revised.metadata['empty_source_artifacts']={'count':len(revised.source_artifacts),'included_in_review':False,'source_inventory_preserved':True}
    revised.metadata.update(review_units=len(revised.needs_review),assigned_units=sum(len(s.blocks) for s in revised.sections),total_units=sum(len(s.blocks) for s in revised.sections)+len(revised.needs_review))
    revised.status='needs_review' if revised.needs_review else 'provisional'
    from local_api.services.source_validation import validate_result
    errors=validate_result(elements,revised)
    if errors:raise ValueError('Invalid source binding after blank artifact separation: '+repr(errors))
    return revised
