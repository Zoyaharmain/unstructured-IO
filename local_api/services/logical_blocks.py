"""Logical record context derived from immutable source spans and record owners."""
from collections import Counter

HEADINGS = {'section_heading', 'structural_heading'}
RECORD_SECTIONS = {'experience', 'education', 'projects', 'certifications',
                   'awards', 'publications', 'volunteering', 'references'}


def logical_blocks(section):
    """Partition record content once; raw headings/layout remain in source blocks."""
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.resume_sections import ALIASES
    # Old/reviewed inventories may retain a content assignment on an exact
    # heading. It establishes section context, never a record's field value.
    content = [i for i, b in enumerate(section.blocks)
               if b.assignment not in HEADINGS
               and heading_boundary(b.text, ALIASES) != (section.category, None)]
    if not content:
        return []

    def group(identifier, indices, kind, reasons=(), entry=None):
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
                'review_reasons': list(reasons),
                'semantic_frame': semantic_frame(section, indices, kind, entry)}

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
        output.append(group(entry.entry_id, indices, 'record', reasons, entry)); used.update(indices)
    # Do not guess which employer/degree should own a remaining paragraph.
    remaining = [i for i in content if i not in used]
    # Keep separated leftovers separated: a single catch-all card can falsely
    # imply a relationship between paragraphs on opposite sides of a record.
    clusters = []
    for index in remaining:
        if not clusters or index != clusters[-1][-1] + 1:
            clusters.append([])
        clusters[-1].append(index)
    for number, indices in enumerate(clusters, 1):
        if any(c.isalnum() for i in indices for c in section.blocks[i].text):
            output.append(group(f'{section.category}-unassigned-{number}', indices, 'unresolved',
                                ['Section identified; association with a specific record has not been established.']))
    return sorted(output, key=lambda g: g['block_indices'][0])


def semantic_frame(section, indices, kind, entry=None):
    """Describe the schema shape without treating structural hints as facts.

    Field hints reference original spans only. The field mapper still has to
    extract and validate each value; an empty hint is not evidence of absence.
    """
    from local_api.schemas.subschema_spec import SUBSCHEMAS
    registry = SUBSCHEMAS.get(section.category, {})
    aliases = {
        'experience': {'employer': 'company', 'title': 'role', 'dates': 'duration'},
        'education': {'qualification': 'degree', 'dates': 'graduation_year',
                      'grade': 'grade_or_gpa'},
        'projects': {'title': 'name'},
    }.get(section.category, {})
    hints = {name: [] for name in registry}
    allowed = set(indices)
    if entry:
        for field, members in entry.fields.items():
            name = aliases.get(field, field)
            if name not in hints:
                continue
            hints[name] = list(dict.fromkeys(
                f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}'
                for i in members if i in allowed))
    if section.category == 'summary' and kind == 'section':
        hints['statements'] = [f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' for i in indices]
    return {
        'schema_target': section.category,
        'meaning': section.label,
        'scope': 'unassigned_fragments' if kind == 'unresolved' else
                 'one_record' if kind == 'record' else 'complete_section',
        'field_slots': [{'name': name, 'multiple': rule['multiple'],
                         'source_hints': hints[name]} for name, rule in registry.items()],
        'interpretation_status': 'requires_association' if kind == 'unresolved' else 'proposed',
        'evidence_policy': 'Extract literal values from original sources; validate every field. '
                           'Hints are not established values and empty hints do not mean absent.',
    }
