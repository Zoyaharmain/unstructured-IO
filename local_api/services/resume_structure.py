"""Structure-led boundaries inspired by knowledge-graph-resume, independently implemented.

Keep source offsets authoritative. Formatting normalization is lookup-only; never
normalize, deduplicate, reconstruct names, or regenerate the returned source text.
"""
import re

# Record fields must not change the owning section, even when their values look
# like another section (a project's tools are still part of that project).
RECORD_FIELDS = {'technologies', 'technology', 'tools', 'tool', 'tech stack',
                 'description', 'project description', 'project title', 'project name',
                 'role', 'job title', 'designation', 'client', 'duration', 'period',
                 'achievement', 'accomplishment'}
EXTRA_HEADINGS = {
    'personal_information': ['contact', 'personal info'],
    'summary': ['objective', 'career summary', 'executive summary', 'profile snapshot', 'profile summary'],
    'experience': ['employment', 'professional background', 'work history'],
    'education': ['qualifications', 'educational background'],
    'skills': ['key strengths', 'technical competencies', 'core skills'],
    'certifications': ['certificates', 'training'],
}


def normalized_heading(text):
    value = text.strip()
    value = re.sub(r'^\s*(?:\d+[.)]|[•▪●*#])\s*', '', value)
    value = value.strip(' |–—_-:.\t\r\n')
    if re.fullmatch(r'(?:[A-Za-z]\s+){2,}[A-Za-z]', value):
        value = re.sub(r'\s+', '', value)
    return ' '.join(value.casefold().replace('&', ' and ').split())


def heading_aliases(anchors):
    return {normalized_heading(text): category for category, anchor in anchors.items()
            for text in anchor['headings'] + EXTRA_HEADINGS.get(category, [])}


def heading_boundary(text, aliases):
    """Return (category, exact split offset or None) for explicit heading syntax."""
    normalized = normalized_heading(text)
    if normalized in RECORD_FIELDS:
        return None, None
    category = aliases.get(normalized)
    if category:
        return category, None
    if ':' in text:
        prefix, body = text.split(':', 1)
        # Numbered Project: is an entry, not a new section.
        if normalized_heading(prefix) in RECORD_FIELDS or re.match(r'^\s*\d+[.)]\s*project\s*$', prefix, re.I):
            return None, None
        category = aliases.get(normalized_heading(prefix))
        if category and body.strip():
            return category, text.index(':') + 1
    # PDF partitioning may flatten a heading and its first paragraph into one
    # element (the requested repository's sample PDFs exhibit this). Restrict
    # recovery to an exact, capitalized leading heading and a capitalized value;
    # never search body substrings such as "experience building services".
    for alias, owner in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in RECORD_FIELDS:
            continue
        pattern = r'^\s*(' + r'\s+'.join(re.escape(word) for word in alias.split()) + r')\s+(?=[A-Z0-9])'
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            prefix = match.group(1)
            remainder = text[match.end():]
            if prefix[0].isupper() and remainder and (remainder[0].isupper() or remainder[0].isdigit()):
                return owner, match.end()
    return None, None


def entry_groups(blocks, category, elements):
    """Reference existing spans, separating explicit entries within each lane/context.

    These are structural proposals, not invented company/degree records. Without
    a visible entry boundary, retain one group rather than guess from similarity.
    """
    groups, active = [], {}
    for index, block in enumerate(blocks):
        key = (block.lane, block.context_source_element_index)
        if block.assignment in {'section_heading', 'structural_heading'}:
            # Heading is a section member but not a job/project entry.
            active = {key_: value for key_, value in active.items() if key_[0] != block.lane}
            continue
        text = block.text.strip()
        element = elements[block.source_element_index]
        explicit_title = (element.type == 'Title' and block.start == 0 and
                          0 < len(text.split()) <= 18 and not re.match(r'^[•▪●*\-]', text))
        labeled_entry = bool(re.match(r'^\s*(?:\d+[.)]\s*)?(?:project(?: name| title)?|company|employer|institution)\s*:', text, re.I))
        dated_header = bool(category in {'experience', 'education'} and len(text.split()) <= 24
                            and re.search(r'\b(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:(?:19|20)\d{2}|present|current)\b', text, re.I)
                            and not re.match(r'^[•▪●*\-]', text))
        boundary = category in {'experience', 'projects', 'education'} and (explicit_title or labeled_entry or dated_header)
        if key not in active or boundary:
            group = {'entry_id': f'{category}-{len(groups) + 1}', 'block_indices': [],
                     'lane': block.lane, 'boundary_reason': 'explicit entry title or dated header' if boundary else 'section continuation; no explicit entry boundary'}
            groups.append(group)
            active[key] = group
        active[key]['block_indices'].append(index)
    return groups
