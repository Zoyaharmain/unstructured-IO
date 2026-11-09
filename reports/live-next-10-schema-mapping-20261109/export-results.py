#!/usr/bin/env python3
"""Export standardized outputs and review summary for 2026-11-09 live test cohort."""

import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent
root = repo / "reports/live-next-10-schema-mapping-20261109"
results_path = root / "results.json"

if not results_path.exists():
    print("results.json does not exist yet.")
    sys.exit(0)

sys.path.insert(0, str(repo))

from local_api.schemas.mapping import SchemaMappingResponse
from local_api.services.standardization.mapping import mapping_input, attach_mapping_findings
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export

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

    # Calculate tokens from provider requests and responses
    prompt_tokens = 0
    completion_tokens = 0
    for req_file in d.glob("provider-request-*.json"):
        try:
            req_data = json.loads(req_file.read_text())
            for msg in req_data.get("messages", []):
                # Rough token estimate: ~4 chars per token
                prompt_tokens += max(1, len(msg.get("content", "")) // 4)
        except Exception:
            pass

    for resp_file in d.glob("provider-response-*.json"):
        try:
            resp_data = json.loads(resp_file.read_text())
            content = resp_data.get("content", "")
            completion_tokens += max(1, len(content) // 4)
        except Exception:
            pass

    total_tokens = prompt_tokens + completion_tokens
    # DeepSeek cache miss: $0.14 per 1M input tokens, $0.28 per 1M output tokens (approximate)
    est_cost = (prompt_tokens / 1_000_000 * 0.14) + (completion_tokens / 1_000_000 * 0.28)

    data = export.get("data", {})
    jobs = data.get("experience", [])
    row.update({
        "provider_calls": len(calls),
        "successful_http_calls": len(list(d.glob("provider-response-*.json"))),
        "prompt_tokens_est": prompt_tokens,
        "completion_tokens_est": completion_tokens,
        "total_tokens_est": total_tokens,
        "estimated_cost_usd": round(est_cost, 4),
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
print(f"Exported summary for {len(rows)} resumes.")
print(json.dumps([
    {k: r.get(k) for k in [
        "file", "seconds", "provider_calls", "successful_http_calls", "audit_status",
        "pipeline_stop_reason", "experience_count", "education_count",
        "jobs_missing_company", "jobs_missing_role", "full_name", "total_experience_years"
    ]} for r in rows
], indent=2))
