"""Measure the header patch with identical refreshed PDF geometry on both sides."""
import inspect,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from local_api.schemas.sections import SectionRequest,SectionResponse
from local_api.services.resume_sections import build_sections
import local_api.services.resume_structure as structure
p=Path(__file__).resolve().parent;run=p/'source-geometry-repair'
original=structure.reviewed_employment_groups
source=inspect.getsource(original)
baseline=source.replace(' or dated_organization_header(text)','').replace(r'job\s+role\s*:|','')
assert baseline!=source
namespace=dict(vars(structure));exec(compile(baseline,'<pre-header-fix-control>','exec'),namespace);control=namespace['reviewed_employment_groups']
def count(sections):
 total=0
 for sec in sections:
  if sec.category!='experience':continue
  owned={i for e in sec.entries for i in e.block_indices}
  total+=sum(i not in owned and any(c.isalnum() for c in b.text) and b.assignment not in {'section_heading','structural_heading'} for i,b in enumerate(sec.blocks))
 return total
rows=[]
try:
 for record in json.loads((run/'per-document.json').read_text()):
  a=json.loads((run/record['artifact']).read_text());req=SectionRequest(elements=a['extraction']['elements']);res=SectionResponse.model_validate(a['repaired_sections']);grouped={s.category:s.blocks for s in res.sections}
  structure.reviewed_employment_groups=control;before=build_sections(grouped,req.elements)
  structure.reviewed_employment_groups=original;after=build_sections(grouped,req.elements)
  rows.append({'file':record['file'],'control_unlinked_employment_blocks':count(before),'fixed_unlinked_employment_blocks':count(after)})
finally:structure.reviewed_employment_groups=original
summary={'documents':len(rows),'control_unlinked_employment_blocks':sum(r['control_unlinked_employment_blocks'] for r in rows),'fixed_unlinked_employment_blocks':sum(r['fixed_unlinked_employment_blocks'] for r in rows),'same_source_geometry_on_both_sides':True,'documents_with_increased_unlinked_employment_blocks':[r['file'] for r in rows if r['fixed_unlinked_employment_blocks']>r['control_unlinked_employment_blocks']],'rows':rows}
(p/'isolated-header-effect.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
