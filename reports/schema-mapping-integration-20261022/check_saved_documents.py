"""Offline compatibility check against the current 350 artifact index."""
import json,socket,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.vendor.handoff_schema.models import ParseResponse
p=Path(__file__).resolve().parent;out=p/'mapped-documents-final';out.mkdir(exist_ok=False)
def deny(*args,**kwargs):raise RuntimeError('Offline mapping check forbids network')
socket.socket.connect=deny;socket.create_connection=deny
# Reconstruct latest live provenance from available batches; earlier composite
# repair reports have been removed from this checkout and are not recreated.
latest={}
for run in sorted((ROOT/'reports').iterdir()):
 manifest=run/'manifest.json';results=run/'deepseek/current-results.json'
 if not manifest.is_file() or not results.is_file():continue
 m=json.loads(manifest.read_text())
 if m.get('run_kind')=='offline_replay' or run.name in {'pilot100-fixed-llm-20261021-041000','structural-grouping-fix-20261021-051500'}:continue
 stamp=m.get('review_completed_utc',m.get('created_utc',''))
 selected={r['file']:r for r in m.get('selected',[])}
 for r in json.loads(results.read_text()):
  if r['file'] not in selected or not r.get('artifact'):continue
  path=run/'deepseek'/r['artifact'];digest=selected[r['file']]['sha256']
  if digest not in latest or stamp>latest[digest][0]:latest[digest]=(stamp,{'file':r['file'],'sha256':digest,'artifact':str(path),'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'section_response_key':'reviewed_sections','source_elements_key':'extraction.elements'})
index=[row for stamp,row in latest.values()];assert len(index)==350,len(index)
(p/'validation-source-index.json').write_text(json.dumps(index,indent=2)+'\n');rows=[]
for row in index:
 path=Path(row['artifact']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['artifact_sha256']
 artifact=json.loads(path.read_text());key=row.get('section_response_key','repaired_sections');source_key=row.get('source_elements_key','extraction.elements')
 elements=artifact['source_elements'] if source_key=='source_elements' else artifact['extraction']['elements']
 req=SchemaMappingRequest(elements=elements,sections=artifact[key],source=row['file']);before=req.model_dump_json();mapped=map_schema(req);assert before==req.model_dump_json();ParseResponse.model_validate(mapped.model_dump())
 assert mapped.meta['provider_calls']==0
 if mapped.meta['document_scope']['candidate_resume'] is not False:
  for category in ('experience','education'):
   section=next((s for s in req.sections.sections if s.category==category),None)
   assert len(getattr(mapped.data,category))==(len(section.entries) if section else 0)
 (out/(row['sha256']+'.json')).write_text(mapped.model_dump_json(indent=2)+'\n')
 rows.append({'file':row['file'],'sha256':row['sha256'],'valid_schema':True,'missing_required_fields':mapped.meta['missing_required_fields'],'document_scope':mapped.meta['document_scope']['kind'],'human_verified':False,'provider_calls':0})
summary={'documents':len(rows),'valid_schema_responses':sum(r['valid_schema'] for r in rows),'source_input_mutations':0,'record_boundary_checks_passed':True,'provider_calls':0,'documents_missing_required_fields':sum(bool(r['missing_required_fields']) for r in rows),'semantic_accuracy_established':False}
(p/'saved-document-results-final.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'saved-document-summary-final.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
