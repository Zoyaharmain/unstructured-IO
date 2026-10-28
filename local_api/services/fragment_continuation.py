"""Recover contiguous tails of a single extracted paragraph, never across records."""
from collections import defaultdict


def recover_fragment_continuations(result, elements):
    from local_api.services.resume_sections import build_sections
    owners = defaultdict(list)
    for section in result.sections:
        for block in section.blocks:
            owners[block.source_element_index].append((section.category, block))
    moved = {}
    for index, fragments in owners.items():
        categories = {category for category, _ in fragments}
        # Mixed paragraphs may contain multiple jobs or headings: no inference.
        if len(categories) != 1:
            continue
        category = next(iter(categories))
        if category not in {'summary', 'personal_information'}:
            continue
        ordered = sorted((b for _, b in fragments), key=lambda b: b.start)
        if any(b.assignment in {'section_heading', 'structural_heading'} for b in ordered):
            continue
        pending = sorted((b for b in result.needs_review if b.source_element_index == index), key=lambda b: b.start)
        cursor = ordered[-1].end
        for block in pending:
            if block.start != cursor or block.cluster_space == 'heading':
                break
            # Pipe-separated opening expertise is skills, not part of a person's name.
            target = category
            if category == 'personal_information':
                if '|' not in elements[index].text or '@' in elements[index].text:
                    break
                target = 'skills'
            moved[(index, block.start, block.end)] = (target, block.model_copy(update={
                'assignment': 'paragraph_continuation',
                'reason': 'Contiguous continuation of a uniquely assigned source paragraph.'}))
            cursor = block.end
    if not moved:
        return result
    grouped = {s.category: list(s.blocks) for s in result.sections}
    for category, block in moved.values():
        grouped.setdefault(category, []).append(block)
    for blocks in grouped.values():
        blocks.sort(key=lambda b: (b.source_element_index, b.start))
    repaired = result.model_copy(deep=True)
    repaired.sections = build_sections(grouped, elements)
    repaired.needs_review = [b for b in result.needs_review if (b.source_element_index, b.start, b.end) not in moved]
    repaired.metadata['assigned_units'] = sum(len(s.blocks) for s in repaired.sections)
    repaired.metadata['review_units'] = len(repaired.needs_review)
    repaired.metadata['paragraph_continuation_recovery'] = {'recovered_blocks': len(moved)}
    return repaired
