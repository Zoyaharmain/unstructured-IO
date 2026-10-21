"""Structure-led boundaries inspired by knowledge-graph-resume, independently implemented.

Keep source offsets authoritative. Formatting normalization is lookup-only; never
normalize, deduplicate, reconstruct names, or regenerate the returned source text.
"""
import re


def word_safe_cut(text, cut):
    """Move a mechanical tokenizer/geometry cut past an ordinary word.

    Preserve explicit camel-case boundaries in joined headings. Offsets and all
    characters remain source based; this never inserts or normalizes text.
    """
    if 0 < cut < len(text) and text[cut-1].isalnum() and text[cut].isalnum():
        if text[cut-1].islower() and text[cut].isupper():
            left=right=cut
            while left>0 and text[left-1].isalnum():left-=1
            while right<len(text) and text[right].isalnum():right+=1
            heading_tokens={re.sub(r'\W','',name).casefold() for names in EXTRA_HEADINGS.values() for name in names}
            heading_tokens.update({'professionalsummary','technicalskills','workexperience','personalinformation'})
            if text[left:right].casefold() in heading_tokens:return cut
        while cut < len(text) and text[cut].isalnum():
            cut += 1
    return cut

# Record fields must not change the owning section, even when their values look
# like another section (a project's tools are still part of that project).
RECORD_FIELDS = {'technologies', 'technology', 'tools', 'tool', 'tech stack',
                 'description', 'project description', 'project title', 'project name',
                 'role', 'job title', 'designation', 'client', 'duration', 'period',
                 'achievement', 'accomplishment'}
EXTRA_HEADINGS = {
    'personal_information': ['contact', 'personal info'],
    'summary': ['objective', 'career summary', 'executive summary', 'profile snapshot', 'profile summary'],
    'projects': ['key projects', 'project highlights'],
    'experience': ['employment', 'professional background', 'work history'],
    'education': ['qualifications', 'educational background'],
    'skills': ['skill set', 'skill sets', 'skillset', 'key strengths', 'technical competencies', 'core skills', 'domain expertise', 'business analysis and product management', 'tools and technology'],
    'certifications': ['certificates', 'training'],
}


def normalized_heading(text):
    value = text.strip()
    value = re.sub(r'^\s*(?:\d+[.)]|[•▪●*#])\s*', '', value)
    value = value.strip(' |–—_-:.\t\r\n')
    if re.fullmatch(r'(?:[A-Za-z]\s+){2,}[A-Za-z]', value):
        value = re.sub(r'\s+', '', value)
    return ' '.join(value.casefold().replace('&', ' and ').split())


def heading_aliases(anchors):
    return {normalized_heading(text): category for category, anchor in anchors.items()
            for text in anchor['headings'] + EXTRA_HEADINGS.get(category, [])}


def heading_boundary(text, aliases):
    """Return (category, exact split offset or None) for explicit heading syntax."""
    normalized = normalized_heading(text)
    if normalized in RECORD_FIELDS:
        return None, None
    category = aliases.get(normalized)
    if category:
        return category, None
    if ':' in text:
        prefix, body = text.split(':', 1)
        # Numbered Project: is an entry, not a new section.
        if normalized_heading(prefix) in RECORD_FIELDS or re.match(r'^\s*\d+[.)]\s*project\s*$', prefix, re.I):
            return None, None
        category = aliases.get(normalized_heading(prefix))
        if category and body.strip():
            return category, text.index(':') + 1
    # PDF partitioning may flatten a heading and its first paragraph into one
    # element (the requested repository's sample PDFs exhibit this). Restrict
    # recovery to an exact, capitalized leading heading and a capitalized value;
    # never search body substrings such as "experience building services".
    for alias, owner in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in RECORD_FIELDS:
            continue
        pattern = r'^\s*(' + r'\s+'.join(re.escape(word) for word in alias.split()) + r')\s+(?=[A-Z0-9])'
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            prefix = match.group(1)
            remainder = text[match.end():]
            if prefix[0].isupper() and remainder and (remainder[0].isupper() or remainder[0].isdigit()):
                return owner, match.end()
    return None, None


