"""Rebind frozen uN responses by exact source spans when artifacts leave prompts."""
import json
from local_api.services.llm_section_review import source_ledger,parse_decisions


def rebind_saved_decisions(content,original,messages):
    ledger=source_ledger(original);document=json.loads(messages[1]['content'])
    categories=set(document['categories'])
    decisions=parse_decisions(content,len(ledger),categories,{f'u{i}':len(b.text) for i,(b,_) in enumerate(ledger)})
    by_source={(b.source_element_index,b.start,b.end):decisions[f'u{i}'] for i,(b,_) in enumerate(ledger)}
    assignments=[]
    for span in document['spans']:
        parts=by_source[(span['source_element'],span['source_start'],span['source_end'])]
        assignments.extend([span['id'],category,start,end] for start,end,category in parts)
    return json.dumps({'assignments':assignments})
