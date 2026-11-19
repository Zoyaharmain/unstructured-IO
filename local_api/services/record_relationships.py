"""Source-reference field evidence and explicit association uncertainty.

These are deterministic structural proposals, never verified entity records.
"""
import re

DEGREE_FAMILIES={
 'bachelor':r'\bbachelors?\b|\bb\s?(?:com|tech|sc|ca|e|s|a)\b',
 'master':r'\bmaster(?:s)?\b|\bm\s?(?:com|tech|sc|ca|ba|e|s|a)\b',
 'postgraduate_certificate':r'\b(?:pg|postgraduate)\s+certificate\b',
 'diploma':r'\bdiploma\b|\b(?:pgdca|pgdb|pgdm)\b',
 'doctorate':r'\bph\s*d\b|\bdoctorate\b',
 'secondary':r'\b(?<!higher\s)(?<!senior\s)(?:ssc|sslc|10th|class\s+x|schooling|matric(?:ulation)?|secondary\s+(?:school(?:\s+certificate)?|certificate))\b',
 'higher_secondary':r'\b(?:hsc|puc|intermediate|12th|class\s+xii|higher\s+secondary)\b',
}

def degree_families(text):
    lookup=re.sub(r'(?<=[A-Za-z])\.(\s*)(?=[A-Za-z])',r'\1',text)
    fams={key for key,pattern in DEGREE_FAMILIES.items() if re.search(pattern,lookup,re.I)}
    if not fams and re.search(r'\bhigh\s+school\b',lookup,re.I):
        fams.add('secondary')
    return fams


def dated_organization_header(text):
    """A short organization/location header with a parenthesized date range.

    Source-shape evidence only: no company-name dictionary or inferred values.
    """
    match=re.fullmatch(r"\s*([A-Za-z][A-Za-z&.,'’ /-]{1,90}?)\s*\(([^()]+)\)(?:\s*[•▪●*o\uf0b7\-–—]\s*)?",text)
    if not match:return False
    name,dates=match.groups()
    if len(name.split())>10 or re.search(r'\b(?:project|client|duration|education|school|university|college|certification|training|responsibilit\w*|performed|developed|managed|worked|experience|summary|engineer|developer|consultant|manager|analyst|lead)\b',name,re.I):return False
    return bool(re.search(r'\b(?:19|20)\d{2}\b',dates) and
                re.search(r'[-–—]|\b(?:to|till|until)\b',dates,re.I) and
                (len(re.findall(r'\b(?:19|20)\d{2}\b',dates))>=2 or re.search(r'\b(?:current(?:ly)?|present|working|date)\b',dates,re.I)))


