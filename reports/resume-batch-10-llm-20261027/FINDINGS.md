# Findings from the approved ten-resume LLM run

Subsequent repairs and offline verification: [repair report](../resume-batch-repairs-20261027/REPAIRS_REPORT.md). The benchmark figures below describe the earlier paid run.

The scope is frozen in scope.json. Only the same ten original files were processed. The production single-resume CLI ran section review, field mapping and advisory audits with its bounded feedback policy. Requests/responses and each pass are retained privately in resume-NN directories. No validation was disabled and no pipeline repair was applied during the evaluation.

## Confirmed problems

1. **DOCX extraction loses employer text in text boxes.** Both Sateesh Kumar variants contain Velocity IT and Netafim in `word/document.xml` paragraphs inside `w:txbxContent`; neither name appears in the extracted elements. This was checked independently with ZIP/XML inspection, not inferred from the LLM result. `local_api/services/text_extraction_service.py:68–76` prepares Word files and serializes the upstream partitioner's output without a DOCX text-box coverage check. The model cannot cite the omitted employer names. In the first variant's final mapping, Amazon Web Services(AWS), a technology mentioned in responsibilities, is incorrectly used as company. Citation validity alone does not establish semantic correctness. Projects are also lost as project records in that variant.

2. **Fairoz's field mapping is rejected and falls back.** Employer statements are present in the original and extracted source, but final company/role remain unresolved. Final diagnostics include `parent_schema_validation / batch_section_mismatch` and `subschema_validation / scalar_multiple_values`, field role. The latter is raised by `llm_schema_mapping.parse_review` when a scalar contains multiple items. This evaluation retained the failure and fallback rather than silently truncating job titles.

3. **Bhargava's field mapping falls back after invalid JSON.** The extracted source contains the seven checked employer occurrences; final company fields recover none of those occurrences in the employer subset check. Both recorded final field-review diagnostics are `json_parsing / invalid_json`. The fallback remains usable for inspection but is not an accurate employment result.

4. **Abdul Shukoor recovers the four checked employers but also has an extra empty experience record.** Employer recall therefore overstates complete record accuracy. Strict citation/schema checks pass while this semantic issue remains. The result is still marked needs_review.

5. **Several advisory audits do not complete.** Most final failures use `foreign_audit_source`; the validator `review_chunking.audit_decisions` at lines 420–440 rejects empty or non-record-visible finding citations (except its explicit required-field absence case). This is an audit-contract/evidence failure, not proof that all mapped fields are wrong or that the entire resume was audited successfully. Other provider/audit validation failures are reported separately. Exact request/response artifacts are preserved for a follow-up diagnosis; validation has not been weakened.

## What the figures mean

- Source/schema checks validate the extracted-source inventory and record-local field citations. They cannot detect text omitted before extraction and cannot by themselves prove that a cited company is semantically an employer.
- `field_review=complete` means the provider output was accepted after validated repairs; consult mapping_result and diagnostic history for remaining concerns.
- Empty optional attributes may be genuinely absent. Their count is not an accuracy metric, and changed record counts make a simple before/after total especially easy to misread.
- The employer subset in source-employer-checks.json was independently inspected by the assistant in original DOCX XML/PDF text. It is not human-approved comprehensive ground truth. Matching ignores punctuation/case and tolerates location suffixes; each expected employer occurrence requires a distinct job record. It does not measure extra invented records, exact company boundaries, roles, dates, education, skills or full-resume accuracy.

The complete table and totals are in report.md and comparison.json. The system should not be considered production-accurate across these layouts based on successful HTTP responses or green step indicators. The next repairs should address original-document extraction coverage, record ownership/identity quality, malformed field responses and the audit contract before another paid benchmark.

## Final measured results

All ten approved sources finished; their hashes match the baseline, and all ten extracted element-text inventories are unchanged from the local run. No files outside the approved set were processed.

- Section review complete: 10/10.
- Final source/schema checks pass: 10/10.
- Final field review complete: 8/10; failed with retained local fallback: 2/10.
- Mapping status: success 1/10, needs_review 7/10, fallback_used 2/10. These are operational statuses, not accuracy certifications.
- Advisory audits complete: 1/10; incomplete: 9/10 (eight foreign_audit_source, one provider_or_audit_validation_failed).
- Selected original-source employer recovery: **17/30 (56.7%)** after LLM processing versus **7/30 (23.3%)** locally. This is limited entity recovery/recall, not overall field accuracy or precision. Four of these employer occurrences are missing from extraction; 26 are available in extracted text. The remaining misses include the rejected Fairoz and Bhargava mappings. Extra empty/wrong experience records are not penalized by this metric and are documented above.
- Empty attributes: 330 locally versus 208 after processing. This count includes genuinely absent optional fields and changed record sets; it must not be interpreted as an accuracy improvement percentage.
- Provider requests: 98 across the ten documents, including chunked section/field review, audits and bounded feedback passes. No additional benchmark/retry calls were started after this run.
- Offline report/comparison tests: 7 passed; changed script compilation and diff whitespace checks passed.

The paid run is complete. Overall semantic accuracy remains unmeasured; the observed extraction, mapping and audit failures mean the current system is not production-ready for these layouts.
