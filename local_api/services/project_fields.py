"""Separate project identity and field labels from literal contiguous descriptions."""
import re
from local_api.services.record_subfields import labelled_fields, responsibility_fragment, RANGE, ALIASES, ACTION


def project_fields(blocks, elements, proposed_title=None):
    content = [b for b in blocks if b.assignment not in {'section_heading', 'structural_heading'} and b.text.strip()]
    title, parts = None, []
    def append(block, value, explicit=False):
        offset = block.text.find(value)
        if offset >= 0: parts.append((value, block.source_element_index, block.start + offset, block.start + offset + len(value), explicit))
    for b in content:
        text = b.text.strip()
        project_header = re.match(
            r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?(?:'
            r'#?\s*\.?\s*\d+[\s:.)-]+(?:project(?:\s+name|\s+title)?|academic\s+project)?\s*[:.)-]?\s*|'
            r'#(?:project(?:\s+name|\s+title)?)\s*[:.)-]\s*|'
            r'(?:academic\s+)?project\s*#?\s*\d*\s*[:.)-]\s*|'
            r'project\s+(?:name|title)\s*[:.)-]\s*'
            r')(\S.*)',
            text, re.I
        )
        if title is None and project_header:
            cand_title = re.split(r'\s+(?:Clients?|Tools|Technologies|Technology|Description)\s*:', project_header[1], flags=re.I)[0].strip()
            has_explicit_word = bool(re.search(r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?#?\s*\.?\s*\d*[\s:.)-]*(?:project(?:\s+name|\s+title)?|academic\s+project)\b', text, re.I))
            words = cand_title.split()
            is_title_cased = (1 <= len(words) <= 6 and not cand_title.endswith(('.', ';', '!', '?'))
                              and all(w[:1].isupper() or w.lower() in {'and', 'or', 'for', 'the', 'of', 'in', '&', 'to', 'with'} for w in words))
            if not has_explicit_word and len(content) > 1 and not is_title_cased and ACTION.search(cand_title) and b is not content[0]:
                append(b, b.text)
                continue
            if len(content) == 1 and '.' in cand_title:
                sp = re.split(r'(?<=\.)\s+(?=[A-Z])', cand_title, maxsplit=1)
                title = sp[0].rstrip('. ')
                if len(sp) > 1 and sp[1].strip():
                    append(b, sp[1].strip())
            else:
                title = cand_title.rstrip('. ')
            continue
        if re.fullmatch(r'(?:academic\s+)?project\s*#?\s*\d+\s*[:.)-]?',text,re.I):continue
        if text.strip()==':':continue
        if title is None and text.startswith(':') and len(text[1:].split())<=18:
            title=text[1:].strip();continue
        from local_api.services.resume_structure import RECORD_FIELDS, normalized_heading
        if normalized_heading(text) in RECORD_FIELDS:continue
        labels = labelled_fields('projects', [b])
        if labels:
            for value in labels.get('description', []): append(b, value, True)
            continue
        if re.fullmatch(r'(?:https?://|www\.|[A-Za-z0-9.-]+\.[A-Za-z]{2,}/)\S+', text) or RANGE.fullmatch(text): continue
        dated = RANGE.search(text)
        if title is None and dated and dated.start() > 0 and not responsibility_fragment(text):
            prefix = text[:dated.start()].rstrip(' |—–-')
            if prefix and len(prefix.split()) <= 18:
                title = prefix
                suffix = text[dated.end():].strip(' |—–-')
                if suffix and responsibility_fragment(suffix): append(b, suffix)
                continue
        combined = re.fullmatch(r'([^:]{1,100}):\s*(.+)', text)
        if (title is None and combined and len(combined[1].split()) <= 12
                and combined[1].casefold() not in ALIASES['projects'] and responsibility_fragment(combined[2])):
            title = combined[1].strip(); append(b, combined[2].strip()); continue
        if text.casefold() in {'project', 'projects', 'project name', 'project title', 'project details', 'description', 'technologies', 'responsibilities'}:
            continue
        plausible_name = (not responsibility_fragment(text) and not text.endswith(('.', '!', '?'))
                          and len(text.split()) <= 18 and not re.fullmatch(r'project\s*#?\s*\d+[:.)-]?', text, re.I))
        if title is None and plausible_name and (proposed_title == text or not parts or b is content[0] or elements[b.source_element_index].type == 'Title'):
            title = text
        else:
            append(b, b.text)
    # Do not insert newlines at physical cuts inside the same source element.
    # Unrelated labelled rows break a description; they cannot be fabricated away.
    groups = []
    for part in parts:
        join, separator = False, ''
        if groups:
            previous = groups[-1][-1][0]
            if part[1] == previous[1]:
                gap = elements[part[1]].text[previous[3]:part[2]]
                join = not re.sub(r'[\s•▪●*,-]', '', gap)
                separator = gap
            elif part[1] > previous[1]:
                gaps = elements[previous[1]].text[previous[3]:] + elements[part[1]].text[:part[2]]
                gaps += ''.join(e.text for e in elements[previous[1]+1:part[1]])
                join = not re.sub(r'[\s•▪●*,-]', '', gaps)
                separator = '\n'
        if not join: groups.append([]); separator = ''
        groups[-1].append((part, separator))
    if not groups: return title or '', None
    valid_groups = [
        g for g in groups
        if any(p[0][0].strip() and not re.match(r'^(?:client|technolog(?:y|ies)|tools|environment|role|duration|domain)\s*:', p[0][0], re.I) for p in g)
    ]
    if len(valid_groups) > 1:
        description = '\n'.join(''.join(sep + part[0] for part, sep in g).strip() for g in valid_groups if g).strip()
    elif valid_groups:
        description = ''.join(separator + part[0] for part, separator in valid_groups[0]).strip()
    else:
        chosen = max(groups, key=lambda group: (any(p[0][4] for p in group), sum(len(p[0][0]) for p in group)))
        description = ''.join(separator + part[0] for part, separator in chosen).strip()
    return title or '', description or None
