"""Record-local refinement from explicit labels and unambiguous date ranges.

Values remain literal source substrings. Conflicting scalar labels are cleared;
labels never move evidence between sections or records.
"""
import re
from local_api.schemas.subschema_spec import SUBSCHEMAS

ALIASES = {
    'personal_information': {
        'name': 'full_name', 'full name': 'full_name', 'candidate name': 'full_name',
        'email address': 'email', 'e-mail': 'email', 'mobile': 'phone', 'telephone': 'phone',
        'phone number': 'phone', 'contact number': 'phone', 'address': 'location', 'based in': 'location',
        'linkedin': 'linkedin_url', 'github': 'github_url', 'portfolio': 'portfolio_url',
        'website': 'portfolio_url', 'job title': 'professional_title', 'headline': 'professional_title',
    },
    'experience': {
        'employer': 'company', 'organization': 'company', 'company name': 'company',
        'job title': 'role', 'designation': 'role', 'position': 'role',
        'start date': 'start_date', 'end date': 'end_date', 'period': 'duration',
        'work base location': 'location', 'job location': 'location',
        'tools': 'technologies', 'technology': 'technologies', 'tech stack': 'technologies',
        'environment': 'technologies', 'key responsibilities': 'responsibilities',
        'roles and responsibilities': 'responsibilities', 'achievements': 'responsibilities',
    },
    'education': {
        'university': 'institution', 'college': 'institution', 'qualification': 'degree',
        'major': 'field_of_study', 'specialization': 'field_of_study',
        'gpa': 'grade_or_gpa', 'cgpa': 'grade_or_gpa', 'grade': 'grade_or_gpa',
        'year of passing': 'graduation_year', 'graduation year': 'graduation_year',
        'start year': 'start_year',
    },
    'projects': {
        'project': 'name', 'project name': 'name', 'project title': 'name',
        'project description': 'description', 'tech stack': 'technologies',
        'technology': 'technologies', 'tools': 'technologies', 'environment': 'technologies',
        'project url': 'url', 'repository': 'url', 'github': 'url',
    },
    'certifications': {
        'certification': 'name', 'certificate': 'name', 'certification name': 'name',
        'issuing organization': 'issuer', 'issued by': 'issuer', 'provider': 'issuer',
        'year': 'issue_year', 'issue date': 'issue_year', 'issued': 'issue_year',
    },
    'awards': {'award': 'name', 'award name': 'name', 'awarded by': 'issuer'},
    'publications': {'publication': 'title', 'publication title': 'title', 'published by': 'publisher'},
    'volunteering': {'organisation': 'organization', 'position': 'role', 'duration': 'dates'},
    'references': {'full name': 'name', 'organisation': 'organization', 'mobile': 'phone'},
    'languages': {'level': 'proficiency', 'fluency': 'proficiency'},
}

MONTH = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
DATE = r'(?:' + MONTH + r'\.?\s+(?:19|20)\d{2}|(?:19|20)\d{2}(?:[-/]\d{1,2})?|\d{1,2}/(?:19|20)\d{2})'
RANGE = re.compile(r'(?<![\w/])(' + DATE + r')\s*(?:[-\u2013\u2014]|\bto\b|\btill\b|\buntil\b)\s*(' + DATE + r'|Present|Current(?:ly working)?|Till Date|Now)(?!\w)', re.I)


ROLE = re.compile(r'\b(?:engineer|developer|analyst|consultant|architect|manager|specialist|scientist|associate|director|administrator|officer|executive|intern|underwriter|supervisor)\b', re.I)


ACTION = re.compile(r'^(?:[\u2022*\-]\s*)?(?:led|built|developed|implemented|configured|prepared|managed|conducted|supported|translated|partnered|owned|drove|validated|participated|facilitated|engaged|expanded|created|designed|acted|worked|engineered|responsible|interact|analy[sz]e|ensure|drive|collaborate|assist|coordinate|conduct|perform|create|own|manage|document|maintain|design|develop|implement|translate|prepare|gather|capture|handle|support|took(?=\s+(?:a\s+)?lead\b)|lead(?!\s+(?:business|software|data|engineer|analyst|developer|consultant)\b)|work(?=\s+(?:with|on|closely|across|in)\b))\b', re.I)
PLACE = re.compile(r'^(?:(?:Chennai|Bangalore|Bengaluru|Pune|Mumbai|Hyderabad|Noida|Delhi|London|Paris|Remote)(?:,\s*[^|]+)?|[^|,]+,\s*(?:India|France|UK|USA))$', re.I)


