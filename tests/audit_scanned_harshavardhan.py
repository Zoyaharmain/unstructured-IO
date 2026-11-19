import json
from local_api.services.text_extraction_service import extract_text
from local_api.core.config import Settings
from local_api.services.resume_sections import detect_sections
from local_api.services.schema_mapping import map_schema
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.standardization.service import standardize_resume_data

# 1. OCR Extraction
print("=== 1. OCR Extraction on HARSHAVARDHAN_B_SCANNED.pdf ===")
import os
cache_path = '/tmp/harshavardhan_ocr_elements.json'
if os.path.exists(cache_path):
    print(f"Loading cached OCR elements from {cache_path}")
    with open(cache_path) as f:
        ocr_elements = json.load(f)
    print(f"Loaded {len(ocr_elements)} cached OCR elements")
else:
    with open('tests/fixtures/HARSHAVARDHAN_B_SCANNED.pdf', 'rb') as f:
        pdf_bytes = f.read()

    settings = Settings()
    ocr_resp = extract_text(pdf_bytes, 'HARSHAVARDHAN_B_SCANNED.pdf', 'ocr_only', include_elements=True, settings=settings)
    ocr_elements = [el.model_dump() for el in ocr_resp.elements]
    with open(cache_path, 'w') as f:
        json.dump(ocr_elements, f)
    print(f"Extracted and cached {len(ocr_elements)} OCR elements, text length = {len(ocr_resp.text)}")

# 2. Section Classification & Record Grouping
print("\n=== 2. Section Classification & Record Grouping ===")
sec_req = SectionRequest(elements=ocr_elements)
sec_resp = detect_sections(sec_req)
sec_categories = [s.category for s in sec_resp.sections]
print(f"Detected sections: {sec_categories}")
print(f"Needs review count: {len(sec_resp.needs_review)}")

# 3. Schema Mapping & Evidence Validation
print("\n=== 3. Schema Mapping & Evidence Validation ===")
map_req = ReviewedSchemaMappingRequest(elements=ocr_elements, sections=sec_resp)
map_resp = map_schema(map_req)
data = map_resp.data
evidence = map_resp.meta.get('field_evidence', {})

print(f"Contact Name: {data.contact.full_name} | Email: {data.contact.email} | Phone: {data.contact.phone}")
print(f"Experience entries: {len(data.experience)}")
for i, e in enumerate(data.experience):
    print(f"  [{i}] Company: {e.company} | Role: {e.role} | Dates: {e.start_date} - {e.end_date} | Duties: {len(e.responsibilities)}")
print(f"Education entries: {len(data.education)}")
for i, ed in enumerate(data.education):
    print(f"  [{i}] Institution: {ed.institution} | Degree: {ed.degree} | Grad Year: {ed.graduation_year}")
print(f"Projects entries: {len(data.projects)}")
for i, p in enumerate(data.projects):
    print(f"  [{i}] Name: {p.name} | Desc len: {len(p.description or '')} | Tech: {p.technologies}")

# 4. Evidence Validation
total_fields = 0
unsupported = []
for k in ('full_name', 'email', 'phone'):
    v = getattr(data.contact, k, None)
    if v:
        total_fields += 1
        if not evidence.get(f"contact.{k}"):
            unsupported.append(f"contact.{k}")
for i, e in enumerate(data.experience):
    for k in ('company', 'role', 'start_date', 'end_date'):
        v = getattr(e, k, None)
        if v:
            total_fields += 1
            if not evidence.get(f"experience[{i}].{k}"):
                unsupported.append(f"experience[{i}].{k}")
for i, ed in enumerate(data.education):
    for k in ('institution', 'degree', 'graduation_year'):
        v = getattr(ed, k, None)
        if v:
            total_fields += 1
            if not evidence.get(f"education[{i}].{k}"):
                unsupported.append(f"education[{i}].{k}")