def field_kinds(text,category):
    if re.search(r'\b(?:system\s+(?:prompt|instruction|override)|ignore\s+all\s+(?:previous|prior)\s+instructions|human\s+review\s*:|output\s+role\s*:)\b', text, re.I):
        return []
    kinds=[]
    if re.search(r'(?:19|20)\d{2}|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*[‘’\']?\d{2,4}',text,re.I):kinds.append('dates')
    if category=='education':
        institution_marker = bool(re.search(r'\b(?:university|college|institute|institution|school|convent|academy|vishwavidyalaya|vishwavidyalay|vidyalaya|vidyapeeth|polytechnic|board|iit|iiit|nit|cbse|icse)\b',text,re.I))
        explicit_credential = bool(re.search(r'\b(?:diploma|certificate|class\s+(?:x|xii)|sslc|ssc|10th|12th|matric(?:ulation)?)\b',text,re.I))
        # A named school is institution evidence, not automatically a degree.
        # Keep an explicit credential such as "High School Diploma" eligible.
        if degree_families(text) and not (institution_marker and not explicit_credential):kinds.append('qualification')
        if institution_marker and not re.match(r'^(?:student|represented|participated|member|won)\b',text,re.I):kinds.append('institution')
        if re.search(r'\b(?:cgpa|gpa|grade|distinction|percentage)\b|\d\s*%',text,re.I):kinds.append('grade')
        if re.search(r'\b(?:computer science|engineering|finance|commerce|accountancy|artificial intelligence|mathematics|business administration)\b',text,re.I):kinds.append('field_of_study')
    else:
        from local_api.services.record_subfields import employment_header_fields, ACTION, ROLE, responsibility_fragment
        if re.match(r'^\s*[•▪●*✓✔\-\uf0b7]\s*', text): return [*kinds, 'responsibilities']
        if re.match(r'^\s*(?:technolog(?:y|ies)\s+(?:used|stack|tools|environment|include|overview)\b|technolog(?:y|ies)\s*[:=-]|tools\s*&|tools\s+used|tools\s*:|environment\s*:|tech stack\b)', text, re.I):
            return [*kinds, 'technologies']
        explicit=employment_header_fields(text)
        if explicit:
            return list(dict.fromkeys(kinds
                + (['employer'] if 'company' in explicit else [])
                + (['title'] if 'role' in explicit else [])
                + (['client'] if 'client' in explicit else [])
                + (['location'] if 'location' in explicit else [])))
        if text.strip() in {'systems', 'delivering systems'}:return []
        if re.match(r'^\s*(?:\d+\.\s*)?Client\b',text,re.I):return [*kinds,'client']
        if responsibility_fragment(text):return [*kinds, 'responsibilities']
        # A delivering clause can continue a responsibility across PDF elements.
        # Require a clause, not just the word: "Delivering Systems Ltd" remains
        # organization evidence. Do this before generic suffixes such as systems.
        if re.match(r'^\s*(?:[•▪●*\-]\s*)?delivering\s+\S.+\s+(?:to|for|through|across|within)\s+\S', text, re.I):
            return [*kinds, 'responsibilities']
        label = re.match(r'^\s*([A-Za-z ]+)\s*[:=-]\s*(.*)$',text)
        if label:
            from local_api.services.record_subfields import ALIASES
            field=ALIASES['experience'].get(label[1].strip().casefold(),label[1].strip().casefold())
            if field in {'technologies','responsibilities','location'}:return [field]
            if field in {'company','employer'} and not label[2].strip():return []
        header=employment_header_fields(text)
        if 'company' in header:kinds.append('employer')
        if 'role' in header:kinds.append('title')
        if 'location' in header:kinds.append('location')
        from local_api.services.record_subfields import ACTION
        if (len(text.split()) <= 18
                and not responsibility_fragment(text)
                and not ACTION.search(text)
                and not re.match(r'^(?:[•▪●*–—\-]\s*)?(?:blended|operated|authored|managed|delivered|supported|worked|engineered|led|built)\b', text, re.I)
                and any(m.group().casefold() not in {'engineering','role','roles'} for m in ROLE.finditer(text))):
            kinds.append('title')
        if dated_organization_header(text) or (
            not responsibility_fragment(text)
            and not re.search(r'\b(?:fellowship|scholarship|research\s+grant|grant\s+funding)\b', text, re.I)
            and (':' not in text or re.match(r'^\s*(?:company|employer|organization)\s*[:=-]', text, re.I))
            and not text[:1].islower()
            and not re.match(r'^\s*(?:tools|technolog(?:y|ies)|environment|skills|tech stack)\b', text, re.I)
            and not re.match(r'^(?:with|for|across|through|by|from|to|and)\s+', text, re.I)
            and not (len(text.split()) > 6 and text.rstrip().endswith('-'))
            and not (text.rstrip().endswith('.') and not re.search(r'\b(?:ltd|inc|corp|co|pvt)\.$', text.rstrip(), re.I))
            and (re.search(r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies|ie)|solutions|ispl|paribas|bnp|pvt|private|labs?|clinic|hospital|center|centre|group|agency|partners|studio|holdings)\b',text,re.I) or re.search(r'\b(?:company|employer)\s*[:=-]',text,re.I))
        ):kinds.append('employer')
        if re.match(r'^\s*[•▪●\-]?\s*(?:led|built|developed|managed|implemented|responsib|worked on|configured|designed|achieved|supported|created|performed|conducted|architect(?:ed|ing)?|optimi[sz](?:ed|ing|e)?|resolv(?:ed|ing|e)?|automat(?:ed|ing|e)?|integrat(?:ed|ing|e)?|analy[sz](?:ed|ing|e)?|proactively|successfully|eliminat(?:ed|ing|e)?|identif(?:ied|y)?)',text,re.I):kinds.append('responsibilities')
    if re.match(r'^\s*(?:location|work base)\s*:',text,re.I):kinds.append('location')
    return list(dict.fromkeys(kinds))


