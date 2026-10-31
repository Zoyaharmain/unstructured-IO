"""Offline local-model replay of saved extracted resumes against a chosen code tree."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Output must be new')
    sys.path.insert(0,str(args.code_root.resolve()))
    from local_api.schemas.sections import SectionRequest
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.resume_sections import get_engine
    from local_api.services.section_recovery import recover_sections
    from local_api.services.contact_sections import recover_contact_sections
    from local_api.services.education_date_recovery import recover_education_dates
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    from local_api.services.source_accounting import account_source
    def blocked(*a,**k): raise RuntimeError('Network forbidden during offline replay')
    socket.socket.connect=blocked;socket.create_connection=blocked
    args.output.mkdir(parents=True)
    engine=get_engine(); rows=[]
    for path in sorted((args.run/'documents').glob('*.json')):
        if path.name.endswith('.schema.json'): continue
        source=json.loads(path.read_text())
        if 'extraction' not in source: continue
        start=time.monotonic()
        request=SectionRequest(elements=source['extraction']['elements'])
        original_elements=[e.model_dump() for e in request.elements]
        detected=engine.detect(request)
        local=recover_sections(request,detected)
        local=recover_contact_sections(recover_education_dates(local,request.elements),request.elements)
        assert not validate_result(request.elements,local)
        mapped=map_schema(SchemaMappingRequest(elements=request.elements,sections=local,source=source['file']))
        assert [e.model_dump() for e in request.elements]==original_elements, 'In-memory extracted input changed'
        section_result=mapped.meta.get('reviewed_sections',local.model_dump())
        from local_api.schemas.sections import SectionResponse
        final=SectionResponse.model_validate(section_result)
        accounting=account_source(request.elements,final)
        record={'file':source['file'],'saved_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'format':Path(source['file']).suffix,'raw_detection_review':len(detected.needs_review),
            'meaningful_unassigned':accounting['unresolved_meaningful_spans'],
            'mapped_responsibilities':sum(len(j.responsibilities) for j in mapped.data.experience),
            'mapped_jobs':len(mapped.data.experience),'mapped_projects':len(mapped.data.projects),
            'mapped_certifications':len(mapped.data.certifications),
            'populated_attributes':sum(bool(a.items) for s in mapped.section_schemas for r in s.records for a in r.attributes),
            'source_preserved':True,'provider_calls':mapped.meta.get('provider_calls',0),
            'seconds':round(time.monotonic()-start,2)}
        rows.append(record)
        artifact={'elements':[e.model_dump() for e in request.elements],'sections':final.model_dump(),
                  'mapping':mapped.model_dump(),'metrics':record}
        (args.output/path.name).write_text(json.dumps(artifact,ensure_ascii=False)+'\n')
        print(json.dumps(record),flush=True)
    summary={'documents':len(rows),'meaningful_unassigned':sum(r['meaningful_unassigned'] for r in rows),
        'mapped_responsibilities':sum(r['mapped_responsibilities'] for r in rows),
        'populated_attributes':sum(r['populated_attributes'] for r in rows),
        'source_preserved':all(r['source_preserved'] for r in rows),'provider_calls':sum(r['provider_calls'] for r in rows),
        'rows':rows,'limitations':'Saved extraction replay using the real pinned local model; does not prove semantic accuracy or re-extract original documents.'}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)


if __name__=='__main__': main()
