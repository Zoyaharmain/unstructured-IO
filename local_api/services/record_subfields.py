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
        'preferred location': 'work_preferences', 'preferred locations': 'work_preferences',
        'work preferences': 'work_preferences', 'relocation preferences': 'work_preferences',
        'target role': 'target_role', 'target position': 'target_role',
    },
    'experience': {
        'employer': 'company', 'organization': 'company', 'company name': 'company',
        'job title': 'role', 'designation': 'role', 'position': 'role',
        'start date': 'start_date', 'end date': 'end_date', 'period': 'duration',
        'work base location': 'location', 'job location': 'location',
        'technology & tools': 'technologies', 'tools & technology': 'technologies',
        'agile/devops': 'technologies', 'cloud & data platforms': 'technologies',
        'etl & data integration': 'technologies', 'database & bi tools': 'technologies',
        'product development stack': 'technologies', 'cloud & backend': 'technologies',
        'ux/ui design': 'technologies', 'mobile development': 'technologies',
        'frontend & mobile': 'technologies', 'automation & qa': 'technologies',
        'tools': 'technologies', 'technology': 'technologies', 'tech stack': 'technologies',
        'environment': 'technologies', 'key responsibilities': 'responsibilities',
        'roles and responsibilities': 'responsibilities', 'achievements': 'responsibilities',
        'employment type': 'engagement_type', 'engagement type': 'engagement_type',
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
        'start date': 'start_date', 'end date': 'end_date', 'organization': 'organization',
        'outcomes': 'outcomes',
    },
    'certifications': {
        'certification': 'name', 'certificate': 'name', 'certification name': 'name',
        'issuing organization': 'issuer', 'issued by': 'issuer', 'provider': 'issuer',
        'year': 'issue_year', 'issue date': 'issue_year', 'issued': 'issue_year',
        'expiry date': 'expiry_date', 'expiration date': 'expiry_date', 'valid until': 'expiry_date',
        'credential id': 'credential_id', 'certificate id': 'credential_id',
        'verification url': 'verification_url', 'credential url': 'verification_url',
    },
    'awards': {'award': 'name', 'award name': 'name', 'awarded by': 'issuer'},
    'publications': {'publication': 'title', 'publication title': 'title', 'published by': 'publisher'},
    'volunteering': {'organisation': 'organization', 'position': 'role', 'duration': 'dates'},
    'references': {'full name': 'name', 'organisation': 'organization', 'mobile': 'phone'},
    'languages': {'level': 'proficiency', 'fluency': 'proficiency'},
}

MONTH = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
DATE = (r"(?:(?:0?[1-9]|[12]\d|3[01])\s*[-/]\s*(?:0?[1-9]|1[0-2]|" + MONTH + r")\s*[-/]\s*(?:19|20)\d{2}|"
        r"\d{1,2}\s+" + MONTH + r"[,.\s]+(?:19|20)\d{2}|"
        + MONTH + r"[.,\s\-‘’']*(?:19|20)?\d{2}|"
        r"(?:19|20)\d{2}(?:[-/]\d{1,2}){0,2}|\d{1,2}[/-](?:\d{1,2}[/-])?(?:19|20)\d{2})")
GLUED_MONTH = r'(?-i:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
RANGE = re.compile(r'(?:(?<![\w/])|(?<=(?-i:[a-z]))(?=' + GLUED_MONTH + r'\s+(?:19|20)\d{2}))(' + DATE + r')\s*(?:[-\u2013\u2014]|\bto\b|\btill\b|\buntil\b)\s*(?:(?:till|until)\s+){0,2}(' + DATE + r'|Present|Current(?:ly working)?|Till Date|Till Now|Now)(?!\w)', re.I)


ROLE = re.compile(r'\b(?:engineer(?:ing)?|developer|analyst|consultant|architect|manager|specialist|scientist|associate|director|administrator|officer|executive|intern|underwriter|supervisor|leader|lead|head|roles?)\b', re.I)


