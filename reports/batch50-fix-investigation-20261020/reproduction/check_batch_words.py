import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.batch_check_resumes import offline_environment
offline_environment()
from local_api.services.resume_sections import get_engine
from local_api.services.resume_structure import word_safe_cut
from local_api.schemas.extraction import ExtractedElement
from local_api.services.pdf_section_layout import annotate_pdf_lines
run=Path('reports/pilot-50-review-20261020-batch1');out=Path('reports/batch50-fix-investigation-20261020')
engine=get_engine();rows=[]
names={'Khushal Narain Lulla.pdf','Mukkadala Ramya Pavani.pdf','Prasad PR.pdf','Ravi RS.pdf','SAIPREETHIJUNGA1_3.pdf'}
for f in (run/'local/documents').glob('*.json'):
 d=json.loads(f.read_text())
 if d['file'] not in names:continue
 raw=d['extraction']['elements']
 for e in raw:e['metadata'].pop('pdf_source_lines',None)
 annotate_pdf_lines((run/'selected-pdfs'/d['file']).read_bytes(),raw)
 elements=[ExtractedElement.model_validate(e) for e in raw]
 units,_=engine.units(elements);splits=[]
 for u in units:
  text=elements[u.index].text
  for cut in (u.start,u.end):
   if word_safe_cut(text,cut)!=cut:splits.append({'element':u.index,'cut':cut})
 rows.append({'file':d['file'],'local_units':len(units),'ordinary_internal_word_cuts':splits,'api_calls':0})
(out/'word-cut-checks.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
