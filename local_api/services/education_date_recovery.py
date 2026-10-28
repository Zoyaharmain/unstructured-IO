"""Recover a misplaced date only when PDF geometry identifies one degree row."""
from local_api.services.record_subfields import RANGE
from local_api.services.education_subfields import DEGREE


def recover_education_dates(result, elements):
    from local_api.services.record_relationships import annotate_relationships
    education = next((s for s in result.sections if s.category == 'education'), None)
    if education is None:
        return result

    def rows(b):
        return [r for r in elements[b.source_element_index].metadata.get('pdf_source_lines', [])
                if len(r.get('bbox', [])) == 4 and min(b.end,r.get('end',0)) > max(b.start,r.get('start',0))]

    degrees = [(i,b,r) for i,b in enumerate(education.blocks) if DEGREE.search(b.text) for r in rows(b)]
    moves = []
    sources = [(s,b) for s in result.sections if s.category == 'experience' for b in s.blocks]
    sources += [(None,b) for b in result.needs_review]
    for source, block in sources:
        match = RANGE.match(block.text.strip())
        if not match or len(block.text.split()) > 12:
            continue
        aligned = {i for i,degree,degree_row in degrees if degree.page_number == block.page_number
                   for date_row in rows(block)
                   if abs(date_row['bbox'][1]-degree_row['bbox'][1]) < .004
                   and date_row['bbox'][0] >= degree_row['bbox'][2]}
        if len(aligned) == 1:
            moves.append((source,block,next(iter(aligned))))
    if not moves:
        return result
    output = result.model_copy(deep=True)
    target = next(s for s in output.sections if s.category == 'education')
    def key(b):return (b.source_element_index,b.start,b.end)
    moved = {key(b) for _,b,_ in moves}
    for section in output.sections:
        if section.category != 'experience':continue
        kept = [(i,b) for i,b in enumerate(section.blocks) if key(b) not in moved]
        remap = {old:new for new,(old,_) in enumerate(kept)}
        section.blocks = [b for _,b in kept]
        for entry in section.entries:
            entry.block_indices = [remap[i] for i in entry.block_indices if i in remap]
            entry.fields = {name:[remap[i] for i in indices if i in remap] for name,indices in entry.fields.items()}
        section.entries = [e for e in section.entries if e.block_indices]
        section.highlights=[];section.readable_blocks=[]
        annotate_relationships(section)
    output.needs_review = [b for b in output.needs_review if key(b) not in moved]
    for _,block,degree_index in moves:
        index = len(target.blocks)
        target.blocks.append(block.model_copy(update={'assignment':'education_date_recovered','reason':'Date physically aligned with a unique degree row in original PDF coordinates.'}))
        owners = [e for e in target.entries if degree_index in e.block_indices]
        if len(owners) == 1:owners[0].block_indices.append(index)
    target.highlights=[];target.readable_blocks=[]
    annotate_relationships(target)
    from local_api.services.schema_mapping import canonical
    for section in output.sections:
        section.text = canonical(section.blocks)
    output.metadata['education_date_recovery'] = {'recovered_blocks':len(moves)}
    return output
