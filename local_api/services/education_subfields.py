"""Conservative refinement of one existing education record, never regrouping it."""
import re

DEGREE = re.compile(r'(?<!\w)(?:M\.?\s?Sc\.?|B\.?\s?Sc\.?|M\.?Tech\.?|B\.?Tech\.?|B\.?E\.?|M\.?E\.?|MBA|MCA|BCA|Master of (?:Technology|Science|Engineering|Business Administration)|Bachelor of (?:Technology|Science|Engineering|Arts|Commerce))(?!\w)', re.I)


def refine_education(values, blocks):
    values = dict(values)
    text = '\n'.join(b.text for b in blocks)
    reasons = []
    if re.search(r'\b(?:expected|pursuing|anticipated|in progress)\b', text, re.I):
        reasons.append('Expected or in-progress education; dates are provisional, not confirmed graduation.')
    degrees = [(b, m) for b in blocks for m in DEGREE.finditer(b.text)]
    if len(degrees) != 1:
        # Never pair qualifications in a merged source span by proximity.
        if len(degrees) > 1:
            reasons.append('Multiple qualifications in one supplied record; child associations unresolved.')
            for field in values:
                values[field] = None
        return values, reasons
    block, match = degrees[0]
    if not values.get('degree') or values['degree'] == block.text.strip():
        values['degree'] = match.group()
    following = block.text[match.end():]
    major = re.match(r'\s*(?:in\s+|[-–]\s*)?\(?([A-Za-z][A-Za-z &/\-]*?)(?:\)|,|\||\s+[-–—]\s+|\s+(?:19|20)\d{2}\b|$)', following)
    if major and not values.get('field_of_study'):
        candidate = major.group(1).strip()
        if not re.search(r'\b(?:university|college|institute|GPA|expected|pursuing)\b', candidate, re.I):
            values['field_of_study'] = candidate
    institutions = []
    for b in blocks:
        for part in re.split(r'[,|\n]', b.text):
            part = part.strip()
            if re.fullmatch(r'[A-Za-z][A-Za-z .&\-]*(?:University|College|Institute|School)(?: of [A-Za-z &\-]+)?', part, re.I):
                institutions.append(part)
    institutions = list(dict.fromkeys(institutions))
    if len(institutions) == 1 and not values.get('institution'):
        values['institution'] = institutions[0]
    ranges = list(re.finditer(r'\b((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2})\b', text))
    if len(ranges) == 1:
        values['start_year'], values['graduation_year'] = ranges[0].group(1, 2)
    grades = list(re.finditer(r'\b(?:CGPA|GPA|Grade)\s*[:=]?\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)', text, re.I))
    if len(grades) == 1 and not values.get('grade_or_gpa'):
        values['grade_or_gpa'] = grades[0].group(1)
    return values, reasons
