"""Logical record context derived from immutable source spans and record owners."""
from collections import Counter

HEADINGS = {'section_heading', 'structural_heading'}
RECORD_SECTIONS = {'experience', 'education', 'projects', 'certifications',
                   'awards', 'publications', 'volunteering', 'references'}


def logical_blocks(section):
    """Partition record content once; raw headings/layout remain in source blocks."""
    content = [i for i, b in enumerate(section.blocks) if b.assignment not in HEADINGS]
    if not content:
        return []

    def group(identifier, indices, kind, reasons=()):
        indices = sorted(indices)
        parts = []; previous = None
        for i in indices:
            b = section.blocks[i]
            if previous is not None and not (previous.source_element_index == b.source_element_index and previous.end == b.start):
                parts.append('\n')
            parts.append(b.text); previous = b
        return {'logical_id': identifier, 'kind': kind, 'text': ''.join(parts),
                'block_indices': indices,
                'source_ids': [f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' for i in indices],
                'relationship_status': 'needs_review' if reasons else 'provisional',
                'review_reasons': list(reasons)}

    if section.category not in RECORD_SECTIONS:
        return [group(f'{section.category}-complete', content, 'section')]
    allowed = set(content)
    owners = [sorted(set(i for i in e.block_indices if i in allowed)) for e in section.entries]
    counts = Counter(i for indices in owners for i in indices)
    if any(n > 1 for n in counts.values()):
        return [group(f'{section.category}-unresolved', content, 'unresolved',
                      ['Record boundaries overlap; separate records have not been established.'])]
    output = []; used = set()
    for entry, indices in zip(section.entries, owners):
        if not indices:
            continue
        reasons = list(entry.review_reasons)
        if entry.relationship_status == 'needs_review' and not reasons:
            reasons.append('Record association requires review.')
        output.append(group(entry.entry_id, indices, 'record', reasons)); used.update(indices)
    # Do not guess which employer/degree should own a remaining paragraph.
    remaining = [i for i in content if i not in used]
    if remaining and any(c.isalnum() for i in remaining for c in section.blocks[i].text):
        output.append(group(f'{section.category}-unassigned', remaining, 'unresolved',
                            ['These source fragments have no established record owner.']))
    return sorted(output, key=lambda g: g['block_indices'][0])
