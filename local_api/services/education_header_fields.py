"""Literal qualification title, subject and institution from dated source cards."""
import re

ORG=re.compile(r'(?:[A-Z][A-Za-z.\x27’&-]*\s+){0,5}(?:University|Institute|College|School)(?:\s+of\s+[A-Z][A-Za-z &-]*)?')


def source_education_fields(blocks,elements):
    from local_api.services.education_subfields import DEGREE
    from local_api.services.record_subfields import DATE
    fields={};dated=[b.text.strip() for b in blocks if re.fullmatch(DATE,b.text.strip(),re.I)]
    if len(dated)==1:fields['graduation_year']=dated[0]
    titles=[b for b in blocks if '|' in b.text and (DEGREE.search(b.text.split('|',1)[0]) or b.text.split('|',1)[0].strip().isupper())]
    if len(titles)!=1:return fields
    block=titles[0];left,right=block.text.split('|',1);fields['degree']=left.strip()
    candidates=[]
    # A separate Word run can isolate the institution after an undelimited major.
    for run in elements[block.source_element_index].metadata.get('word_source_runs',[]):
        if run['start']<block.start or run['end']>block.end:continue
        value=elements[block.source_element_index].text[run['start']:run['end']].strip()
        if ORG.fullmatch(value) and not DEGREE.search(value):candidates.append(value)
    if len(set(candidates))==1:institution=candidates[0]
    else:
        candidates=[m.group().strip() for m in ORG.finditer(right) if not DEGREE.search(m.group())]
        institution=candidates[0] if len(set(candidates))==1 else None
    if institution:
        fields['institution']=institution
        subject=right[:right.find(institution)].strip(' |,')
        if subject:fields['field_of_study']=subject
    elif not re.search(r'\b(?:University|Institute|College|School)\b',right):
        fields['field_of_study']=right.strip()
    return fields
