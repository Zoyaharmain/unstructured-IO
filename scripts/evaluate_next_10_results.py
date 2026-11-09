#!/usr/bin/env python3
import json
from pathlib import Path
import pypdf

out = Path("reports/live-next-10-schema-mapping-20261106")
selection = json.loads((out / "selection.json").read_text())

results = []
for item in selection["selected"]:
    d = out / item["folder_name"]
    pdf_path = Path(item["local_path"])
    
    reader = pypdf.PdfReader(str(pdf_path))
    pdf_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    lines = [l.strip() for l in pdf_text.splitlines() if l.strip()]
    
    std_file = d / "standardized.json"
    data = {}
    warnings = []
    if std_file.exists():
        std = json.loads(std_file.read_text())
        data = std.get("data", {})
        warnings = std.get("warnings", [])
    
    contact = data.get("contact", {})
    jobs = data.get("experience", [])
    edu = data.get("education", [])
    certs = data.get("certifications", [])
    
    audit_file = d / "schema-audit.json"
    audit = json.loads(audit_file.read_text()) if audit_file.exists() else {}
    
    summary = {
        "index": item["index"],
        "folder": item["folder_name"],
        "file": item["file"],
        "pdf_first_lines": lines[:6],
        "full_name": contact.get("full_name"),
        "professional_title": data.get("professional_title"),
        "total_experience_years": data.get("total_experience_years"),
        "job_count": len(jobs),
        "jobs": [
            {
                "company": j.get("company"),
                "role": j.get("role"),
                "start": j.get("start_date"),
                "end": j.get("end_date"),
                "is_current": j.get("is_current"),
                "resp_count": len(j.get("responsibilities", []))
            }
            for j in jobs
        ],
        "edu_count": len(edu),
        "education": [
            {
                "inst": e.get("institution"),
                "degree": e.get("degree"),
                "start": e.get("start_date"),
                "end": e.get("end_date")
            }
            for e in edu
        ],
        "cert_count": len(certs),
        "certifications": [
            {
                "name": c.get("name"),
                "issuer": c.get("issuer")
            }
            for c in certs
        ],
        "audit_status": audit.get("status"),
        "audit_reason": audit.get("reason"),
        "audit_findings": audit.get("findings", []),
        "warnings_count": len(warnings)
    }
    results.append(summary)

eval_json = out / "evaluation-analysis.json"
eval_json.write_text(json.dumps(results, indent=2))
print(f"Wrote evaluation analysis to {eval_json}")

