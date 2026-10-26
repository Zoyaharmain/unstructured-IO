"""Reproduce this document through extraction, local grouping, and grounded review."""
import json
from pathlib import Path
import sys
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from local_api.core.provider_env import load_provider_env
load_provider_env(ROOT/'.env')
from local_api.services.text_extraction_service import extract_text
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import detect_sections
from local_api.services.section_recovery import recover_sections
from local_api.services.llm_section_review import ReviewSettings,review_sections,call_deepseek
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services.review_chunking import new_budget
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=Path(__file__).parent);args=parser.parse_args()
out=args.output;out.mkdir(parents=True,exist_ok=True)
source=Path('/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT/Abhijit_Dey.docx')
def save(name,value): (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
extraction=extract_text(source.read_bytes(),source.name,'auto');save('extraction.json',extraction.model_dump());print('Extraction',len(extraction.elements),flush=True)
req=SectionRequest(elements=extraction.elements);local=recover_sections(req,detect_sections(req));save('local-sections.json',local.model_dump())
settings=replace(ReviewSettings.from_env(),max_document_requests=8,max_pass_requests=8,max_total_requests=8)
budget=new_budget(settings);calls=[]
def transport(config,messages):
 number=len(calls)+1;calls.append({'call':number,'status':'attempted'});save('provider-calls.json',calls)
 content=call_deepseek(config,messages);save(f'provider-response-{number}.json',{'content':content});calls[-1]['status']='complete';save('provider-calls.json',calls);print('Provider call',number,'completed',flush=True);return content
sections=review_sections(req,local,settings=settings,transport=transport,_budget=budget);save('sections.json',sections.model_dump());print('Section review',sections.metadata.get('llm_review',{}).get('status'),flush=True)
mapped=map_with_field_review(SchemaMappingRequest(elements=req.elements,sections=sections,source=source.name),settings=settings,transport=transport,budget=budget)
save('after.schema.json',mapped.model_dump());print('Field review',mapped.meta.get('field_review'),flush=True);print('Missing required',mapped.meta['missing_required_fields'],flush=True)
