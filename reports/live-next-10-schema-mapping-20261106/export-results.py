#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from local_api.schemas.mapping import SchemaMappingResponse
from local_api.services.standardization.mapping import mapping_input, attach_mapping_findings
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export

root = Path("reports/live-next-10-schema-mapping-20261106")
results_path = root / "results.json"
if not results_path.exists():
    print("results.json does not exist yet.")
    sys.exit(1)

rows = []
for timing in json.loads(results_path.read_text()):
    d = root / timing["directory"]
    row = dict(timing)
    if not (d / "schema.json").exists():
        row["status"] = "failed before saving mapped schema"
        rows.append(row)
        continue
    
    raw = json.loads((d / "schema.json").read_text())
    mapped = SchemaMappingResponse.model_validate(raw)
    resume, metadata, status, warnings = standardize_resume_data(mapping_input(mapped))
    mapped.standardized_data = resume
    metadata.source_evidence = mapped.meta.get("field_evidence", {})
    mapped.schema_version = metadata.schema_version
    mapped.standardization_metadata = metadata
    mapped.validation_status = status
    mapped.warnings = warnings
    attach_mapping_findings(mapped, warnings)
    
    export = standardized_export(mapped, include_audit=True)
    (d / "standardized.json").write_text(json.dumps(export, indent=2, ensure_ascii=False))
    
    sections = json.loads((d / "sections.json").read_text()) if (d / "sections.json").exists() else {}
    pipeline = json.loads((d / "pipeline.json").read_text()) if (d / "pipeline.json").exists() else {}
    audit = json.loads((d / "schema-audit.json").read_text()) if (d / "schema-audit.json").exists() else {}
    calls = json.loads((d / "provider-calls.json").read_text()) if (d / "provider-calls.json").exists() else []
    
    data = export.get("data", {})
    jobs = data.get("experience", [])
    row.update({
        "provider_calls": len(calls),
        "successful_http_calls": len(list(d.glob("provider-response-*.json"))),
        "section_review": sections.get("metadata", {}).get("llm_review", {}),
        "field_review": raw.get("meta", {}).get("field_review", {}),
        "audit_status": audit.get("status"),
        "audit_findings": audit.get("findings", []),
        "pipeline_stop_reason": pipeline.get("stop_reason"),
        "provider_coverage_status": pipeline.get("provider_coverage_status"),
        "needs_review": len(sections.get("needs_review", [])),
        "missing_required_fields": raw.get("meta", {}).get("missing_required_fields", []),
        "completeness_check": raw.get("meta", {}).get("completeness_check", {}),
        "full_name": data.get("contact", {}).get("full_name"),
        "professional_title": data.get("professional_title"),
        "experience_count": len(jobs),
        "education_count": len(data.get("education", [])),
        "certification_count": len(data.get("certifications", [])),
        "jobs_missing_company": sum(not j.get("company") for j in jobs),
        "jobs_missing_role": sum(not j.get("role") for j in jobs),
        "warning_count": len(export.get("warnings", [])),
        "total_experience_years": data.get("total_experience_years")
    })
    rows.append(row)

(root / "review-summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
print(json.dumps([
    {k: r.get(k) for k in [
        "file", "seconds", "provider_calls", "successful_http_calls", "audit_status",
        "pipeline_stop_reason", "needs_review", "experience_count", "education_count",
        "jobs_missing_company", "jobs_missing_role", "full_name", "total_experience_years"
    ]} for r in rows
], indent=2))

