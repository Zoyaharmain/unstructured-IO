import json
import re
from local_api.services.resume_sections import detect_sections
from local_api.services.schema_mapping import map_schema, source_id
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.standardization.service import standardize_resume_data

FIXTURES = {
    'Astha Saraogi': 'tests/fixtures/real_resumes/AsthaSaraogi.extraction.json',
    'Harshavardhan B': 'ground_truth/corpus_audit/documents/2c3ffd474cb60ef954ce.json',
    'Abdul Shukoor': 'tests/fixtures/real_resumes/Abdul Shukoor.extraction.json',
    'Aashish Golhani': 'tests/fixtures/real_resumes/_Aashish Golhani.extraction (1).json',
    'Zaved Ahmed': 'ground_truth/corpus_audit/documents/2ced8baefebf3c876f65.json',
    'Affan Asad Alangayam': 'ground_truth/corpus_audit/documents/55d2ab34b050912d66c7.json',
    'Akmal Yezdani': 'ground_truth/corpus_audit/documents/284808b143f1ba749c09.json',
    'Abhishek HV': 'ground_truth/corpus_audit/documents/86ca79a7aead8cedc055.json',
}

results = {}

for name, path in FIXTURES.items():
    print(f"\n==========================================")
    print(f"Auditing: {name} ({path})")
    print(f"==========================================")
    with open(path) as f:
        doc = json.load(f)
    elements = doc.get('elements') or doc.get('extraction', {}).get('elements')
    
    sec_req = SectionRequest(elements=elements)
    sec_resp = detect_sections(sec_req)
    
    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=sec_resp)
    mapped_resp = map_schema(map_req)
    
    data = mapped_resp.data
    evidence = mapped_resp.meta.get('field_evidence', {})
    std_schema, std_meta, val_status, warnings = standardize_resume_data(mapped_resp.data)
    
    # Evidence check
    total_populated_fields = 0
    unsupported_fields = []
    
    # Contact
    contact_dict = data.contact.model_dump()
    for k, v in contact_dict.items():
        if v:
            total_populated_fields += 1
            ev = evidence.get(f"contact.{k}")
            if not ev:
                unsupported_fields.append(f"contact.{k}")
    
    # Experience
    for i, exp in enumerate(data.experience):
        for k in ('company', 'role', 'start_date', 'end_date', 'duration', 'location'):
            v = getattr(exp, k, None)
            if v:
                total_populated_fields += 1
                ev = evidence.get(f"experience[{i}].{k}")
                if not ev:
                    unsupported_fields.append(f"experience[{i}].{k}")
        for j, resp in enumerate(exp.responsibilities):
            total_populated_fields += 1
            ev = evidence.get(f"experience[{i}].responsibilities[{j}]")
            if not ev:
                unsupported_fields.append(f"experience[{i}].responsibilities[{j}]")
                
    # Education
    for i, edu in enumerate(data.education):
        for k in ('institution', 'degree', 'start_year', 'graduation_year'):
            v = getattr(edu, k, None)
            if v:
                total_populated_fields += 1
                ev = evidence.get(f"education[{i}].{k}")
                if not ev:
                    unsupported_fields.append(f"education[{i}].{k}")
                    
    # Projects
    for i, proj in enumerate(data.projects):
        for k in ('name', 'description', 'role', 'start_date', 'end_date', 'organization'):
            v = getattr(proj, k, None)
            if v:
                total_populated_fields += 1
                ev = evidence.get(f"projects[{i}].{k}")
                if not ev:
                    unsupported_fields.append(f"projects[{i}].{k}")
        for j, tech in enumerate(proj.technologies):
            total_populated_fields += 1
            ev = evidence.get(f"projects[{i}].technologies[{j}]")
            if not ev:
                unsupported_fields.append(f"projects[{i}].technologies[{j}]")
                
    # Certifications
    for i, cert in enumerate(data.certifications):
        for k in ('name', 'issuer', 'issue_year'):
            v = getattr(cert, k, None)
            if v:
                total_populated_fields += 1
                ev = evidence.get(f"certifications[{i}].{k}")
                if not ev:
                    unsupported_fields.append(f"certifications[{i}].{k}")
                    
    print(f"Contact Name: {data.contact.full_name} | Email: {data.contact.email} | Phone: {data.contact.phone}")
    print(f"Experience entries: {len(data.experience)}")
    for i, e in enumerate(data.experience[:4]):
        print(f"  [{i}] {e.company} | {e.role} | {e.start_date} - {e.end_date} | {len(e.responsibilities)} duties")
    print(f"Education entries: {len(data.education)}")
    for i, ed in enumerate(data.education):
        print(f"  [{i}] {ed.institution} | {ed.degree} | grad: {ed.graduation_year}")
    print(f"Projects entries: {len(data.projects)}")
    for i, p in enumerate(data.projects[:3]):
        print(f"  [{i}] {p.name} | desc len: {len(p.description or '')} | tech: {p.technologies[:4]}")
    print(f"Certifications: {len(data.certifications)}")
    for i, c in enumerate(data.certifications[:3]):
        print(f"  [{i}] {c.name} | issuer: {c.issuer}")
    print(f"Populated fields count: {total_populated_fields}")
    print(f"Unsupported fields count: {len(unsupported_fields)} ({unsupported_fields[:5]})")
    print(f"Standardized Contact Phone: {std_schema.contact.phone}")
    
    results[name] = {
        'total_fields': total_populated_fields,
        'unsupported_count': len(unsupported_fields),
        'unsupported_fields': unsupported_fields,
        'experience_count': len(data.experience),
        'education_count': len(data.education),
        'projects_count': len(data.projects),
        'certifications_count': len(data.certifications),
        'needs_review': len(sec_resp.needs_review)
    }

print("\n\n================ SUMMARY RESULTS ================")
print(json.dumps(results, indent=2))
