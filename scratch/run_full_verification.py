"""Comprehensive Project Verification & Benchmarking Script.
Evaluates format compatibility, extraction, sectioning, schema mapping, evidence, and performance.
"""
from io import BytesIO
import json
import hashlib
import os
from pathlib import Path
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

from unstructured.partition.auto import partition
from local_api.services import text_extraction_service as extract_svc
from local_api.services.resume_sections import detect_sections
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.utils.file_validation import ExtractionError
from fastapi.testclient import TestClient
from local_api.app import app

client = TestClient(app)
FIXTURES = Path('tests/fixtures')
PILOT_PDFS = Path('reports/chunked-schema-pilot5-20261024/execution/selected-pdfs')

results = {
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    'compatibility_matrix': [],
    'performance_benchmarks': {},
    'concurrency_benchmark': {},
    'unsupported_formats_audit': []
}

tracemalloc.start()

# --- 1. RESUME COMPATIBILITY MATRIX ---
test_samples = [
    # Category A: PDFs
    ('digital-multipage.pdf', (FIXTURES / 'digital-multipage.pdf').read_bytes(), 'application/pdf', 'Digital multi-page PDF', True),
    ('Jayesh Yadav-CV.pdf', (FIXTURES / 'Jayesh Yadav-CV.pdf').read_bytes(), 'application/pdf', 'Multi-page structured resume (2 pages)', True),
    ('Abhishek.S.pdf', (PILOT_PDFS / 'Abhishek.S.pdf').read_bytes(), 'application/pdf', 'Two-column sidebar resume (1 page)', True),
    ('IdaJose.pdf', (PILOT_PDFS / 'IdaJose.pdf').read_bytes(), 'application/pdf', 'Single-column multi-job resume (2 pages)', True),
    ('Priyotosh Kumar Singh.pdf', (PILOT_PDFS / 'Priyotosh Kumar Singh.pdf').read_bytes(), 'application/pdf', 'Two-column resume with tables & languages (2 pages)', True),
    ('PriyankaRoy[8y_0m].pdf', (PILOT_PDFS / 'PriyankaRoy[8y_0m].pdf').read_bytes(), 'application/pdf', 'Two-column dense skills resume (2 pages)', True),
    ('Kaleru Abhiram.pdf', (PILOT_PDFS / 'Kaleru Abhiram.pdf').read_bytes(), 'application/pdf', 'Dense projects & experience resume (3 pages)', True),
    ('rotated-page-90.pdf', (FIXTURES / 'rotated-page-90.pdf').read_bytes(), 'application/pdf', 'Rotated 90 degrees PDF', True),
    ('scanned.pdf', (FIXTURES / 'scanned.pdf').read_bytes(), 'application/pdf', 'Scanned image-only PDF', True),
]

