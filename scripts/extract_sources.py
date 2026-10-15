#!/usr/bin/env python3
"""Rebuild vendored sources from an already extracted supplied archive.

Usage: python scripts/extract_sources.py /path/to/unstructured-main
The original archive must be extracted first (python -m zipfile -e archive.zip .upstream).
"""
import sys
from pathlib import Path
base = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]).resolve()
import ast,json,re,shutil,hashlib
seen=set(); queue=['unstructured.partition.pdf']; external=set()
def path(m):
 p=root.joinpath(*m.split('.'))
 return p.with_suffix('.py') if p.with_suffix('.py').exists() else p/'__init__.py'
while queue:
 m=queue.pop()
 if m in seen or not path(m).is_file(): continue
 seen.add(m)
 for i in range(1,len(m.split('.'))):queue.append('.'.join(m.split('.')[:i]))
 for n in ast.walk(ast.parse(path(m).read_text())):
  names=[]
  if isinstance(n,ast.Import):names=[a.name for a in n.names]
  if isinstance(n,ast.ImportFrom) and n.module:
   names=[n.module]+[n.module+'.'+a.name for a in n.names]
  for name in names:
   if name=='unstructured' or name.startswith('unstructured.'):queue.append(name)
   else:external.add(name.split('.')[0])

src=root/'unstructured'; dst=base/'src/pdf_hires/_vendor'
mods=sorted(seen)
# Dynamic OCR modules are not discoverable through static imports.
mods += ['unstructured.partition.utils.ocr_models.'+p.stem for p in (src/'partition/utils/ocr_models').glob('*.py')]
manifest=[]
for m in sorted(set(mods)):
 p=root.joinpath(*m.split('.')); p=p.with_suffix('.py') if p.with_suffix('.py').exists() else p/'__init__.py'
 if not p.is_file():continue
 rel=p.relative_to(src); dest=dst/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 original=p.read_text(); changed=re.sub(r'\bunstructured\.(?!io\b)',lambda mt:'pdf_hires._vendor.',original)
 # Fix distribution names and domain URLs that are not Python module names.
 changed=changed.replace('pdf_hires._vendor-inference','unstructured-inference').replace('pdf_hires._vendor-client','unstructured-client').replace('pdf_hires._vendor-pytesseract','unstructured-pytesseract')
 changed=changed.replace('from unstructured import ', 'from pdf_hires._vendor import ')
 dest.write_text(changed)
 manifest.append({'source':str(p.relative_to(root)),'target':str(dest.relative_to(base)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for p in src.rglob('*'):
 if p.is_file() and p.suffix!='.py' and '__pycache__' not in p.parts:
  rel=p.relative_to(src)
  if (dst/rel).parent.exists():shutil.copy2(p,dst/rel)
for n in ['LICENSE','NOTICE']:
 if (root/n).exists():shutil.copy2(root/n,base/n)
(base/'docs/source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Copied',len(manifest),'modules')

b=base;v=dst
def remove_functions(rel,names):
 p=v/rel;s=p.read_text();lines=s.splitlines(keepends=True); edits=[]
 for n in ast.parse(s).body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names:
   start=min([n.lineno]+[d.lineno for d in n.decorator_list])-1;edits.append((start,n.end_lineno))
 for a,z in sorted(edits,reverse=True):del lines[a:z]
 p.write_text(''.join(lines))
remove_functions('partition/text.py',{'partition_text','_split_by_paragraph'})
remove_functions('staging/base.py',{'create_file_from_elements'})
for rel in ['partition/pdf.py','partition/text.py']:
 p=v/rel;p.write_text(p.read_text().replace('from pdf_hires._vendor.chunking import add_chunking_strategy\n','').replace('@add_chunking_strategy\n',''))
for rel in ['chunking','partition/html']:
 shutil.rmtree(v/rel)
p=b/'docs/source-manifest.json';data=json.loads(p.read_text());data=[x for x in data if (b/x['target']).exists()]
for x in data:
 x['edits']=['Python namespace references: unstructured. → pdf_hires._vendor.']
 if x['source'].endswith('partition/pdf.py'):x['edits'].append('Removed chunking decorator and its import; public API rejects chunking.')
 if x['source'].endswith('partition/text.py'):x['edits'].append('Removed partition_text entry point, paragraph splitter, and chunking import; retained element_from_text and position/classification helpers.')
 if x['source'].endswith('staging/base.py'):x['edits'].append('Removed create_file_from_elements export conversion entry point (only consumer of HTML partitioner).')
p.write_text(json.dumps(data,indent=2)+'\n')

shutil.copy2(root/'LICENSE.md',base/'LICENSE.md')
