# Check ten resumes offline

From the project directory:

```bash
.venv/bin/python scripts/check_resume_batch.py \
  --folder '/mnt/c/Users/Gopi Gedar/Desktop/resume' \
  --limit 10 \
  --output "reports/resume-batch-$(date +%Y%m%d-%H%M%S)"
```

Files are selected recursively in filename order. To test a deliberate mix of layouts, put exactly the ten chosen documents in a separate folder and pass that folder. PDF, DOCX and DOC are supported; extraction dependencies still need to be installed. Cached local models are required. Empty PDF extraction attempts OCR once. A default 120-second extraction/sectioning deadline applies per document; change with `--timeout`.

The runner reuses the existing offline corpus extractor and the production local mapper. It disables DeepSeek and Python network connections; no `.env` credentials are loaded. It checks source interval coverage, field citations, record ownership and schema contracts. It saves extracted text, sections, mapped schema, private per-document reports, results.json, summary.json and report.md. Output directories are created with restricted access and must be new.

## Check semantic accuracy

Open each original resume alongside its `.schema.json` artifact. Copy `expected.template.json` to a separate reviewed-answer file. Each filename is bound to its PDF/DOCX SHA256. Fill only facts independently confirmed in the original, for example:

```json
{
  "Example.pdf": {
    "sha256": "keep-the-generated-source-hash",
    "human_reviewed": true,
    "expected_data": {
      "contact": {"full_name": "Alex Example", "email": "alex@example.com"},
      "experience": [
        {"company": "Example Labs", "role": "Software Engineer"}
      ],
      "education": [{"institution": "Example University", "degree": "BSc"}],
      "projects": [{"name": "Search Portal"}]
    }
  }
}
```

Use the existing schema's exact names and types. Object fields omitted from expectations are not scored. Lists require the exact number of records, match without ordering, and compare the specified fields together within each record. Use `[]` to assert that a category has no records. Expected values use exact equality, including punctuation and spelling. This intentionally exposes incorrect extraction or normalization.

Run the same folder again with a new output directory:

```bash
.venv/bin/python scripts/check_resume_batch.py \
  --folder '/mnt/c/Users/Gopi Gedar/Desktop/resume' \
  --limit 10 \
  --expected reports/reviewed-resume-answers.json \
  --output "reports/resume-batch-reviewed-$(date +%Y%m%d-%H%M%S)"
```

Accuracy remains `not_reviewed` until human_reviewed is true. Changed source hashes produce stale_expectations, and empty approved expectations are invalid. A comparison pass certifies only the declared fields; it does not certify every word or every field. Unresolved attributes and review reasons are reported even when operational checks pass. Unknown unexpected exceptions expose their type and sanitized diagnostics rather than raw resume text.

Exit code 1 indicates extraction/mapping failure, expected-answer mismatch, stale expectations or invalid approved expectations. Exit code 0 means operational checks and any supplied comparisons passed; it does not imply unreviewed resumes are semantically correct.

Initial execution: reports/resume-batch-10-20261027/report.md — ten filename-sorted documents from the Desktop resume folder; ten source/schema check passes, ten require review, zero human-answer comparisons, zero provider calls.
