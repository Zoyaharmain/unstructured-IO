"""Freeze and prepare all 350 resumes into structured batches with deterministic token ceilings."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.source_validation import validate_result
from local_api.vendor.handoff_schema.models import ResumeSchema

OUT = Path(__file__).parent

rows = json.loads((ROOT / 'reports/workflow-verification-350-20261022/per-resume.json').read_text())
assert len(rows) == 350
assert len({r['file'] for r in rows}) == 350

previously_attempted = {
    'A Lokhande.pdf', 'A Madhavi.pdf', 'A Suribhotla.pdf', 'Abhishek Barnwa.pdf', 'Ajay Bandagi.pdf',
    'Aparna_Bharti.pdf', 'AswathyRajagopal.pdf', 'Boovanesh Kumar.pdf', 'DDhanush.pdf', 'G S Sandhya Rani.pdf',
    'KARTHIYAYINI S_1.pdf', 'MADHUSUDHANHK.pdf', 'Manisha Singh.pdf', 'Nithin Eswarappa.pdf', 'RAMU AKKENAPALLY.pdf',
    'AbhishekTiwari.pdf', 'Ashfaq Rahman.pdf',
    'Hari Om Tiwary.pdf', 'Ankit_Kumar_Jain.pdf', 'AshutoshAgrawal.pdf', 'Avinash Kumar Singh.pdf', 'AkarshGupta.pdf'
}

# The 30 approved, pristine resumes for the initial gate batch
gate_30_files = [
    # 1p (6)
    'ChetanSai.pdf', 'Dinesh Patnaik.pdf', 'Diwakar kumar K.pdf',
    'GowthamSelvaraj.pdf', 'Jaya Upadhyay.pdf', 'K_Yugandhar__CV.pdf',
    # 2p (12)
    'AakritiAggarwal.pdf', 'Adithya_M_Hegde.pdf', 'AdityaSharma.pdf',
    'AjitSingh.pdf', 'AkshataJadhav.pdf', 'AkshayPatni (1).pdf',
    'AkshitaKothari.pdf', 'AmarjeetsinghRathod.pdf', 'AmenDeebaSiddiqui.pdf',
    'Ananya Guha Resume.pdf', 'Ankit Ojha.pdf', 'AnupGurnani[7y_0m].pdf',
    # 3p (8)
    'Abdul Shukoor.pdf', 'Ajay Chaudhari_13Y_PO.pdf', 'AjinkyaLenekar.pdf',
    'Akshay Wadhwa.pdf', 'Alvina _Fernandes.pdf', 'AMIT_RANA.pdf',
    'Amol.pdf', 'AncyImmediatejoiner[8y_1m].pdf',
    # 4p (4)
    'Aarchit Ranjan.pdf', 'Abhishek_HV.pdf', 'AJAY KUMAR CHAUDHAR.pdf', 'Akanksha Bhand.pdf'
]

assert len(gate_30_files) == 30
assert len(set(gate_30_files)) == 30
assert set(gate_30_files).isdisjoint(previously_attempted)

# Order all 350 files: Gate 30 first, then remaining 320 files deterministically
remaining_files = [r['file'] for r in rows if r['file'] not in set(gate_30_files)]
ordered_files = gate_30_files + remaining_files
assert len(ordered_files) == 350

row_by_file = {r['file']: r for r in rows}
manifest = []

for idx, filename in enumerate(ordered_files, 1):
    row = row_by_file[filename]
    path = ROOT / row['artifact']
    a = json.loads(path.read_text())
    req = SectionRequest(elements=a['extraction']['elements'])
    s = SectionResponse.model_validate(a['local_sections'])
    errs = validate_result(req.elements, s)
    assert not errs, f"Validation error on {filename}: {errs}"

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

    pages = sorted({e.page_number for e in req.elements if e.page_number})
    source_chars = sum(len(e.text) for e in req.elements)

    # Deterministic ceiling rule for dense resumes:
    # Dense: >= 3 pages, OR >= 75 blocks, OR >= 7500 chars -> 32,000 max_tokens
    # Standard: < 3 pages AND < 75 blocks AND < 7500 chars -> 18,000 max_tokens
    is_dense = len(pages) >= 3 or len(blocks) >= 75 or source_chars >= 7500
    token_ceiling = 32000 if is_dense else 18000

    # Batch assignment:
    # Batch 1: resumes 1..30 (controlled gate)
    # Batch 2: resumes 31..80 (50)
    # Batch 3: resumes 81..130 (50)
    # Batch 4: resumes 131..180 (50)
    # Batch 5: resumes 181..230 (50)
    # Batch 6: resumes 231..280 (50)
    # Batch 7: resumes 281..350 (70)
    if idx <= 30:
        batch_id = 'batch01_gate30'
    elif idx <= 80:
        batch_id = 'batch02_50'
    elif idx <= 130:
        batch_id = 'batch03_50'
    elif idx <= 180:
        batch_id = 'batch04_50'
    elif idx <= 230:
        batch_id = 'batch05_50'
    elif idx <= 280:
        batch_id = 'batch06_50'
    else:
        batch_id = 'batch07_70'

    directory = OUT / 'resumes' / f'{idx:03d}'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'source-blocks.json').write_text(json.dumps(blocks, ensure_ascii=False, indent=2) + '\n')

    manifest.append({
        'index': idx,
        'file': filename,
        'batch': batch_id,
        'is_gate_batch': idx <= 30,
        'sha256': row['sha256'],
        'source_artifact': str(path.relative_to(ROOT)),
        'pages': len(pages),
        'page_list': pages,
        'blocks': len(blocks),
        'source_characters': source_chars,
        'is_dense': is_dense,
        'token_ceiling': token_ceiling,
        'document_scope': row.get('document_scope', {})
    })

(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
(OUT / 'target-schema.json').write_text(json.dumps(ResumeSchema.model_json_schema(), indent=2) + '\n')

dense_count = sum(1 for m in manifest if m['is_dense'])
print(f'Prepared all 350 resumes across 7 batches. Dense resumes (32k ceiling): {dense_count}, Standard (18k): {350 - dense_count}.')

