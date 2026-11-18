"""Reproduce one synthetic heading failure; optionally inspect the local pipeline.

Exit 0 means the whole-heading assertion passed; exit 1 means it failed.
No external review calls are made. The sample is synthetic, not a real resume.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SAMPLE = {
    'elements': [
      
        {'type': 'NarrativeText',
         'text': 'Software Engineer | Northstar Systems | January 2021 – December 2023',
         'page_number': 1, 'metadata': {}},
        {'type': 'ListItem',
         'text': 'Developed reporting services and maintained production applications.',
         'page_number': 1, 'metadata': {}},
        {'type': 'Title', 'text': 'Education', 'page_number': 1, 'metadata': {}},
        {'type': 'NarrativeText',
         'text': 'Bachelor of Science in Computer Science | Lakeside University | 2020',
         'page_number': 1, 'metadata': {}},
    ],
    # This synthetic inventory tests classification, not extraction accuracy.
    'extraction_verified': True,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-pipeline', action='store_true',
                        help='Also run local section processing and deterministic mapping (no DeepSeek).')
    args = parser.parse_args()

    from local_api.services.resume_structure import heading_aliases, heading_boundary
    anchors = json.loads((ROOT / 'local_api/data/section_anchors.json').read_text())
    heading = SAMPLE['elements'][0]['text']
    expected = ('experience', None)
    actual = heading_boundary(heading, heading_aliases(anchors))
    passed = actual == expected
    print('Synthetic test: recognize the ENTIRE Employment Details heading')
    print(f'Input:    {heading!r}')
    print(f'Expected: {expected!r}')
    print(f'Actual:   {actual!r}')
    print('PASS' if passed else 'FAIL: heading was not recognized as one complete Experience heading.')
    if actual[1] is not None:
        print(f'Recognized prefix: {heading[:actual[1]]!r}')
        print(f'Treated as body:  {heading[actual[1]:]!r}')

    if args.local_pipeline:
        from local_api.schemas.sections import SectionRequest
        from local_api.schemas.mapping import SchemaMappingRequest
        from local_api.routes.sections import local_resume_sections
        from local_api.services.schema_mapping import map_schema
        from local_api.services.source_validation import validate_result
        request = SectionRequest.model_validate(SAMPLE)
        result = asyncio.run(local_resume_sections(request))
        print('\nLocal pipeline output (does not change the heading-test verdict):')
        for section in result.sections:
            print(f'\n{section.label}:')
            for block in section.blocks:
                print(f'  e{block.source_element_index}:{block.start}:{block.end}'
                      f' [{block.assignment}] {block.text!r}')
            for entry in section.entries:
                print(f'  Record {entry.entry_id}: block indices {entry.block_indices}')
        print('Unassigned:', [b.text for b in result.needs_review])
        print('Source-validation errors:', validate_result(request.elements, result))
        mapped = map_schema(SchemaMappingRequest(elements=request.elements, sections=result))
        print('Mapped jobs:', len(mapped.data.experience))
        print('Mapped education records:', len(mapped.data.education))
        print('A repaired final assignment does not make the original heading match correct.')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
