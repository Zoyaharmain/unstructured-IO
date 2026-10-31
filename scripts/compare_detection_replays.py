"""Compare source-bound replay outputs without calling a provider."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse
from local_api.schemas.subschemas import SectionSchema
from local_api.services.mapping_completeness import mapping_completeness
from local_api.services.subschema_validation import validate_hierarchy


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--after',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Output must be new')
    summaries=[json.loads((p/'summary.json').read_text()) for p in (args.before,args.after)]
    rows=[]
    for before_path in sorted(args.before.glob('*.json')):
        if before_path.name=='summary.json':continue
        before=json.loads(before_path.read_text());after=json.loads((args.after/before_path.name).read_text())
        assert before['elements']==after['elements'],'Original extracted input changed'
        checks=[]
        for value in (before,after):
            elements=[ExtractedElement.model_validate(e) for e in value['elements']]
            sections=SectionResponse.model_validate(value['sections'])
            hierarchy=[SectionSchema.model_validate(s) for s in value['mapping']['section_schemas']]
            validate_hierarchy(hierarchy,sections)
            check=mapping_completeness(elements,sections,hierarchy)
            checks.append({'meaningful_unmapped_fragments':check['meaningful_unmapped_fragments'],
                'conflicting_field_overlaps':len(check['conflicting_field_overlaps']),
                'all_meaningful_content_accounted_for':check['all_meaningful_content_accounted_for']})
        job_identities=[[(j['company'],j['role']) for j in value['mapping']['data']['experience']] for value in (before,after)]
        rows.append({'file':before['metrics']['file'],'format':before['metrics']['format'],
            'original_extracted_input_unchanged':True,'job_identities_unchanged':job_identities[0]==job_identities[1],
            'before':{**before['metrics'],'field_completeness':checks[0]},
            'after':{**after['metrics'],'field_completeness':checks[1]}})
    result={'documents':len(rows),'formats':{extension:sum(r['format']==extension for r in rows) for extension in {r['format'] for r in rows}},
        'before':{k:summaries[0][k] for k in ('meaningful_unassigned','mapped_responsibilities','populated_attributes')},
        'after':{k:summaries[1][k] for k in ('meaningful_unassigned','mapped_responsibilities','populated_attributes')},
        'conflicting_field_overlaps_before':sum(r['before']['field_completeness']['conflicting_field_overlaps'] for r in rows),
        'conflicting_field_overlaps_after':sum(r['after']['field_completeness']['conflicting_field_overlaps'] for r in rows),
        'unmapped_field_fragments_before':sum(r['before']['field_completeness']['meaningful_unmapped_fragments'] for r in rows),
        'unmapped_field_fragments_after':sum(r['after']['field_completeness']['meaningful_unmapped_fragments'] for r in rows),
        'all_original_extracted_inputs_unchanged':True,
        'job_identity_change_documents':sum(not r['job_identities_unchanged'] for r in rows),
        'all_source_intervals_and_citations_validated':True,'provider_calls':0,
        'semantic_accuracy_verified':False,'rows':rows}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':main()