ACTION = re.compile(r'^(?:[\u2022*\-]\s*)?(?:collaborated|orchestrated|researched|provided|served|utilize|migrated|applied|completed|established|delivered|directed|spearheaded|oversaw|monitored|streamlined|closed|reduced|realized|executed|guided|championed|used|utilized|leveraged|led|built|developed|implemented|configured|prepared|managed|conducted|supported|translated|partnered|owned|drove|validated|participated|facilitated|engaged|expanded|created|designed|acted|worked|engineered|responsible|interact|analy[sz]e|ensure|drive|collaborate|assist|coordinate|conduct|perform|create|own|manage|document|maintain|design|develop|implement|translate|prepare|gather|capture|handle|support|architected|optimi[sz]ed|resolved|proactively\b\s*\w+|took(?=\s+(?:a\s+)?lead\b)|lead(?!\s+(?:business|software|data|engineer|analyst|developer|consultant)\b)|work(?=\s+(?:with|on|closely|across|in)\b))\b', re.I)
CITY = r'(?:Chennai|Bangalore|Bengaluru|Pune|Mumbai|Hyderabad|Noida|Delhi|Gurgaon|Kolkata|London|Paris|Remote|Singapore|New York|San Francisco|Tokyo|Sydney)'
COUNTRY = r'(?:India|France|UK|USA|Singapore|Australia|Germany|Canada|Japan)'
PLACE = re.compile(r'^(?:' + CITY + r'(?:,\s*[^|]+)?|[A-Za-z.\s]{2,30},\s*' + COUNTRY + r')$', re.I)
COMPANY_KEYWORD = re.compile(r'\b(?:ltd|limited|inc|services|solutions|systems|bank|company|pvt|telecom|teleservices|technolog(?:y|ies)|corp|corporation)\b', re.I)


def employment_duration_literal(match):
    """Keep a source-stated elapsed duration immediately following a date range."""
    suffix = re.match(r'\s*\(\s*(?:(?:\d+)\s*(?:years?|yrs?)\s*(?:and\s*)?)?(?:(?:\d+)\s*(?:months?|mos?)\s*)?\)',
                      match.string[match.end():], re.I)
    if suffix and re.search(r'\d', suffix.group()):
        return match.string[match.start():match.end() + suffix.end()]
    return match.group()


def is_place(text):
    text = text.strip()
    return bool((PLACE.fullmatch(text) or re.fullmatch(COUNTRY, text, re.I)) and not COMPANY_KEYWORD.search(text))


CAPABILITY = re.compile(r'^\s*(?:[•▪●*\-]\s*)?(?:proven\s+track\s+record|familiar\s+with|proficient\s+in|knowledge\s+(?:of|on)|experienced?\s+(?:with|in)|hands[- ]on\s+(?:experience|with))\b', re.I)


def narrative_identity(text):
    """Sentence grammar, not company-name vocabulary, excludes prose identities."""
    text=text.strip()
    return len(text.split())>=4 and bool(re.match(
        r'^(?:[•▪●*\-]\s*)?(?:I\s+(?:have|am|speciali[sz]e|thrive|work|excel|focus)\b|My\s+(?:proficiency|expertise|experience|background)\b|With\s+(?:a\s+)?(?:robust|strong|extensive|solid|broad)\s+background\b|[a-z][^,]{0,80},\s*I\s+(?:speciali[sz]e|have|thrive|am)\b)',text,re.I))


