"""Source-reference field evidence and explicit association uncertainty.

These are deterministic structural proposals, never verified entity records.
"""
import re

DEGREE_FAMILIES={
 'bachelor':r'\bbachelor\b|\bb\s?(?:com|tech|sc|ca|e|s|a)\b',
 'master':r'\bmaster(?:s)?\b|\bm\s?(?:com|tech|sc|ca|ba|e|s|a)\b',
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
        if degree_families(text):kinds.append('qualification')
        if re.search(r'\b(?:university|college|institute|institution|school|convent|academy|vidyalaya|vidyapeeth|polytechnic|board|iit|iiit|nit|cbse|icse)\b',text,re.I):kinds.append('institution')
        if re.search(r'\b(?:cgpa|gpa|grade|distinction|percentage)\b|\d\s*%',text,re.I):kinds.append('grade')
        if re.search(r'\b(?:computer science|engineering|finance|commerce|accountancy|artificial intelligence|mathematics|business administration)\b',text,re.I):kinds.append('field_of_study')
    else:
        if re.search(r'\b(?:engineer|developer|analyst|associate|consultant|manager|architect|intern|specialist|director|officer|executive|practitioner|lead|administrator)\b',text,re.I):kinds.append('title')
        if dated_organization_header(text) or re.search(r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies|ie)|solutions)\b|\b(?:company|employer)\s*:',text,re.I):kinds.append('employer')
        if re.match(r'^\s*[•▪●\-]?\s*(?:led|built|developed|managed|implemented|responsib|worked on|configured|designed|achieved|supported|created|performed|conducted)',text,re.I):kinds.append('responsibilities')
    if re.match(r'^\s*(?:location|work base)\s*:',text,re.I):kinds.append('location')
    return kinds


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
            for kind in field_kinds(text,section.category):fields.setdefault(kind,[]).append(index)
            if section.category=='education' and len(degree_families(text))>1:reasons.append('multiple_qualifications_in_one_source_span')
        if section.category=='education' and not fields.get('qualification'):reasons.append('qualification_not_established')
        if section.category=='experience' and not fields.get('employer'):reasons.append('employer_not_established_from_supported_fields')
        entry.fields=fields;entry.review_reasons=sorted(set(reasons));entry.relationship_status='needs_review' if reasons else 'provisional'
