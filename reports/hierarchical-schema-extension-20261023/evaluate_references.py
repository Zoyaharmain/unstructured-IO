"""Strict saved-block reference agreement, not independent PDF accuracy."""
import json
import re
from pathlib import Path
OUT=Path(__file__).parent
facts=json.loads(Path('reports/deepseek-schema-pilot5-20261022/reference-facts.json').read_text())['facts']
selection=json.loads(Path('reports/deepseek-schema-pilot5-20261022/selection.json').read_text())

def norm(value):
    return ' '.join(re.findall(r'\w+',str(value).casefold()))

results=[]
for fact in facts:
    doc=fact['document']; mapped=json.loads((OUT/f'{doc:02d}'/'mapping.json').read_text())
    parent=fact['collection']; child=fact['field']
    if parent=='root':
        if child.startswith('contact.'):
            parent='personal_information'; child=child.split('.',1)[1]
        elif child=='professional_title': parent='personal_information'
        else: parent='summary'
    parents=[s for s in mapped['section_schemas'] if s['category']==parent]
    records=[r for s in parents for r in s['records']]
    selector=fact.get('selector')
    if selector:
        records=[r for r in records if all(any(norm(v)==norm(i['value']) for a in r['attributes'] if a['name']==k for i in a['items']) for k,v in selector.items())]
    matches=[i for r in records for a in r['attributes'] if a['name']==child for i in a['items'] if norm(i['value'])==norm(fact['expected'])]
    evidence_matches=[i for i in matches if set(fact['source_ids']) & {e['source_id'] for e in i['evidence']}]
    source=json.loads(Path(selection[doc-1]['source_artifact']).read_text())['local_sections']
    correct_parent_ids={f"e{b['source_element_index']}:{b['start']}:{b['end']}" for s in source['sections'] if s['category']==parent for b in s['blocks']}
    status='strict_source_bound_match' if evidence_matches else 'value_match_different_reference_block' if matches else (
        'upstream_parent_assignment_differs' if not correct_parent_ids.intersection(fact['source_ids']) else 'unresolved_or_different_local_field_or_association')
    results.append(dict(fact, hierarchy_parent=parent, hierarchy_child=child, status=status))
summary={'method':'Strict case/punctuation-normalized exact value agreement with the 113 existing AI-authored saved-block reference opportunities; record selectors must match in the same record. No semantic equivalence inference. Not human/PDF verified.',
         'denominator':len(results),'strict_source_bound_matches':sum(r['status']=='strict_source_bound_match' for r in results),
         'value_matches':sum(r['status']in {'strict_source_bound_match','value_match_different_reference_block'} for r in results),
         'upstream_parent_assignment_differences':sum(r['status']=='upstream_parent_assignment_differs' for r in results),
         'human_verified':False,'facts':results}
(OUT/'reference-agreement.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='facts'}))