def entry_groups(blocks, category, elements):
    """Reference existing spans, separating explicit entries within each lane/context.

    These are structural proposals, not invented company/degree records. Without
    a visible entry boundary, retain one group rather than guess from similarity.
    """
    if category=='experience' and blocks and all(b.reviewed_by_llm for b in blocks):
        geometry_groups=reviewed_employment_groups(blocks,elements)
        if geometry_groups:return geometry_groups
    if category=='education' and blocks and all(b.reviewed_by_llm for b in blocks):
        geometry_groups=reviewed_education_groups(blocks,elements)
        if geometry_groups:return geometry_groups
    groups, active = [], {}
    for index, block in enumerate(blocks):
        key = (block.lane, None if block.reviewed_by_llm else block.context_source_element_index)
        if block.assignment in {'section_heading', 'structural_heading'}:
            # Heading is a section member but not a job/project entry.
            active = {key_: value for key_, value in active.items() if key_[0] != block.lane}
            continue
        text = block.text.strip()
        if not re.search(r'[A-Za-z0-9]', text):
            # Non-alphanumeric token (bullet, comma) does not create a standalone entry
            if active:
                first_active = next(iter(active.values()))
                first_active['block_indices'].append(index)
            continue
        element = elements[block.source_element_index]
        explicit_title = (element.type == 'Title' and block.start == 0 and
                          0 < len(text.split()) <= 18 and not re.match(r'^[•▪●*\-]', text))
        labeled_entry = bool(re.match(r'^\s*(?:\d+[.)]\s*)?(?:project(?: name| title)?|company|employer|institution)\s*:', text, re.I))
        if block.reviewed_by_llm:
            # A title detector's field labels and embedded project titles are not
            # employer boundaries after semantic reassignment to Experience.
            if category=='experience':
                explicit_title=employment_start(text)
                labeled_entry=bool(re.match(r'^\s*(?:company|employer)\s*:\s*\S',text,re.I))
            elif category=='education':
                explicit_title=explicit_title and bool(re.search(r'\b(?:university|college|institute|bachelor|master|diploma|phd|bsc|msc|b\.?tech|m\.?tech)\b',text,re.I))
                labeled_entry=bool(re.match(r'^\s*(?:institution|university|college)\s*:\s*\S',text,re.I))
        dated_header = bool(category in {'experience', 'education'} and len(text.split()) <= 24
                            and re.search(r'\b(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:(?:19|20)\d{2}|present|current)\b', text, re.I)
                            and not re.match(r'^[•▪●*\-]', text))
        boundary = category in {'experience', 'projects', 'education'} and (explicit_title or labeled_entry or dated_header)
        if key not in active or boundary:
            group = {'entry_id': f'{category}-{len(groups) + 1}', 'block_indices': [],
                     'lane': block.lane, 'boundary_reason': 'explicit entry title or dated header' if boundary else 'section continuation; no explicit entry boundary'}
            groups.append(group)
            active[key] = group
        active[key]['block_indices'].append(index)
    if category in {'experience','education'} and any(b.reviewed_by_llm for b in blocks):
        groups = attach_aligned_dates(groups, blocks, elements)
    return groups