def employment_header_fields(text):
    """Identify role/employer by unambiguous component shapes, not field order."""
    text = text.strip()
    if len(text.split()) > 32 or ACTION.search(text):return {}
    dates = list(RANGE.finditer(text))
    if len(dates) > 1:return {}
    prefix = text[:dates[0].start()].rstrip(' |\u2013\u2014-()') if dates else text
    parts = [part.strip() for part in re.split(r'\s*\|\s*|\s+[\u2013\u2014]\s+|\s+-\s+', prefix) if part.strip()]
    role_indices = [i for i, part in enumerate(parts) if ROLE.search(part) and len(part.split()) <= 12
                    and not re.search(r'\b(?:ltd|limited|inc|services|systems|bank|company|pvt)\b', part, re.I)]
    if len(role_indices) != 1 or len(parts) < 2:return {}
    role_index = role_indices[0]
    result = {'role': parts[role_index]}
    rest = [part for i, part in enumerate(parts) if i != role_index]
    locations = [part for part in rest if PLACE.fullmatch(part)]
    if len(locations) == 1:result['location'] = locations[0];rest.remove(locations[0])
    if len(rest) == 1 and not re.search(r'@|https?://|\b(?:19|20)\d{2}\b', rest[0]):
        result['company'] = rest[0]
    # Multiple employer-like components remain ambiguous rather than picked by position.
    return result if 'company' in result else {}


def labelled_fields(category, blocks):
    registry = SUBSCHEMAS[category]
    labels = {key.replace('_', ' '): key for key in registry}
    labels.update(ALIASES.get(category, {}))
    pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(k) for k in sorted(labels, key=len, reverse=True)) + r')\s*[:=]\s*', re.I)
    found = {}
    for block in blocks:
        if block.assignment in {'section_heading', 'structural_heading'}:
            continue
        matches = list(pattern.finditer(block.text))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(block.text)
            value = block.text[match.end():end].strip().strip('|; \u2022\n\r\t')
            field = labels[match.group(1).lower()]
            if category in {'personal_information', 'references'} and field == 'email':
                token = re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', value)
                value = token.group().rstrip('.') if token else ''
            if value:
                found.setdefault(labels[match.group(1).lower()], []).append(value)
    return found


def refine_record(category, values, blocks, *, header_fields=None):
    values = dict(values)
    reasons = []
    found = labelled_fields(category, blocks)
    for name, candidates in found.items():
        if name not in values:
            continue
        unique = list(dict.fromkeys(candidates))
        if SUBSCHEMAS[category][name]['multiple']:
            values[name] = list(dict.fromkeys(p.strip() for v in unique for p in re.split(r'[,;|\n]', v) if p.strip()))
        elif len({v.casefold() for v in unique}) == 1:
            values[name] = unique[0]
        else:
            values[name] = None
            reasons.append(f'Conflicting explicit labels for {name}.')
    if category == 'projects' and 'url' in values and 'url' not in found:
        # A PDF hyperlink target can occupy its own span after a separate label.
        # Only accept a complete URL row inside this supplied project record.
        url_row = re.compile(r'(?:https?://|www\.|(?=[A-Za-z0-9.-]+\.[A-Za-z]{2,63}/))[A-Za-z0-9][^\s<>@]*', re.I)
        candidates = list(dict.fromkeys(
            b.text.strip().rstrip('.,;') for b in blocks
            if b.assignment not in {'section_heading', 'structural_heading'}
            and url_row.fullmatch(b.text.strip())
        ))
        if len(candidates) == 1:
            values['url'] = candidates[0]
        elif len(candidates) > 1:
            values['url'] = None
            reasons.append('Multiple project URLs in one record; URL requires review.')
    if category == 'experience':
        from local_api.services.source_fragments import texts
        headers = [employment_header_fields(text) for text in [*texts(blocks), *(b.text for b in blocks)]]
        for name in ('company', 'role', 'location'):
            candidates = list(dict.fromkeys(h[name] for h in headers if name in h))
            if (header_fields is None or name in header_fields or (name == 'location' and {'company','role'} <= header_fields)) and name not in found and len(candidates) == 1 :
                values[name] = candidates[0]
        date_blocks = [b for b in blocks if len(b.text.split()) <= 24 and not re.match(
            r'^\s*(?:[\u2022*]\s*)?(?:led|built|developed|implemented|migrated|managed|supported|worked)\b', b.text, re.I)]
        ranges = [m for text in texts(date_blocks) for m in RANGE.finditer(text)]
        unique = {m.group(0).casefold(): m for m in ranges}
        if len(unique) == 1:
            match = next(iter(unique.values()))
            for name, value in zip(('start_date', 'end_date', 'duration'), (*match.group(1, 2), match.group())):
                if name not in found:
                    values[name] = value
        elif len(unique) > 1:
            reasons.append('Multiple employment date ranges in one record; dates require review.')
            for name in ('start_date', 'end_date', 'duration'):
                if name not in found:
                    values[name] = None
        start, end = values.get('start_date'), values.get('end_date')
        years = [re.search(r'\b(?:19|20)\d{2}\b', v or '') for v in (start, end)]
        if all(years) and int(years[0].group()) > int(years[1].group()):
            reasons.append('Employment end date precedes start date; inspect the source.')
    if category in {'projects', 'certifications'} and found and 'name' not in found:
        name = values.get('name')
        if name and any(name == b.text.strip() and labelled_fields(category, [b]) for b in blocks):
            values['name'] = None
    return values, reasons
