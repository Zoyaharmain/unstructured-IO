"""One bounded local resegmentation pass for unresolved, merged source text."""
import re


def recover_sections(request, local_result):
    from local_api.services.resume_sections import ALIASES, get_engine
    updates = {}
    # Strong title-style labels only. Never match lowercase body vocabulary.
    aliases = sorted((a for a in ALIASES if len(a)>=5),key=len,reverse=True)
    for block in local_result.needs_review:
        for alias in aliases:
            pattern = r'(?<![A-Z])' + r'\s*'.join(re.escape(word.capitalize()) for word in alias.split())
            for match in re.finditer(pattern,block.text):
                if match.start()>0 and (match.end()==len(block.text) or not block.text[match.end()].islower()):
                    updates.setdefault(block.source_element_index,set()).update([block.start+match.start(),block.start+match.end()])
    if not updates:
        local_result.metadata['recovery']={'passes':0,'remaining_review_units':len(local_result.needs_review)}
        from local_api.services.quality_assessment import assess_quality
        local_result.metadata['quality_assessment']=assess_quality(request.elements,local_result)
        return local_result
    elements=[]
    for index,element in enumerate(request.elements):
        metadata=dict(element.metadata)
        if index in updates:metadata['recovery_cuts']=sorted(updates[index])
        elements.append(element.model_copy(update={'metadata':metadata}))
    repaired=get_engine().detect(request.model_copy(update={'elements':elements}))
    repaired.metadata['recovery']={'passes':1,'boundary_count':sum(map(len,updates.values())),
        'initial_review_units':len(local_result.needs_review),'remaining_review_units':len(repaired.needs_review)}
    from local_api.services.quality_assessment import assess_quality
    repaired.metadata['quality_assessment']=assess_quality(request.elements,repaired)
    return repaired
