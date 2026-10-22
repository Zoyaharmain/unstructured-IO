"""Source-bound adapter to the handoff schema; no extraction, regrouping or LLM calls."""
import hashlib
import json
import re
from local_api.vendor.handoff_schema.models import (
    ResumeSchema, ContactInfo, WorkExperience, Education, Project, Certification,
    CategorizedSkills, ParseResponse,
)
from local_api.vendor.handoff_schema.service import (
    extract_contact_info, extract_work_experience, extract_education,
    extract_skills_categorized, build_schema_mapping_report,
)
from local_api.services.source_accounting import account_source
from local_api.services.review_resolution import document_scope
from local_api.services.record_relationships import dated_organization_header
from local_api.services.source_validation import validate_result


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
    if errors:raise ValueError('Sections are not bound to the supplied source inventory')
    accounting=account_source(request.elements,request.sections)
    scope=document_scope(request.elements)
    sections={s.category:s for s in request.sections.sections}
    raw={key:canonical(s.blocks) for key,s in sections.items()}
    evidence={};warnings=[];record_reviews=[];used=set()
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
        header=blocks('personal_information');text=canonical(header)
        guessed=extract_contact_info(text,text)
        for field in type(guessed).model_fields:
            value=getattr(guessed,field)
            if value in {'Candidate','Not specified','not_specified@domain.com'}:value=None
            value=literal(value,header)
            if field in {'full_name','email','phone'}:value=value or ''
            setattr(data.contact,field,remember('contact.'+field,value,header))
        for b in header:
            if len(b.text.split())<=12 and '@' not in b.text and re.search(r'\b(?:engineer|developer|analyst|consultant|architect|manager|specialist|scientist)\b',b.text,re.I):
                data.professional_title=remember('professional_title',b.text.strip(),[b]);break
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
        flat=[]
        for b in skill_blocks:
            value=re.sub(r'^\s*[•▪●*\-]\s*','',b.text).strip()
            if ':' in value and re.fullmatch(r'(?:technical skills|skills|languages|tools|platforms|frameworks|databases|programming)',value.split(':',1)[0].strip(),re.I):value=value.split(':',1)[1].strip()
            flat.extend(piece.strip() for piece in re.split(r'[,;|\n]',value) if piece.strip())
        data.skills.all_skills=list(dict.fromkeys(data.skills.technical_skills+data.skills.tools_and_platforms+data.skills.domain_and_functional+data.skills.soft_skills+flat))
        for field in type(data.skills).model_fields:
            values=getattr(data.skills,field)
            # Dictionary recognition must still have literal evidence in skills.
            values=[value for value in values if supported(value,skill_blocks)]
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
                    role_pattern=r'\b(?:engineer|developer|analyst|consultant|architect|manager|specialist|director|lead)\b'
                    company_pattern=r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies)|solutions|company)\b'
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
                    record=WorkExperience(company=company or '',role=role or '',responsibilities=[b.text for b in refs('responsibilities')])
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
                        i=len(data.certifications);value=canonical(contents).strip();data.certifications.append(Certification(name=value));remember(f'certifications[{i}].name',value,contents)
        for b in blocks('languages'):
            i=len(data.languages);data.languages.append(b.text.strip());remember(f'languages[{i}]',b.text.strip(),[b])
    else:warnings.append('Document scope is non-resume; candidate fields were left empty and source sections retained.')
    missing=['contact.'+f for f in ('full_name','email','phone') if not getattr(data.contact,f)]
    for category,fields in [('experience',('company','role')),('education',('institution','degree')),('projects',('name',)),('certifications',('name',))]:
        for i,record in enumerate(getattr(data,category)):
            missing.extend(f'{category}[{i}].{field}' for field in fields if not getattr(record,field))
    mapping=build_schema_mapping_report(data)
    warnings+=['Schema validity and field completion do not establish extraction or relationship accuracy.',
               'Handoff confidence scores are fixed heuristics, not calibrated probabilities.',
               'Missing required strings use empty strings for handoff compatibility; inspect missing_required_fields.']
    all_blocks=[(s.category,b) for s in request.sections.sections for b in s.blocks]+[(None,b) for b in request.sections.needs_review]
    return ParseResponse(success=True,source=request.source,extraction_mode='existing_blocks_schema_mapping',data=data,schema_mapping=mapping,raw_sections=raw,
        meta={'status':'needs_review','human_verified':False,'provider_calls':0,'source_accounting':accounting,'document_scope':scope,
              'source_inventory_sha256':hashlib.sha256(json.dumps([e.model_dump() for e in request.elements],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
              'field_evidence':evidence,'record_reviews':record_reviews,'missing_required_fields':missing,'warnings':warnings,
              'unmapped_blocks':[{'source_id':source_id(b),'category':category,'text':b.text,'page_number':b.page_number} for category,b in all_blocks if source_id(b) not in used],
              'needs_review':[b.model_dump() for b in request.sections.needs_review]})
