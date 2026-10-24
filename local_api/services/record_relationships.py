"""Source-reference field evidence and explicit association uncertainty.

These are deterministic structural proposals, never verified entity records.
"""
import re

DEGREE_FAMILIES={
 'bachelor':r'\bbachelor\b|\bb\s?(?:com|tech|sc|ca|e|s|a)\b',
 'master':r'\bmaster(?:s)?\b|\bm\s?(?:com|tech|sc|ca|ba|e|s|a)\b',
 'postgraduate_certificate':r'\b(?:pg|postgraduate)\s+certificate\b',
 'diploma':r'\bdiploma\b|\bpgdca\b',
 'doctorate':r'\bphd\b|\bdoctorate\b',
 'secondary':r'\b(?:ssc|sslc|10th|class\s+x|schooling|matric(?:ulation)?)\b',
 'higher_secondary':r'\b(?:hsc|puc|intermediate|12th|class\s+xii|higher\s+secondary)\b',
}

def degree_families(text):
    lookup=re.sub(r'(?<=[A-Za-z])\.\s*(?=[A-Za-z])','',text)
    fams={key for key,pattern in DEGREE_FAMILIES.items() if re.search(pattern,lookup,re.I)}
    if not fams and re.search(r'\bhigh\s+school\b',lookup,re.I):
        fams.add('secondary')
    return fams


def dated_organization_header(text):
    """A short organization/location header with a parenthesized date range.

    Source-shape evidence only: no company-name dictionary or inferred values.
    """
    match=re.fullmatch(r"\s*([A-Za-z][A-Za-z&.,'’ /-]{1,90}?)\s*\(([^()]+)\)\s*",text)
    if not match:return False
    name,dates=match.groups()
    if len(name.split())>10 or re.search(r'\b(?:project|client|duration|education|school|university|college|certification|training|responsibilit\w*|performed|developed|managed|worked|experience|summary|engineer|developer|consultant|manager|analyst|lead)\b',name,re.I):return False
    return bool(re.search(r'\b(?:19|20)\d{2}\b',dates) and
                re.search(r'[-–—]|\b(?:to|till|until)\b',dates,re.I) and
                (len(re.findall(r'\b(?:19|20)\d{2}\b',dates))>=2 or re.search(r'\b(?:current(?:ly)?|present|working|date)\b',dates,re.I)))


def field_kinds(text,category):
    kinds=[]
    if re.search(r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\s*[‘’\']?\d{2}',text,re.I):kinds.append('dates')
    if category=='education':
        institution_marker = bool(re.search(r'\b(?:university|college|institute|institution|school|convent|academy|vidyalaya|vidyapeeth|polytechnic|board|iit|iiit|nit|cbse|icse)\b',text,re.I))
        explicit_credential = bool(re.search(r'\b(?:diploma|certificate|class\s+(?:x|xii)|sslc|ssc|10th|12th|matric(?:ulation)?)\b',text,re.I))
        # A named school is institution evidence, not automatically a degree.
        # Keep an explicit credential such as "High School Diploma" eligible.
        if degree_families(text) and not (institution_marker and not explicit_credential):kinds.append('qualification')
        if institution_marker:kinds.append('institution')
        if re.search(r'\b(?:cgpa|gpa|grade|distinction|percentage)\b|\d\s*%',text,re.I):kinds.append('grade')
        if re.search(r'\b(?:computer science|engineering|finance|commerce|accountancy|artificial intelligence|mathematics|business administration)\b',text,re.I):kinds.append('field_of_study')
    else:
        from local_api.services.record_subfields import employment_header_fields, ACTION, ROLE
        if ACTION.search(text):return [*kinds, 'responsibilities']
        # A delivering clause can continue a responsibility across PDF elements.
        # Require a clause, not just the word: "Delivering Systems Ltd" remains
        # organization evidence. Do this before generic suffixes such as systems.
        if re.match(r'^\s*(?:[•▪●*\-]\s*)?delivering\s+\S.+\s+(?:to|for|through|across|within)\s+\S', text, re.I):
            return [*kinds, 'responsibilities']
        if employment_header_fields(text):kinds.extend(['employer', 'title'])
        if len(text.split()) <= 18 and re.search(r'\b(?:engineer|developer|analyst|associate|consultant|manager|architect|intern|specialist|director|officer|executive|practitioner|lead|administrator|underwriter|supervisor)\b',text,re.I):kinds.append('title')
        if dated_organization_header(text) or re.search(r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies|ie)|solutions|ispl|paribas|bnp|pvt|private)\b|\b(?:company|employer)\s*:',text,re.I):kinds.append('employer')
        if re.match(r'^\s*[•▪●\-]?\s*(?:led|built|developed|managed|implemented|responsib|worked on|configured|designed|achieved|supported|created|performed|conducted)',text,re.I):kinds.append('responsibilities')
    if re.match(r'^\s*(?:location|work base)\s*:',text,re.I):kinds.append('location')
    return list(dict.fromkeys(kinds))


def annotate_relationships(section):
    """Add field source references, detect invalid/mixed/unsupported ownership."""
    if section.category not in {'experience','education'}:return
    assigned=set()
    for entry in section.entries:
        fields={};reasons=[]
        for index in entry.block_indices:
            if index in assigned:reasons.append('source_block_owned_by_multiple_entries')
            assigned.add(index)
            text=section.blocks[index].text
            kinds = field_kinds(text,section.category)
            if section.category == 'experience' and not kinds and fields.get('responsibilities') and section.blocks[index].assignment not in {'structural_heading','section_heading'} and text.strip() and not re.match(r'\s*(?:tools|technology|environment|skills|client|project)\b', text, re.I):
                kinds = ['responsibilities']
            for kind in kinds:fields.setdefault(kind,[]).append(index)
            if section.category=='education' and len(degree_families(text))>1:reasons.append('multiple_qualifications_in_one_source_span')
        if section.category=='education' and not fields.get('qualification'):reasons.append('qualification_not_established')
        if section.category=='experience' and not fields.get('employer'):reasons.append('employer_not_established_from_supported_fields')
        entry.fields=fields;entry.review_reasons=sorted(set(reasons));entry.relationship_status='needs_review' if reasons else 'provisional'
