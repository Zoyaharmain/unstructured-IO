"""Record-local refinement from explicit labels and unambiguous date ranges.

Values remain literal source substrings. Conflicting scalar labels are cleared;
labels never move evidence between sections or records.
"""
import re
from local_api.schemas.subschema_spec import SUBSCHEMAS

ALIASES = {
    'personal_information': {
        'name': 'full_name', 'full name': 'full_name', 'candidate name': 'full_name',
        'email-id': 'email', 'email id': 'email', 'e-mail id': 'email', 'email address': 'email', 'e-mail': 'email', 'mobile': 'phone', 'telephone': 'phone',
        'contact no': 'phone', 'mobile no': 'phone', 'phone number': 'phone', 'contact number': 'phone', 'address': 'location', 'based in': 'location',
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
        'project': 'name', 'project name': 'name', 'project title': 'name', 'title':'name', 'details':'description',
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
DATE = r"(?:" + MONTH + r"[.\-‘’']?\s*(?:19|20)?\d{2}|(?:19|20)\d{2}(?:[-/]\d{1,2})?|\d{1,2}/(?:19|20)\d{2})"
RANGE = re.compile(r'(?<![\w/])(' + DATE + r')\s*(?:[-\u2013\u2014]|\bto\b|\btill\b|\buntil\b)\s*(' + DATE + r'|Present|Current(?:ly working)?|Till Date|Till Now|Now)(?!\w)', re.I)


ROLE = re.compile(r'\b(?:engineer(?:ing)?|developer|analyst|consultant|architect|manager|specialist|scientist|associate|director|administrator|officer|executive|intern|underwriter|supervisor|leader|lead|head|roles?)\b', re.I)


ACTION = re.compile(r'^(?:[\u2022*\-]\s*)?(?:established|delivered|directed|spearheaded|oversaw|monitored|streamlined|closed|reduced|realized|executed|guided|championed|used|utilized|leveraged|led|built|developed|implemented|configured|prepared|managed|conducted|supported|translated|partnered|owned|drove|validated|participated|facilitated|engaged|expanded|created|designed|acted|worked|engineered|responsible|interact|analy[sz]e|ensure|drive|collaborate|assist|coordinate|conduct|perform|create|own|manage|document|maintain|design|develop|implement|translate|prepare|gather|capture|handle|support|took(?=\s+(?:a\s+)?lead\b)|lead(?!\s+(?:business|software|data|engineer|analyst|developer|consultant)\b)|work(?=\s+(?:with|on|closely|across|in)\b))\b', re.I)
CITY = r'(?:Chennai|Bangalore|Bengaluru|Pune|Mumbai|Hyderabad|Noida|Delhi|Gurgaon|Kolkata|London|Paris|Remote|Singapore|New York|San Francisco|Tokyo|Sydney)'
COUNTRY = r'(?:India|France|UK|USA|Singapore|Australia|Germany|Canada|Japan)'
PLACE = re.compile(r'^(?:' + CITY + r'(?:,\s*[^|]+)?|[A-Za-z.\s]{2,30},\s*' + COUNTRY + r')$', re.I)
COMPANY_KEYWORD = re.compile(r'\b(?:ltd|limited|inc|services|solutions|systems|bank|company|pvt|telecom|teleservices|technolog(?:y|ies)|corp|corporation)\b', re.I)


def is_place(text):
    text = text.strip()
    return bool((PLACE.fullmatch(text) or re.fullmatch(COUNTRY, text, re.I)) and not COMPANY_KEYWORD.search(text))


CAPABILITY = re.compile(r'^\s*(?:[•▪●*\-]\s*)?(?:familiar\s+with|proficient\s+in|knowledge\s+(?:of|on)|experienced?\s+(?:with|in)|hands[- ]on\s+(?:experience|with))\b', re.I)


def responsibility_fragment(text):
    """A wrapped prose clause is not an employer just because it says systems."""
    text = text.strip()
    return bool(CAPABILITY.search(text) or ACTION.search(text) or len(text.split()) > 6 and (
        re.search(r'\b(?:setting up|cut average|ensuring|enhancing|working across)\b', text, re.I)
        or text[:1].islower() and text.endswith('.')))


def employment_header_fields(text):
    """Identify role/employer by unambiguous component shapes, not field order."""
    text = re.sub(r'^\s*[•▪●*\uf0b7-]\s+', '', text.strip())
    if re.match(r'^Client\b',text,re.I):return {}
    if len(text.split()) > 32:return {}
    stated = re.fullmatch(r'(?:I\s+)?(?:am\s+)?(?:currently\s+)?work(?:ed|ing)\s+as\s+(?:a|an)\s+(.+?)\s+(?:at|with|for)\s+(.+?)(?:\s+(?:from|since))?[ .\uf020]*', text, re.I)
    if stated and ROLE.search(stated[1]):
        employer = re.split(r'\s+(?=' + DATE + r')', stated[2], maxsplit=1, flags=re.I)[0].rstrip(' .–—-')
        employer = re.sub(r'\s+(?:from|since)$', '', employer, flags=re.I)
        return {'role': stated[1], 'company': employer} if employer else {}
    employer_statement=re.fullmatch(r'(?:I\s+)?Worked\s+(?:at|for|with)\s+(.+?)\s+(?:from|since)\s+(.+?)[.\s]*',text,re.I)
    if employer_statement and RANGE.fullmatch(employer_statement[2]):
        return {'company':employer_statement[1]}
    dated = RANGE.match(text)
    if dated:
        remainder = text[dated.end():].lstrip(' :|–—-')
        depth = 0
        splits = []
        for match in re.finditer(r'\(|\)|\s+as\s+', remainder, re.I):
            if match.group() == '(':depth += 1
            elif match.group() == ')':depth = max(0, depth-1)
            elif depth == 0:splits.append(match)
        if len(splits) == 1:
            split = splits[0]
            company, role = remainder[:split.start()].rstrip(' ,'), remainder[split.end():].rstrip('.')
            if company and ROLE.search(role) and not responsibility_fragment(role):
                return {'company': company, 'role': role}
    if responsibility_fragment(text):return {}
    client_header = re.match(r'^(?:Company\s*[:=-]\s*)?(.+?)\s*,?\s+Client\s*[:=-]\s*\S',text,re.I)
    if client_header and len(client_header[1].split())<=10:
        prefix=client_header[1].strip(' ,')
        return employment_header_fields(prefix) or {'company':prefix}
    if ':' in text:
        identity,period=text.split(':',1)
        known_labels=set(ALIASES['experience'])|set(SUBSCHEMAS['experience'])
        if (RANGE.fullmatch(period.strip()) and 1<=len(identity.split())<=10
                and identity.strip().casefold() not in known_labels
                and not ROLE.search(identity) and not responsibility_fragment(identity)):
            return {'company':identity.strip()}
    dates = list(RANGE.finditer(text))
    if len(dates) > 1:return {}
    prefix = text[:dates[0].start()].rstrip(' |\u2013\u2014-()') if dates else text
    parts = [part.strip() for part in re.split(r'\s*\|\s*|\s+[\u2013\u2014]\s+|\s+-\s+', prefix) if part.strip()]
    if len(parts) == 1 and ',' in prefix:
        # Common resume header: Employer, Role. Keep employer punctuation exact
        # and split only when the suffix is a short explicit role phrase.
        employer, title = prefix.rsplit(',', 1)
        title = title.strip()
        if (employer.strip() and ROLE.search(title) and len(title.split()) <= 12
                and not responsibility_fragment(title)
                and not re.match(r'^(?:and|&|with|for|in|at|to)\b', title, re.I)
                and not ACTION.search(employer)
                and not responsibility_fragment(employer)):
            parts = [employer.strip(), title]
    role_indices = [i for i, part in enumerate(parts) if ROLE.search(part) and len(part.split()) <= 12
                    and not re.search(r'\b(?:ltd|limited|inc|services|systems|bank|company|pvt)\b', part, re.I)]
    if len(role_indices) != 1 or len(parts) < 2:return {}
    role_index = role_indices[0]
    result = {'role': parts[role_index]}
    rest = [part for i, part in enumerate(parts) if i != role_index]
    locations = [part for part in rest if is_place(part)]
    if len(locations) == 1:result['location'] = locations[0];rest.remove(locations[0])
    for i, part in enumerate(rest):
        if ',' in part:
            prefix, loc = part.rsplit(',', 1)
            if is_place(loc) or is_place(part.split(',', 1)[1]):
                if is_place(part.split(',', 1)[1]):
                    prefix, loc = part.split(',', 1)
                result['location'] = loc.strip()
                rest[i] = prefix.strip()
                break
    if len(rest) == 1 and not re.search(r'@|https?://|\b(?:19|20)\d{2}\b', rest[0]):
        result['company'] = rest[0].rstrip(' ,')
    elif len(rest) == 2:
        company_candidates = [part for part in rest if not (re.search(r'\b(?:services|practice|division|department|group|team)\b', part, re.I) and re.search(r'\b(?:cybersecurity|information|operations|engineering|technology)\b', part, re.I) and not re.search(r'\b(?:chartered|bank|global|solutions|technologies|pvt|ltd|limited|inc|corp)\b', part, re.I))]
        if len(company_candidates) == 1 and not re.search(r'@|https?://|\b(?:19|20)\d{2}\b', company_candidates[0]):
            result['company'] = company_candidates[0].rstrip(' ,')
    # Multiple employer-like components remain ambiguous rather than picked by position.
    return result if 'company' in result else {}


def labelled_fields(category, blocks):
    registry = SUBSCHEMAS[category]
    labels = {key.replace('_', ' '): key for key in registry}
    labels.update(ALIASES.get(category, {}))
    pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(k) for k in sorted(labels, key=len, reverse=True)) + r')(?:\s*[:=]\s*|\s+-\s*|\s*-\s+)', re.I)
    found = {}
    for block in blocks:
        if block.assignment in {'section_heading', 'structural_heading'}:
            continue
        matches = list(pattern.finditer(block.text))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(block.text)
            value = block.text[match.end():end].strip().strip('|; \u2022\n\r\t')
            field = labels[match.group(1).lower()]
            if category=='experience' and field=='company':
                value=re.split(r',?\s+Client\s*[:=-]\s*',value,maxsplit=1,flags=re.I)[0].strip(' ,')
            if category in {'personal_information', 'references'} and field == 'email':
                token = re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', value)
                value = token.group().rstrip('.') if token else ''
            if category=='projects' and field=='name' and match.group(1).casefold()=='project' and value.isdigit():
                continue
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
        company = values.get('company')
        contexts = [b for b in blocks if company and company.casefold() in b.text.casefold()]
        if 'company' not in found and contexts and all(CAPABILITY.search(b.text) for b in contexts):
            values['company'] = None
            reasons.append('Company mention occurs only in a capability statement; employment is not established.')
        from local_api.services.source_fragments import texts
        headers = [employment_header_fields(text) for text in [*texts(blocks), *(b.text for b in blocks)]]
        for name in ('company', 'role', 'location'):
            candidates = list(dict.fromkeys(h[name] for h in headers if name in h))
            if name == 'company' and header_fields is not None and values.get('company') and not ROLE.search(values['company']) and not employment_header_fields(values['company']) and not any('company' in h and 'role' not in h for h in headers):
                continue
            if (header_fields is None or name in header_fields or (name == 'location' and {'company','role'} <= header_fields)) and name not in found and len(candidates) == 1 :
                values[name] = candidates[0]
        # Within an established experience record, a complete identity/date
        # header outranks incidental organization words in wrapped duties.
        dated_companies=[]
        for block in blocks:
            match=re.fullmatch(r'(.+?)\s*\(\s*(.+?)\s*\)\s*',block.text.strip())
            if (match and RANGE.fullmatch(match[2]) and 1<=len(match[1].split())<=10
                    and not ROLE.search(match[1]) and not responsibility_fragment(match[1])):
                dated_companies.append(match[1].strip())
        dated_companies=list(dict.fromkeys(dated_companies))
        if (len(dated_companies)==1 and not values.get('company') and 'company' not in found
                and (header_fields is None or 'company' in header_fields)):
            values['company']=dated_companies[0]
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
    if category=='projects' and re.fullmatch(r'(?:project|poc)\s*[:#-]?\s*\d+',str(values.get('name') or ''),re.I):
        values['name']=None
        reasons.append('A project number is an identifier; a descriptive project name is not established.')
    return values, reasons


def paired_employment_header(company, following):
    """A short identity row followed by a dated, explicitly labelled job role."""
    if not company.strip() or len(company.split())>10 or responsibility_fragment(company):return False
    if re.search(r'\d|[@:;]|\b(?:project|client|duration|description)\b',company,re.I):return False
    return bool(re.fullmatch(r'\s*'+MONTH+r'\s+\d{2,4}\s*(?:to|[-–—])\s*(?:'+MONTH+r'\s+\d{2,4}|Current|Present|Now)\s+Role\s*:\s*\S.+', following, re.I))