def annotate_relationships(section):
    """Add field source references, detect invalid/mixed/unsupported ownership."""
    if section.category not in {'experience','education'}:return
    assigned=set()
    for entry in section.entries:
        if entry.fields or entry.boundary_reason == 'validated source ownership':
            if any(index in assigned for index in entry.block_indices):
                entry.relationship_status = 'needs_review'
                entry.review_reasons = sorted(set(entry.review_reasons + ['source_block_owned_by_multiple_entries']))
            assigned.update(entry.block_indices)
            continue
        generated = {'source_block_owned_by_multiple_entries','multiple_qualifications_in_one_source_span',
                     'qualification_not_established','employer_not_established_from_supported_fields'}
        fields={};reasons=[r for r in entry.review_reasons if r not in generated]
        for index in entry.block_indices:
            if index in assigned:reasons.append('source_block_owned_by_multiple_entries')
            assigned.add(index)
            text=section.blocks[index].text
            kinds = field_kinds(text,section.category)
            if section.category == 'experience' and section.blocks[index].assignment in {'local_record_continuation','local_responsibility_bullet'}:
                kinds = ['responsibilities']
            from local_api.services.record_subfields import employment_header_fields
            if (section.category=='experience' and fields.get('employer') and fields.get('title')
                    and len(text.split())>8 and text.rstrip().endswith('.')
                    and not employment_header_fields(text)):
                kinds=['responsibilities']
            if section.category == 'experience' and not kinds and fields.get('responsibilities') and section.blocks[index].assignment not in {'structural_heading','section_heading'} and text.strip() and not re.match(r'\s*(?:tools|technology|environment|skills|client|project)\b', text, re.I):
                kinds = ['responsibilities']
            for kind in kinds:fields.setdefault(kind,[]).append(index)
            if section.category=='education' and len(degree_families(text))>1:reasons.append('multiple_qualifications_in_one_source_span')
        if section.category == 'experience' and len(entry.block_indices) >= 2:
            first, second = (section.blocks[i] for i in entry.block_indices[:2])
            first_text = first.text.strip()
            from local_api.services.record_subfields import paired_employment_header, RANGE, ROLE, employment_header_fields
            if (paired_employment_header(first_text,second.text) or (first.source_element_index == second.source_element_index and first.end == second.start
                    and 0 < len(first_text.split()) <= 10 and not re.search(r'\d|[@:;]', first_text)
                    and not (set(field_kinds(first_text, 'experience')) - {'employer'}) and 'title' in field_kinds(second.text, 'experience'))):
                if RANGE.search(first_text) or re.search(r'\b(?:19|20)\d{2}\b', first_text):
                    fields['dates'] = [entry.block_indices[0]]
                    fields['employer'] = [entry.block_indices[1]]
                elif ROLE.search(first_text) and not employment_header_fields(first_text).get('company') and (employment_header_fields(second.text).get('company') or not ROLE.search(second.text)):
                    fields['title'] = [entry.block_indices[0]]
                    fields['employer'] = [entry.block_indices[1]]
                else:
                    fields['employer'] = [entry.block_indices[0]]
        if section.category == 'experience' and not fields.get('employer'):
            from local_api.services.record_subfields import RANGE, is_place, ROLE, ACTION, responsibility_fragment, employment_header_fields
            from local_api.services.resume_structure import heading_boundary
            from local_api.services.resume_sections import ALIASES
            for idx in entry.block_indices[:5]:
                if section.blocks[idx].assignment in {'section_heading', 'structural_heading', 'heading_context'}:
                    continue
                if idx in fields.get('responsibilities', []):
                    continue
                if employment_header_fields(section.blocks[idx].text).get('company'):
                    fields['employer'] = [idx]
                    break
                if idx in fields.get('title', []):
                    continue
                cand_text = section.blocks[idx].text.strip()
                clean_cand = re.split(r'\s*[|—–-]\s*', cand_text)[0].strip()
                words = clean_cand.split()
                if not (1 <= len(words) <= 6 and clean_cand and clean_cand[0].isupper() and not re.search(r'[@:;]', clean_cand)):
                    continue
                if (re.match(r'^(?:client|project)\b', clean_cand, re.I) or RANGE.search(cand_text) or RANGE.search(clean_cand)
                        or re.search(r'(?:19|20)\d{2}', cand_text) or ROLE.search(clean_cand) or ACTION.search(clean_cand)
                        or responsibility_fragment(clean_cand) or heading_boundary(clean_cand, ALIASES)[0]):
                    continue
                if is_place(clean_cand):
                    continue
                fields['employer'] = [idx]
                break
        if section.category=='education' and not fields.get('qualification'):reasons.append('qualification_not_established')
        if section.category=='experience' and not fields.get('employer'):
            from local_api.services.employer_context import valid_employer_context
            established_parent = any(valid_employer_context(section, entry, i) for i in entry.context_fields.get('company', []))
            first_block = section.blocks[entry.block_indices[0]] if entry.block_indices else None
            is_client_entry = bool('client' in fields or (first_block and re.match(r'^\s*(?:\d+\.\s*)?Client\b', first_block.text, re.I)))
            if not is_client_entry and not established_parent:
                reasons.append('employer_not_established_from_supported_fields')
        entry.fields=fields;entry.review_reasons=sorted(set(reasons));entry.relationship_status='needs_review' if reasons else 'provisional'
