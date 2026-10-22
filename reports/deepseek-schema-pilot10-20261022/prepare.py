"""Freeze exactly ten saved local block inventories; no model/provider calls."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.source_validation import validate_result
from local_api.vendor.handoff_schema.models import ResumeSchema

OUT = Path(__file__).parent

specs = [
    ('KARTHIYAYINI S_1.pdf', 'Dense four-page banking operations and financial control resume with multiple employers and education tables; previously failed JSON parsing.'),
    ('A Lokhande.pdf', 'Two-page Java developer resume with garbled/repeated header fragments, split identity, and multiple client-employer layers.'),
    ('Abhishek Barnwa.pdf', 'One-page ServiceNow technical resume with compact sections, client/project distinctions, and icon glyph artifacts.'),
    ('A Suribhotla.pdf', 'Four-page data analytics resume with multiple historical engagements and dual job titles.'),
    ('AswathyRajagopal.pdf', 'Two-page regulatory QA resume with explicit date ranges, future-dated chronology, and non-standard pipe delimiters.'),
    ('Manisha Singh.pdf', 'One-page software engineer resume with compact single-column structure and clear degree/employer sections.'),
    ('MADHUSUDHANHK.pdf', 'Two-page IT infrastructure and systems engineer resume with multi-employer dated history.'),
    ('RAMU AKKENAPALLY.pdf', 'Two-page database administrator and Oracle PL-SQL developer resume with categorized technical skills.'),
    ('Aparna_Bharti.pdf', 'Three-page business analyst resume with cross-page responsibilities and client consulting engagements.'),
    ('G S Sandhya Rani.pdf', 'Four-page QA lead and automation tester resume with multi-role historical progression across 4 pages.')
]

rows = json.loads((ROOT / 'reports/workflow-verification-350-20261022/per-resume.json').read_text())
selected = []

for number, (name, reason) in enumerate(specs, 1):
    row = next(r for r in rows if r['file'] == name)
    path = ROOT / row['artifact']
    a = json.loads(path.read_text())
    req = SectionRequest(elements=a['extraction']['elements'])
    s = SectionResponse.model_validate(a['local_sections'])
    assert not validate_result(req.elements, s)
    blocks = [{
        'source_id': f"e{b.source_element_index}:{b.start}:{b.end}",
        'source_element': b.source_element_index,
        'start': b.start,
        'end': b.end,
        'page': b.page_number,
        'local_category': sec.category,
        'text': b.text
    } for sec in s.sections for b in sec.blocks]
    blocks.extend({
        'source_id': f"e{b.source_element_index}:{b.start}:{b.end}",
        'source_element': b.source_element_index,
        'start': b.start,
        'end': b.end,
        'page': b.page_number,
        'local_category': 'needs_review',
        'text': b.text
    } for b in s.needs_review)
    blocks.sort(key=lambda b: (b['source_element'], b['start']))

    directory = OUT / f'{number:02d}'
    directory.mkdir(mode=0o700, exist_ok=True)
    (directory / 'source-blocks.json').write_text(json.dumps(blocks, ensure_ascii=False, indent=2) + '\n')
    (directory / 'source-blocks.md').write_text(
        '# ' + name + ' — saved local blocks\n\n' +
        '\n\n'.join(f"**{b['source_id']} · page {b['page']} · local {b['local_category']}**\n\n{b['text']}" for b in blocks)
    )

    selected.append({
        'number': number,
        'file': name,
        'reason': reason,
        'source_pdf_sha256': row['sha256'],
        'source_artifact': str(path.relative_to(ROOT)),
        'source_artifact_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'section_key': 'local_sections',
        'blocks': len(blocks),
        'pages': sorted({e.page_number for e in req.elements if e.page_number}),
        'source_characters': sum(len(e.text) for e in req.elements),
        'source_blocks_sha256': hashlib.sha256((directory / 'source-blocks.json').read_bytes()).hexdigest()
    })

assert len(selected) == len({r['source_pdf_sha256'] for r in selected}) == 10
(OUT / 'selection.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
(OUT / 'target-schema.json').write_text(json.dumps(ResumeSchema.model_json_schema(), indent=2) + '\n')

files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'local_api').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(OUT / 'input-local-api-hashes.json').write_text(json.dumps(files, indent=2) + '\n')
print('Frozen exactly ten unique resumes from saved local blocks. No extraction or block detection executed.')

