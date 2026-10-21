"""Structure-led boundaries inspired by knowledge-graph-resume, independently implemented.

Keep source offsets authoritative. Formatting normalization is lookup-only; never
normalize, deduplicate, reconstruct names, or regenerate the returned source text.
"""
import re


def word_safe_cut(text, cut):
    """Move a mechanical tokenizer/geometry cut past an ordinary word.

    Preserve explicit camel-case boundaries in joined headings. Offsets and all
    characters remain source based; this never inserts or normalizes text.
    """
    if 0 < cut < len(text) and text[cut-1].isalnum() and text[cut].isalnum():
        if text[cut-1].islower() and text[cut].isupper():
            return cut
        while cut < len(text) and text[cut].isalnum():
            cut += 1
    return cut

# Record fields must not change the owning section, even when their values look
# like another section (a project's tools are still part of that project).
RECORD_FIELDS = {'technologies', 'technology', 'tools', 'tool', 'tech stack',
                 'description', 'project description', 'project title', 'project name',
                 'role', 'job title', 'designation', 'client', 'duration', 'period',
                 'achievement', 'accomplishment'}
EXTRA_HEADINGS = {
    'personal_information': ['contact', 'personal info'],
    'summary': ['objective', 'career summary', 'executive summary', 'profile snapshot', 'profile summary'],
    'projects': ['key projects', 'project highlights'],
    'experience': ['employment', 'professional background', 'work history'],
    'education': ['qualifications', 'educational background'],
    'skills': ['skill set', 'skill sets', 'skillset', 'key strengths', 'technical competencies', 'core skills', 'domain expertise', 'business analysis and product management', 'tools and technology'],
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
        key = (block.lane, None if block.reviewed_by_llm else block.context_source_element_index)
        if block.assignment in {'section_heading', 'structural_heading'}:
            # Heading is a section member but not a job/project entry.
            active = {key_: value for key_, value in active.items() if key_[0] != block.lane}
            continue
        text = block.text.strip()
        element = elements[block.source_element_index]
        explicit_title = (element.type == 'Title' and block.start == 0 and
                          0 < len(text.split()) <= 18 and not re.match(r'^[•▪●*\-]', text))
        labeled_entry = bool(re.match(r'^\s*(?:\d+[.)]\s*)?(?:project(?: name| title)?|company|employer|institution)\s*:', text, re.I))
        if block.reviewed_by_llm:
            # A title detector's field labels and embedded project titles are not
            # employer boundaries after semantic reassignment to Experience.
            if category=='experience':
                explicit_title=employment_start(text)
                labeled_entry=bool(re.match(r'^\s*(?:company|employer)\s*:\s*\S',text,re.I))
            elif category=='education':
                explicit_title=explicit_title and bool(re.search(r'\b(?:university|college|institute|bachelor|master|diploma|phd|bsc|msc|b\.?tech|m\.?tech)\b',text,re.I))
                labeled_entry=bool(re.match(r'^\s*(?:institution|university|college)\s*:\s*\S',text,re.I))
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
    if category in {'experience','education'} and any(b.reviewed_by_llm for b in blocks):
        groups = attach_aligned_dates(groups, blocks, elements)
    return groups


def attach_aligned_dates(groups, blocks, elements):
    """Attach date-only fragments only with an unambiguous same-row source match.

    Lanes are layout evidence, not record identities. Do not use source order to
    guess a distant date's owner. Leave ambiguous and unlocated dates unchanged.
    """
    def row(block):
        hints=elements[block.source_element_index].metadata.get('pdf_source_lines',[])
        candidates=[h for h in hints if len(h.get('bbox',[]))==4 and
                    min(block.end,h.get('end',0))>max(block.start,h.get('start',0))]
        if not candidates:return None
        # A multi-line body cannot establish a unique header row.
        centers=[(h['bbox'][1]+h['bbox'][3])/2 for h in candidates]
        if max(centers)-min(centers)>.015:return None
        return sum(centers)/len(centers)
    def date_only(text):
        return bool(re.search(r'\b(?:19|20)\d{2}\b',text)) and not re.sub(
            r'(?i)\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|present|current|to|since|till)\b|[\d\s.,/|:–—\-\'’()]','',text)
    membership={i:g for g in groups for i in g['block_indices']}
    for index,block in enumerate(blocks):
        if not block.reviewed_by_llm or index not in membership or not date_only(block.text):continue
        y=row(block)
        if y is None:continue
        candidates=[]
        for other_index,other in enumerate(blocks):
            if other_index not in membership or other.page_number!=block.page_number or date_only(other.text):continue
            if len(other.text.strip())<4:continue
            other_y=row(other)
            if other_y is not None and abs(other_y-y)<=.006:
                candidates.append(membership[other_index])
        unique={id(g):g for g in candidates}
        if len(unique)!=1:continue
        target=next(iter(unique.values()));old=membership[index]
        if target is old:continue
        old['block_indices'].remove(index);target['block_indices'].append(index)
        target['block_indices'].sort();membership[index]=target
        target['boundary_reason']='source-aligned date attached across layout lanes; other associations remain proposals'
    result=[g for g in groups if g['block_indices']]
    for i,g in enumerate(result):g['entry_id']=f"{g['entry_id'].rsplit('-',1)[0]}-{i+1}"
    return result


def employment_start(text):
    from local_api.vendor.resume_semantic_blocks import PERIOD, employment_header, ACTION, EDUCATION
    period = PERIOD.search(text)
    prefix = text[:period.start()].strip(' |,–—-') if period else ''
    if not period or len(text.split()) > 30 or EDUCATION.search(prefix) or ACTION.search(prefix):
        return False
    business = re.search(r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank)\b', prefix, re.I)
    return bool(employment_header(text) or business or ('|' in text[:period.start()] and len(prefix.split()) <= 14))
