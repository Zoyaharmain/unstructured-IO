"""Conservative candidate-contact routing and literal contact values."""
import re
from local_api.services.source_fragments import texts

EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r'(?<![\w@])(?:\+\d{1,3}[ .-]?)?(?:\(?\d{2,5}\)?[ .-]?){1,4}\d{2,5}(?![\w@])')
PROFILE = re.compile(r"(?<![\w./-])(?:https?://)?(?:www\.)?(?:github\.com/[A-Za-z0-9][A-Za-z0-9-]*|linkedin\.com/in/[A-Za-z0-9_-]+)/*(?=$|[\s),;])", re.I)


def profile_values(blocks):
    output = {'github_url': set(), 'linkedin_url': set()}
    for text in texts(blocks):
        for match in PROFILE.finditer(text):
            value = match.group()
            key = 'github_url' if 'github.com/' in value.casefold() else 'linkedin_url'
            output[key].add(value)
    return output


LABEL = re.compile(r'^\s*(?:e[ -]?mail(?:[ -]?(?:id|address))?|contact(?:\s+(?:details|number|no\.?))?|mobile(?:\s+(?:number|no\.?))?|phone(?:\s+(?:number|no\.?))?|tel(?:ephone)?)\s*[:=\-]', re.I)


def contact_values(blocks):
    output = {'email': set(), 'phone': set()}
    for text in texts(blocks):
        email_matches = list(EMAIL.finditer(text))
        email_ranges = [m.span() for m in email_matches]
        for match in email_matches:
            literal = match.group()
            # Some PDF runs join a country-prefixed phone directly to an email.
            # Split only with that explicit phone prefix; digit-leading emails
            # without this source context remain untouched.
            country = re.search(r'\+\d{1,3}[ .-]+$', text[:match.start()])
            digits = re.match(r'\d{10}(?=[A-Za-z])', literal)
            if country and digits:
                output['email'].add(literal[digits.end():])
                output['phone'].add(text[country.start():match.start()+digits.end()])
            else:
                output['email'].add(literal)
        for match in PHONE.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in email_ranges):
                continue
            if 10 <= sum(c.isdigit() for c in match.group()) <= 15:
                output['phone'].add(match.group().strip())
    return output


