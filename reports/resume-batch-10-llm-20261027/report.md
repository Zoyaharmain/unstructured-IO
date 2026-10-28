# Ten-resume LLM comparison

```json
{
  "scope": 10,
  "completed": 10,
  "source_schema_checks": {
    "pass": 10
  },
  "section_review_statuses": {
    "complete": 10
  },
  "field_review_statuses": {
    "complete": 8,
    "failed": 2
  },
  "audit_statuses": {
    "incomplete": 9,
    "complete": 1
  },
  "audit_failure_reasons": {
    "foreign_audit_source": 8,
    "provider_or_audit_validation_failed": 1
  },
  "mapping_statuses": {
    "needs_review": 7,
    "fallback_used": 2,
    "success": 1
  },
  "provider_calls": 98,
  "local_unresolved": 330,
  "llm_unresolved_completed": 208,
  "accuracy_percentage": null,
  "reason": "No independently reviewed complete ground truth",
  "unique_source_hashes": 10,
  "employer_spot_check": {
    "expected": 30,
    "source_available": 26,
    "local_recovered": 7,
    "llm_recovered": 17
  }
}
```

Source/schema checks measure coverage, ownership, types and citations; they do not prove semantic correctness. Unresolved attributes include genuinely absent optional values. Fewer unresolved fields is not an accuracy score. Provider calls include section placement, field mapping, audits and bounded feedback retries.

| Resume | Source/schema | Section review | Field review | Mapping result | Unresolved local → LLM | Calls |
|---|---|---|---|---|---|---|
| A A Ashwini.docx | pass | complete | complete | needs_review | 52 → 27 | 12 |
| A Fairoz.docx | pass | complete | failed | fallback_used | 16 → 19 | 9 |
| A Lokhande.pdf | pass | complete | complete | needs_review | 32 → 6 | 12 |
| A Sateesh Kumar 2.docx | pass | complete | complete | needs_review | 17 → 15 | 11 |
| A Sateesh Kumar.docx | pass | complete | complete | needs_review | 17 → 10 | 11 |
| A Suribhotla.pdf | pass | complete | complete | success | 17 → 5 | 6 |
| A.Bhargava.docx | pass | complete | failed | fallback_used | 18 → 21 | 9 |
| AananthyManoharan.docx | pass | complete | complete | needs_review | 33 → 18 | 7 |
| Abdul Shukoor.pdf | pass | complete | complete | needs_review | 106 → 70 | 11 |
| Abhishek Hanashi.pdf | pass | complete | complete | needs_review | 22 → 17 | 10 |

## Employer source spot-check

The employer subset was independently inspected in original DOCX XML and PDF text. This is an assistant spot-check, not human-approved comprehensive ground truth. It matches employer cores to distinct company fields, ignoring punctuation/case and tolerating city suffixes; it does not score roles, dates, responsibilities, exact boundaries, invented extra records or other fields.

| Resume | Checked employers | In extraction | Local recovered | LLM recovered |
|---|---|---|---|---|
| A A Ashwini.docx | 3 | 3 | 0 | 3 |
| A Fairoz.docx | 2 | 2 | 0 | 0 |
| A Lokhande.pdf | 3 | 3 | 1 | 3 |
| A Sateesh Kumar 2.docx | 2 | 0 | 0 | 0 |
| A Sateesh Kumar.docx | 2 | 0 | 0 | 0 |
| A Suribhotla.pdf | 3 | 3 | 0 | 3 |
| A.Bhargava.docx | 7 | 7 | 0 | 0 |
| AananthyManoharan.docx | 2 | 2 | 2 | 2 |
| Abdul Shukoor.pdf | 4 | 4 | 4 | 4 |
| Abhishek Hanashi.pdf | 2 | 2 | 0 | 2 |

Detailed sanitized statuses, mapping diagnostics, audit findings counts and record counts are in comparison.json. Each resume-NN folder preserves source extraction, review requests/responses, final schema, pass history and advisory findings. No additional API calls are made by this report.

[Confirmed failure details and interpretation](FINDINGS.md)

Employer subset recovery: **17/30 (56.7%) with LLM**, versus **7/30 (23.3%) local-only**. This is not an overall accuracy percentage and does not penalize invented extra records. All 10 source hashes and extracted text inventories match the baseline.
