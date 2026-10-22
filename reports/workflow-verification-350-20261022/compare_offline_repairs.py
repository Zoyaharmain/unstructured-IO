"""Describe offline repair evidence separately from fresh provider verification."""
import json,sys,hashlib
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from local_api.schemas.sections import SectionRequest,SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.source_accounting import account_source
from local_api.services.quality_assessment import assess_quality
OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
base=read(OUT/'per-resume.json');latest={r['sha256']:r for r in base};checks=[]
source=ROOT/'reports/pilot100-additional-llm-20261021-025143'
original={r['file']:r for r in read(source/'deepseek/current-results.json')}
repaired=ROOT/'reports/structural-grouping-fix-20261021-051500'
manifest=read(repaired/'manifest.json');selected={r['file']:r for r in manifest['selected']}
for r in read(repaired/'deepseek/current-results.json'):
 info=selected[r['file']];a=read(repaired/'deepseek'/r['artifact']);o=read(source/'deepseek'/original[r['file']]['artifact'])
 req=SectionRequest(elements=a['extraction']['elements']);sec=SectionResponse.model_validate(a['reviewed_sections'])
 same_source=a['extraction']==o['extraction']
 responsefile=r['id']+'.json'
 replay_decisions=repaired/'deepseek/provider-decisions'/responsefile
 source_decisions=source/'deepseek/provider-decisions'/responsefile
 same_decisions=replay_decisions.read_bytes()==source_decisions.read_bytes()
 errors=validate_result(req.elements,sec)
 mapped=map_schema(SchemaMappingRequest(elements=req.elements,sections=sec,source=r['file']))
 quality=assess_quality(req.elements,sec)
 checks.append({'file':r['file'],'sha256':info['sha256'],'same_source_extraction':same_source,
  'provider_response_files_identical_to_live_source':same_decisions,'interval_errors':errors,
  'provider_state':sec.metadata['llm_review']['status'],'schema_valid':True,
  'missing_required_fields':mapped.meta['missing_required_fields'],
  'meaningful_unassigned':account_source(req.elements,sec)['unresolved_meaningful_spans'],
  'was_failed_in_live':original[r['file']]['llm_review']['status']!='complete'})
summary={'offline_repair_documents':len(checks),'same_extractions':sum(r['same_source_extraction'] for r in checks),
 'identical_recorded_provider_response_files':sum(r['provider_response_files_identical_to_live_source'] for r in checks),
 'interval_checks_passed':sum(not r['interval_errors'] for r in checks),
 'structurally_valid_replays':sum(r['provider_state']=='complete' for r in checks),
 'live_failures_accepted_in_replay':[r['file'] for r in checks if r['was_failed_in_live'] and r['provider_state']=='complete'],
 'repair_scope_meaningful_unassigned':sum(r['meaningful_unassigned'] for r in checks),
 'repair_scope_documents_missing_required_fields':sum(bool(r['missing_required_fields']) for r in checks),
 'new_provider_calls':0,'independent_semantic_accuracy_established':False}
combined_states=Counter(r['provider_state'] for r in base)
for r in checks:
 previous=latest[r['sha256']]
 combined_states[previous['provider_state']]-=1;combined_states[r['provider_state']]+=1
summary['combined_live_plus_replayed_provider_states']=dict(combined_states)
(OUT/'offline-repair-comparison.json').write_text(json.dumps({'summary':summary,'documents':checks},indent=2)+'\n')
print(json.dumps(summary,indent=2))