def recover_contact_sections(result, elements=None):
    """Move only identifiable contact fragments; never search reference records."""
    from local_api.schemas.sections import ResumeSection
    # Unlabelled contact values are eligible only before professional content.
    body_start = min((b.source_element_index for s in result.sections
                      if s.category in {'experience','education','projects','references'} for b in s.blocks), default=3)
    reference_start = min((b.source_element_index for s in result.sections if s.category == 'references' for b in s.blocks), default=float('inf'))

    def candidate(b):
        if b.page_number not in {None, 1} or b.source_element_index >= reference_start or len(b.text) > 300:
            return False
        values = contact_values([b])
        profiles = profile_values([b])
        if not any(values.values()) and not any(profiles.values()):
            return False
        if any(profiles.values()) and b.source_element_index < body_start:
            return True
        if LABEL.match(b.text):
            return True
        value = b.text.strip(' \t\r\n|•')
        return b.source_element_index < body_start and bool(EMAIL.fullmatch(value) or PHONE.fullmatch(value))

    heading_contacts = [b for s in result.sections if s.category == 'personal_information'
                        for b in s.blocks if b.assignment in {'section_heading','structural_heading'}
                        and LABEL.match(b.text) and candidate(b)]
    moved = [b for b in result.needs_review if candidate(b)]
    # A two-column PDF can leave the prominent name outside the contact lane.
    # Require unique, dominant first-page typography, not a person's name list.
    if elements:
        from statistics import median
        from local_api.services.resume_structure import heading_aliases, normalized_heading
        from local_api.services.record_subfields import ROLE
        from local_api.services.resume_sections import ANCHORS
        aliases = heading_aliases(ANCHORS)
        sizes = [h['font_size'] for el in elements if el.page_number == 1
                 for h in el.metadata.get('pdf_source_lines', []) if h.get('font_size')]
        candidates = []
        for b in result.needs_review:
            hs = elements[b.source_element_index].metadata.get('pdf_source_lines', [])
            hs = [h for h in hs if min(b.end,h.get('end',0)) > max(b.start,h.get('start',0))]
            text = b.text.strip()
            if (sizes and b.page_number == 1 and 2 <= len(text.split()) <= 5
                    and all(c.isalpha() or c in " .'-" for c in text)
                    and normalized_heading(text) not in aliases and not ROLE.search(text)
                    and hs and max(h.get('font_size',0) for h in hs) >= 1.5*median(sizes)
                    and all(len(h.get('bbox',[])) == 4 and h['bbox'][1] < .1 for h in hs)):
                candidates.append(b)
        if len(candidates) == 1:
            moved.extend(b for b in candidates if b not in moved)
    for section in result.sections:
        if section.category in {'summary','skills'}:
            moved.extend(b for b in section.blocks if (LABEL.match(b.text) or any(profile_values([b]).values())) and candidate(b))
    if not moved and not heading_contacts:
        return result
    repaired = result.model_copy(deep=True)
    keys = {(b.source_element_index,b.start,b.end) for b in moved}
    def key(b): return (b.source_element_index,b.start,b.end)
    def canonical(blocks):
        pieces=[];previous=None
        for b in blocks:
            if previous is not None and not (previous.source_element_index == b.source_element_index and previous.end == b.start):pieces.append('\n')
            pieces.append(b.text);previous=b
        return ''.join(pieces)
    repaired.needs_review = [b for b in repaired.needs_review if key(b) not in keys]
    parent = next((s for s in repaired.sections if s.category == 'personal_information'),None)
    if parent is None:
        parent=ResumeSection(category='personal_information',label='Personal information',blocks=[])
        repaired.sections.insert(0,parent)
    for section in repaired.sections:
        if section is parent:
            continue
        if any(key(b) in keys for b in section.blocks):
            kept = [(i,b) for i,b in enumerate(section.blocks) if key(b) not in keys]
            old_to_new = {old:new for new,(old,_) in enumerate(kept)}
            section.blocks = [b for _,b in kept]
            for entry in section.entries:
                entry.block_indices=[old_to_new[i] for i in entry.block_indices if i in old_to_new]
                entry.fields={name:[old_to_new[i] for i in indices if i in old_to_new] for name,indices in entry.fields.items()}
            section.entries=[e for e in section.entries if e.block_indices]
            section.text=canonical(section.blocks);section.highlights=[];section.readable_blocks=[]
    heading_keys = {key(b) for b in heading_contacts}
    parent.blocks = [b.model_copy(update={'assignment':'contact_recovered','reason':'Inline contact values are content, not a section heading.'}) if key(b) in heading_keys else b for b in parent.blocks]
    parent.blocks=sorted(parent.blocks+[b.model_copy(update={'assignment':'contact_recovered','reason':'Explicit candidate contact source recovered without changing text or offsets.'}) for b in moved], key=key)
    parent.text=canonical(parent.blocks);parent.highlights=[];parent.entries=[];parent.readable_blocks=[]
    repaired.metadata['contact_section_recovery']={'recovered_blocks':len(moved)+len(heading_contacts)}
    repaired.metadata['assigned_units']=sum(len(s.blocks) for s in repaired.sections)
    repaired.metadata['review_units']=len(repaired.needs_review)
    total=sum(len(b.text) for s in repaired.sections for b in s.blocks)+sum(len(b.text) for b in repaired.needs_review)
    repaired.metadata['assigned_text_percent']=round(100*(total-sum(len(b.text) for b in repaired.needs_review))/total,2) if total else 0
    repaired.status='needs_review' if repaired.needs_review else 'provisional'
    return repaired
