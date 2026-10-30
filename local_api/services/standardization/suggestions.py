"""Auditable spelling suggestions, without changing source assertions."""
import re
from local_api.services.standardization.dictionaries import OCR_AND_SPELLING_CORRECTIONS
from local_api.services.standardization.contracts import StandardizationWarning


def spelling_suggestions(data):
    warnings=[]
    def visit(value,path):
        if isinstance(value,dict):
            for key,item in value.items():visit(item,f'{path}.{key}' if path else key)
        elif isinstance(value,list):
            for i,item in enumerate(value):visit(item,f'{path}[{i}]')
        elif isinstance(value,str) and not any(k in path for k in ('email','phone','url')):
            proposed=value
            for mistake,fix in OCR_AND_SPELLING_CORRECTIONS.items():
                proposed=re.sub(r'\b'+re.escape(mistake)+r'\b',lambda _:fix,proposed,flags=re.I)
            if proposed!=value:
                warnings.append(StandardizationWarning(field=path,warning_type='possible_spelling_error',
                    severity='review_required',original_value=value,normalized_value=value,
                    suggested_value=proposed,basis='Local curated spelling/alias dictionary; no external identity or geographic verification.',
                    applied=False,message='Possible spelling or naming variant. Review the suggested value against the original source.'))
    visit(data,'')
    # Document-local consensus can suggest a spelling variant, never prove geography.
    from collections import Counter
    from difflib import SequenceMatcher
    locations = [('contact.location',data.get('contact',{}).get('location'))]
    locations += [(f'experience[{i}].location',r.get('location')) for i,r in enumerate(data.get('experience',[]))]
    counts=Counter(v.strip() for _,v in locations if isinstance(v,str) and v.strip())
    for path,value in locations:
        if not isinstance(value,str) or not value.strip() or counts[value.strip()] != 1:
            continue
        candidates=[v for v,count in counts.items() if count>=2 and v.casefold()!=value.strip().casefold()
                    and SequenceMatcher(None,v.casefold(),value.strip().casefold()).ratio()>=0.88]
        if len(candidates)==1:
            warnings.append(StandardizationWarning(field=path,warning_type='possible_location_spelling_variant',
                severity='review_required',original_value=value,normalized_value=value,suggested_value=candidates[0],
                basis=f'Similar location occurs {counts[candidates[0]]} times in this document; not geographic verification.',
                applied=False,message='Possible inconsistent location spelling; source value retained pending review.'))
    return warnings
