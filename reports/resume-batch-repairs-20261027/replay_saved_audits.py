"""Replay paid audit responses offline; never calls a provider."""
import json
from copy import deepcopy
from pathlib import Path
from local_api.schemas.sections import SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.review_chunking import audit_plan,audit_decisions
root=Path('reports/resume-batch-10-llm-20261027');out=Path('reports/resume-batch-repairs-20261027')
rows=[]
for number in range(1,11):
    directory=root/f'resume-{number:02d}'
    audit=json.loads((directory/'schema-audit.json').read_text())
    schema=json.loads((directory/'schema.json').read_text())
    sections=SectionResponse.model_validate(json.loads((directory/'sections.json').read_text()))
    elements=[ExtractedElement.model_validate(e) for e in json.loads((directory/'extraction.json').read_text())['elements']]
    plan=audit_plan(elements,sections,schema,ReviewSettings())
    units={u['id']:u for c in plan['chunks'] for u in c['targets']}
    requests=[(p,json.loads(p.read_text())) for p in directory.glob('provider-request-*')]
    row={'resume':number,'original_status':audit['status'],'replayed_chunks':0,'valid_chunks':0,'failure_codes':[]}
    for chunk in audit['coverage']['chunks']:
        matches=[p for p,request in requests if request['messages']==chunk['messages']]
        if not matches:continue
        path=directory/matches[0].name.replace('request','response')
        if not path.exists():continue
        content=json.loads(path.read_text())['content']
        corrected=deepcopy(chunk)
        for unit in corrected['targets']:
            # Resolve actual record keys, retaining precisely the original
            # provider-visible text/citations and checked target IDs.
            if unit['id'] in units:unit['record_key']=units[unit['id']]['record_key']
        row['replayed_chunks']+=1
        try:
            audit_decisions(corrected,content);row['valid_chunks']+=1
        except Exception as exc:
            row['failure_codes'].append(str(exc) if type(exc).__name__=='ChunkError' else type(exc).__name__)
    row['replay_complete']=bool(row['replayed_chunks']) and row['valid_chunks']==row['replayed_chunks'] and row['replayed_chunks']==len(audit['coverage']['chunks'])
    rows.append(row)
(out/'audit-replay.json').write_text(json.dumps({'provider_calls':0,'documents':rows},indent=2)+'\n')
print(json.dumps(rows))