def attach_aligned_dates(groups, blocks, elements):
    """Attach date-only fragments only with an unambiguous same-row source match.

    Lanes are layout evidence, not record identities. Do not use source order to
    guess a distant date's owner. Leave ambiguous and unlocated dates unchanged.
    """
    def row(block):
        hints=elements[block.source_element_index].metadata.get('pdf_source_lines',[])
        candidates=[h for h in hints if len(h.get('bbox',[]))==4 and
                    min(block.end,h.get('end',0))>max(block.start,h.get('start',0))]
        if not candidates:return None
        # A multi-line body cannot establish a unique header row.
        centers=[(h['bbox'][1]+h['bbox'][3])/2 for h in candidates]
        if max(centers)-min(centers)>.015:return None
        return sum(centers)/len(centers)
    def date_only(text):
        return bool(re.search(r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s*[\'‘’]?\d{2}\b',text,re.I)) and not re.sub(
            r'(?i)\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|present|current|to|since|till)\b|[\d\s.,/|:–—\-\'‘’()]','',text)
    membership={i:g for g in groups for i in g['block_indices']}
    for index,block in enumerate(blocks):
        if not block.reviewed_by_llm or index not in membership or not date_only(block.text):continue
        y=row(block)
        if y is None:continue
        candidates=[]
        for other_index,other in enumerate(blocks):
            if other_index not in membership or other.page_number!=block.page_number or date_only(other.text):continue
            if len(other.text.strip())<4:continue
            other_y=row(other)
            if other_y is not None and abs(other_y-y)<=.006:
                candidates.append(membership[other_index])
        unique={id(g):g for g in candidates}
        if len(unique)!=1:continue
        target=next(iter(unique.values()));old=membership[index]
        if target is old:continue
        old['block_indices'].remove(index);target['block_indices'].append(index)
        target['block_indices'].sort();membership[index]=target
        target['boundary_reason']='source-aligned date attached across layout lanes; other associations remain proposals'
    result=[g for g in groups if g['block_indices']]
    for i,g in enumerate(result):g['entry_id']=f"{g['entry_id'].rsplit('-',1)[0]}-{i+1}"
    return result


def reviewed_employment_groups(blocks,elements):
    """Use visible employment headers as anchors, independent of layout lanes.

    This returns source-membership proposals, never invented fields. If source
    typography cannot establish anchors, retain the existing fallback grouping.
    """
    role=re.compile(r'\b(?:engineer|developer|analyst|associate|consultant|manager|architect|intern|specialist|director|officer|executive|practitioner|lead|administrator)\b',re.I)
    business=re.compile(r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies|ie)|solutions)\b',re.I)
    date_pat=re.compile(r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\s*[‘’\']?\d{2}',re.I)
    def hints(b):
        return [h for h in elements[b.source_element_index].metadata.get('pdf_source_lines',[]) if
                len(h.get('bbox',[]))==4 and min(b.end,h.get('end',0))>max(b.start,h.get('start',0))]
    def y(b):
        hs=hints(b)
        return min((h['bbox'][1] for h in hs),default=None)
    from local_api.services.record_relationships import dated_organization_header
    anchors=[]
    for i,b in enumerate(blocks):
        text=b.text.strip();hs=hints(b)
        if len(text.split())>30 or re.match(r'^(?:job\s+role\s*:|[•▪●*]|projects?\s*[:\-]|projects?\s+(?:name|title|description|summary)\b|client\s*[:\-]|responsibilit)',text,re.I):continue
        bold=any(h.get('bold') for h in hs)
        dated_history=bool(re.match(r'^(?:Since|From)\b.+\bwith\b.+\bas\b',text,re.I) and re.search(r'\b(?:19|20)\d{2}\b',text))
        top=y(b)
        aligned_date=False
        if not bold and not employment_start(text) and (role.search(text) or business.search(text)) and len(text.split())<=18:
            for other in blocks:
                if other.page_number==b.page_number and date_pat.search(other.text) and len(other.text.split())<=10:
                    other_top=y(other)
                    if other_top is not None and top is not None and abs(other_top-top)<=.025:
                        aligned_date=True
                        break
        if not (((role.search(text) or business.search(text)) and (bold or employment_start(text) or aligned_date)) or (bold and dated_history) or dated_organization_header(text)):continue
        # Employer and title can occupy two adjacent source rows. Merge a
        # title-only continuation with the immediately preceding employer row.
        if anchors and top is not None and anchors[-1]['page']==b.page_number and anchors[-1]['y'] is not None and 0<=top-anchors[-1]['y']<=.03 and (
            (role.search(text) and not business.search(text) and not re.search(r'\d|[,|]',text)) or
            (business.search(text) and not role.search(text) and not re.search(r'\d|[,|]',text))
        ):
            continue
        anchors.append({'index':i,'page':b.page_number,'y':top})
    if not anchors:return []
    groups=[{'entry_id':f'experience-{i+1}','block_indices':[],'lane':'source_geometry','boundary_reason':'source employment header; source row/page membership, not layout lane'} for i in range(len(anchors))]
    shared_from=None
    for i,b in enumerate(blocks):
        if not re.fullmatch(r'\s*(?:accomplishments|career highlights|selected career highlights|key achievements)\s*:?\s*',b.text,re.I):continue
        previous=[a for a in anchors if a['index']<i]
        if len(previous)<2:continue
        between=blocks[previous[-2]['index']:i]
        if not any(len(part.text.split())>30 or re.match(r'^\s*(?:[•▪●*]\s*)?(?:led|built|developed|implemented|managed|configured|responsible)\b',part.text,re.I) for part in between):
            shared_from=i
            break
    for i,b in enumerate(blocks):
        if not re.search(r'[A-Za-z0-9]',b.text) or normalized_heading(b.text) in {'experience','work experience','professional experience','employment','work history'}:continue
        if shared_from is not None and i>=shared_from and not any(shared_from<=a['index']<=i for a in anchors):
            # A shared career-accomplishments list after several history-only
            # headers cannot be attributed to the last employer without evidence.
            continue
        top=y(b);eligible=[]
        for j,a in enumerate(anchors):
            if top is not None and a['y'] is not None and b.page_number is not None and a['page'] is not None:
                if a['page']<b.page_number or (a['page']==b.page_number and a['y']<=top+.006):eligible.append((a['page'],a['y'],j))
            elif a['index']<=i:eligible.append((0,a['index'],j))
        if not eligible:
            # Career-wide highlights preceding employment are section content,
            # not evidence of responsibilities for the first job.
            continue
        best=max(eligible)
        competitors=[a for a in eligible if a[0]==best[0] and abs(a[1]-best[1])<.008]
        if len(competitors)>1:
            # Simultaneous column anchors need explicit ownership; source order
            # or mere proximity cannot establish which employer owns the field.
            if i not in [anchors[a[2]]['index'] for a in competitors]:continue
            owner=next(a[2] for a in competitors if anchors[a[2]]['index']==i)
        else:owner=best[2]
        groups[owner]['block_indices'].append(i)
    return [g for g in groups if g['block_indices']]


def reviewed_education_groups(blocks,elements):
    """Link source rows to visible qualification anchors; preserve uncertainty.

    No inferred degree, institution, date or grade is generated. Geometry is
    required, and multi-qualification blocks remain unsplit source proposals.
    """
    from local_api.services.record_relationships import degree_families,field_kinds
    rows={}
    for i,b in enumerate(blocks):
        hs=[h for h in elements[b.source_element_index].metadata.get('pdf_source_lines',[]) if len(h.get('bbox',[]))==4 and min(b.end,h.get('end',0))>max(b.start,h.get('start',0))]
        if not hs:continue
        # Multi-line text cannot establish a precise row relation here.
        tops=[h['bbox'][1] for h in hs]
        if max(tops)-min(tops)>.025:continue
        rows[i]=(sum(tops)/len(tops),min(h['bbox'][0] for h in hs))
    anchors=[i for i,b in enumerate(blocks) if i in rows and (len(degree_families(b.text))==1 or (len(degree_families(b.text))==2 and len(b.text.split())<=6)) and len(b.text.split())<=30 and normalized_heading(b.text) not in {'qualification','qualifications','education','academic credentials','academic profile'}]
    if not anchors:return []
    # Several source spans may be words on the very same qualification row.
    unique=[]
    for i in anchors:
        if not any(blocks[j].page_number==blocks[i].page_number and abs(rows[j][0]-rows[i][0])<.006 and abs(rows[j][1]-rows[i][1])<.25 for j in unique):unique.append(i)
    anchors=unique
    groups=[{'entry_id':f'education-{i+1}','block_indices':[],'lane':'source_geometry','boundary_reason':'visible qualification anchor and nearby source rows; field values remain unverified'} for i in range(len(anchors))]
    for i,b in enumerate(blocks):
        if not re.search(r'[A-Za-z0-9]',b.text) or normalized_heading(b.text) in {'education','qualifications','academic credentials','educational background','qualification','college/university/institution','academic profile'}:continue
        candidates=[]
        if i in rows:
            top,x=rows[i]
            for group_index,a in enumerate(anchors):
                if blocks[a].page_number!=b.page_number:continue
                ay,ax=rows[a]
                distance=abs(ay-top)
                semantic=bool(field_kinds(b.text,'education'))
                same_source=b.source_element_index==blocks[a].source_element_index
                same_row=abs(ay-top)<=.008
                aligned=same_row or abs(ax-x)<=.18
                if distance<=.065 and aligned and (same_row or semantic or same_source):
                    candidates.append((0 if same_row else distance,abs(ax-x),group_index))
        if i in anchors:
            owner=anchors.index(i)
        elif candidates:
            candidates.sort();best=candidates[0]
            if len(candidates)>1 and abs(candidates[1][0]-best[0])<.002 and abs(candidates[1][1]-best[1])<.02:
                c1_a=anchors[candidates[0][2]]
                c2_a=anchors[candidates[1][2]]
                if abs(rows[c1_a][0]-rows[c2_a][0])<.008:
                    return [] # True horizontal column ambiguity: leave fallback proposals intact.
            owner=best[2]
        else:
            # Section text stays visible but entry ownership is unestablished.
            # Never attach an unrelated institution/date by source order alone.
            continue
        groups[owner]['block_indices'].append(i)
    return [g for g in groups if g['block_indices']]


def employment_start(text):
    from local_api.vendor.resume_semantic_blocks import PERIOD, employment_header, ACTION, EDUCATION
    lookup=text.strip().lstrip('•▪●*\uf0b7- ').strip()
    if re.match(r'^(?:projects?\s*[:\-]|projects?\s+(?:name|title|description|summary)\b|client\s*[:\-]|duration\s*:|responsibilities\s*:|accomplishments\s*:)',lookup,re.I):return False
    # A dated "Worked as ... at/with ..." statement is a history header,
    # whereas a responsibility mentioning a date is not.
    stated=bool(re.match(r'^(?:working|worked|currently working)\s+as\b.+\b(?:at|with)\b',lookup,re.I))
    date=re.search(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*[‘’']?\d{2,4}",lookup,re.I)
    period=PERIOD.search(lookup)
    raw_prefix=lookup[:(period.start() if period else date.start())] if (period or date) else ''
    prefix=raw_prefix.strip(' |,–—-')
    if not (period or date) or len(lookup.split())>30 or EDUCATION.search(prefix) or (ACTION.search(prefix) and not stated):return False
    business=re.search(r'\b(?:ltd|limited|inc|llc|corp|corporation|systems|services|bank|technolog(?:y|ies|ie)|solutions)\b',prefix,re.I)
    role=re.search(r'\b(?:engineer|developer|analyst|associate|consultant|manager|architect|intern|specialist|director|officer|executive|lead|administrator)\b',prefix,re.I)
    has_delim=bool(re.search(r'[,|–—\-/]',raw_prefix))
    return bool(employment_header(lookup) or business or stated or (role and (has_delim or len(prefix.split())<=4)))
