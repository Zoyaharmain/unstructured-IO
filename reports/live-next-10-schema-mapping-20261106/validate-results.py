#!/usr/bin/env python3
import json
from pathlib import Path
from local_api.schemas.sections import SectionResponse, SectionRequest
from local_api.services.source_validation import validate_result

root = Path("reports/live-next-10-schema-mapping-20261106")
summary_path = root / "review-summary.json"
if not summary_path.exists():
    print("review-summary.json not found.")
    sys.exit(1)

rows = json.loads(summary_path.read_text())
for row in rows:
    d = root / row["directory"]
    if not (d / "extraction.json").exists() or not (d / "sections.json").exists():
        continue
    ex = json.loads((d / "extraction.json").read_text())
    req = SectionRequest(elements=ex["elements"])
    sections = SectionResponse.model_validate_json((d / "sections.json").read_text())
    errors = validate_result(req.elements, sections)
    row["final_source_validation_errors"] = errors
    
    audit = json.loads((d / "schema-audit.json").read_text()) if (d / "schema-audit.json").exists() else {}
    row["audit_incomplete_reason"] = audit.get("reason")
    row["audit_findings_count"] = len(audit.get("findings", []))
    row["empty_review_count"] = sum(not any(c.isalnum() for c in b.text) for b in sections.needs_review)
    
    first_req = d / "provider-request-1.json"
    if first_req.exists():
        try:
            row["provider_model"] = json.loads(first_req.read_text()).get("model")
        except Exception:
            row["provider_model"] = None
    else:
        row["provider_model"] = None
    
    print(
        row["file"],
        "source validation:", errors,
        "empty review:", row["empty_review_count"],
        "section:", row.get("section_review", {}).get("status"),
        "field:", row.get("field_review", {}).get("status")
    )

summary_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))

