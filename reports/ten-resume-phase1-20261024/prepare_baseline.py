"""Snapshot immutable evidence and replay saved field annotation/mapping offline."""
import hashlib,json,os,socket,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).parent;RUN=ROOT/'reports/end-to-end10-preflight-20261024/execution'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def deny(*a,**k):raise AssertionError('Network forbidden in Phase 1 replay')
socket.socket.connect=deny;socket.create_connection=deny
for key in ('DEEPSEEK_API_KEY','OPENAI_API_KEY'):os.environ.pop(key,None)
os.environ['DEEPSEEK_REVIEW_ENABLED']='false'
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.record_relationships import annotate_relationships
from local_api.services.schema_mapping import map_schema
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy

def replay(destination):
 destination.mkdir();result=[]
 selection=json.loads((RUN.parent/'selection-manifest.json').read_text())
 for row in selection['selected']:
  src=RUN/f"{row['index']:02d}";folder=destination/f"{row['index']:02d}";folder.mkdir()
  extraction=json.loads((src/'extraction.json').read_text());elements=[ExtractedElement.model_validate(e) for e in extraction['elements']]
  sections=SectionResponse.model_validate_json((src/'sections.json').read_text())
  ownership=[(s.category,[(e.entry_id,e.block_indices) for e in s.entries]) for s in sections.sections]
  for s in sections.sections:annotate_relationships(s)
  assert ownership==[(s.category,[(e.entry_id,e.block_indices) for e in s.entries]) for s in sections.sections]
  assert not validate_result(elements,sections)
  mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections,source=row['file'])).model_dump(mode='json')
  validate_hierarchy(mapped['section_schemas'],sections)
  save(folder/'sections.json',sections.model_dump(mode='json'));save(folder/'schema.json',mapped)
  result.append({'file':row['file'],'index':row['index'],'source_sha256':row['sha256'],'extraction_sha256':sha(src/'extraction.json'),'frozen_sections_sha256':sha(src/'sections.json'),'source_intervals':'passed','hierarchy':'passed','entry_ownership_unchanged':True})
 save(destination/'summary.json',result)
 return result

def main():
 if (OUT/'protected-before.json').exists():raise ValueError('Preserve existing baseline')
 protected={}
 for folder in [ROOT/'ground_truth',ROOT/'reports',ROOT/'tests/fixtures']:
  for p in folder.rglob('*'):
   if p.is_file() and OUT not in p.parents and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
 for row in json.loads((RUN.parent/'selection-manifest.json').read_text())['selected']:protected[row['source_path']]=sha(Path(row['source_path']))
 save(OUT/'protected-before.json',protected)
 save(OUT/'production-before.json',{str(p):sha(p) for folder in [ROOT/'local_api',ROOT/'scripts',ROOT/'tests'] for p in folder.rglob('*.py')})
 replay(OUT/'before')
if __name__=='__main__':main()
