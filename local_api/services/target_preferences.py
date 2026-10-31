"""Source-backed desired-role sections are preferences, never employment history."""
import re

TARGET_HEADING = re.compile(r'^\s*(?:target roles?|target positions?|desired roles?|desired positions?|roles sought|preferred roles?)\s*:?\s*$', re.I)


def target_groups(blocks):
    from local_api.services.record_subfields import ROLE, RANGE
    from local_api.services.resume_sections import ALIASES
    from local_api.services.resume_structure import heading_boundary
    ordered = sorted(blocks, key=lambda b: (b.source_element_index, b.start))
    groups = []
    active = None
    for block in ordered:
        if TARGET_HEADING.fullmatch(block.text):
            active = [block]; groups.append(active); continue
        if active is None: continue
        heading = active[0]
        if (block.page_number != heading.page_number or (block.lane != heading.lane and 'wide' not in {block.lane, heading.lane})
            or block.source_element_index - heading.source_element_index > 6
            or heading_boundary(block.text, ALIASES)[0] or RANGE.search(block.text)
            or (len(block.text.split()) <= 8 and block.text.strip().isupper() and '|' not in block.text)):
            active = None; continue
        if sum(len(b.text.split()) for b in active) + len(block.text.split()) > 220:
            active = None; continue
        active.append(block)
    return [group for group in groups if any(ROLE.search(b.text) for b in group[1:])]


def target_section_values(blocks):
    from local_api.services.record_subfields import ROLE
    groups = target_groups(blocks)
    if len(groups) > 1: return {}
    body = groups[0][1:] if groups else [b for b in blocks if b.assignment == 'local_target_preferences']
    if not body: return {}
    text = ''
    previous = None
    for block in body:
        if previous is not None and block.source_element_index != previous.source_element_index:
            text += '\n'
        text += block.text
        previous = block
    text = text.strip()
    # A trailing list after a dash can express locations/remote scope. Never
    # remove a suffix containing another title, or interpret it as residence.
    split = None
    for match in re.finditer(r'\s+[—–]\s+', text):
        tail = text[match.end():]
        if not ROLE.search(tail) and ('|' in tail or re.search(r'\b(?:remote|global|relocat\w*)\b', tail, re.I)):
            split = match
    if split:
        return {'target_role': text[:split.start()].strip(), 'work_preferences': text[split.end():].strip()}
    return {'target_role': text} if text else {}


def recover_target_preferences(result, elements):
    from local_api.services.resume_sections import build_sections
    from local_api.services.source_validation import validate_result
    all_blocks = [b for s in result.sections for b in s.blocks] + list(result.needs_review)
    groups = target_groups(all_blocks)
    if not groups: return result
    keys = {(b.source_element_index, b.start, b.end) for group in groups for b in group}
    grouped = {s.category: [b for b in s.blocks if (b.source_element_index,b.start,b.end) not in keys] for s in result.sections}
    recovered = []
    for group in groups:
        for index, block in enumerate(group):
            recovered.append(block.model_copy(update={
                'assignment': 'structural_heading' if index == 0 else 'local_target_preferences',
                'reason': 'Explicit target-role heading and bounded contiguous desired roles/work preferences; not employment or residence.'}))
    # Idempotence avoids needless rebuilding during subsequent mapping/review.
    current = next((s for s in result.sections if s.category == 'personal_information'), None)
    if current and all(any(b.source_element_index == n.source_element_index and b.start == n.start and b.end == n.end and b.assignment == n.assignment for b in current.blocks) for n in recovered):
        return result
    grouped.setdefault('personal_information', []).extend(recovered)
    grouped = {k: sorted(v,key=lambda b:(b.source_element_index,b.start)) for k,v in grouped.items() if v}
    updated = result.model_copy(deep=True)
    rebuilt = build_sections(grouped, elements, refine=False)
    old = {s.category:s for s in result.sections}
    affected = {s.category for s in result.sections if any((b.source_element_index,b.start,b.end) in keys for b in s.blocks)} | {'personal_information'}
    updated.sections = [s if s.category in affected else old[s.category].model_copy(deep=True) for s in rebuilt]
    updated.needs_review = [b for b in result.needs_review if (b.source_element_index,b.start,b.end) not in keys]
    updated.metadata['target_preferences_recovery'] = {'source_spans':len(keys)}
    updated.metadata.update(assigned_units=sum(len(s.blocks) for s in updated.sections),review_units=len(updated.needs_review))
    updated.status = 'needs_review' if updated.needs_review else 'provisional'
    if validate_result(elements, updated): raise ValueError('Invalid source binding after target preference recovery')
    return updated
