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
from local_api.services.source_accounting import account_source
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
    # Fail closed on stale/altered/overlapping source intervals or foreign fields.
    if sum(len(s.blocks) for s in request.sections.sections)+len(request.sections.needs_review)>10000:
        raise ValueError('Too many section blocks')
    errors=validate_result(request.elements,request.sections)
    if errors:
        from local_api.services.schema_diagnostics import fail
        fail('source_binding_validation', errors[0], ('sections',))
    from local_api.services.contact_sections import recover_contact_sections, contact_values as literal_contact_values
    from local_api.services.education_date_recovery import recover_education_dates
    recovered_sections = recover_education_dates(request.sections, request.elements)
    recovered_sections = recover_contact_sections(recovered_sections, request.elements)
    contacts_reassigned = recovered_sections is not request.sections
    if contacts_reassigned:
        request = request.model_copy(update={'sections': recovered_sections})
    accounting=account_source(request.elements,request.sections)
    scope=document_scope(request.elements)
    sections={s.category:s for s in request.sections.sections}
    raw={key:canonical(s.blocks) for key,s in sections.items()}
    evidence={};warnings=[];record_reviews=[];used=set();record_bindings={}
    inventory={source_id(b):b.text for section in request.sections.sections for b in section.blocks}
    inventory.update({source_id(b):b.text for b in request.sections.needs_review})
    def field_quotes(value, bs):
        refs=citations(value,bs)
        if any(str(value).casefold() in r['quote'].casefold() for r in refs) or contiguous_support(value,[SourceQuote(**r) for r in refs],inventory):return refs
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
        header=blocks('personal_information');text='\n'.join(b.text for b in header)
        doc_text='\n'.join(e.text for e in request.elements)
        guessed=extract_contact_info(text,doc_text)
        # Prefer a distinct opening identity fragment over words in a role headline.
        from local_api.services.record_subfields import ROLE
        identity = [b.text.strip() for b in header
                    if b.source_element_index == min((h.source_element_index for h in header), default=-1)
                    and 2 <= len(b.text.split()) <= 5
                    and all(c.isalpha() or c in " .'-" for c in b.text.strip())
                    and not ROLE.search(b.text)]
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
                value=literal(value,header)
                if field in {'email','phone'}:value=value or ''
                setattr(data.contact,field,remember('contact.'+field,value,header))
        title_candidates = [(text, run) for run in runs(header) for text in [''.join(b.text for b in run)]
                            if len(text.split())<=12 and not re.search(r'@|Technical Skills|Core AI|linkedin|github',text,re.I)]
        title_candidates += [(b.text,[b]) for b in header]
        for title, refs in title_candidates:
            if len(title.split())<=12 and '@' not in title and re.search(r'\b(?:engineer|engineering lead|developer|analyst|consultant|architect|manager|specialist|scientist)\b',title,re.I):
                title=title.strip()
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
        for key, matches in literal_contact_values(header).items():
            if len(matches) == 1:
                value = next(iter(matches))
                setattr(data.contact, key, remember('contact.'+key, value, header))
        from local_api.services.contact_sections import profile_values
        for key, matches in profile_values(header).items():
            if len(matches) == 1:
                value = next(iter(matches))
                setattr(data.contact, key, remember('contact.'+key, value,
                    [b for b in header if value in b.text]))
            elif len(matches) > 1:
                setattr(data.contact, key, None)
                evidence.pop('contact.'+key, None)
                warnings.append('Multiple candidate profile links require review: '+key)
        summary=blocks('summary')
        data.summary=remember('summary',canonical(summary).strip() or None,summary)
        # Never infer experience from education, birth years or a whole-document span.
        for b in summary:
            match=re.search(r'\b(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of)?\s+(?:professional\s+|work\s+)?experience\b',b.text,re.I)
            if match:
                data.total_experience_years=remember('total_experience_years',float(match.group(1)),[b]);break
        skill_blocks=blocks('skills');skill_text=canonical(skill_blocks)
        data.skills=extract_skills_categorized(skill_text,'')
        # The handoff's word-boundary regex misses names ending in punctuation.
        for skill in ('C#','C++'):
            if re.search(r'(?<!\w)'+re.escape(skill)+r'(?!\w)',skill_text,re.I) and skill not in data.skills.technical_skills:
                data.skills.technical_skills.append(skill)
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
            for entry in section.entries:
                bs=[section.blocks[i] for i in entry.block_indices]
                def refs(name):return [section.blocks[i] for i in entry.fields.get(name,[])]
                def field(name):return canonical(refs(name)).strip()
                def sole(name):
                    value=field(name)
                    return value if len(refs(name))==1 else None
                text=canonical(bs)
                review={'category':category,'entry_id':entry.entry_id,'source_ids':[source_id(b) for b in bs],
                        'relationship_status':entry.relationship_status,'review_reasons':entry.review_reasons}
                record_reviews.append(review)
                if category=='experience':
                    candidates=extract_work_experience(text,text)
                    candidate=candidates[0] if len(candidates)==1 else None
                    company=literal(candidate.company,refs('employer')) if candidate else None
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
                    if not company and sole('employer') and dated_organization_header(field('employer')):
                        prefix=field('employer').rsplit('(',1)[0].strip()
                        if ',' not in prefix:company=prefix
                        else:
                            organization,location=prefix.rsplit(',',1)
                            matched_location=extract_contact_info(location,location).location
                            if matched_location and norm(matched_location)==norm(location):company=organization.strip()
                    # Isolated source fields may map directly; combined lines remain uncertain.
                    if not company and sole('employer') and not re.search(r'\d|\||\b(?:engineer|developer|consultant|manager)\b',field('employer'),re.I):company=field('employer')
                    if not role and sole('title') and not re.search(r'\d|\||\b(?:ltd|inc|corporation|company)\b',field('title'),re.I):role=field('title')
                    record=WorkExperience(company=company or '',role=role or '',responsibilities=[part.strip() for text in texts(refs('responsibilities')) for part in re.split(r'[\u2022\u25cf\u25aa]',text) if part.strip()])
                    dates=field('dates')
                    date=r'(?:\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?\b(?:19|20)\d{2}\b'
                    matches=list(re.finditer('('+date+r')\s*(?:[-–—]|\bto\b|\btill\b)\s*('+date+r'|Currently working|Present|Current|Till Date)(?!\w)',dates,re.I))
                    if len(matches)==1:record.start_date,record.end_date=matches[0].group(1,2);record.duration=matches[0].group()
                    i=len(data.experience);data.experience.append(record);prefix=f'experience[{i}]'
                    for key,ref in [('company','employer'),('role','title'),('start_date','dates'),('end_date','dates'),('duration','dates')]:remember(prefix+'.'+key,getattr(record,key),refs(ref))
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
                    i=len(data.education);data.education.append(record)
                    for key,ref in [('degree','qualification'),('institution','institution'),('graduation_year','dates')]:remember(f'education[{i}].'+key,getattr(record,key),refs(ref))
                elif category=='projects':
                    title=sole('title') or next((b.text.strip() for b in bs if b.assignment not in {'section_heading','structural_heading'} and len(b.text.split())<=18),'')
                    record=Project(name=title,description=text or None);i=len(data.projects);data.projects.append(record)
                    remember(f'projects[{i}].name',title,bs);remember(f'projects[{i}].description',record.description,bs)
                else:
                    contents=[b for b in bs if b.assignment not in {'section_heading','structural_heading'}]
                    if contents:
                        i=len(data.certifications);value=canonical(contents).strip();record=Certification(name=value);data.certifications.append(record);remember(f'certifications[{i}].name',value,contents)
                if category == 'certifications' and not contents:
                    continue
                review['mapped_index'] = i
                original = record.model_dump()
                base, education_reasons = refine_education(original, bs) if category == 'education' else (original, [])
                refined, reasons = refine_record(category, base, bs, header_fields=(
                    {'company' if field == 'employer' else 'role' if field == 'title' else field for field in entry.fields}
                    if entry.fields else None))
                review['review_reasons'] = list(dict.fromkeys(review['review_reasons'] + education_reasons + reasons))
                if reasons or education_reasons:review['relationship_status'] = 'needs_review'
                for key, value in refined.items():
                    if value is None:
                        value = [] if isinstance(original[key], list) else '' if key in {'company','role','degree','institution','name'} else None
                    if isinstance(value,list):value=[item for item in value if field_quotes(item,bs)]
                    elif value and not field_quotes(value,bs):value='' if key in {'company','role','degree','institution','name'} else None
                    setattr(record, key, value)
                    path = f'{category}[{i}].{key}'
                    for old_path in list(evidence):
                        if old_path == path or old_path.startswith(path + '['):evidence.pop(old_path)
                    for j, item in enumerate(value if isinstance(value, list) else [value]):
                        remember(f'{path}[{j}]' if isinstance(value, list) else path, item,
                                 [b for b in bs if any(r['source_id']==source_id(b) for r in field_quotes(item,bs))])
        for language, level, b in language_rows(blocks('languages')):
            value=language if level is None else next((part.strip() for part in re.split(r'[\u2022\u25cf\n]',b.text) if language in part and level in part),language)
            i=len(data.languages);data.languages.append(value);remember(f'languages[{i}]',value,[b])
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
                if category in {'experience', 'education'} and not any(record.model_dump().values()) and not review['review_reasons']:
                    review['mapped_index'] = None
                    continue
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
              'needs_review':[b.model_dump() for b in request.sections.needs_review]})

    if contacts_reassigned:
        response.meta['reviewed_sections'] = request.sections.model_dump()
    return response
