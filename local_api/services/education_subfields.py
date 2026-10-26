"""Conservative refinement of one existing education record, never regrouping it."""
import re
from local_api.services.source_fragments import runs, texts

DEGREE = re.compile(r'(?<!\w)(?:PG\s+Certificate|Post\s+Graduate\s+Diploma|PGDM|Diploma|Master of (?:Technology|Science|Engineering|Business Administration|Computer Applications?)|Bachelor of (?:Technology|Science|Engineering|Arts|Commerce|Pharmacy)|M\.?\s?Sc\.?|B\.?\s?Sc\.?|B\.?Com\.?|M\.?Com\.?|M\.?Tech\.?|B\.?Tech\.?|B\.?E\.?|M\.?E\.?|MBA|MCA|BCA)(?!\w)', re.I)


def refine_education(values, blocks):
    values = dict(values)
    source_texts = texts(blocks)
    text = '\n'.join(source_texts)
    reasons = []
    if re.search(r'\b(?:expected|pursuing|anticipated|in progress)\b', text, re.I):
        reasons.append('Expected or in-progress education; dates are provisional, not confirmed graduation.')
    degrees = []
    for run in runs(blocks):
        previous = None
        for b in run:
            for local in DEGREE.finditer(b.text):
                # Match physical rows first: PDF joins may put a year directly
                # before Master/Bachelor, defeating a whole-element word boundary.
                source = ''.join(part.text for part in run)[b.start-run[0].start+local.start():]
                match = re.match(re.escape(local.group()),source,re.I)
                if previous and re.fullmatch(r'\s*\(\s*', b.text[previous.end():local.start()]) and b.text[local.end():].startswith(')'):
                    continue
                if (previous and local.group().casefold() == 'pgdm' and 'diploma' in previous.group().casefold()
                        and re.fullmatch(r'\s+in\s+[A-Za-z ]+\(\s*', b.text[previous.end():local.start()])
                        and b.text[local.end():].startswith(')')):
                    continue
                degrees.append((source,match));previous=local
    if not degrees:
        degrees=[(source,match) for source in source_texts for match in DEGREE.finditer(source)]
    if len(degrees) > 1:
        reasons.append('Multiple qualifications in one supplied record; child associations unresolved.')
        return {key: None for key in values}, reasons
    if degrees:
        source, match = degrees[0]
        values['degree'] = match.group()
        following = source[match.end():]
        major = re.match(r'\s*(?:in\s+|[-\u2013]\s*)?\(?([A-Za-z][A-Za-z &/\-]*?)(?:\)|\s*\(|,|\||\s+from\b|\s+[-\u2013\u2014]\s+|\s+(?:19|20)\d{2}\b|$)', following)
        if major and not values.get('field_of_study'):
            candidate = major.group(1).strip()
            if not re.fullmatch(r'(?:MCA|MBA|B\.?Com|B\.?E\.?|B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc)', candidate, re.I) and not re.search(r'\b(?:university|college|institute|GPA|expected|pursuing)\b', candidate, re.I):
                values['field_of_study'] = candidate
    institutions = []
    for source in [*(b.text for b in blocks), *source_texts]:
        for part in re.split(r'[,|\n]|\s+[-\u2013\u2014]\s+', source):
            part = re.sub(r'^(?:Institution|University|College)\s*:\s*', '', part.strip(), flags=re.I)
            if re.fullmatch(r"[A-Za-z][A-Za-z .&/'\u2019\-]*(?:University|College|Institute|School|Vidyalaya)(?: of [A-Za-z &\-]+)?", part, re.I) and not DEGREE.search(part):
                institutions.append(part)
    institutions = list(dict.fromkeys(institutions))
    institutions = [value for value in institutions if not any(other != value and value.endswith(other) for other in institutions)]
    if len(institutions) == 1:
        values['institution'] = institutions[0]
    elif len(institutions) > 1:
        values['institution'] = None
        reasons.append('Multiple institutions in one record; association requires source review.')
    ranges = list(re.finditer(r'\b((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2})\b', text))
    if len(ranges) == 1:
        values['start_year'], values['graduation_year'] = ranges[0].group(1, 2)
    abbreviated = list(re.finditer(r'\b((?:19|20)\d{2})\s*[-\u2013\u2014]\s*(\d{2})(?!\d)',text))
    if not ranges and len(abbreviated)==1:
        values['start_year']=abbreviated[0].group(1)
        values['graduation_year']=None
        reasons.append('Abbreviated completion year in source; no century inferred.')
    if len(ranges) == 0 and not abbreviated:
        years = list(dict.fromkeys(re.findall(r'\b(?:19|20)\d{2}\b', text)))
        if len(years) == 1:values['graduation_year'] = years[0]
    grades = list(re.finditer(r'\b(?:CGPA|GPA|Grade)\s*[:=]?\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)', text, re.I))
    if len(grades) == 1 and not values.get('grade_or_gpa'):
        values['grade_or_gpa'] = grades[0].group(1)
    return values, reasons
