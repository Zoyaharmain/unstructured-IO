"""Strict provider contract, structured diagnostics and source-supported cuts."""
import json
from local_api.services.resume_structure import word_safe_cut


def allowed_split_offsets(block, elements=None):
    text=block.text
    allowed={0,len(text)}|{i for i in range(1,len(text)) if word_safe_cut(text,i)==i}
    if elements is not None:
        # PDF source lines may meet without whitespace in partitioned text.
        # A physical line boundary is evidence, not an arbitrary word split.
        for hint in elements[block.source_element_index].metadata.get('pdf_source_lines',[]):
            if len(hint.get('bbox',[]))!=4:continue
            for key in ('start','end'):
                cut=hint.get(key)
                if type(cut)==int and block.start<cut<block.end:allowed.add(cut-block.start)
    return sorted(allowed)


def inspect_assignments(content,count,categories,lengths,texts=None,cuts=None):
    errors=[];decisions={}
    def error(kind,**fields):errors.append({'kind':kind,**fields})
    try:value=json.loads(content)
    except (ValueError,TypeError):return {},[{'kind':'invalid_json'}]
    if not isinstance(value,dict) or not isinstance(value.get('assignments'),list) or (set(value)-{'assignments','type'}) or ('type' in value and value['type']!='json_object'):
        return {},[{'kind':'invalid_schema','expected':'{"assignments":[[id,category],[id,category,start,end]]}'}]
    allowed=set(categories)|{'needs_review'}
    for index,pair in enumerate(value['assignments']):
        if not isinstance(pair,list) or len(pair) not in {2,4}:
            error('invalid_tuple_shape',assignment_index=index);continue
        key,category=pair[:2]
        if not isinstance(key,str) or key not in lengths:
            error('nonexistent_span_id',assignment_index=index);continue
        if not isinstance(category,str) or category not in allowed:
            error('invalid_category_or_tuple_order',id=key,assignment_index=index,expected='[id,category,start,end]');continue
        start,end=(0,lengths[key]) if len(pair)==2 else pair[2:]
        if type(start)!=int or type(end)!=int:
            error('noninteger_offsets',id=key);continue
        if not 0<=start<=end<=lengths[key]:
            error('offset_out_of_range',id=key,start=start,end=end,required_length=lengths[key]);continue
        if start==end and lengths[key]!=0:
            error('empty_segment',id=key,start=start,end=end);continue
        if texts is not None:
            accepted=set(cuts[key]) if cuts is not None else None
            invalid=[v for v in (start,end) if (v not in accepted if accepted is not None else word_safe_cut(texts[key],v)!=v)]
            if invalid:
                error('unsupported_word_boundary',id=key,offsets=invalid,allowed_split_offsets=sorted(accepted) if accepted is not None else [i for i in range(len(texts[key])+1) if word_safe_cut(texts[key],i)==i]);continue
        decisions.setdefault(key,[]).append((start,end,category))
    expected={f'u{i}' for i in range(count)}
    for key in sorted(expected-set(decisions),key=lambda s:int(s[1:])):error('missing_span',id=key,required_length=lengths[key])
    for key,parts in decisions.items():
        parts.sort();cursor=0
        for start,end,_ in parts:
            if start!=cursor:error('gap_or_overlap',id=key,expected_start=cursor,actual_start=start)
            cursor=end
        if cursor!=lengths[key]:error('incomplete_coverage',id=key,covered_end=cursor,required_length=lengths[key])
        if lengths[key]==0 and len(parts)!=1:error('duplicate_empty_span',id=key)
    return decisions,errors
