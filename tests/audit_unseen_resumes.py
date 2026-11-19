"""Test 3 unseen resumes through the complete parsing and standardization pipeline."""
import json
from local_api.services.resume_sections import detect_sections
from local_api.services.schema_mapping import map_schema
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.standardization.service import standardize_resume_data

UNSEEN = {
    'Narendra D (PDF)': 'ground_truth/corpus_audit/documents/002dc47a2c1af679d105.json',
    'Anantha Rama Bharavi Kundurthi (PDF)': 'ground_truth/corpus_audit/documents/0056b645017d717c2ece.json',
    'Rakesh MR (DOCX)': 'ground_truth/corpus_audit/documents/01081b906ccd870010ff.json',
}

results = {}

for name, path in UNSEEN.items():
    print(f"\n==========================================")
    print(f"Testing Unseen Resume: {name}")
    print(f"==========================================")
    with open(path) as f:
        doc = json.load(f)
    elements = doc.get('elements') or doc.get('extraction', {}).get('elements')
    
    sec_req = SectionRequest(elements=elements)
    sec_resp = detect_sections(sec_req)
    print(f"Sections detected: {[s.category for s in sec_resp.sections]}")
    
    map_req = ReviewedSchemaMappingRequest(elements=elements, sections=sec_resp)
    mapped_resp = map_schema(map_req)
    
    data = mapped_resp.data
    std_schema, std_meta, val_status, warnings = standardize_resume_data(mapped_resp.data)
    
    print(f"Contact Name: {std_schema.contact.full_name} | Email: {std_schema.contact.email} | Phone: {std_schema.contact.phone_e164 or std_schema.contact.phone}")
    print(f"Experience entries: {len(std_schema.experience)}")
    for i, exp in enumerate(std_schema.experience):
        print(f"  [{i}] Company: {exp.company!r} | Role: {exp.role!r} | Dates: {exp.start_date}-{exp.end_date} (is_current={exp.is_current}) | Dur: {exp.duration!r} | Duties: {len(exp.responsibilities)}")
    
    print(f"Education entries: {len(std_schema.education)}")
    for i, edu in enumerate(std_schema.education):
        print(f"  [{i}] Inst: {edu.institution!r} | Degree: {edu.degree!r} | Grad: {edu.graduation_year}")
        
    print(f"Projects entries: {len(std_schema.projects)}")
    for i, proj in enumerate(std_schema.projects[:3]):
        print(f"  [{i}] Name: {proj.name!r} | Desc len: {len(proj.description or '')}")
        
    print(f"Certifications: {len(std_schema.certifications)}")
    for i, cert in enumerate(std_schema.certifications[:3]):
        print(f"  [{i}] Name: {cert.name!r} | Issuer: {cert.issuer!r}")
        
    print(f"Total warnings: {len(warnings)}")
    results[name] = {
        'candidate': std_schema.contact.full_name,
        'experience_count': len(std_schema.experience),
        'education_count': len(std_schema.education),
        'projects_count': len(std_schema.projects),
        'certifications_count': len(std_schema.certifications),
        'warnings_count': len(warnings)
    }

print("\n\n================ SUMMARY RESULTS ================")
print(json.dumps(results, indent=2))
