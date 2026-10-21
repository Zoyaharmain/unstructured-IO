"""Conservative source-backed resolution of abstentions; never discard source text."""
import re


def document_scope(elements):
    text='\n'.join(e.text for e in elements)
    opening=text[:2500]
    # Require document-purpose evidence, not a filename or an isolated skill.
    if re.search(r'website\s+critique\s+assignment',opening,re.I) and re.search(r'website\s+reviewed\s*:',opening,re.I) and re.search(r'submitted\s+by\s*:',opening,re.I):
        return {'kind':'website_critique','candidate_resume':False,'reason':'Website critique assignment, submitted-by field and reviewed-website field'}
    if re.search(r'(?im)^\s*hiring\s+manager\s*:',opening) and re.search(r'(?im)^\s*open\s+position\s*:\s*\d+',opening) and re.search(r'\bmandatory\b|\bat\s+least\s+\d+\+?\s*year',text,re.I):
        return {'kind':'job_description','candidate_resume':False,'reason':'Hiring-manager field, open-position count and mandatory candidate requirements'}
    if re.search(r'(?im)^\s*detailed\s+critique\s+on\s+.{1,100}\bwebsite\b',opening) and re.search(r'upon\s+reviewing\s+the\s+website',opening,re.I):
        return {'kind':'website_critique','candidate_resume':False,'reason':'Explicit website-critique title and document-purpose statement'}
    if re.search(r'(?im)^\s*.{0,60}interview\s+preparation\s+guide\b',opening) and re.search(r'purpose\s+of\s+this\s+document|this\s+guide\s+is\s+meant',text,re.I):
        return {'kind':'interview_preparation_guide','candidate_resume':False,'reason':'Explicit preparation-guide heading and document-purpose statement'}
    if re.search(r'\b(?:I|we)\s+(?:need|require|are\s+looking\s+for)\b.{0,100}\b(?:resources|candidates|developers)\b',opening,re.I|re.S) and re.search(r'\b(?:below\s+defined\s+JD|job\s+description)\b',opening,re.I):
        return {'kind':'job_description','candidate_resume':False,'reason':'Explicit hiring request and job-description declaration, not candidate history'}
    blank_fields=re.findall(r'(?im)^\s*[^\n:]{2,90}:?\s*\*\s*$',text)
    requirements=bool(re.search(r'education\s+and\s+work\s+experience\s+requirements',text,re.I))
    mandatory=bool(re.search(r'mandatory\s+skills',text,re.I))
    if requirements and mandatory and len(blank_fields)>=3:
        return {'kind':'job_requirements','candidate_resume':False,'reason':'Requirements headings and at least three blank starred form fields; not evidence of candidate history'}
    headings={m.group(0).casefold() for m in re.finditer(r'\b(?:education|experience|skills|projects|qualifications|work history)\b',text,re.I)}
    contact=bool(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',opening))
    if contact and len(headings)>=3 and re.search(r'\b(?:19|20)\d{2}\b',text):
        return {'kind':'likely_resume','candidate_resume':True,'reason':'Contact details, multiple resume section families and dated history; provisional scope only','human_verified':False}
    return {'kind':'candidate_or_unknown','candidate_resume':None,'requires_scope_review':True}


def resolve_unassigned(request,result):
    """Resolve only exact combined headings or source-confirmed final declarations.

    All remaining meaningful content retains needs_review and an explicit reason.
    The input is a fresh candidate copy owned by the reviewer, not a saved artifact.
    """
    from local_api.services.resume_sections import build_sections
    elements=request.elements;scope=document_scope(elements);result.metadata['document_scope']=scope
    if scope['candidate_resume'] is False:
        result.metadata['candidate_sections_are_applicable']=False
        warning=f"Source scope is {scope['kind']}. Retained section proposals are not candidate employment or earned education; document scope needs explicit review."
        if warning not in result.warnings:result.warnings.append(warning)
    grouped={s.category:list(s.blocks) for s in result.sections};remaining=[];events=[]
    declarations=[]
    for i,e in enumerate(elements):
        if re.fullmatch(r'\s*declaration\s*:?\s*',e.text,re.I) and i+1<len(elements) and re.search(r'\bI\s+(?:do\s+)?hereby\s+declare\b',elements[i+1].text,re.I):
            declarations.append(i)
    for b in result.needs_review:
        target=None;parts=None;reason=None
        combined=re.fullmatch(r'\s*(awards|certifications)\s*(&|and)\s*(awards|certifications)\s*:?\s*',b.text,re.I)
        if scope['candidate_resume'] is not False and combined and combined[1].lower()!=combined[3].lower() and all(k in grouped for k in ('awards','certifications')):
            cut=combined.start(3);parts=[(0,cut,combined[1].lower()),(cut,len(b.text),combined[3].lower())];reason='Exact combined heading; both section families have assigned source content'
        elif scope['candidate_resume'] is not False:
            for start in declarations:
                if not start<=b.source_element_index<=start+3:continue
                e=elements[b.source_element_index]
                if e.page_number!=elements[start].page_number:continue
                if b.source_element_index==start or b.source_element_index==start+1 or re.match(r'^\s*(?:place|date|signature)\s*:?\s*',e.text,re.I):
                    target='personal_information';reason='Explicit declaration and adjacent sign-off on the same source page';break
        if target:parts=[(0,len(b.text),target)]
        if parts:
            for start,end,category in parts:
                new=b.model_copy(update={'start':b.start+start,'end':b.start+end,'text':b.text[start:end],
                    'assignment':'structural_heading' if combined else 'source_backed_recovery',
                    'reason':reason,'llm_action':'abstained_then_source_backed_recovery'})
                grouped.setdefault(category,[]).append(new)
                events.append({'source_id':f'e{new.source_element_index}:{new.start}:{new.end}','category':category,'reason':reason})
        else:remaining.append(b)
    if events:
        for group in grouped.values():group.sort(key=lambda b:(b.source_element_index,b.start,b.end))
        result.sections=build_sections(grouped,elements)
    result.needs_review=remaining
    result.metadata['deterministic_review_resolution']=result.metadata.get('deterministic_review_resolution',[])+events
    result.metadata['unresolved_details']=[{'source_id':f'e{b.source_element_index}:{b.start}:{b.end}',
        'text':b.text,'page':b.page_number,'classification':'UNKNOWN',
        'reason':'out_of_scope_'+scope['kind'] if scope['candidate_resume'] is False else 'provider_abstained_no_supported_section'}
        for b in remaining if b.text.strip()]
    return result
