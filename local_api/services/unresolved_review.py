"""Contextual, read-only evidence for a bounded unresolved-only LLM pass."""


def contextual_groups(elements,blocks):
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.resume_sections import ALIASES
    groups=[]
    for index in sorted({b.source_element_index for b in blocks}):
        preceding=[]
        for i in range(index-1,-1,-1):
            element=elements[i]
            if heading_boundary(element.text,ALIASES)[0] or element.type in {'Title','Header'} and 0<len(element.text.split())<=10:
                preceding.append({'source_element':i,'text':element.text,'page':element.page_number})
                if len(preceding)==2:break
        groups.append({'source_element':index,'original_text':elements[index].text,'preceding_headings':preceding,
                       'neighboring_source':[{'source_element':i,'text':elements[i].text,'page':elements[i].page_number} for i in range(max(0,index-1),min(len(elements),index+2))]})
    return groups


def contextual_messages(messages,elements,blocks):
    import json
    result=[dict(m) for m in messages]
    result[0]['content']+='''
This is a TARGETED SECOND REVIEW, not a repeat of the first classification.
Only the supplied span IDs are editable targets. All other source/context is read-only.
Use the complete original paragraph and preceding heading to interpret wrapped fragments together.
An earlier needs_review decision is an abstention, not evidence that the text is unclassifiable.
Resolve recognizable professional skills, expertise descriptions, career-wide achievements and summaries from context.
Do not infer an employer-specific job from a career-wide capability statement.
Keep genuinely ambiguous/out-of-scope text in needs_review; do not invent missing facts.
You may additionally return abstention_reasons: {span_id: concise source-based reason} for unresolved targets.'''
    document=json.loads(result[1]['content']);document['review_mode']='unresolved_contextual_review'
    document['unresolved_groups']=contextual_groups(elements,blocks)
    document['context_read_only']=True
    result[1]['content']=json.dumps(document,ensure_ascii=False)
    return result
