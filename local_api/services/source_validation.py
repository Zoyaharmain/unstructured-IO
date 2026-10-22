"""Shared exact source/record validation for batch and HTTP paths."""

def validate_result(elements, result):
    errors = []
    from local_api.services.resume_sections import ANCHORS
    categories = [s.category for s in result.sections]
    if any(c not in ANCHORS for c in categories):errors.append('invalid_section_category')
    if len(categories) != len(set(categories)):
        errors.append('duplicate_categories')
    spans = sorted([b for s in result.sections for b in s.blocks] + result.needs_review,
                   key=lambda b: (b.source_element_index, b.start))
    if any(not 0 <= b.source_element_index < len(elements) for b in spans):
        errors.append('invalid_source_index')
    for i, el in enumerate(elements):
        cursor = 0
        pieces=[b for b in spans if b.source_element_index==i]
        if not pieces or (len(el.text)==0 and len(pieces)!=1):errors.append('source_coverage_incomplete')
        for b in pieces:
            if (b.start==b.end and len(el.text)>0) or b.start != cursor or not 0 <= b.start <= b.end <= len(el.text) or b.text != el.text[b.start:b.end]:
                errors.append('source_range_or_text_mismatch')
            cursor = b.end
        if cursor != len(el.text):
            errors.append('source_coverage_incomplete')
    for section in result.sections:
        expected, previous = '', None
        for b in section.blocks:
            if previous is not None and not (previous.source_element_index == b.source_element_index and previous.end == b.start):
                expected += '\n'
            expected += b.text
            previous = b
        if section.text != expected:
            errors.append('canonical_text_mismatch')
        end = 0
        for h in section.highlights:
            if not 0 <= h.start < h.end <= len(section.text) or h.start < end:
                errors.append('invalid_highlight_offsets')
            end = h.end
        ownership=[];entry_ids=[]
        for entry in section.entries:
            entry_ids.append(entry.entry_id);ownership.extend(entry.block_indices)
            if any(index not in entry.block_indices for values in entry.fields.values() for index in values):errors.append('invalid_field_entry_reference')
            if any(not 0 <= i < len(section.blocks) for i in entry.block_indices):
                errors.append('invalid_entry_reference')
        if len(ownership)!=len(set(ownership)):errors.append('overlapping_entry_ownership')
        if len(entry_ids)!=len(set(entry_ids)):errors.append('duplicate_entry_id')
    return sorted(set(errors))

