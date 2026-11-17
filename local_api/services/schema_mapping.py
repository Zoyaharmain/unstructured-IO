"""Source-bound adapter to the handoff schema; no extraction, regrouping or LLM calls."""
import hashlib
import json
import re
from local_api.vendor.handoff_schema.models import (
    ResumeSchema, ContactInfo, WorkExperience, Education, Project, Certification,
)
from local_api.vendor.handoff_schema.service import (
    extract_contact_info, extract_work_experience, extract_education,
    extract_skills_categorized, build_schema_mapping_report,
)
from local_api.services.source_accounting import account_source, artifact_reason
from local_api.services.review_resolution import document_scope
from local_api.services.record_relationships import dated_organization_header
from local_api.services.source_validation import validate_result
from local_api.schemas.mapping import SchemaMappingResponse
from local_api.services.section_subschemas import build_subschemas
from local_api.services.record_subfields import refine_record
from local_api.services.source_fragments import texts, citations, runs, contiguous_support
from local_api.schemas.subschemas import SourceQuote
from local_api.services.education_subfields import refine_education
from local_api.services.list_fields import skill_candidates, unique, language_rows


def source_id(block):
    return f'e{block.source_element_index}:{block.start}:{block.end}'


def canonical(blocks):
    parts=[];previous=None
    for block in blocks:
        separator='' if previous is None or (previous.source_element_index==block.source_element_index and previous.end==block.start) else '\n'
        parts.append(separator+block.text);previous=block
    return ''.join(parts)


def norm(text):return ' '.join(text.split()).casefold()