def responsibility_fragment(text):
    """A wrapped prose clause is not an employer just because it says systems."""
    text = text.strip()
    identity = re.split(r'\s+[—–]\s+|\s*\|\s*',text, maxsplit=1)[0]
    if len(identity.split()) <= 6 and not re.search(r'\b(?:to|for|with|at|across|prior|during|from|as)\b',identity,re.I) and re.search(r'\b(?:ltd\.?|limited|inc\.?|llc|corp\.?|corporation)\s*$',identity,re.I):
        return False
    if re.match(r'^By\s+[A-Za-z-]+ing\b',text,re.I):return True
    narrative = re.match(r'^(?:[•▪●*\-]\s*)?(?:I\s+(?:have|am|speciali[sz]e|thrive|work|excel|focus)\b|My\s+(?:proficiency|expertise|experience|background)\b|With\s+(?:a\s+)?(?:robust|strong|extensive|solid|broad)\s+background\b)',text,re.I)
    return bool(narrative or CAPABILITY.search(text) or ACTION.search(text) or len(text.split()) > 6 and (
        re.search(r'\b(?:setting up|cut average|ensuring|enhancing|working across)\b', text, re.I)
        or text[:1].islower() and text.endswith('.')))


def employment_header_fields(text):
    """Identify role/employer by unambiguous component shapes, not field order."""
    text = re.sub(r'^\s*[•▪●*\uf0b7-]\s+', '', text.strip())
    if re.search(r'\brole[- ]based\b', text, re.I):return {}
    if re.match(r'^(?:Client\b|(?:Technology\s*&\s*Tools|Tools\s*&\s*Technology|Tech(?:nology)? Stack)\s*:)',text,re.I):return {}
    lookup=re.sub(r'^[^\w]+','',text).strip()
    # Explicit relation labels establish identities even when role spelling is
    # unfamiliar. Do not derive employers from generic capability prose.
    statement=re.match(r'^(?:Having\s+)?(?:currently\s+working|experience)\s+in\s+(.+?)\s+post\s*of\s+(.+?)(?=\s+(?:start|from|payroll)\b|$)',lookup,re.I|re.S)
    if statement and 1<=len(statement[1].split())<=14 and 1<=len(statement[2].split())<=12:
        company=statement[1].strip();role=statement[2].strip()
        payroll=re.search(r'\bpayroll\s+(?:was|is|with)\s+(.+?)(?=\.?\s+(?:start|from)\b|$)',lookup,re.I|re.S)
        if payroll:company=payroll[1].strip().rstrip('.')
        return {'company':company,'role':role}
    internship=re.match(r'^(?:Having\s+)?(?:experience\s+in\s+)?(?:\d+(?:\.\d+)?\s+months?\s+)?(internship)\s+in\s+(.+?)[.]?$',lookup,re.I)
    if internship and len(internship[2].split())<=12:
        return {'company':internship[2].rstrip('.'),'role':internship[1]}

    if len(text.split()) > 32:return {}
    # A short employer followed by an explicit department/operation qualifier
    # is identity context, not a second employer or a duty paragraph.
    department=re.fullmatch(r'(.+?)\s+[-–—]\s+(.+)',text)
    if (department and 1<=len(department[1].split())<=8
        and not responsibility_fragment(text) and not ROLE.search(department[1]) and not ROLE.search(department[2])
        and re.search(r'\b(?:office|department|division|operations|business unit)\b',department[2],re.I)
        and len(department[2].split())<=14 and not RANGE.search(text)):
        return {'company':department[1].strip()}
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
    client_header = re.match(r'^(?:Company\s*[:=-]\s*)?(.+?)\s*,?\s+Client\s*(?:[:=]|-\s*(?!server\b|side\b|facing\b))\s*\S',text,re.I)
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
    # A pipe separates role from an organization compound. Preserve the whole
    # organization side when an unlabelled dash may introduce a client.
    pipe_parts=[part.strip() for part in text.split('|')]
    if len(pipe_parts)==2 and not RANGE.search(text):
        if is_place(pipe_parts[1]) and not is_place(pipe_parts[0]) and not ROLE.search(pipe_parts[0]) and not responsibility_fragment(pipe_parts[0]):
            return {'company': pipe_parts[0], 'location': pipe_parts[1]}
        if is_place(pipe_parts[0]) and not is_place(pipe_parts[1]) and not ROLE.search(pipe_parts[1]) and not responsibility_fragment(pipe_parts[1]):
            return {'company': pipe_parts[1], 'location': pipe_parts[0]}
        if ROLE.search(pipe_parts[1]) and not ROLE.search(pipe_parts[0]) and not responsibility_fragment(pipe_parts[1]):
            comp = pipe_parts[0]; loc = None
            if any(sep in comp for sep in ('–','-','—',',')):
                cparts = [p.strip() for p in re.split(r'[-–—,]', comp) if p.strip()]
                if len(cparts) == 2 and is_place(cparts[1]):
                    comp = cparts[0]; loc = cparts[1]
            res = {'company': comp, 'role': pipe_parts[1]}
            if loc: res['location'] = loc
            return res
        role_parts=[i for i,part in enumerate(pipe_parts) if ROLE.search(part) and len(part.split())<=12 and not responsibility_fragment(part)]
        if len(role_parts)==1:
            role_index=role_parts[0]; organization=pipe_parts[1-role_index]
            if re.search(r'\s+[—–]\s+',organization) and not ROLE.search(organization) and not re.search(r'@|https?://',organization):
                return {'role':pipe_parts[role_index], 'company':organization}
    dates = list(RANGE.finditer(text))
    if len(dates) > 1:return {}
    prefix = text[:dates[0].start()].rstrip(' |\u2013\u2014-()') if dates else text
    parts=[];depth=0;last=0
    for delimiter in re.finditer(r'[()]|\s*\|\s*|\s+[–—-]\s+|\s*[•▪●]\s*',prefix):
        if delimiter[0]=='(':depth+=1
        elif delimiter[0]==')':depth=max(0,depth-1)
        elif not depth:
            if prefix[last:delimiter.start()].strip():parts.append(prefix[last:delimiter.start()].strip())
            last=delimiter.end()
    if prefix[last:].strip():parts.append(prefix[last:].strip())
    if len(parts) == 1 and ',' in prefix:
        # Common resume header: Employer, Role or Employer, Location.
        employer, title = prefix.rsplit(',', 1)
        title = title.strip(); employer = employer.strip()
        if is_place(title) and not is_place(employer) and not ROLE.search(employer) and not responsibility_fragment(employer) and len(employer.split()) <= 10:
            return {'company': employer, 'location': title}
        if (employer and ROLE.search(title) and len(title.split()) <= 12
                and not responsibility_fragment(title)
                and not re.match(r'^(?:and|&|with|for|in|at|to)\b', title, re.I)
                and not ACTION.search(employer)
                and not responsibility_fragment(employer)):
            parts = [employer, title]
    role_indices = [i for i, part in enumerate(parts) if ROLE.search(part) and len(part.split()) <= 12
                    and not re.search(r'\b(?:ltd|limited|inc|services|systems|bank|company|pvt)\b', part, re.I)]
    if len(role_indices) != 1 or len(parts) < 2:
        if len(parts) == 2 and not role_indices and not RANGE.search(text):
            if is_place(parts[1]) and not is_place(parts[0]) and not responsibility_fragment(parts[0]) and len(parts[0].split()) <= 10:
                return {'company': parts[0], 'location': parts[1]}
            if is_place(parts[0]) and not is_place(parts[1]) and not responsibility_fragment(parts[1]) and len(parts[1].split()) <= 10:
                return {'company': parts[1], 'location': parts[0]}
        return {}
    role_index = role_indices[0]
    # Independent work plus a generic practice area does not name an employer.
    if (role_index == 0 and len(parts) == 2
        and re.match(r'^(?:independent|freelance|self[- ]employed)\s+',parts[0],re.I)
        and re.fullmatch(r'(?:business|digital|organizational|software|data|process|operations|IT)\s+(?:transformation|engineering|development|consulting|analytics|improvement)',parts[1],re.I)):
        return {'role':prefix}
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
        if re.search(r'^(?:projects?|client|responsibilities|work|duties|assignment|role)\b', rest[0], re.I):
            return {'role': text[:dates[0].start()].rstrip(' |\u2013\u2014-()') if dates else text}
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
    if category=='experience' and any(b.assignment=='local_employment_header' for b in blocks):
        from types import SimpleNamespace
        from local_api.services.source_fragments import texts
        found=labelled_fields(category,[SimpleNamespace(text=text,assignment='source_paragraph') for text in texts(blocks)])
        header_labels=labelled_fields(category,[b for b in blocks if b.assignment=='local_employment_header'])
        for name in ('company','role','start_date','end_date','duration','location'):
            if name in header_labels:found[name]=header_labels[name]
            else:found.pop(name,None)
    for name, candidates in found.items():
        if name not in values:
            continue
        unique = list(dict.fromkeys(candidates))
        if category == 'experience' and name == 'responsibilities':
            # A labelled row supplements the record; it must not replace duties
            # before/after it. Commas and semicolons inside a duty are prose.
            from types import SimpleNamespace
            merged = []
            for item in values.get(name) or []:
                labelled = labelled_fields(category, [SimpleNamespace(text=item, assignment='semantic')]).get(name)
                merged.extend(labelled or [item])
            merged.extend(unique)
            values[name] = list(dict.fromkeys(p.strip() for item in merged
                for p in re.split(r'[•▪●\uf0b7]', item) if p.strip()))
        elif category == 'projects' and name == 'description' and values.get(name) and all(v in values[name] for v in unique):
            # Preserve source-contiguous continuation paragraphs. Evidence is
            # still validated by the caller; disjoint synthetic prose is rejected.
            pass
        elif SUBSCHEMAS[category][name]['multiple']:
            values[name] = list(dict.fromkeys(p.strip() for v in unique for p in re.split(r'[,;|\n]', v) if p.strip()))
        elif len({v.casefold() for v in unique}) == 1:
            values[name] = unique[0]
        else:
            values[name] = None
            reasons.append(f'Conflicting explicit labels for {name}.')
    if category == 'projects' and {'start_date','end_date'} & values.keys():
        from local_api.services.source_fragments import texts
        ranges = {m.group():m for text in texts(blocks) if not responsibility_fragment(text) for m in RANGE.finditer(text)}
        if len(ranges) == 1:
            match = next(iter(ranges.values()))
            for name,value in zip(('start_date','end_date'),match.group(1,2)):
                if name in values and name not in found: values[name] = value
        elif len(ranges) > 1:
            reasons.append('Multiple project date ranges in one record; association requires review.')
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
    if category == 'personal_information':
        from local_api.services.target_preferences import target_section_values
        for name, value in target_section_values(blocks).items():
            values[name] = value
        preference = re.compile(r'\b(?:open to|preferred? (?:work )?locations?|willing to relocate|relocation preferences?)\b', re.I)
        preference_rows = [b.text.strip() for b in blocks if preference.search(b.text)]
        if len(set(preference_rows)) == 1 and not values.get('work_preferences'):
            values['work_preferences'] = preference_rows[0]
        location = values.get('location')
        contexts = [b.text for b in blocks if location and location in b.text and b.assignment != 'local_target_preferences']
        if contexts and all(preference.search(text) for text in contexts):
            values['location'] = None
            reasons.append('Preferred work locations do not establish current residence.')
    if category == 'experience':
        from local_api.services.dated_record_headers import dated_header_candidates
        dated_headers=dated_header_candidates(blocks)
        for name in ('company','role'):
            if values.get(name) and responsibility_fragment(values[name]) and name not in found:values[name]=None
        company = values.get('company')
        contexts = [b for b in blocks if company and company.casefold() in b.text.casefold()]
        if 'company' not in found and contexts and all(CAPABILITY.search(b.text) for b in contexts):
            values['company'] = None
            reasons.append('Company mention occurs only in a capability statement; employment is not established.')
        from local_api.services.source_fragments import texts
        headers = [employment_header_fields(text) for text in [*texts(blocks), *(b.text for b in blocks)]]
        opening_identity = employment_header_fields(blocks[0].text) if blocks else {}
        # A complete literal opening header outranks concatenated field hints
        # that may include wrapped responsibility fragments from later rows.
        if {'company', 'role'} <= opening_identity.keys() and '|' in blocks[0].text:
            headers = [opening_identity]
            for name in ('company', 'role'):
                if name not in found:values[name] = opening_identity[name]
        post_statement = bool(blocks and re.search(r'\bpost\s*of\b',blocks[0].text,re.I) and employment_header_fields(blocks[0].text))
        joined_post = '\n'.join(texts(blocks)) if post_statement else None
        if joined_post:
            complete=employment_header_fields(joined_post)
            if complete:headers=[complete]

        independent_roles=[h['role'] for h in headers if 'role' in h and 'company' not in h and re.match(r'^(?:independent|freelance|self[- ]employed)\s+',h['role'],re.I)]
        if len(set(independent_roles)) == 1 and values.get('company') and values['company'] in independent_roles[0] and 'company' not in found:
            values['company'] = None
        for name in ('company', 'role', 'location'):
            candidates = list(dict.fromkeys(h[name] for h in headers if name in h))
            if name == 'company' and header_fields is not None and values.get('company') and not ROLE.search(values['company']) and not employment_header_fields(values['company']) and not any('company' in h and 'role' not in h for h in headers):
                continue
            if (header_fields is None or name in header_fields or name == 'location' or (name == 'location' and {'company','role'} <= header_fields)) and name not in found and len(candidates) == 1 :
                values[name] = candidates[0]
        if values.get('role') and not values.get('location'):
            loc_match = re.match(r'^(.*?,\s*[A-Za-z]+|\b(?:Bangalore|Bengaluru|Chennai|Hyderabad|Mumbai|Pune|Delhi|Noida|Gurgaon|London|Singapore|Dubai)\b)\s+([A-Za-z].*)$', values['role'], re.I)
            if loc_match and is_place(loc_match.group(1)) and not ROLE.search(loc_match.group(1)):
                values['location'] = loc_match.group(1).strip(' ,')
                values['role'] = loc_match.group(2).strip()
        if len(dated_headers)==1:
            for name,value in dated_headers[0].items():
                if name in values and name not in found:values[name]=value
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
        date_blocks = [b for b in blocks if len(b.text.split()) <= 24 and (not responsibility_fragment(b.text) or employment_header_fields(b.text))]
        ranges = [m for text in texts(date_blocks) for m in RANGE.finditer(text)]
        if joined_post:
            ranges=list(RANGE.finditer(joined_post))
        unique = {m.group(0).casefold(): m for m in ranges}
        if len(unique) == 1:
            match = next(iter(unique.values()))
            for name, value in zip(('start_date', 'end_date', 'duration'), (*match.group(1, 2), employment_duration_literal(match))):
                if name not in found:
                    values[name] = value
        elif len(unique) > 1:
            reasons.append('Multiple employment date ranges in one record; dates require review.')
            for name in ('start_date', 'end_date', 'duration'):
                if name not in found:
                    values[name] = None
        elif not ranges and 'duration' not in found and not values.get('duration'):
            for b in date_blocks:
                dur_match = re.search(r'\b(?:(\d+)\s*(?:years?|yrs?)\s*(?:and\s*)?)?(?:(\d+)\s*(?:months?|mos?))\b|\b(\d+(?:\.\d+)?\s*(?:years?|yrs?))\b', b.text, re.I)
                if dur_match and not re.search(r'\b(?:experience|exp|batch)\b', dur_match.group(0), re.I):
                    values['duration'] = dur_match.group(0).strip()
                    break
        start, end = values.get('start_date'), values.get('end_date')
        years = [re.search(r'\b(?:19|20)\d{2}\b', v or '') for v in (start, end)]
        if all(years) and int(years[0].group()) > int(years[1].group()):
            reasons.append('Employment end date precedes start date; inspect the source.')
        if values.get('role') and (values.get('company') or 'role' in found or any(h.get('role') == values['role'] for h in headers)):
            # Supplied entries can have no field hints. Recover source-local
            # duties from their established identity instead of requiring the
            # detector to have populated responsibilities in advance.
            duties = list(values.get('responsibilities') or [])
            for block in blocks:
                text = block.text.strip()
                labels = labelled_fields(category, [block])
                if block.assignment in {'section_heading', 'structural_heading'} or (labels and 'responsibilities' not in labels): continue
                if text in {values.get('company'), values['role']} or employment_header_fields(text): continue
                action = responsibility_fragment(text) or (len(text.split()) >= 6 and re.match(
                    r'^(?:[•▪●*\-]\s*)?(?:integrate|automate|optimi[sz]e|maintain|improve|deliver|troubleshoot)\b', text, re.I))
                if action:
                    duties.extend(labels.get('responsibilities', [block.text.strip()]))
            for paragraph in texts(blocks):
                if responsibility_fragment(paragraph):
                    duties = [d for d in duties if d.strip() not in paragraph]
                    duties.append(paragraph.strip())
            source = '\n'.join(b.text for b in blocks)
            values['responsibilities'] = sorted(dict.fromkeys(duties),
                key=lambda value: source.find(value) if value in source else len(source))
    if category=='experience' and any(b.assignment=='local_employment_header' for b in blocks):
        from local_api.services.employment_details import duties_from_source
        source_duties=duties_from_source(blocks)
        if source_duties:values['responsibilities']=source_duties
        values['responsibilities']=[v for v in values.get('responsibilities',[])
            if not re.match(r'^\s*(?:Technology\s*&\s*Tools|Tools\s*&\s*Technology|Tech Stack)\s*:',v,re.I)
            and not re.fullmatch(r'\s*(?:Key\s+)?(?:Responsibilities(?:\s*(?:&|and)\s*Achievements)?|Achievements)\s*:?\s*[•▪● ]*',v,re.I)]
    if category == 'certifications':
        from local_api.services.certification_integrity import credential_values
        credential_fields, credential_reasons = credential_values(blocks)
        values.update({name:value for name,value in credential_fields.items() if name in values})
        reasons.extend(credential_reasons)
    if category in {'projects', 'certifications'} and found and 'name' not in found:
        name = values.get('name')
        if name and any(name == b.text.strip() and labelled_fields(category, [b]) for b in blocks):
            values['name'] = None
    if category=='projects' and re.fullmatch(r'(?:project|poc)\s*[:#-]?\s*\d+',str(values.get('name') or ''),re.I):
        values['name']=None
        reasons.append('A project number is an identifier; a descriptive project name is not established.')
    return values, reasons


def paired_employment_header(company, following):
    """A short identity row followed by a dated, explicitly labelled job role, or company|location + role."""
    if not company.strip() or len(company.split())>10 or responsibility_fragment(company):return False
    if re.search(r'\d|[@:;]|\b(?:project|client|duration|description)\b',company,re.I):return False
    if bool(re.fullmatch(r'\s*'+MONTH+r'\s+\d{2,4}\s*(?:to|[-–—])\s*(?:'+MONTH+r'\s+\d{2,4}|Current|Present|Now)\s+Role\s*:\s*\S.+', following, re.I)):
        return True
    if ROLE.search(following) and len(following.split()) <= 12 and not responsibility_fragment(following):
        fields = employment_header_fields(company)
        if fields.get('company') and fields.get('location'):
            return True
    return False