# Generate Word DOCX
from docx import Document
doc = Document()
doc.add_heading('John Doe - Software Engineer', 0)
doc.add_paragraph('john.doe@example.com | +1 555-0199')
doc.add_heading('Experience', level=1)
doc.add_paragraph('Senior Developer at Tech Corp (2020 - Present)')
doc.add_heading('Education', level=1)
doc.add_paragraph('BS Computer Science, State University (2016 - 2020)')
doc.add_heading('Skills', level=1)
doc.add_paragraph('Python, TypeScript, Docker, SQL')
docx_stream = BytesIO()
doc.save(docx_stream)
test_samples.append(('sample_resume.docx', docx_stream.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Native Word DOCX Resume', True))

# Generate Image PNG
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (1000, 400), 'white')
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
except Exception:
    font = ImageFont.load_default()
draw = ImageDraw.Draw(img)
draw.text((20, 20), 'Jane Smith - Data Scientist\njane@example.com\nExperience: Data Analyst at Analytics Inc (2021-2023)', fill='black', font=font)
png_stream = BytesIO()
img.save(png_stream, format='PNG')
test_samples.append(('sample_resume.png', png_stream.getvalue(), 'image/png', 'Rendered PNG Image Resume', True))

# Textual formats
test_samples.append(('sample_resume.txt', b'Jane Doe\njane@example.com\nExperience: Developer at Web Co (2019-2022)\nSkills: Python, Go', 'text/plain', 'Plain text resume', True))
test_samples.append(('sample_resume.md', b'# Alex Brown\nalex@example.com\n## Experience\nEngineer at Cloud Inc (2018-2023)\n## Skills\nKubernetes, Python', 'text/markdown', 'Markdown resume', True))

# Corrupt / Unsupported samples
test_samples.append(('empty.pdf', b'', 'application/pdf', 'Empty PDF document', False))
test_samples.append(('broken.pdf', b'%PDF-1.4 invalid corrupt content \x00\x01\x02', 'application/pdf', 'Corrupted PDF document', False))
test_samples.append(('program.exe', b'MZ\x00\x01' + b'\x00' * 100, 'application/x-msdownload', 'Executable / unsupported binary format', False))

for name, payload, expected_mime, description, should_succeed in test_samples:
    sha = hashlib.sha256(payload).hexdigest() if payload else 'empty'
    t0 = time.perf_counter()
    sample_res = {
        'filename': name,
        'description': description,
        'sha256': sha,
        'bytes': len(payload),
        'expected_mime': expected_mime,
        'should_succeed': should_succeed,
    }
    
    if not should_succeed:
        # Test error handling
        try:
            resp = extract_svc.extract_text(payload, name)
            sample_res['status'] = 'UNEXPECTED_PASS'
            sample_res['error'] = None
        except ExtractionError as exc:
            sample_res['status'] = 'CORRECTLY_REJECTED'
            sample_res['http_status'] = exc.status
            sample_res['error_message'] = str(exc)
        except Exception as exc:
            sample_res['status'] = 'REJECTED_WITH_EXCEPTION'
            sample_res['error_type'] = type(exc).__name__
            sample_res['error_message'] = str(exc)
        sample_res['duration_seconds'] = round(time.perf_counter() - t0, 3)
        results['compatibility_matrix'].append(sample_res)
        continue

    # Execute extraction
    try:
        strat = 'ocr_only' if name in {'scanned.pdf', 'sample_resume.png'} else 'auto'
        ext_resp = extract_svc.extract_text(payload, name, strategy=strat)
        sample_res['extraction_success'] = ext_resp.success
        sample_res['detected_file_type'] = ext_resp.file_type
        elements = [e.model_dump() for e in ext_resp.elements] if ext_resp.elements else []
        sample_res['elements_count'] = len(elements)
        sample_res['word_count'] = len(ext_resp.text.split()) if ext_resp.text else 0
        
        # Section detection
        sec_req = SectionRequest(elements=elements)
        sec_resp = detect_sections(sec_req)
        sample_res['sections_detected'] = [s.category for s in sec_resp.sections]
        sample_res['needs_review_count'] = len(sec_resp.needs_review)
        
        # Schema mapping
        mapping_req = SchemaMappingRequest(elements=sec_req.elements, sections=sec_resp, source=name)
        mapped = map_schema(mapping_req)
        data = mapped.data
        meta = mapped.meta
        
        sample_res['contact'] = {
            'name': data.contact.full_name,
            'email': data.contact.email,
            'phone': data.contact.phone
        }
        sample_res['experience_records'] = len(data.experience)
        sample_res['education_records'] = len(data.education)
        sample_res['skills_count'] = len(data.skills.technical_skills)
        sample_res['missing_required_fields'] = len(meta.get('missing_required_fields', []))
        sample_res['unmapped_blocks'] = len(meta.get('unmapped_blocks', []))
        sample_res['section_schemas_count'] = len(mapped.section_schemas)
        
        # Assessment
        if not data.contact.full_name and sample_res['elements_count'] > 20:
            sample_res['status'] = 'SUPPORTED_PARTIAL'
            sample_res['limitation'] = 'Candidate name unextracted or fragmented'
        elif sample_res['missing_required_fields'] > 10:
            sample_res['status'] = 'SUPPORTED_PARTIAL'
            sample_res['limitation'] = 'High missing required fields due to section fragmentation'
        else:
            sample_res['status'] = 'SUPPORTED_PASS'
            sample_res['limitation'] = None
    except Exception as exc:
        sample_res['status'] = 'SUPPORTED_FAIL'
        sample_res['error_type'] = type(exc).__name__
        sample_res['error_message'] = str(exc)
        
    sample_res['duration_seconds'] = round(time.perf_counter() - t0, 3)
    results['compatibility_matrix'].append(sample_res)

# --- 2. PERFORMANCE BENCHMARKS ---
perf_runs = []
test_pdf = (FIXTURES / 'digital-multipage.pdf').read_bytes()
for strat in ['fast', 'auto']:
    durations = []
    for _ in range(5):
        t0 = time.perf_counter()
        extract_svc.extract_text(test_pdf, 'digital-multipage.pdf', strategy=strat)
        durations.append(time.perf_counter() - t0)
    durations.sort()
    perf_runs.append({
        'workload': f'digital-multipage.pdf ({strat})',
        'iterations': 5,
        'min_seconds': round(durations[0], 4),
        'median_seconds': round(durations[2], 4),
        'p95_seconds': round(durations[-1], 4),
        'mean_seconds': round(sum(durations)/len(durations), 4)
    })

# End-to-end pipeline latency on Jayesh Yadav-CV.pdf
jayesh_bytes = (FIXTURES / 'Jayesh Yadav-CV.pdf').read_bytes()
e2e_durations = []
for _ in range(3):
    t0 = time.perf_counter()
    ext = extract_svc.extract_text(jayesh_bytes, 'Jayesh Yadav-CV.pdf', strategy='auto')
    elems = [e.model_dump() for e in ext.elements]
    sec_req = SectionRequest(elements=elems)
    sec_resp = detect_sections(sec_req)
    m_req = SchemaMappingRequest(elements=sec_req.elements, sections=sec_resp, source='Jayesh Yadav-CV.pdf')
    mapped = map_schema(m_req)
    e2e_durations.append(time.perf_counter() - t0)

e2e_durations.sort()
perf_runs.append({
    'workload': 'Jayesh Yadav-CV.pdf (End-to-End: extract+sections+schema)',
    'iterations': 3,
    'min_seconds': round(e2e_durations[0], 4),
    'median_seconds': round(e2e_durations[1], 4),
    'p95_seconds': round(e2e_durations[-1], 4),
    'mean_seconds': round(sum(e2e_durations)/len(e2e_durations), 4)
})

results['performance_benchmarks'] = perf_runs

# --- 3. CONCURRENCY BENCHMARK ---
def run_api_request(idx):
    t0 = time.perf_counter()
    resp = client.post('/api/v1/extract/text', files={'file': ('note.txt', f'Candidate #{idx} note content.')})
    return resp.status_code, time.perf_counter() - t0

t0_conc = time.perf_counter()
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(run_api_request, i) for i in range(10)]
    conc_results = [f.result() for f in futures]
total_conc_time = time.perf_counter() - t0_conc

statuses = [r[0] for r in conc_results]
latencies = sorted([r[1] for r in conc_results])

current_mem, peak_mem = tracemalloc.get_traced_memory()
tracemalloc.stop()

results['concurrency_benchmark'] = {
    'total_requests': 10,
    'concurrency': 5,
    'all_succeeded': all(s == 200 for s in statuses),
    'total_duration_seconds': round(total_conc_time, 3),
    'throughput_req_per_sec': round(10 / total_conc_time, 2),
    'median_latency_seconds': round(latencies[5], 4),
    'p95_latency_seconds': round(latencies[-1], 4),
    'peak_memory_mb': round(peak_mem / (1024 * 1024), 2)
}

print(json.dumps(results, indent=2))