for i, p in enumerate(data.projects):
    for k in ('name', 'description'):
        v = getattr(p, k, None)
        if v:
            total_fields += 1
            if not evidence.get(f"projects[{i}].{k}"):
                unsupported.append(f"projects[{i}].{k}")

print(f"\nTotal populated checked fields: {total_fields}")
print(f"Unsupported fields count: {len(unsupported)} ({unsupported})")

# 5. Standardization
print("\n=== 4. Standardization & Final JSON Export ===")
std_schema, std_meta, val_status, warnings = standardize_resume_data(data)
print(f"Validation status: is_valid={val_status.is_valid}, usable={val_status.usable}, requires_review={val_status.requires_human_review}")
print(f"Standardized Contact Phone: {std_schema.contact.phone}")
print(f"Standardized Skills count: {len(std_schema.skills.technical_skills)}")
print(f"Standardization warnings count: {len(warnings)}")

final_json = std_schema.model_dump_json(indent=2)
with open('tests/fixtures/HARSHAVARDHAN_B_SCANNED.standardized.json', 'w') as out:
    out.write(final_json)
print("Saved final JSON export to tests/fixtures/HARSHAVARDHAN_B_SCANNED.standardized.json")

# 6. Comparison with Text-based PDF Ground Truth
print("\n=== 5. Comparison: Scanned OCR vs Original Text PDF ===")
with open('ground_truth/corpus_audit/documents/2c3ffd474cb60ef954ce.json') as f:
    orig_doc = json.load(f)
orig_elements = orig_doc['extraction']['elements']
orig_sec_resp = detect_sections(SectionRequest(elements=orig_elements))
orig_map_resp = map_schema(ReviewedSchemaMappingRequest(elements=orig_elements, sections=orig_sec_resp))
orig_data = orig_map_resp.data

print(f"Field comparison:")
print(f"  Name: Scanned = {repr(data.contact.full_name)} | Text = {repr(orig_data.contact.full_name)}")
print(f"  Email: Scanned = {repr(data.contact.email)} | Text = {repr(orig_data.contact.email)}")
print(f"  Phone: Scanned = {repr(data.contact.phone)} | Text = {repr(orig_data.contact.phone)}")
print(f"  Exp count: Scanned = {len(data.experience)} | Text = {len(orig_data.experience)}")
if data.experience and orig_data.experience:
    print(f"  Exp[0] Company: Scanned = {repr(data.experience[0].company)} | Text = {repr(orig_data.experience[0].company)}")
    print(f"  Exp[0] Role: Scanned = {repr(data.experience[0].role)} | Text = {repr(orig_data.experience[0].role)}")
    print(f"  Exp[0] Dates: Scanned = ({data.experience[0].start_date}, {data.experience[0].end_date}) | Text = ({orig_data.experience[0].start_date}, {orig_data.experience[0].end_date})")
print(f"  Edu count: Scanned = {len(data.education)} | Text = {len(orig_data.education)}")
if data.education and orig_data.education:
    print(f"  Edu[0] Institution: Scanned = {repr(data.education[0].institution)} | Text = {repr(orig_data.education[0].institution)}")
    print(f"  Edu[0] Degree: Scanned = {repr(data.education[0].degree)} | Text = {repr(orig_data.education[0].degree)}")
    print(f"  Edu[0] Grad: Scanned = {repr(data.education[0].graduation_year)} | Text = {repr(orig_data.education[0].graduation_year)}")
print(f"  Proj count: Scanned = {len(data.projects)} | Text = {len(orig_data.projects)}")
for i in range(max(len(data.projects), len(orig_data.projects))):
    p_scanned = data.projects[i].name if i < len(data.projects) else 'N/A'
    p_text = orig_data.projects[i].name if i < len(orig_data.projects) else 'N/A'
    print(f"  Proj[{i}]: Scanned = {repr(p_scanned)} | Text = {repr(p_text)}")
