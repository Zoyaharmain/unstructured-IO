"""Replay five frozen reviewed placements through current local grouping/mapping.

No provider or model invocation. Historical placement decisions remain inputs;
this does not simulate a fresh DeepSeek decision under the changed code.
"""
import argparse
import hashlib
import json
import socket
import sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def field_values(schema):
    result=defaultdict(list)
    for parent in schema['section_schemas']:
        for record in parent['records']:
            for attr in record['attributes']:result[parent['category']+'.'+attr['name']].extend(v['value'] for v in attr['items'])
    return dict(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def no_network(*a,**k):raise AssertionError('Network/provider calls prohibited during deterministic replay')
    socket.socket.connect=no_network
    from local_api.services import llm_section_review as llm
    llm.provider_json=no_network;llm.call_deepseek=no_network
    from local_api.schemas.sections import SectionResponse
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.schemas.extraction import ExtractedElement
    from local_api.services.resume_sections import build_sections
    from local_api.services.schema_mapping import map_schema
    from local_api.services.source_validation import validate_result
    from local_api.services.subschema_validation import validate_hierarchy
    selection=json.loads((args.source_run/'selection.json').read_text())
    if len(selection['selected'])!=5:raise ValueError('Exactly five saved sources required')
    args.output.mkdir(mode=0o700)
    rows=[]
    for item in selection['selected']:
        old=args.source_run/'results'/('%02d'%item['index'])
        directory=args.output/('%02d'%item['index']);directory.mkdir(mode=0o700)
        extraction=json.loads((old/'extraction.json').read_text())
        elements=[ExtractedElement.model_validate(e) for e in extraction['elements']]
        original=SectionResponse.model_validate(json.loads((old/'sections.json').read_text()))
        original_errors=validate_result(elements,original)
        if original_errors:raise ValueError('Invalid saved source inventory: '+str(original_errors))
        original_snapshot=original.model_dump()
        sections=original.model_copy(deep=True)
        historical_review=sections.metadata.pop('llm_review',None)
        sections.metadata['offline_replay']={'provider_calls':0,'source_run':str(args.source_run),
                                            'historical_review':historical_review,'fresh_llm_review':False}
        sections.sections=build_sections({s.category:s.blocks for s in sections.sections},elements)
        errors=validate_result(elements,sections)
        if errors:raise ValueError(str(errors))
        mapped=map_schema(SchemaMappingRequest(elements=elements,sections=sections,source=item['file']))
        validate_hierarchy(mapped.section_schemas,sections)
        output=mapped.model_dump(mode='json')
        before=json.loads((old/'schema.json').read_text())
        save(directory/'sections.json',sections.model_dump(mode='json'));save(directory/'schema.json',output)
        assert original.model_dump()==original_snapshot
        previous,current=field_values(before),field_values(output)
        differences=[{'field':key,'before':previous.get(key,[]),'after':current.get(key,[])}
                     for key in sorted(set(previous)|set(current)) if previous.get(key,[])!=current.get(key,[])]
        save(directory/'differences.json',differences)
        warnings=[]
        for category in ('experience','education'):
            for i,record in enumerate(output['data'][category]):
                reasons=next((r['review_reasons'] for r in output['meta']['record_reviews'] if r['category']==category and r['entry_id']==f'{category}-{i+1}'),[])
                if reasons:warnings.append({'category':category,'record':i,'reasons':reasons})
        stats=Counter()
        for parent in mapped.section_schemas:
            for record in parent.records:
                for attr in record.attributes:
                    stats[attr.status+'_attributes']+=1
                    for v in attr.items:stats['populated_items']+=1;stats['quotes']+=len(v.evidence)
        rows.append({'file':item['file'],'source_sha256':item['sha256'],'provider_calls':0,
                     'source_inventory_unchanged':True,'schema_valid':True,'hierarchy_evidence_valid':True,
                     'before_record_counts':{k:len(before['data'][k]) for k in ('experience','education','projects')},
                     'after_record_counts':{k:len(output['data'][k]) for k in ('experience','education','projects')},
                     'before_contact':before['data']['contact'],'after_contact':output['data']['contact'],
                     'before_title':before['data']['professional_title'],'after_title':output['data']['professional_title'],
                     'before_languages':before['data']['languages'],'after_languages':output['data']['languages'],
                     'missing_required_fields':output['meta']['missing_required_fields'],
                     'relationship_reviews':warnings,'counts_not_accuracy':dict(stats),'semantic_accuracy':None})
    save(args.output/'summary.json',{'source_run':str(args.source_run),'documents':rows,'provider_calls':0,
         'fresh_llm_review':False,'semantic_accuracy':None,
         'limitations':'Frozen saved placement categories; no new model decisions or exhaustive human field references.'})
    print(json.dumps({'documents':len(rows),'provider_calls':0,'outputs':str(args.output)},indent=2))


if __name__=='__main__':main()
