"""Run a local document through extraction/grouping; keep document output private.

Example: HF_HOME=... python scripts/check_resume_sections.py /path/resume.pdf
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_api.schemas.sections import SectionRequest
from local_api.services.text_extraction_service import extract_text
from local_api.services.resume_sections import get_engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', type=Path)
    parser.add_argument('--strategy', default='fast', choices=['auto', 'fast', 'hi_res', 'ocr_only'])
    parser.add_argument('--private-output', type=Path, default=Path('.upstream/resume-validation'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    payload = args.document.read_bytes()
    extracted = extract_text(payload, args.document.name, strategy=args.strategy)
    result = get_engine().detect(SectionRequest(elements=extracted.elements, extraction_verified=True))
    # This CLI exercises grouping; caller attestation is not an OCR benchmark.
    blocks = [b for s in result.sections for b in s.blocks] + result.needs_review
    for index, element in enumerate(extracted.elements):
        spans = sorted((b for b in blocks if b.source_element_index == index), key=lambda b:b.start)
        assert ''.join(b.text for b in spans) == element.text
    assert len({s.category for s in result.sections}) == len(result.sections)
    args.private_output.mkdir(parents=True, exist_ok=True)
    (args.private_output/'extracted.json').write_text(extracted.model_dump_json(indent=2))
    (args.private_output/'sections.json').write_text(result.model_dump_json(indent=2))
    (args.private_output/'sections.txt').write_text('\n\n'.join(f'{s.label}\n{"="*len(s.label)}\n{s.text}' for s in result.sections))
    report = {'document_sha256':hashlib.sha256(payload).hexdigest(), 'strategy':args.strategy,
              'page_numbers':extracted.metadata.page_numbers, 'canonical_section_count':len(result.sections),
              'categories':[s.category for s in result.sections],
              'section_word_counts':{s.category:len(s.text.split()) for s in result.sections},
              'review_units':len(result.needs_review), 'all_extracted_text_preserved':True,
              'one_block_per_category':True, 'pdf_layout_elements':sum(bool(e.metadata.get('pdf_source_lines')) for e in extracted.elements),
              'original_pdf_word_accuracy_measured':False}
    if args.report:
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
