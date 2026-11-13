"""Export blind source worksheets or validate independently reviewed annotations.

No model labels or inferred records are included in exports. Editing a worksheet
never changes extraction or existing ground truth. Reference intervals may be
split manually; validation checks exact source text, offsets and coverage.
"""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_api.schemas.extraction import ExtractedElement
from local_api.services.ownership_evaluation import source_hash, reference_spans
from local_api.services.evaluation_datasets import validate_annotation


def load_elements(path):
    data = json.loads(Path(path).read_text())
    return [ExtractedElement.model_validate(e) for e in data.get('extraction', data)['elements']]


def blind_template(elements):
    from local_api.services.resume_sections import ANCHORS
    spans = []
    for index, element in enumerate(elements):
        cuts = {0, len(element.text)}
        cursor = 0
        for line in element.text.splitlines(keepends=True):
            cursor += len(line)
            cuts.add(cursor)
        for hint in element.metadata.get('pdf_source_lines', []):
            for key in ('start','end'):
                offset = hint.get(key)
                if type(offset) is int and 0 <= offset <= len(element.text):
                    cuts.add(offset)
        ordered = sorted(cuts)
        for start,end in zip(ordered,ordered[1:]):
            spans.append({'source_id':f'e{index}:{start}:{end}', 'text':element.text[start:end],
                          'page':element.page_number, 'section':None, 'record_anchor':None,
                          'kind':None, 'unit_id':None, 'notes':''})
    return {'source_digest':source_hash(elements), 'canonical_sections':list(ANCHORS),
            'annotation_origin':'unlabeled_template', 'human_verified':False,
            'review':{'method':'independent_human', 'reviewer_id':None, 'adjudicator_id':None,
                      'saw_parser_predictions':None, 'independence_attested':False}, 'spans':spans}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['export','validate'])
    p.add_argument('--extraction', type=Path, required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--annotation', type=Path)
    p.add_argument('--original', type=Path, help='Original PDF/DOCX for source-byte hash binding')
    p.add_argument('--held-out', action='store_true')
    args = p.parse_args()
    elements = load_elements(args.extraction)
    if args.action == 'validate':
        if args.annotation is None:
            p.error('--annotation is required')
        annotation = json.loads(args.annotation.read_text())
        try:
            validate_annotation(annotation, source_hash(elements), held_out=args.held_out)
            reference_spans(elements, annotation)
        except ValueError as exc:
            p.error(str(exc))
        print(json.dumps({'status':'valid','source_digest':source_hash(elements),'held_out_review':args.held_out}))
        return
    if args.output is None or args.output.exists():
        p.error('Supply a new --output directory')
    args.output.mkdir(parents=True, mode=0o700)
    template = blind_template(elements)
    if args.original:
        from hashlib import sha256
        template['source_sha256'] = sha256(args.original.read_bytes()).hexdigest()
    (args.output/'annotation.json').write_text(json.dumps(template,indent=2,ensure_ascii=False))
    # Source inventory contains extraction evidence only, never section results.
    (args.output/'immutable-source.json').write_text(json.dumps({'source_digest':source_hash(elements),
         'elements':[e.model_dump() for e in elements]},indent=2,ensure_ascii=False))
    with (args.output/'worksheet.tsv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['source_id','text','page','section','record_anchor','kind','unit_id','notes'], delimiter='\t')
        writer.writeheader()
        for span in template['spans']:
            # Worksheet display only; immutable JSON retains literal source.
            writer.writerow({key:("'"+value if isinstance(value,str) and value[:1] in {'=','+','-','@','\t','\r'} else value)
                             for key,value in span.items()})
    print(json.dumps({'status':'unlabeled_export','spans':len(template['spans']),'human_verified':False}))


if __name__ == '__main__':
    main()
