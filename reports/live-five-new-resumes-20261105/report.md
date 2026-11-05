# Five new resumes: live DeepSeek test — 2026-11-05

All five files came directly from the requested RESUMES_FLAT folder. Their SHA-256 hashes differ from every file in the twelve manually tested originals. See selection.json for exact source paths, exclusions and hashes. The earlier AMAN AHUJA run was not included or rerun.

Fresh processes loaded the updated .env. Provider: https://api.deepseek.com; actual recorded model: deepseek-flash. User explicitly approved this destination. No application code or .env was changed.

**Result: five executed, zero clean accuracy passes.** All processes exited 0 and produced JSON, but all retained mapping defects or incomplete verification. HTTP success, source coverage and schema validity do not establish semantic correctness.

| Resume | Seconds | Calls / returned responses | Section review | Field review | Final audit |
|---|---:|---:|---|---|---|
| A Lokhande.pdf | 100.8 | 8 / 8 | complete | failed | complete |
| A Madhavi.pdf | 91.8 | 15 / 15 | complete | partial | complete |
| AJAY KUMAR CHAUDHAR.pdf | 66.7 | 7 / 7 | complete | failed | incomplete |
| AMIT_RANA.pdf | 200.0 | 18 / 17 | complete | failed | incomplete |
| ANANDKUMAR.pdf | 58.8 | 13 / 13 | failed | partial | not_run |

Total: 61 call attempts, 60 saved successful responses; 518.1 seconds processing (~8.6 minutes). Per-document times include extraction, local models, live section/field review and audit/recovery. Standardization exports were generated afterward locally using the API route's standardization functions.

All five final section outputs passed deterministic extracted-source interval validation. No empty/punctuation-only needs_review entries remained. These checks did not prevent the semantic errors listed below. The two complete schema audits reported concerns; complete means the audit ran, not that the resume passed.

## Source-to-output findings

### A Lokhande.pdf

Source names Capgemini and Cognizant. Output uses a responsibility fragment as the first employer and leaves the second employer null. First responsibility is a mid-sentence fragment. Field review rejected an invalid/cross-record responsibility quote and retained local values. Education lacks an institution in the extracted source; do not invent one.

Stop reason: `no_source_or_mapping_progress`. Needs-review blocks: 2. Final audit findings: 33.

[Standardized JSON](01/standardized.json) · [Extracted source](01/extraction.json) · [Mapping](01/schema.json) · [Audit](01/schema-audit.json) · [Pipeline](01/pipeline.json)

### A Madhavi.pdf

Four employer names and date ranges are captured. Professional title retains the Role: label. Education retains Andhra University but omits Gayatri Vidya Parishad. The advisory audit flags responsibility sentences mapped as project names, underpopulated skill categories, and certification names containing issuer/year text. Field review is partial; zero needs_review blocks does not mean correct mapping.

Stop reason: `recovery_budget_exhausted`. Needs-review blocks: 0. Final audit findings: 16.

[Standardized JSON](02/standardized.json) · [Extracted source](02/extraction.json) · [Mapping](02/schema.json) · [Audit](02/schema-audit.json) · [Pipeline](02/pipeline.json)

### AJAY KUMAR CHAUDHAR.pdf

Source has employer/client hierarchy under Virtusa (Citi and HSBC) and CMS, plus four earlier employers. Output misuses a coordination responsibility as a Virtusa role, has no employer for the HSBC role, loses several date ranges, and appends responsibility text to older roles. Education institution retains the prefix from. Field review rejected invalid evidence; final audit rejected foreign source references (foreign_audit_source). Total experience remains null.

Stop reason: `schema_audit_failed`. Needs-review blocks: 0. Final audit findings: 0.

[Standardized JSON](03/standardized.json) · [Extracted source](03/extraction.json) · [Mapping](03/schema.json) · [Audit](03/schema-audit.json) · [Pipeline](03/pipeline.json)

### AMIT_RANA.pdf

Source contains six jobs: Mercor, TMO, AT&T, Sungard, Telefonica and Datamatics. Output contains five: AT&T is absent; Mercor and TMO employers/dates are empty. Education splits Bhagalpur College of Engineering incorrectly. The PMP issuer line becomes a separate certificate; CSM and HCIA are merged. Field review ends provider_unavailable after one unsuccessful call. Audit ends invalid_audit_finding. Total experience remains null.

Stop reason: `recovery_budget_exhausted`. Needs-review blocks: 0. Final audit findings: 0.

[Standardized JSON](04/standardized.json) · [Extracted source](04/extraction.json) · [Mapping](04/schema.json) · [Audit](04/schema-audit.json) · [Pipeline](04/pipeline.json)

### ANANDKUMAR.pdf

Source identifies ANAND KUMAR at the top and labels Late Rameshwar Shah as Father Name. Output incorrectly uses the father name as full_name. Four employers are captured, but all normalized dates and durations are null despite explicit source ranges using ordinal days and two-digit years. Academic Profile contains M.Tech, B.Tech, HSC and SSC; output education is empty. Section review rejects invalid assignments; field review remains partial and the final schema audit does not run.

Stop reason: `section_review_failed`. Needs-review blocks: 0. Final audit findings: 0.

[Standardized JSON](05/standardized.json) · [Extracted source](05/extraction.json) · [Mapping](05/schema.json) · [Audit](05/schema-audit.json) · [Pipeline](05/pipeline.json)

## What these tests establish

The current pipeline still fails on general record boundaries, employer/role ownership, wrapped lines, parent employer/client relationships, identity-versus-family details, grouped education/certification records and ordinal/two-digit date parsing. Invalid LLM evidence correctly fails validation, but retaining defective local fields and spending additional calls does not repair those defects. A clean needs_review panel can coexist with severe incorrect assignments.

Recommended next work: correct these general parsing/ownership rules, keep invalid provider assignments rejected, ensure failed/partial field review makes the result explicitly review-required, and add reproducible source-backed regressions for these five before rerunning paid calls. Audit responses must use existing source IDs. Failed audits must never be treated as zero findings or a pass.

## Reproduction and limits

Runner: scripts/check_single_resume.py with --llm-review --recovery-attempts 1, directly reading each manifest path. Each numbered folder retains extraction, local sections, reviewed sections, field evidence, original provider requests/responses and per-pass feedback. standardized.json includes the consumer result, warnings, calculation metadata and source audit. selection.json and review-summary.json provide machine-readable scope/results.

Successful response counts are based on saved response files, not only provider-calls.json statuses: the existing recorded_transport updates provider_calls[-1] across concurrent field requests, which can leave misleading per-call statuses. Total attempts use the numbered request/call inventory. No additional paid calls were made for reporting.

This review compares meaningful extracted source content against JSON, with advisory LLM audit findings labeled as such. It is not an independent word-by-word visual certification of the PDFs or a claim that every field was checked. Extraction has visible glyph, hyphenation and layout artifacts in some files. JSON artifacts preserve these for diagnosis.