def map_schema(request):
    request = request.model_copy(deep=True)
    # Fail closed on stale/altered/overlapping source intervals or foreign fields.
    if sum(len(s.blocks) for s in request.sections.sections)+len(request.sections.needs_review)>10000:
        raise ValueError('Too many section blocks')
    errors=validate_result(request.elements,request.sections)
    if errors:
        from local_api.services.schema_diagnostics import fail
        fail('source_binding_validation', errors[0], ('sections',))
    ownership_locked = request.sections.metadata.get('structure_review', {}).get('status') == 'provisional'
    if ownership_locked:
        from local_api.services.source_ownership import validated_ownership_state
        validated_ownership_state(request.elements, request.sections)
    from local_api.services.local_completion import recover_local_content
    completed = request.sections if ownership_locked else recover_local_content(request.sections, request.elements)
    local_completed = completed is not request.sections
    if completed is not request.sections:
        request = request.model_copy(update={'sections': completed})
    from local_api.services.contact_sections import recover_contact_sections, contact_values as literal_contact_values
    from local_api.services.education_date_recovery import recover_education_dates
    recovered_sections = request.sections if ownership_locked else recover_education_dates(request.sections, request.elements)
    if not ownership_locked: recovered_sections = recover_contact_sections(recovered_sections, request.elements)
    from local_api.services.education_context import recover_education_context
    if not ownership_locked: recovered_sections = recover_education_context(recovered_sections)
    from local_api.services.preamble_recovery import recover_summary_preamble
    if not ownership_locked: recovered_sections = recover_summary_preamble(recovered_sections, request.elements)
    contacts_reassigned = recovered_sections is not request.sections
    if contacts_reassigned:
        request = request.model_copy(update={'sections': recovered_sections})
    from local_api.services.source_ownership import finalize_ownership
    owned_sections = finalize_ownership(request.elements, request.sections)
    ownership_repaired = any(a.entries != b.entries for a,b in zip(owned_sections.sections, request.sections.sections))
    request = request.model_copy(update={'sections': owned_sections})
    accounting=account_source(request.elements,request.sections)
    scope=document_scope(request.elements)
    sections={s.category:s for s in request.sections.sections}
    raw={key:canonical(s.blocks) for key,s in sections.items()}
    evidence={};warnings=[];record_reviews=[];used=set();record_bindings={}
    inventory={source_id(b):b.text for section in request.sections.sections for b in section.blocks}
    inventory.update({source_id(b):b.text for b in request.sections.needs_review})
    def field_quotes(value, bs):
        refs=citations(value,bs)
        if not refs:
            refs=citations(value,bs,flexible_whitespace=True)
        if (any(str(value).casefold() in r['quote'].casefold() for r in refs)
                or contiguous_support(value,[SourceQuote(**r) for r in refs],inventory)
                or (refs and re.sub(r'[\s\W_]+','',''.join(r['quote'] for r in refs)).casefold() == re.sub(r'[\s\W_]+','',str(value)).casefold())):
            return refs
        return []
    def blocks(category):
        return [b for b in sections[category].blocks if b.assignment not in {'section_heading','structural_heading'} and b.text.strip()] if category in sections else []
    def remember(path,value,bs):
        if value is None or value=='' or value==[]:return value
        refs=[source_id(b) for b in bs]
        evidence[path]=refs;used.update(refs);return value
    def supported(value,bs):
        return bool(value and norm(value) in norm(canonical(bs)))
    def literal(value,bs):
        return value if supported(value,bs) else None
    empty=ContactInfo(full_name='',email='',phone='')
    data=ResumeSchema(contact=empty)
    if scope['candidate_resume'] is not False:
        all_section_blocks = [b for s in request.sections.sections for b in s.blocks] + request.sections.needs_review
        header=blocks('personal_information')
        identity_header=[b for b in header if b.assignment != 'local_target_preferences']
        text='\n'.join(b.text for b in identity_header)
        doc_text='\n'.join(e.text for e in request.elements)
        guessed=extract_contact_info(text,doc_text) if identity_header else ContactInfo(full_name='',email='',phone='')
        # Prefer a distinct opening identity fragment over words in a role headline.
        from local_api.services.record_subfields import ROLE
        identity_parts = [b for b in identity_header
                    if b.source_element_index == min((h.source_element_index for h in identity_header), default=-1)
                    and all(c.isalpha() or c in " .'-" for c in b.text.strip())
                    and not ROLE.search(b.text) and b.assignment!='professional_headline']
        # Join only adjacent literal pieces of the SAME extracted element.
        # A surname split by PDF typography must not disappear from the identity.
        identity_runs = []
        for part in identity_parts:
            previous = identity_runs[-1][-1] if identity_runs else None
            adjacent_words = (previous and previous.source_element_index == part.source_element_index
                and previous.end == part.start and (previous.text[-1:].isspace() or part.text[:1].isspace()))
            if adjacent_words: identity_runs[-1].append(part)
            else: identity_runs.append([part])
        identity = [re.split(r'\s*(?:E-?mail(?:\s*Id)?|Ph:|Phone|Mobile|Contact|Location|Address)\b.*', ''.join(b.text for b in run), flags=re.I)[0].strip() for run in identity_runs]
        identity = [value for value in identity if 2 <= len(value.split()) <= 5]
        if len(identity) == 1:
            guessed.full_name = identity[0]
        for field in type(guessed).model_fields:
            value=getattr(guessed,field)
            if value in {'Candidate','Not specified','not_specified@domain.com'}:value=None
            if field == 'full_name' and value:
                supported_name = supported(value, header) or supported(value, all_section_blocks)
                value = value if supported_name else ''
                evidence_blocks = [b for b in header if norm(value) in norm(b.text)] or [b for b in all_section_blocks if norm(value) in norm(b.text)]
                setattr(data.contact, field, remember('contact.' + field, value, evidence_blocks or header))
            else:
                value=literal(value,identity_header)
                if field in {'email','phone'}:value=value or ''
                setattr(data.contact,field,remember('contact.'+field,value,header))
        title_candidates = [(text, run) for run in runs(identity_header) for text in [''.join(b.text for b in run)]
                            if len(text.split())<=12 and not re.search(r'@|Technical Skills|Core AI|linkedin|github',text,re.I)]
        title_candidates += [(b.text,[b]) for b in identity_header]
        title_candidates=[(b.text,[b]) for b in identity_header if b.assignment=='professional_headline']+title_candidates
        for title, refs in title_candidates:
            if any(b.assignment == 'local_target_preferences' for b in refs): continue
            if re.search(r'\b(?:target (?:role|position)|seeking|open to|preferred locations?)\b', title, re.I):
                continue
            if len(title.split())<=12 and '@' not in title and (any(b.assignment=='professional_headline' for b in refs) or re.search(r'\b(?:engineer|engineering lead|developer|analyst|consultant|architect|manager|specialist|scientist)\b',title,re.I)):
                title=title.strip()
                m_name_title = re.match(r'^\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})\s*(?:\(([^)]+)\)|[-–—|:,]\s*([A-Za-z][^+\n/|]+))\s*(?:[+,|/].*)?$', title)
                from local_api.services.record_subfields import ROLE
                if m_name_title:
                    cand_name = m_name_title.group(1).strip()
                    cand_sub_title = (m_name_title.group(2) or m_name_title.group(3)).strip()
                    if (ROLE.search(cand_sub_title)
                            and not re.search(r'\b(?:senior|junior|lead|principal|staff|associate|chief|director|head|manager|analyst|engineer|developer|consultant)\b', cand_name, re.I)
                            and (not data.contact.full_name or '(' in data.contact.full_name or data.contact.full_name.startswith(cand_name))):
                        setattr(data.contact, 'full_name', remember('contact.full_name', cand_name, refs))
                        title = cand_sub_title
                if data.contact.full_name and title.startswith(data.contact.full_name + ' '):title=title[len(data.contact.full_name):].strip()
                data.professional_title=remember('professional_title',title,refs);break
        contact_values, contact_reasons = refine_record('personal_information',
            data.contact.model_dump() | {'professional_title': data.professional_title}, header)
        warnings.extend(contact_reasons)
        for key, value in contact_values.items():
            target = data if key == 'professional_title' else data.contact
            if key == 'full_name' and value:
                supported_name = supported(value, header) or supported(value, all_section_blocks)
                value = value if supported_name else ''
                evidence_blocks = [b for b in header if norm(value) in norm(b.text)] or [b for b in all_section_blocks if norm(value) in norm(b.text)]
                setattr(target, key, value)
                path = 'contact.' + key
                evidence.pop(path, None)
                remember(path, value, evidence_blocks or header)
            else:
                value = literal(value, header)
                if key in {'full_name', 'email', 'phone'}:value = value or ''
                setattr(target, key, value)
                path = key if key == 'professional_title' else 'contact.' + key
                evidence.pop(path, None)
                remember(path, value, [b for b in header if any(r['source_id']==source_id(b) for r in field_quotes(value,header))])
        # Recover unique literal contacts even when vendor parsing misses labels
        # such as Email-ID or international number formatting.
        for key, matches in literal_contact_values(identity_header).items():
            if len(matches) == 1:
                value = next(iter(matches))
                setattr(data.contact, key, remember('contact.'+key, value, header))
        from local_api.services.contact_sections import profile_values
        for key, matches in profile_values(header).items():
            if len(matches) == 1:
                value = next(iter(matches))
                evidence_blocks = [b for b in header if any(ref['source_id']==source_id(b) for ref in field_quotes(value,header))]
                if not evidence_blocks:
                    handle = value.rstrip('/').split('/')[-1]
                    evidence_blocks = [b for b in header if handle.casefold() in b.text.casefold()]
                setattr(data.contact, key, remember('contact.'+key, value, evidence_blocks or header))
            elif len(matches) > 1:
                setattr(data.contact, key, None)
                evidence.pop('contact.'+key, None)
                warnings.append('Multiple candidate profile links require review: '+key)
        summary=blocks('summary')
        data.summary=remember('summary',canonical(summary).strip() or None,summary)
        # Never infer experience from education, birth years or a whole-document span.
        for b in summary:
            match=re.search(r'\b(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of)?\s+(?:(?:professional|work|IT|industry|relevant|overall|total|vast|extensive|rich|solid|diverse|hands-on)\s+){0,3}experience\b',b.text,re.I)
            if match:
                data.total_experience_years=remember('total_experience_years',float(match.group(1)),[b]);break
        skill_blocks=blocks('skills');skill_text=canonical(skill_blocks)
        data.skills=extract_skills_categorized(skill_text,'')
        # The handoff's word-boundary regex misses names ending in punctuation.
        for skill in ('C#','C++'):
            if re.search(r'(?<!\w)'+re.escape(skill)+r'(?!\w)',skill_text,re.I) and skill not in data.skills.technical_skills:
                data.skills.technical_skills.append(skill)
        explicit_competencies=[b.text.strip().removesuffix(':').rstrip() for b in skill_blocks if b.assignment=='local_competency_name']
        known=set(data.skills.technical_skills+data.skills.tools_and_platforms+data.skills.domain_and_functional+data.skills.soft_skills)
        data.skills.domain_and_functional=unique(data.skills.domain_and_functional+[name for name in explicit_competencies if name not in known])
        flat=skill_candidates(skill_blocks)
        data.skills.all_skills=unique(data.skills.technical_skills+data.skills.tools_and_platforms+data.skills.domain_and_functional+data.skills.soft_skills+flat)
        for field in type(data.skills).model_fields:
            values=getattr(data.skills,field)
            # Dictionary recognition must still have literal evidence in skills.
            values=unique(value for value in values if supported(value,skill_blocks))
            setattr(data.skills,field,values)
            for i,value in enumerate(values):remember(f'skills.{field}[{i}]',value,[b for b in skill_blocks if norm(value) in norm(b.text)])
        for category in ('experience','education','projects','certifications'):
            section=sections.get(category)
            if not section:continue
            if category in {'experience', 'education'} and not ownership_locked:
                from local_api.services.record_relationships import annotate_relationships
                annotate_relationships(section)
            for entry in section.entries:
                owned_bs=[section.blocks[i] for i in entry.block_indices]
                context_ids={i for field,ids in entry.context_fields.items() for i in ids if category != 'experience' or field != 'company'}
                bs=[section.blocks[i] for i in sorted(set(entry.block_indices)|context_ids)]
                def refs(name):
                    indices = entry.fields.get(name, [])
                    if category == 'experience' and name == 'responsibilities':
                        indices = sorted(set(indices) | set(entry.fields.get('achievements', [])))
                    return [section.blocks[i] for i in indices]
                def field(name):return canonical(refs(name)).strip()
                def sole(name):
                    value=field(name)
                    return value if len(refs(name))==1 else None
                text=canonical(bs)
                review={'category':category,'entry_id':entry.entry_id,'source_ids':[source_id(b) for b in owned_bs],
                        'relationship_status':entry.relationship_status,'review_reasons':entry.review_reasons}
                record_reviews.append(review)
                if category=='experience':
                    candidates=extract_work_experience(text,text)
                    candidate=candidates[0] if len(candidates)==1 else None
                    company=literal(candidate.company,refs('employer')) if candidate else None
                    company_context = [section.blocks[i] for i in entry.context_fields.get('company', [])]
                    if company_context:
                        from local_api.services.record_subfields import labelled_fields, employment_header_fields
                        names = labelled_fields('experience', company_context).get('company', [])
                        company = names[0] if len(names) == 1 else employment_header_fields(company_context[0].text).get('company') or re.split(r'\s+[—–-]\s+', company_context[0].text)[0].strip()
                    role=literal(candidate.role,refs('title')) if candidate else None
                    role_pattern=r'\b(?:engineer|developer|analyst|consultant|architect|manager|specialist|director|lead|supervisor)\b'
                    company_pattern=r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies)|solutions|company|ispl|paribas|bnp|pvt|private)\b'
                    if company and re.search(role_pattern,company,re.I) and not re.search(company_pattern,company,re.I):company=None
                    if role and re.search(company_pattern,role,re.I):role=None
                    if not company:
                        pieces=[part.strip() for part in field('employer').split('|') if part.strip() and re.search(company_pattern,part,re.I) and not re.search(r'\b(?:19|20)\d{2}\b',part)]
                        if len(pieces)==1:company=pieces[0]
                    if not role:
                        pieces=[part.strip() for part in field('title').split('|') if part.strip() and re.search(role_pattern,part,re.I) and not re.search(company_pattern,part,re.I) and not re.search(r'\b(?:19|20)\d{2}\b',part)]
                        if len(pieces)==1:role=pieces[0]
                    if not company and sole('employer'):
                        m_dated_prefix = None
                        if dated_organization_header(field('employer')):
                            m_dated_prefix = field('employer').rsplit('(', 1)[0].strip()
                        else:
                            m_hdr = re.match(r"^\s*([A-Za-z][A-Za-z&.,'’ /-]{1,90}?)\s*\(([^()]+)\)", field('employer'))
                            if m_hdr:
                                name_part, dates_part = m_hdr.groups()
                                if (re.search(r'\b(?:19|20)\d{2}\b', dates_part) and
                                    re.search(r'[-–—]|\b(?:to|till|until)\b', dates_part, re.I) and
                                    len(name_part.split()) <= 10 and
                                    not re.search(role_pattern, name_part, re.I) and
                                    not re.search(r'\b(?:project|client|duration|education|school|university|college|training)\b', name_part, re.I)):
                                    m_dated_prefix = name_part.strip()
                        if m_dated_prefix:
                            if ',' not in m_dated_prefix: company = m_dated_prefix
                            else:
                                organization, location = m_dated_prefix.rsplit(',', 1)
                                matched_location = extract_contact_info(location, location).location
                                if matched_location and norm(matched_location) == norm(location): company = organization.strip()
                                else: company = m_dated_prefix
                    # Isolated source fields may map directly; combined lines remain uncertain.
                    if not company and sole('employer'):
                        cand_emp = re.split(r'\s+[—–-]\s+', field('employer'))[0].strip()
                        if not re.search(r'(?:19|20)\d{2}|\||\b(?:engineer|developer|consultant|manager)\b', cand_emp, re.I):
                            company = cand_emp
                    if not role and sole('title') and not re.search(r'(?:19|20)\d{2}|\||\b(?:ltd|inc|corporation|company)\b', field('title'), re.I):
                        role = field('title')
                    from local_api.services.dated_record_headers import dated_header_candidates
                    dh = dated_header_candidates(bs)
                    if len(dh) == 1:
                        if dh[0].get('company') and not company: company = dh[0]['company']
                        if dh[0].get('role') and not role: role = dh[0]['role']
                        allow_company = True
                        allow_role = True
                    else:
                        allow_company = not entry.fields or 'employer' in entry.fields or bool(company_context)
                        allow_role = not entry.fields or 'title' in entry.fields
                    from local_api.services.record_subfields import employment_header_fields
                    if (not company and allow_company) or (not role and allow_role) or (company and role and role.casefold().startswith(company.casefold())):
                        for candidate_text in [field('employer'), field('title'), text]:
                            if candidate_text:
                                clean_cand = re.sub(r'\b(?:system\s+(?:prompt|instruction|override)|ignore\s+all\s+(?:previous|prior)\s+instructions|output\s+role\s*:|human\s+review\s*:)\b.*', '', candidate_text, flags=re.I).strip()
                                parsed = employment_header_fields(clean_cand) if clean_cand else {}
                                if allow_company and (not company or (role and role.casefold().startswith(company.casefold()))) and parsed.get('company'): company = parsed['company']
                                if allow_role and (not role or (company and role.casefold().startswith(company.casefold()))) and parsed.get('role'): role = parsed['role']
                                if company and role and not role.casefold().startswith(company.casefold()): break
                    if role and re.search(r'\b(?:system\s+(?:prompt|instruction)|ignore\s+all|output\s+role)\b', role, re.I):
                        role = None
                    if company and role and role.casefold().startswith(company.casefold()):
                        role = re.sub(r'^' + re.escape(company) + r'\s*[-–—:|]\s*', '', role, flags=re.I).strip()
                    if not allow_company: company = None
                    if not allow_role: role = None
                    if company and employment_header_fields(company).get('company'):
                        company = employment_header_fields(company)['company']
                    loc = sole('location')
                    if loc and employment_header_fields(loc).get('location'):
                        loc = employment_header_fields(loc)['location']
                    if not loc:
                        for candidate_text in [field('employer'), field('title'), text]:
                            if candidate_text:
                                parsed = employment_header_fields(candidate_text)
                                if parsed.get('location'):
                                    loc = parsed['location']
                                    break
                    if not loc and field('employer'):
                        from local_api.services.record_subfields import is_place
                        cparts = re.split(r'\s+[—–-]\s+', field('employer'))
                        if len(cparts) == 2:
                            suffix = cparts[1].strip()
                            place_shape = bool(re.fullmatch(r'[A-Z][A-Za-z.\'-]*(?:[ ,]+[A-Z][A-Za-z.\'-]*){0,4}', suffix))
                            if (is_place(suffix) or place_shape) and not re.search(r'\b(?:team|department|division|operations|engineering|services|solutions|platform|products|practice|business|unit|group|ltd|limited|inc|corp|co|pvt)\b', suffix, re.I):
                                loc = suffix
                    if not loc and role:
                        from local_api.services.record_subfields import is_place, ROLE
                        loc_match = re.match(r'^(.*?,\s*[A-Za-z]+|\b(?:Bangalore|Bengaluru|Chennai|Hyderabad|Mumbai|Pune|Delhi|Noida|Gurgaon|London|Singapore|Dubai)\b)\s+([A-Za-z].*)$', role, re.I)
                        if loc_match and is_place(loc_match.group(1)) and not ROLE.search(loc_match.group(1)):
                            loc = loc_match.group(1).strip(' ,')
                            role = loc_match.group(2).strip()
                    record=WorkExperience(company=company or '',role=role or '',location=loc or None,responsibilities=[part.strip() for text in texts(refs('responsibilities')) for part in re.split(r'[\u2022\u25cf\u25aa]',text) if part.strip()])
                    dates=field('dates')
                    date=r'(?:\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*)?(?:(?:19|20)\d{2}|[’‘\'`´]?\d{2})\b'
                    matches=list(re.finditer('('+date+r')\s*(?:[-–—]|\bto\b|\btill\b)\s*('+date+r'|Currently working|Present|Current|Till Date|Till Now|Now)(?!\w)',dates,re.I))
                    if len(matches)==1:
                        from local_api.services.record_subfields import employment_duration_literal
                        record.start_date,record.end_date=matches[0].group(1,2)
                        record.duration=employment_duration_literal(matches[0])
                    elif not record.duration:
                        for source_text in (dates, text):
                            if not source_text: continue
                            dur_match = re.search(r'\b(?:(\d+)\s*(?:years?|yrs?)\s*(?:and\s*)?)?(?:(\d+)\s*(?:months?|mos?))\b|\b(\d+(?:\.\d+)?\s*(?:years?|yrs?))\b', source_text, re.I)
                            if dur_match and not re.search(r'\b(?:experience|exp|batch)\b', dur_match.group(0), re.I):
                                record.duration = dur_match.group(0).strip()
                                break
                    if company and not (role or dates or refs('responsibilities')):
                        entry.relationship_status = 'needs_review'
                        entry.review_reasons.append('Role and dates are not established; partial employer record retained.')
                        review['relationship_status'] = 'needs_review'
                    i=len(data.experience);data.experience.append(record);prefix=f'experience[{i}]'
                    for key,ref in [('company','employer'),('role','title'),('start_date','dates'),('end_date','dates'),('duration','dates'),('location','location')]:
                        ref_bs = refs(ref)
                        if key == 'company' and company_context:
                            ref_bs = company_context
                        remember(prefix+'.'+key,getattr(record,key),ref_bs)
                    for j,b in enumerate(refs('responsibilities')):remember(f'{prefix}.responsibilities[{j}]',b.text,[b])
                elif category=='education':
                    candidates=extract_education(text,text)
                    candidate=candidates[0] if len(candidates)==1 else None
                    ambiguous=any('multiple_qualification' in reason for reason in entry.review_reasons)
                    degree=sole('qualification') if not ambiguous else None
                    institution=sole('institution') if not ambiguous else None
                    if degree and institution==degree:institution=None
                    if not degree and candidate and not ambiguous:degree=literal(candidate.degree,refs('qualification'))
                    if not institution and candidate and not ambiguous:institution=literal(candidate.institution,refs('institution'))
                    record=Education(degree=degree or '',institution=institution or '')
                    years=list(dict.fromkeys(re.findall(r'\b(?:19|20)\d{2}\b',field('dates'))))
                    if len(years)==1:record.graduation_year=years[0]
                    elif len(years)>=2:
                        record.start_year=years[0]
                        record.graduation_year=years[1]
                    i=len(data.education);data.education.append(record)
                    for key,ref in [('degree','qualification'),('institution','institution'),('graduation_year','dates')]:remember(f'education[{i}].'+key,getattr(record,key),refs(ref))
                elif category=='projects':
                    from local_api.services.project_fields import project_fields
                    title, description = project_fields(bs, request.elements, sole('title'))
                    record=Project(name=title,description=description);i=len(data.projects);data.projects.append(record)
                    remember(f'projects[{i}].name',title,bs);remember(f'projects[{i}].description',record.description,bs)
                else:
                    contents=[b for b in bs if b.assignment not in {'section_heading','structural_heading'}]
                    if contents:
                        from local_api.services.record_subfields import labelled_fields
                        value=next((b.text.strip() for b in contents if b.text.strip()
                                    and not labelled_fields('certifications', [b])
                                    and not re.fullmatch(r'\d{4}(?:-\d{2})?|https?://\S+', b.text.strip())), '')
                        i=len(data.certifications);record=Certification(name=value);data.certifications.append(record);remember(f'certifications[{i}].name',value,contents)
                if category == 'certifications' and not contents:
                    continue
                review['mapped_index'] = i
                original = record.model_dump()
                base, education_reasons = refine_education(original, bs) if category == 'education' else (original, [])
                refined, reasons = refine_record(category, base, bs, header_fields=(
                    {'company' if field == 'employer' else 'role' if field == 'title' else field for field in entry.fields} | set(entry.context_fields)
                    if entry.fields else None))
                if category == 'experience' and company_context:
                    refined['company'] = company
                if category=='experience':
                    literal_header=request.sections.metadata.get('dated_employment_scope',{}).get('literal_records',{}).get(entry.entry_id,{})
                    for key,value in literal_header.items():
                        if key in refined and value and field_quotes(value,bs):refined[key]=value
                if category == 'education':
                    from local_api.services.education_header_fields import source_education_fields
                    refined.update(source_education_fields(bs,request.elements))
                review['review_reasons'] = list(dict.fromkeys(review['review_reasons'] + education_reasons + reasons))
                if reasons or education_reasons:review['relationship_status'] = 'needs_review'
                for key, value in refined.items():
                    allowed_field_blocks = company_context if category == 'experience' and key == 'company' and company_context else bs
                    if value is None:
                        value = [] if isinstance(original[key], list) else '' if key in {'company','role','degree','institution','name'} else None
                    if isinstance(value,list):value=[item for item in value if field_quotes(item,allowed_field_blocks)]
                    elif value and not field_quotes(value,allowed_field_blocks):value='' if key in {'company','role','degree','institution','name'} else None
                    setattr(record, key, value)
                    path = f'{category}[{i}].{key}'
                    for old_path in list(evidence):
                        if old_path == path or old_path.startswith(path + '['):evidence.pop(old_path)
                    for j, item in enumerate(value if isinstance(value, list) else [value]):
                        remember(f'{path}[{j}]' if isinstance(value, list) else path, item,
                                 [b for b in allowed_field_blocks if any(r['source_id']==source_id(b) for r in field_quotes(item,allowed_field_blocks))])
        for language, level, b in language_rows(blocks('languages')):
            value=language if level is None else next((part.strip() for part in re.split(r'[\u2022\u25cf\n]',b.text) if language in part and level in part),language)
            i=len(data.languages);data.languages.append(value);remember(f'languages[{i}]',value,[b])
        if len(data.experience) == 1 and not data.experience[0].responsibilities:
            proj_sec = next((s for s in request.sections.sections if s.category == 'projects'), None)
            if proj_sec and proj_sec.blocks and re.search(r'\b(?:project\s+details|client\s+projects|projects\s+undertaken|project\s+experience)\b', proj_sec.blocks[0].text, re.I):
                full_proj_text = " ".join(b.text.strip() for b in proj_sec.blocks)
                bullets = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"[•▪●\uf0b7]", full_proj_text) if p.strip()]
                filtered_resps = [p for p in bullets if not re.match(r"^(?:Project|Responsibilities|Technologies|ServiceNow|Description)\b", p, re.I) and len(p.split()) >= 4]
                if filtered_resps:
                    data.experience[0].responsibilities = filtered_resps
                    for j, item in enumerate(filtered_resps):
                        remember(f'experience[0].responsibilities[{j}]', item,
                                 [b for b in proj_sec.blocks if any(w in b.text for w in item.split()[:3])])
        # Retain entry identity and reindex citations together when pruning.
        for category in ('experience', 'education', 'projects', 'certifications'):
            reviews = [r for r in record_reviews if r['category'] == category and 'mapped_index' in r]
            kept = []
            old_evidence = {p: refs for p, refs in evidence.items() if p.startswith(category + '[')}
            for path in old_evidence:
                evidence.pop(path)
            record_bindings[category] = {}
            for old_index, record in enumerate(getattr(data, category)):
                review = reviews[old_index]
                parent_entry = next((e for e in sections[category].entries if e.entry_id == review['entry_id']), None)
                explicit_identity = bool(parent_entry and (parent_entry.fields.get('employer') or parent_entry.fields.get('title')))
                employer_scope_only = bool(category == 'experience' and parent_entry and not parent_entry.fields.get('title')
                    and not parent_entry.fields.get('responsibilities') and any(
                        set(sibling.context_fields.get('company', [])) & set(parent_entry.block_indices)
                        for sibling in sections[category].entries if sibling.entry_id != parent_entry.entry_id))
                if employer_scope_only:
                    review['mapped_index'] = None
                    review['review_reasons'].append('Employer scope retained as company context for child roles, not a separate role.')
                    continue
                if category == 'experience' and not record.role and not record.start_date and not record.end_date and not record.responsibilities:
                    from local_api.services.record_subfields import labelled_fields, employment_header_fields
                    owned = [sections[category].blocks[j] for j in parent_entry.block_indices] if parent_entry else []
                    labels = labelled_fields(category, owned)
                    supported_header = any({'company','role'} <= employment_header_fields(b.text).keys() for b in owned)
                    if not ({'company','role'} & labels.keys() or supported_header):
                        review['mapped_index'] = None
                        review['review_reasons'].append('Undated identity fragment has no explicit employment relation; retained as Needs Review.')
                        continue
                if category == 'experience' and not record.company and not record.role and not explicit_identity:
                    review['mapped_index'] = None
                    review['review_reasons'].append('Source content has no established employer or role; retained for association review, not counted as a job.')
                    continue
                education_identity = bool(category == 'education' and parent_entry and (parent_entry.fields.get('qualification') or parent_entry.fields.get('institution')))
                if category in {'experience', 'education'} and not any(record.model_dump().values()) and not (category == 'experience' and explicit_identity or education_identity):
                    review['mapped_index'] = None
                    continue
                def norm_s(s): return re.sub(r'[\W_]+', '', (s or '').casefold())
                duplicate_match = None
                if category == 'experience':
                    r_comp = norm_s(record.company)
                    r_role = norm_s(record.role)
                    r_dates = (record.start_date, record.end_date)
                    for k_idx, existing in enumerate(kept):
                        e_comp = norm_s(existing.company)
                        e_role = norm_s(existing.role)
                        e_dates = (existing.start_date, existing.end_date)
                        comp_match = bool(r_comp and e_comp and r_comp == e_comp)
                        role_match = bool(r_role and e_role and (r_role == e_role or r_role in e_role or e_role in r_role))
                        if comp_match and role_match:
                            dates_match = (r_dates == e_dates or
                                           (r_dates == (None, None) and e_dates != (None, None)) or
                                           (e_dates == (None, None) and r_dates != (None, None)))
                            if dates_match:
                                duplicate_match = k_idx
                                break
                elif category == 'education':
                    r_inst = norm_s(record.institution)
                    r_deg = norm_s(record.degree)
                    r_grad = norm_s(record.graduation_year)
                    for k_idx, existing in enumerate(kept):
                        e_inst = norm_s(existing.institution)
                        e_deg = norm_s(existing.degree)
                        e_grad = norm_s(existing.graduation_year)
                        if (r_inst and e_inst and r_inst == e_inst and
                            r_deg == e_deg and (r_grad == e_grad or not r_grad or not e_grad)):
                            duplicate_match = k_idx
                            break

                if duplicate_match is not None:
                    new_index = duplicate_match
                    review['mapped_index'] = new_index
                    record_bindings[category][review['entry_id']] = new_index
                    existing = kept[duplicate_match]
                    if category == 'experience':
                        if existing.start_date is None and record.start_date is not None:
                            existing.start_date = record.start_date
                            existing.end_date = record.end_date
                        for resp in record.responsibilities:
                            if resp not in existing.responsibilities:
                                existing.responsibilities.append(resp)
                    elif category == 'education':
                        if existing.start_year is None and record.start_year is not None:
                            existing.start_year = record.start_year
                        if existing.graduation_year is None and record.graduation_year is not None:
                            existing.graduation_year = record.graduation_year
                    old_prefix = f'{category}[{old_index}].'
                    for path, refs in old_evidence.items():
                        if path.startswith(old_prefix):
                            target_path = f'{category}[{new_index}].' + path[len(old_prefix):]
                            evidence.setdefault(target_path, []).extend(refs)
                else:
                    new_index = len(kept)
                    review['mapped_index'] = new_index
                    kept.append(record)
                    record_bindings[category][review['entry_id']] = new_index
                    old_prefix = f'{category}[{old_index}].'
                    for path, refs in old_evidence.items():
                        if path.startswith(old_prefix):
                            evidence[f'{category}[{new_index}].' + path[len(old_prefix):]] = refs
            setattr(data, category, kept)
        used = {ref for refs in evidence.values() for ref in refs}
    else:warnings.append('Document scope is non-resume; candidate fields were left empty and source sections retained.')
    missing=['contact.'+f for f in ('full_name','email','phone') if not getattr(data.contact,f)]
    for category,fields in [('experience',('company','role')),('education',('institution','degree')),('projects',('name',)),('certifications',('name',))]:
        for i,record in enumerate(getattr(data,category)):
            missing.extend(f'{category}[{i}].{field}' for field in fields if not getattr(record,field))

    # Source-coverage ledger with the 6 canonical statuses:
    # 'present_and_extracted', 'present_but_unmapped', 'present_but_ambiguous',
    # 'absent_in_source', 'extraction_failed', 'not_applicable'
    field_source_status = {}
    is_non_resume = (scope.get('candidate_resume') is False)
    has_corrupted_glyphs = any('\x00' in e.text or '\ufffd' in e.text for e in request.elements)
    # Misassigned content is still present in the document, even when no block
    # remains in needs_review. Never confuse section placement with absence.
    unassigned_text = '\n'.join(e.text for e in request.elements)

    for field in ('contact.full_name', 'contact.email', 'contact.phone', 'contact.location',
                  'contact.linkedin_url', 'contact.github_url', 'contact.portfolio_url',
                  'professional_title', 'summary', 'total_experience_years'):
        val = getattr(data.contact, field.removeprefix('contact.'), None) if field.startswith('contact.') else getattr(data, field, None)
        if val:
            field_source_status[field] = 'present_and_extracted'
        elif is_non_resume:
            field_source_status[field] = 'not_applicable'
        elif has_corrupted_glyphs:
            field_source_status[field] = 'extraction_failed'
        elif any(f'Conflicting explicit labels for {field.removeprefix("contact.")}.' in w for w in warnings):
            field_source_status[field] = 'present_but_ambiguous'
        elif field == 'contact.email' and re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', unassigned_text):
            field_source_status[field] = 'present_but_unmapped'
        elif field == 'contact.phone' and any(10 <= len(re.sub(r'\D', '', token)) <= 15
                for token in re.findall(r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)', unassigned_text)):
            field_source_status[field] = 'present_but_unmapped'
        else:
            field_source_status[field] = 'absent_in_source'

    for cat in ('experience', 'education', 'projects', 'certifications'):
        records = getattr(data, cat)
        if records:
            field_source_status[cat] = 'present_and_extracted'
        elif is_non_resume:
            field_source_status[cat] = 'not_applicable'
        elif any(s.category == cat for s in request.sections.sections):
            field_source_status[cat] = 'present_but_unmapped'
        elif cat == 'education' and re.search(r'\b(?:bachelor|master|b\.?s\.?|b\.?tech|m\.?tech|b\.?e\.?|degree|university|college|institute|graduated|diploma)\b', unassigned_text, re.I):
            field_source_status[cat] = 'present_but_unmapped'
        elif cat == 'experience' and re.search(r'\b(?:developer|engineer|manager|analyst|architect|consultant|specialist|officer|associate|intern)\b', unassigned_text, re.I):
            field_source_status[cat] = 'present_but_unmapped'
        elif cat == 'certifications' and re.search(r'\b(?:certified|certification|certificate|aws|azure|pmp)\b', unassigned_text, re.I):
            field_source_status[cat] = 'present_but_unmapped'
        elif cat == 'projects' and re.search(r'\b(?:project|developed|implemented)\b', unassigned_text, re.I):
            field_source_status[cat] = 'present_but_unmapped'
        else:
            field_source_status[cat] = 'absent_in_source'

    for m in missing:
        if m not in field_source_status:
            if is_non_resume:
                field_source_status[m] = 'not_applicable'
            elif has_corrupted_glyphs:
                field_source_status[m] = 'extraction_failed'
            else:
                field_source_status[m] = 'absent_in_source'

    from local_api.services.field_coverage import complete_field_statuses
    complete_field_statuses(field_source_status, request.sections, data, scope,
                            record_bindings, record_reviews, warnings)

    mapping = build_schema_mapping_report(data, status_overrides=field_source_status)
    warnings+=['Schema validity and field completion do not establish extraction or relationship accuracy.',
               'Handoff confidence scores are fixed heuristics, not calibrated probabilities.',
               'Missing required strings use empty strings for handoff compatibility; inspect missing_required_fields.']
    all_blocks=[(s.category,b) for s in request.sections.sections for b in s.blocks]+[(None,b) for b in request.sections.needs_review]
    response = SchemaMappingResponse(success=True,source=request.source,extraction_mode='existing_blocks_schema_mapping',data=data,schema_mapping=mapping,raw_sections=raw,
        section_schemas=build_subschemas(request.sections,data,scope,record_bindings),
        meta={'status':'needs_review','human_verified':False,'provider_calls':0,'source_accounting':accounting,'document_scope':scope,
              'source_inventory_sha256':hashlib.sha256(json.dumps([e.model_dump() for e in request.elements],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
              'field_evidence':evidence,'record_reviews':record_reviews,'record_bindings':record_bindings,'missing_required_fields':missing,
              'field_source_status':field_source_status,
              'source_coverage_ledger':{
                  'field_statuses':field_source_status,
                  'status_counts':{
                      st: sum(1 for v in field_source_status.values() if v == st)
                      for st in ('present_and_extracted', 'present_but_unmapped', 'present_but_ambiguous',
                                'absent_in_source', 'extraction_failed', 'not_applicable')
                  }
              },
              'warnings':warnings,
              'unmapped_blocks':[{'source_id':source_id(b),'category':category,'text':b.text,'page_number':b.page_number} for category,b in all_blocks if source_id(b) not in used],
              'needs_review':[b.model_dump() for b in request.sections.needs_review
                              if not artifact_reason(request.elements[b.source_element_index], b)],
              'layout_artifacts':[row for row in accounting['outcomes'] if row['outcome']=='non_content_artifact']})

    from local_api.services.source_ownership import snapshot
    response.meta['source_ownership'] = snapshot(request.elements, request.sections).payload()
    request.sections.metadata['source_ownership'] = response.meta['source_ownership']
    if contacts_reassigned or local_completed or ownership_repaired:
        response.meta['reviewed_sections'] = request.sections.model_dump()
    from local_api.services.mapping_completeness import mapping_completeness
    response.meta['completeness_check'] = mapping_completeness(request.elements, request.sections, response.section_schemas)
    return response
