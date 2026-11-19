"""Explicit employer-heading scope for sibling roles; company evidence only.

A combined employer/role header describes one job and cannot establish a shared
employer scope. A standalone employer heading may scope subsequent roles in the
same reading lane until another employer or section heading occurs.
"""
from local_api.services.decision_trace import traced
from local_api.services.record_relationships import field_kinds


def valid_employer_context(section, entry, index, *, allow_combined=False):
    if section.category != 'experience' or not entry.block_indices or not 0 <= index < len(section.blocks):
        return False
    start = min(entry.block_indices)
    has_title = bool(entry.fields.get('title') or any('title' in field_kinds(section.blocks[i].text, 'experience') for i in entry.block_indices))
    has_employer = bool(entry.fields.get('employer') or any('employer' in field_kinds(section.blocks[i].text, 'experience') for i in entry.block_indices))
    if index >= start or not has_title or has_employer:
        return False
    employer = section.blocks[index]
    kinds = set(field_kinds(employer.text, 'experience'))
    forbidden = {'responsibilities'} if allow_combined else {'title', 'dates', 'responsibilities', 'client'}
    if kinds & forbidden or len(employer.text.split()) > (30 if allow_combined else 14):
        return False
    if not any(index in e.block_indices and (index in e.fields.get('employer', []) or 'employer' in field_kinds(section.blocks[index].text, 'experience')) for e in section.entries):
        return False
    title_indices = entry.fields.get('title', []) or [i for i in entry.block_indices if 'title' in field_kinds(section.blocks[i].text, 'experience')]
    role_block = section.blocks[title_indices[0]] if title_indices else section.blocks[start]
    if employer.lane != role_block.lane and 'wide' not in {employer.lane, role_block.lane}:
        return False
    for block in section.blocks[index + 1:start]:
        if block.lane != role_block.lane and 'wide' not in {block.lane, role_block.lane}:
            continue
        if block.assignment in {'section_heading', 'structural_heading'}:
            return False
        if 'employer' in field_kinds(block.text, 'experience'):
            return False
    return True


@traced('recover_employer_context', detail=True)
def recover_employer_context(result):
    section = next((s for s in result.sections if s.category == 'experience'), None)
    if section is None:
        return result
    revised = section.model_copy(deep=True)
    if any(not e.fields for e in revised.entries):
        from local_api.services.record_relationships import annotate_relationships
        annotate_relationships(revised)
    changed = False
    for entry in revised.entries:
        if entry.fields.get('employer') or not entry.fields.get('title'):
            continue
        candidates = [i for i in range(min(entry.block_indices, default=0))
                      if valid_employer_context(revised, entry, i)]
        if len(candidates) == 1 and entry.context_fields.get('company') != candidates:
            entry.context_fields['company'] = candidates
            entry.review_reasons = [r for r in entry.review_reasons if r not in {
                'employer_not_established_from_supported_fields', 'employer_requires_parent_context_review'}]
            entry.relationship_status = 'needs_review' if entry.review_reasons else 'provisional'
            changed = True
    if not changed:
        return result
    out = result.model_copy(deep=True)
    out.sections = [revised if s.category == 'experience' else s for s in out.sections]
    return out


def valid_record_context(section, entry):
    if not entry.context_fields:
        return True
    if any(type(i) is not int or not 0 <= i < len(section.blocks)
           for indices in entry.context_fields.values() for i in indices):
        return False
    if section.category == 'education' and set(entry.context_fields) == {'institution'}:
        from local_api.services.education_context import valid_institution_context
        return all(valid_institution_context(section, entry, i) for i in entry.context_fields['institution'])
    if section.category == 'experience' and set(entry.context_fields) == {'company'}:
        return len(entry.context_fields['company']) == 1 and valid_employer_context(section, entry, entry.context_fields['company'][0],
            allow_combined=entry.boundary_reason == 'validated source ownership')
    return False
