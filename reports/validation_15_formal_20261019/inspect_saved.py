"""Read-only source inspection; writes only beside this script. No model/provider imports."""
import json,hashlib,subprocess,csv,re
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
S=json.loads((ROOT/'ground_truth/selected_15_resumes.json').read_text())
BASE=Path('/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for folder in ['ground_truth','.upstream/batch-validation','reports'] for p in (ROOT/folder).rglob('*') if p.is_file() and OUT not in p.parents}
protected.update({str(BASE/s['file']):sha(BASE/s['file']) for s in S})
(OUT/'protected-before.json').write_text(json.dumps(protected,indent=2))
records=[]
for s in S:
 id=Path(s['artifact']).stem;d=OUT/id;d.mkdir(exist_ok=True);pdf=BASE/s['file'];localp=ROOT/'.upstream/batch-validation'/s['artifact'];livep=ROOT/'ground_truth/recovery_pilot/live/documents'/f'{id}.json'
 local=json.loads(localp.read_text());live=json.loads(livep.read_text());els=local['extraction']['elements']
 subprocess.run(['pdftotext','-layout',str(pdf),str(d/'independent.txt')],check=True)
 subprocess.run(['pdftoppm','-scale-to','1500','-png',str(pdf),str(d/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 pages=sorted(d.glob('page-*.png'));canvas=Image.new('RGB',(1500*min(2,len(pages)),(len(pages)+1)//2*1550),'#cccccc');draw=ImageDraw.Draw(canvas)
 for i,p in enumerate(pages):
  im=Image.open(p).convert('RGB');im.thumbnail((1500,1500));x=i%2*1500;y=i//2*1550;canvas.paste(im,(x,y+30));draw.text((x+15,y+8),f"{s['file']} PAGE {i+1}",fill='black')
 canvas.save(d/'all-pages.jpg',quality=90)
 lines=[]
 for i,e in enumerate(els):lines.append(f"ELEMENT {i} PAGE {e.get('page_number')} TYPE {e.get('type')}\n{e['text']}\n")
 (d/'extracted.txt').write_text('\n'.join(lines))
 for label,response in [('local',local['sections']),('recovered',live['reviewed_sections'])]:
  txt=[]
  for sec in response['sections']:
   txt.append('\nSECTION '+sec['category'])
   for b in sec['blocks']:txt.append(json.dumps(b,ensure_ascii=False))
   txt.append('ENTRIES '+json.dumps(sec.get('entries',[]),ensure_ascii=False))
  txt.append('UNASSIGNED '+json.dumps(response.get('needs_review',[]),ensure_ascii=False));(d/(label+'.txt')).write_text('\n'.join(txt))
 ck=json.loads((ROOT/'ground_truth/recovery_pilot/live/checkpoints'/f'{id}.json').read_text())
 r={'file':s['file'],'id':id,'source':str(pdf),'source_sha256':sha(pdf),'selection_hash_match':sha(pdf)==s['sha256'],'copy_hash_match':sha(pdf)==sha(ROOT/'ground_truth/pilot_resumes'/s['file']),'pages_rendered':len(pages),'element_pages':sorted(set(e.get('page_number') for e in els if e.get('page_number'))),'local_path':str(localp.relative_to(ROOT)),'recovered_path':str(livep.relative_to(ROOT)),'extraction_inventory_identical':els==live['extraction']['elements'],'local_inventory_identical':local['sections']==live['local_sections'],'local_unassigned':len(local['sections'].get('needs_review',[])),'recovered_unassigned':len(live['reviewed_sections'].get('needs_review',[])),'recorded_live_calls':ck['api_calls'],'source_reextracted_in_live_run':ck['source_reextracted']}
 records.append(r)
(OUT/'artifact-inventory.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
