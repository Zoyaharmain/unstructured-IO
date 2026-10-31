# Repeated employer headings lost during PDF extraction

The actual AbhishekTiwari.pdf was inspected visually and replayed locally. It explicitly prints Crystaltech Services Private Limited above both roles. The initial extraction contained only its first occurrence; the second employer heading was missing while the Associate Software Engineer title and July–December 2023 date range survived. This was an extraction completeness failure, not evidence that the candidate omitted a company.

`local_api/services/pdf_source_recovery.py::recover_pdf_source` previously skipped every PDF character line whose compact text occurred anywhere in the extracted page. That page-wide substring check incorrectly treated a repeated heading at a different physical location as already represented.

The check now distinguishes physical occurrences. For repeated PDF lines, exact source-text matches are paired with retained PDF line bounding boxes. A match elsewhere on the page cannot suppress an unrepresented occurrence. Existing same-region occurrences are still skipped; no recovery is attempted from text alone when location evidence is absent. A precomputed occurrence counter keeps the additional geometry check limited to repeated lines. No company, candidate or job title constants were added to production code. No previous job's company is copied or inferred.

A fresh local extraction now has 36 elements instead of 35. The restored company line carries its own PDF character-layer text, bounding box and recovery audit event. Existing detection and mapping then attach it to the Associate Software Engineer job. Both roles remain separate employment records, each sourced to its own employer occurrence. Original upstream text is retained; re-extraction intentionally creates a new source inventory, so cached old blocks must not be reused.

The restarted API was checked end to end: upload/extract -> local section detection -> schema -> consumer export, with field review disabled and zero provider calls. The second job exports Crystaltech Services Private Limited / Associate Software Engineer / 2023-07 to 2023-12 / five elapsed months. See corrected-consumer.json, live-extraction.json, live-mapping.json and live-check.json. These are actual PDF results, not a synthetic replacement document.

Regression tests in tests/test_pdf_repeated_source_lines.py cover a missing repeated employer, both occurrences already retained, immutable input, recovery idempotence, missing location evidence and equal-height occurrences in different columns. Existing duplicate/overlap and source validation tests also pass.

Validation: 880 passed, 2 skipped, 15 deselected in 57.50 seconds for the unit/mock-provider/API-integration/local-model selection. Two existing Node frontend checks were excluded. git diff --check passed. The local app was restarted at http://localhost:8080. External LLM output for this PDF was not exercised during this verification.
