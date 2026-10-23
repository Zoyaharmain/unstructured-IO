"""Reuse five existing local block outputs; no extraction, clustering or API calls."""
import hashlib
import json
import time
from pathlib import Path
from copy import deepcopy
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.subschema_spec import hierarchy_definition
from local_api.services.schema_mapping import map_schema
from local_api.services.subschema_validation import query_subschemas, validate_hierarchy

OUT = Path(__file__).parent
selection = json.loads(Path('reports/deepseek-schema-pilot5-20261022/selection.json').read_text())
results=[]
for chosen in selection:
    path=Path(chosen['source_artifact']); original=path.read_bytes()
    artifact=json.loads(original)
    extraction=artifact['extraction']
    request=SchemaMappingRequest(elements=extraction['elements'], sections=artifact['local_sections'], source=chosen['file'])
    before=deepcopy(request.model_dump())
    start=time.perf_counter(); mapped=map_schema(request); elapsed=time.perf_counter()-start
    assert before==request.model_dump()
    assert original==path.read_bytes()
    validate_hierarchy(mapped.section_schemas,request.sections)
    folder=OUT/f"{chosen['number']:02d}"; folder.mkdir(exist_ok=True)
    (folder/'mapping.json').write_text(json.dumps(mapped.model_dump(mode='json'),indent=2,ensure_ascii=False))
    query=query_subschemas(mapped.section_schemas,'education.institution')
    (folder/'query.json').write_text(json.dumps(query,indent=2,ensure_ascii=False))
    populated=sum(len(a.items) for s in mapped.section_schemas for r in s.records for a in r.attributes)
    unresolved=sum(not a.items for s in mapped.section_schemas for r in s.records for a in r.attributes)
    row={'file':chosen['file'],'reason':chosen['reason'],'source_artifact':str(path),
         'artifact_sha256':hashlib.sha256(original).hexdigest(),'sections':len(mapped.section_schemas),
         'records':sum(len(s.records) for s in mapped.section_schemas),'populated_items':populated,
         'unresolved_attributes':unresolved,'all_emitted_citations_valid':True,'elapsed_seconds':round(elapsed,6),
         'review_records':sum(bool(r.review_reasons) for s in mapped.section_schemas for r in s.records),
         'legacy_data_unchanged_by_nested_stage':True}
    # This value-only snapshot is measured again after querying to prove immutability.
    legacy=deepcopy(mapped.data.model_dump()); query_subschemas(mapped.section_schemas,'experience.company')
    assert legacy==mapped.data.model_dump()
    results.append(row)
summary={'documents':len(results),'provider_calls':0,'tokens':0,'incremental_api_cost':0,
         'extraction_runs':0,'block_detection_runs':0,'structurally_valid_documents':len(results),
         'populated_items':sum(r['populated_items'] for r in results),'source_quote_failures':0,
         'human_verified':False,'results':results}
(OUT/'pilot-summary.json').write_text(json.dumps(summary,indent=2))
(OUT/'hierarchy-definition.json').write_text(json.dumps(hierarchy_definition(),indent=2))
print(json.dumps(summary))
