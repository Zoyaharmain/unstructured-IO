"""Freeze exactly thirty saved local block inventories; no model/provider calls."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.source_validation import validate_result
from local_api.vendor.handoff_schema.models import ResumeSchema

OUT = Path(__file__).parent

specs = [
    # 1-page resumes (6)
    ('AbhishekTiwari.pdf', 'One-page software engineering resume with compact structure and explicit skill blocks.'),
    ('Ashfaq Rahman.pdf', 'One-page full stack developer resume with project bullet points and technical skill sets.'),
    ('ChetanSai.pdf', 'One-page developer resume with concise professional summary and educational entries.'),
    ('Dinesh Patnaik.pdf', 'One-page data engineering resume with segmented technical proficiencies and work items.'),
    ('GowthamSelvaraj.pdf', 'One-page software engineer resume with multi-element project entries and skills.'),
    ('Jaya Upadhyay.pdf', 'One-page test analyst resume with clear company chronology and test automation tools.'),
    # 2-page resumes (12)
    ('AakritiAggarwal.pdf', 'Two-page data analyst and BI developer resume with rich project details and KPIs.'),
    ('AdityaSharma.pdf', 'Two-page software engineer resume with multiple employment roles and technical skills.'),
    ('AjitSingh.pdf', 'Two-page systems engineer resume with infrastructure projects and certifications.'),
    ('AkshataJadhav.pdf', 'Two-page Java software developer resume with dense framework and database citations.'),
    ('AkshayPatni (1).pdf', 'Two-page QA automation engineer resume with framework tools and test methodologies.'),
    ('AkshitaKothari.pdf', 'Two-page frontend developer resume with UI/UX technologies and application features.'),
    ('AmarjeetsinghRathod.pdf', 'Two-page DevOps and cloud engineer resume with CI/CD pipelines and infrastructure.'),
    ('AmenDeebaSiddiqui.pdf', 'Two-page business analyst resume with stakeholder management and domain knowledge.'),
    ('Ankit Ojha.pdf', 'Two-page software engineer resume with distributed systems and microservices experience.'),
    ('AnupGurnani[7y_0m].pdf', 'Two-page senior software engineer resume with 7-year employment history and skills.'),
    ('Anuradha Yadav.pdf', 'Two-page database developer resume with PL/SQL queries and data warehousing.'),
    ('Ayush Sharma.pdf', 'Two-page data science and ML engineer resume with model development and analytics.'),
    # 3-page resumes (8)
    ('Abdul Shukoor.pdf', 'Three-page enterprise IT infrastructure and network administrator resume with extensive blocks.'),
    ('Ajay Chaudhari_13Y_PO.pdf', 'Three-page product owner / project manager resume with 13-year multi-company roadmap experience.'),
    ('AjinkyaLenekar.pdf', 'Three-page cloud architect and backend engineer resume with cloud migrations and APIs.'),
    ('Akshay Wadhwa.pdf', 'Three-page technical lead and Java developer resume with multi-tier enterprise systems.'),
    ('Alvina _Fernandes.pdf', 'Three-page HR and business operations specialist resume with cross-functional initiatives.'),
    ('AMIT_RANA.pdf', 'Three-page solution architect resume with high character volume and client engagements.'),
    ('Amol.pdf', 'Three-page QA lead resume with automation frameworks and test governance.'),
    ('Ankur Jain.pdf', 'Three-page senior consultant resume with enterprise ERP implementations and analytics.'),
    # 4-page resumes (4)
    ('Aarchit Ranjan.pdf', 'Four-page dense data engineering and big data analytics resume with massive block depth.'),
    ('Abhishek_HV.pdf', 'Four-page senior test engineer resume with end-to-end QA suites and team leadership.'),
    ('Akanksha Bhand.pdf', 'Four-page technical project lead resume with multi-vendor delivery and stakeholder tracking.'),
    ('Akilash P Nair.pdf', 'Four-page senior systems consultant resume with global multi-country project deliveries.')
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

assert len(selected) == len({r['source_pdf_sha256'] for r in selected}) == 30
(OUT / 'selection.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
(OUT / 'target-schema.json').write_text(json.dumps(ResumeSchema.model_json_schema(), indent=2) + '\n')

files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'local_api').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(OUT / 'input-local-api-hashes.json').write_text(json.dumps(files, indent=2) + '\n')
print(f'Frozen exactly thirty unique resumes from saved local blocks. Total resumes: {len(selected)}.')

