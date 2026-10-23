import hashlib,json
from pathlib import Path
OUT=Path(__file__).parent
before=json.loads((OUT/'hashes-before.json').read_text())
allowed={'local_api/schemas/subschemas.py','local_api/schemas/mapping.py','local_api/services/section_subschemas.py','local_api/routes/schema_mapping.py'}
changed=[]
for name,digest in before.items():
 p=Path(name)
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(name)
unexpected=sorted(set(changed)-allowed)
result={'snapshot_files':len(before),'authorized_existing_code_changes':sorted(set(changed)&allowed),
        'unexpected_changes':unexpected,'saved_input_and_raw_output_changes':[p for p in changed if p.startswith('reports/')],
        'extraction_segmentation_vendor_and_provider_files_unchanged':not any(p.startswith(('local_api/vendor/','scripts/')) or any(token in p for token in ['resume_sections.py','source_validation.py','llm_section_review.py','text_extraction_service.py','section_recovery.py']) for p in changed)}
(OUT/'preservation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
assert not unexpected
