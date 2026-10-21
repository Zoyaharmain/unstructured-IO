"""Rebuild record proposals for every distinct saved live document; no model calls.

Retains extraction and section decisions exactly. New record memberships are
source-supported deterministic proposals, never human-approved corrections.
"""
import argparse,csv,json,sys,hashlib,socket
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_api.schemas.sections import SectionRequest,SectionResponse
from local_api.services.resume_sections import build_sections
from local_api.services.llm_section_review import assert_coverage,source_ledger
from local_api.services.source_accounting import account_source
from local_api.services.quality_assessment import assess_quality
from scripts.batch_check_resumes import validate_result

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(res):
 out={}
 for s in res.sections:
  if s.category not in {'experience','education'}:continue
  owned={i for e in s.entries for i in e.block_indices}
  out[s.category]={'records':len(s.entries),'unlinked_meaningful_blocks':sum(i not in owned and any(c.isalnum() for c in b.text) and b.assignment not in {'section_heading','structural_heading'} for i,b in enumerate(s.blocks)),
   'record_review_reasons':dict(Counter(reason for e in s.entries for reason in e.review_reasons))}
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--refresh-pdf-geometry',action='store_true');a=p.parse_args()
 if a.output.exists():p.error('Output already exists; previous results remain immutable')
 def deny(*args,**kwargs):raise RuntimeError('Offline record repair forbids network calls')
 socket.socket.connect=deny;socket.create_connection=deny
 with a.inventory.open() as f:inventory=list(csv.DictReader(f))
 if len({r['sha256'] for r in inventory})!=len(inventory):raise ValueError('Inventory must contain distinct source hashes')
 a.output.mkdir(parents=True);(a.output/'documents').mkdir()
 rows=[];protected={};cache={}
 for d in inventory:
  run=ROOT/'reports'/d['run']
  if d['run'] not in cache:
   cache[d['run']]={r['file']:r for r in json.loads((run/'deepseek/current-results.json').read_text())}
  row=cache[d['run']][d['file']];src=run/'deepseek'/row['artifact'];protected[str(src)]=sha(src)
  pdf=run/'selected-pdfs'/d['file'];protected[str(pdf)]=sha(pdf)
  if protected[str(pdf)]!=d['sha256']:raise ValueError('PDF hash mismatch')
  artifact=json.loads(src.read_text());req=SectionRequest(elements=artifact['extraction']['elements']);res=SectionResponse.model_validate(artifact['reviewed_sections'])
  before=stats(res)
  if a.refresh_pdf_geometry:
   from local_api.services.pdf_section_layout import annotate_pdf_lines
   annotate_pdf_lines(pdf.read_bytes(),artifact['extraction']['elements'])
   req=SectionRequest(elements=artifact['extraction']['elements'])
  old_ledger=[(b.source_element_index,b.start,b.end,b.text,c) for b,c in source_ledger(res)]
  res.sections=build_sections({s.category:s.blocks for s in res.sections},req.elements)
  assert_coverage(req.elements,source_ledger(res));errors=validate_result(req.elements,res)
  if errors:raise ValueError('Repaired output invariant failure: '+str(errors))
  if old_ledger!=[(b.source_element_index,b.start,b.end,b.text,c) for b,c in source_ledger(res)]:raise ValueError('Record repair changed source text or section decisions')
  res.metadata['source_accounting']=account_source(req.elements,res)
  res.metadata['quality_assessment']=assess_quality(req.elements,res)
  res.metadata['record_repair']={'execution_mode':'offline_saved_section_regrouping','new_api_calls':0,'source_artifact':str(src),'source_artifact_sha256':protected[str(src)],'human_approved':False,'historical_provider_status':row['status']}
  after=stats(res);changed=any(s.entries!=next((o.entries for o in SectionResponse.model_validate(artifact['reviewed_sections']).sections if o.category==s.category),[]) for s in res.sections)
  dest=a.output/'documents'/(d['sha256']+'.json')
  dest.write_text(json.dumps({'file':d['file'],'sha256':d['sha256'],'extraction':artifact['extraction'],'repaired_sections':res.model_dump(),'before':before,'after':after},ensure_ascii=False)+'\n')
  rows.append({'file':d['file'],'sha256':d['sha256'],'historical_live_status':row['status'],'artifact':str(dest.relative_to(a.output)),'records_changed':changed,'before':before,'after':after,'source_intervals_and_labels_unchanged':True,'integrity_errors':errors,'source_fidelity':res.metadata['quality_assessment']['source_fidelity']})
 changed_sources=[name for name,h in protected.items() if sha(Path(name))!=h]
 total=lambda phase,key:sum(category.get(key,0) for row in rows for category in row[phase].values())
 summary={'documents':len(rows),'record_proposals_changed':sum(r['records_changed'] for r in rows),'integrity_checks_passed':len(rows),'section_labels_and_text_unchanged':True,'pdf_geometry_refreshed':a.refresh_pdf_geometry,
  'unlinked_meaningful_blocks_before':total('before','unlinked_meaningful_blocks'),'unlinked_meaningful_blocks_after':total('after','unlinked_meaningful_blocks'),
  'new_api_calls':0,'human_approvals_created':0,'historical_live_statuses':dict(Counter(r['historical_live_status'] for r in rows)),'protected_inputs_checked':len(protected),'protected_inputs_changed':changed_sources,'semantic_accuracy_established':False}
 (a.output/'per-document.json').write_text(json.dumps(rows,indent=2)+'\n');(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
