"""Recover literal explicit URLs, retaining source whitespace until normalization."""
import re
from urllib.parse import urlsplit


def repair_url_whitespace(value):
    if not re.match(r'^https?://',value,re.I):return value
    # Only joins at explicit URL separators or a visibly split TLD before a path.
    repaired=re.sub(r'(?<=[/:.?#=&_-])\s+(?=[A-Za-z0-9/%?=&_.~-])','',value)
    repaired=re.sub(r'\s+(?=[/:.?#=&_-])','',repaired)
    repaired=re.sub(r'(\.[A-Za-z]{1,6})\s+([A-Za-z]{1,6})(?=/)',r'\1\2',repaired)
    return repaired


def raw_profile_values(blocks):
    from local_api.services.source_fragments import texts
    from local_api.services.contact_sections import PROFILE
    rows=texts(blocks);output={k:set() for k in ('linkedin_url','github_url','portfolio_url')}
    consumed=set()
    for index,text in enumerate(rows):
        if index in consumed:continue
        stripped=text.strip();label=re.match(r'^(?:portfolio|website|linkedin|github)\s*[:=]\s*(https?://.+)$',stripped,re.I)
        raw=label[1] if label else stripped
        if re.match(r'^https?://',raw,re.I):
            if raw.endswith('-') and index+1<len(rows):
                tail=rows[index+1].strip()
                if re.fullmatch(r'[a-z0-9][A-Za-z0-9._~/%+-]{0,100}',tail) and ('/' in tail or any(c.isdigit() for c in tail)):
                    raw+='\n'+tail;consumed.add(index+1)
            candidate=repair_url_whitespace(raw)
            if re.search(r'\s|[<>|]',candidate):continue
            try:parts=urlsplit(candidate)
            except ValueError:continue
            host=(parts.hostname or '').lower()
            if not host or '.' not in host:continue
            if (host=='linkedin.com' or host.endswith('.linkedin.com')):
                key='linkedin_url' if re.fullmatch(r'/in/[A-Za-z0-9_-]+/?',parts.path) else None
            elif (host=='github.com' or host.endswith('.github.com')):
                key='github_url' if re.fullmatch(r'/[A-Za-z0-9-]+/?',parts.path) else None
            else:key='portfolio_url'
            if key:output[key].add(raw)
        else:
            for match in PROFILE.finditer(text):
                output['github_url' if 'github.com/' in match.group().lower() else 'linkedin_url'].add(match.group())
            for match in re.finditer(r'(?<![/.\w])(?:(?:\(cid:239\)|/linkedin)\s*[:/]?\s*|(?:linkedin|in)\s*[:/]\s*)([A-Za-z0-9_-]{3,50})', text, re.I):
                handle = match.group(1)
                if not any(u.rstrip('/').endswith('/' + handle) for u in output['linkedin_url']):
                    output['linkedin_url'].add(f"linkedin.com/in/{handle}")
            for match in re.finditer(r'(?<![/.\w])(?:(?:\(cid:238\)|/github)\s*[:/]?\s*|github\s*[:/]\s*)([A-Za-z0-9_-]{3,50})', text, re.I):
                handle = match.group(1)
                if not any(u.rstrip('/').endswith('/' + handle) for u in output['github_url']):
                    output['github_url'].add(f"github.com/{handle}")
    return output


def linked_profile_label(element):
    return bool(element.metadata.get('word_source_hyperlinks') and
                re.fullmatch(r'\s*(?:portfolio|website|linkedin|github|profile)\s*[:=]?\s*',element.text,re.I))


def recover_header_urls(result,elements):
    from local_api.services.resume_sections import ALIASES,build_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.source_fragments import citations
    end=min((i for i,e in enumerate(elements) if heading_boundary(e.text,ALIASES)[0] and not linked_profile_label(e)),default=min(10,len(elements)))
    all_blocks=[b for s in result.sections for b in s.blocks]+list(result.needs_review)
    header=sorted([b for b in all_blocks if b.source_element_index<end],key=lambda b:(b.source_element_index,b.start))
    values=raw_profile_values(header);refs=[ref for items in values.values() for value in items for ref in citations(value,header)]
    ids={ref['source_id'] for ref in refs}
    if not ids:return result
    key=lambda b:f'e{b.source_element_index}:{b.start}:{b.end}'
    current=next((s for s in result.sections if s.category=='personal_information'),None)
    if current and ids<={key(b) for b in current.blocks}:return result
    grouped={s.category:[b for b in s.blocks if key(b) not in ids] for s in result.sections}
    grouped.setdefault('personal_information',[]).extend(b for b in header if key(b) in ids)
    grouped={c:sorted(bs,key=lambda b:(b.source_element_index,b.start)) for c,bs in grouped.items() if bs}
    updated=result.model_copy(deep=True);old={s.category:s for s in result.sections}
    affected={s.category for s in result.sections if any(key(b) in ids for b in s.blocks)}|{'personal_information'}
    updated.sections=[s if s.category in affected else old[s.category].model_copy(deep=True) for s in build_sections(grouped,elements,refine=False)]
    updated.needs_review=[b for b in result.needs_review if key(b) not in ids]
    updated.metadata['header_url_recovery']={'source_spans':len(ids)}
    return updated
