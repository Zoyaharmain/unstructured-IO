"""One bounded local resegmentation pass for unresolved, merged source text."""
import re


def recover_sections(request, local_result):
    from local_api.services.resume_sections import ALIASES, get_engine
    updates = {}
    # Strong title-style or uppercase labels only. Never match lowercase body vocabulary.
    aliases = sorted((a for a in ALIASES if len(a) >= 5), key=len, reverse=True)
    all_blocks = list(local_result.needs_review)
    for section in local_result.sections:
        all_blocks.extend(b for b in section.blocks if len(b.text) > 15)

    for block in all_blocks:
        for alias in aliases:
            # Match both Title Case (e.g. Work Experience) and UPPERCASE (e.g. WORK EXPERIENCE, CONTACT, SKILLS)
            upper_pattern = r'\s*'.join(re.escape(word.upper()) for word in alias.split())
            cap_pattern = r'\s*'.join(re.escape(word.capitalize()) for word in alias.split())
            pattern = r'(?<![A-Za-z])(' + upper_pattern + r'|' + cap_pattern + r')(?![a-z])'
            for match in re.finditer(pattern, block.text):
                if match.start() > 0 and (match.end() == len(block.text) or not block.text[match.end()].islower()):
                    # Avoid cutting inside regular sentences unless preceded by punctuation or boundary
                    prefix = block.text[:match.start()]
                    if (block in local_result.needs_review or
                            prefix.endswith(('.', '!', '?', ';', '\n', '\r', ':')) or
                            (prefix and prefix[-1].islower())):
                        updates.setdefault(block.source_element_index, set()).update(
                            [block.start + match.start(), block.start + match.end()]
                        )
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
