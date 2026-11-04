"""Conservative refinement of one existing education record, never regrouping it."""
import re
from local_api.services.source_fragments import runs, texts

DEGREE = re.compile(
    r'(?<!\w)(?:Higher\s+Secondary(?:\s+School)?\s+Certificate(?:\s*\([^)]*\))?|'
    r'Secondary\s+School\s+Certificate(?:\s*\([^)]*\))?|'
    r'Higher\s+Secondary(?!\s+School\b)|High\s+School\s+Diploma|HSC|SSC|SSLC|'
    r'PG\s+Certificate|Post\s+Graduate\s+Diploma|PGDM|PGDB|Diploma|'
    r'Master of (?:Software Engineering|Technology|Science|Engineering|Business Administration|Computer Applications?)|'
    r'Bachelors? (?:of|in) (?:Technology|Science|Engineering|Arts|Commerce|Pharmacy)|'
    r'M\.?\s?Sc\.?|B\.?\s?Sc\.?|B\.?Com\.?|M\.?Com\.?|M\.?Tech\.?|B\.?Tech\.?|B\.?E\.?|M\.?E\.?|MBA|MCA|BCA)(?!\w)',
    re.I
)


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
    expansions={'pgdb':r'Post\s+Graduate\s+Diploma','pgdm':r'Post\s+Graduate\s+Diploma',
                'mba':r'Master\s+of\s+Business\s+Administration',
                'btech':r'Bachelor\s+of\s+Technology'}
    if len(degrees)==2:
        for acronym,expansion in expansions.items():
            short=[item for item in degrees if re.sub(r'[^a-z]','',item[1].group().casefold())==acronym]
            if len(short)==1 and re.search(r'\b'+r'\.?'.join(acronym)+r'\.?\s*(?:\(|[–—-])\s*'+expansion,text,re.I):
                degrees=short
                break
    if len(degrees) > 1:
        reasons.append('Multiple qualifications in one supplied record; child associations unresolved.')
        return {key: None for key in values}, reasons
    if degrees:
        source, match = degrees[0]
        values['degree'] = match.group()
        following = source[match.end():]
        # "from" introduces the institution, never a subject. A parser hint
        # must not turn the institution into the qualification's major.
        if re.match(r'\s*from\b', following, re.I):
            values['field_of_study'] = None
        major = re.match(r'\s*(?:in\s+|[-\u2013]\s*)?\(?([A-Za-z][A-Za-z &/\-]*?)(?:\)|\s*\(|,|\||\s+from\b|\s+[-\u2013\u2014]\s+|\s+(?:19|20)\d{2}\b|$)', following)
        if major and not values.get('field_of_study'):
            candidate = major.group(1).strip()
            if not re.match(r'from\b', candidate, re.I) and not re.fullmatch(r'(?:MCA|MBA|B\.?Com|B\.?E\.?|B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc)', candidate, re.I) and not re.search(r'\b(?:university|college|institute|GPA|expected|pursuing)\b', candidate, re.I):
                values['field_of_study'] = candidate
        subject = re.match(r'(?:Master|Bachelor) of (.+)', match.group(), re.I)
        if subject and not values.get('field_of_study'):
            values['field_of_study'] = subject[1]
    # An expanded qualification name is not a subject/major.
    degree_key=re.sub(r'[^a-z]','',str(values.get('degree','')).casefold())
    major_key=re.sub(r'[^a-z]','',str(values.get('field_of_study','')).casefold())
    if degree_key in expansions:
        expanded_key=re.sub(r'[^a-z]','',expansions[degree_key].replace(r'\s+','').casefold())
        if major_key and expanded_key.startswith(major_key) and following.lstrip().startswith(('(', '–', '—', '-')):
            values['field_of_study']=None
    parenthetic=values.get('field_of_study')
    if parenthetic and re.match(r'^[A-Z][A-Z0-9.]{2,}\s+[A-Za-z]',parenthetic) and degrees and following.lstrip().startswith('('):
        values['field_of_study']=None
        reasons.append('Parenthesized acronym/location text may identify an institution rather than a subject; association requires review.')
    institutions = []
    # Explicit "qualification from institution passing year ..." establishes
    # the institution even for acronyms without University/College suffixes.
    for source in source_texts:
        relation = re.search(r'\bfrom\s+(.+?)\s+(?:passing\s+year|year\s+of\s+passing)\b', source, re.I)
        if relation and DEGREE.search(source[:relation.start()]):
            institutions.append(relation[1].strip(' ,'))
    for source in [*(b.text for b in blocks), *source_texts]:
        for part in re.split(r'[,|\n]|\s+[-\u2013\u2014]\s+', source):
            part = re.sub(r'^(?:Institution|University|College)\s*:\s*', '', part.strip(), flags=re.I)
            if (re.fullmatch(r"[A-Za-z][A-Za-z .&/'\u2019\-(),]*", part)
                    and re.search(r'\b(?:University|College|Institute|School|Vidyalaya)\b',part,re.I)
                    and len(part.split())<=18 and not DEGREE.search(part)
                    and not re.match(r'^(?:student|represented|participated|member|won)\b',part,re.I)):
                institutions.append(part)
    institutions = list(dict.fromkeys(institutions))
    institutions = [value for value in institutions if not any(other != value and value.endswith(other) for other in institutions)]
    if len(institutions) == 1:
        values['institution'] = institutions[0]
    elif len(institutions) > 1:
        values['institution'] = None
        reasons.append('Multiple institutions in one record; association requires source review.')
    from local_api.services.record_subfields import RANGE
    exact_ranges={m.group():m for source in source_texts for m in RANGE.finditer(source)}
    if len(exact_ranges)==1:
        period=next(iter(exact_ranges.values()))
        values['start_year'],values['graduation_year']=period[1],period[2]
    ranges = list(re.finditer(r'\b((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2})\b', text))
    if len(ranges) == 1:
        values['start_year'], values['graduation_year'] = ranges[0].group(1, 2)
    month_ranges = list(re.finditer(r'\b(\d{1,2}/(?:19|20)\d{2})\s*[-–—]\s*(\d{1,2}/(?:19|20)\d{2})\b', text))
    if not ranges and len(month_ranges) == 1:
        values['start_year'], values['graduation_year'] = month_ranges[0].group(1, 2)
    abbreviated = list(re.finditer(r'\b((?:19|20)\d{2})\s*[-\u2013\u2014]\s*(\d{2})(?!\d)',text))
    if not ranges and not month_ranges and len(abbreviated)==1:
        values['start_year']=abbreviated[0].group(1)
        values['graduation_year']=None
        reasons.append('Abbreviated completion year in source; no century inferred.')
    if len(ranges) == 0 and not abbreviated and not exact_ranges:
        years = list(dict.fromkeys(re.findall(r'\b(?:19|20)\d{2}\b', text)))
        if len(years) == 1:values['graduation_year'] = years[0]
    school_levels=list(re.finditer(r'\bClass\s+(?:10th|12th|XII|X)(?!\w)',text,re.I))
    if len(school_levels)==1:
        values['degree']=school_levels[0].group()
        score=re.search(r'\b(\d+(?:\.\d+)?\s*(?:%|CGPA))\b|\b(\d+(?:\.\d+)?)\s*%',text,re.I)
        if score:values['grade_or_gpa']=score.group(1) or score.group(2)+'%'
    grades = list(re.finditer(r'\b(?:CGPA|GGPA|GPA|Grade)\s*[:=]?\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)', text, re.I))
    if len(grades) == 1 and not values.get('grade_or_gpa'):
        values['grade_or_gpa'] = grades[0].group(1)
    if not grades and not values.get('grade_or_gpa'):
        scales = [m.group(1) for m in re.finditer(r'(?<![\w.])(\b\d+(?:\.\d+)?\s*/\s*(?:4|5|10|100)(?:\.0+)?)\b', text)]
        if len(scales) == 1:
            values['grade_or_gpa'] = scales[0]
    if not grades and not values.get('grade_or_gpa'):
        percentages=[m.group() for m in re.finditer(r'(?<![\w.])(?:100|[0-9]{1,2})(?:\.[0-9]+)?\s*%',text)]
        if len(percentages)==1:values['grade_or_gpa']=percentages[0]
    return values, reasons
