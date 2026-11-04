# Employment continuations and empty review artifacts

Verified against the actual Girish Morab.pdf through fresh localhost upload, extraction, local section detection and final standardized JSON. Additional field review used a mocked provider with a deliberately split tools record. No resume content was sent to an external provider during verification.

## Root causes

- Work subheadings such as Key Responsibilities & Achievements were treated as top-level award headings. This broke the surrounding employment scope and allowed following prose/tools to be proposed as independent jobs.
- Header splitting treated hyphens inside parentheses as field separators, fragmenting qualified role titles and project names.
- Tool-list labels and introductory By ...ing narrative clauses were insufficiently distinguished from employer identities.
- Nested client-project Role labels could overwrite the employment role.
- Source coverage correctly retained empty PDF elements, but those empty spans were also sent for classification and displayed as review work. Empty text has no classification uncertainty.

## Changes

`employment_scope.py::recover_employment_scope` identifies the explicit employment chapter and complete literal employer/role/date headers. It restores the section and job membership around those headers, preserving nested tools, results, client programs and responsibilities with their dated owner. It requires at least two strong headers and abstains if another date range in the chapter is not represented, preventing an unfamiliar dated job from being silently folded into its neighbor. Work subheadings do not become new jobs or top-level award sections. `physical_card_recovery.py` preserves this established scope.

`record_subfields.py::employment_header_fields` now splits separators only outside parentheses. Technology & Tools and Tools & Technology use existing technology fields rather than company inference. Gerund-led By clauses are narrative. In established dated cards, client-project identity labels cannot overwrite top-level employment identity. Label-only responsibilities and standalone tools rows are excluded from responsibility values, while their original source remains retained.

`employment_scope.py::repair_dated_employment_scope` restores the source-established job boundaries if field review splits a tools paragraph into another record, merges jobs or omits a job. If ownership is already correct, it repairs only literal identity/date fields; it retains reviewed duties and technologies. It adds no provider calls.

`empty_source_artifacts.py::separate_empty_source` moves blank/whitespace spans into the additive `SectionResponse.source_artifacts` audit collection. It preserves their original element IDs, offsets, page and text, and reindexes existing entry/field/readable-group references. It does not drop or reclassify meaningful text. Local detection, recovery, mapping and section review apply this separation. Source validation, accounting and coverage include artifacts; review prompts and chunk plans exclude them. The frontend additionally suppresses blank review cards from cached responses. Meaningful uncertain text can still require review.

## Actual output checks

The actual fresh API run has exactly four jobs:

1. PayPal (Contract) — Senior Program Manager (TPMO - Technical Program Management Office), October 2024–Present.
2. Trianz Digital Consulting — Associate Director, Delivery, October 2021–May 2023.
3. Genpact Headstrong Capital Markets — Sr. Manager (Senior Principal Consultant), July 2017–September 2021.
4. Wipro Technologies — Project / Program Manager, August 2000–July 2017.

Tools remain in technologies; the insurance/reinsurance impact text belongs to Trianz; the fixed-price client program and platform migration remain under Wipro. None of the three reported false company values is an independent employment record. All four jobs have calculated durations. The 24 empty PDF spans remain auditable artifacts, and there are zero empty `needs_review` blocks. This does not claim that all meaningful uncertain preamble text was classified in the local-only run; it remains available for actual semantic review.

Artifacts: `corrected-consumer.json`, `live-extraction.json`, `live-sections.json`, `live-mapping.json`, `live-check.json`, `mock-reviewed-mapping.json`. The actual-source mocked field review also passed with four jobs, 24 audited artifacts and no empty review items.

## Regression checks

- New generic tests cover nested qualified titles, tools, narrative results, client-project roles, scope recovery after subsection bleed, prevention of a model-created tools job, blank/whitespace auditing, omission of blank prompt spans, coverage preservation and abstention for unfamiliar dated header formats.
- Existing classification, chunking, source preservation and frozen-response tests pass. Frozen uN responses are rebound in test code by exact original source spans because blank artifacts no longer get classification IDs. Source ownership assertions remain in place; old blank-review assertions were updated to require audit retention instead.
- Full local selection: 922 passed, 6 pre-existing failures, 2 skipped, 15 deselected, in 101.30 seconds. The same six failures were documented in `../source-mapping-20261103/report.md`: three absent private fixtures and three mapping assertions reproduced against unchanged HEAD. No new failures remained in that selection.
- Final focused selection after responsibility-label cleanup: 88 passed in 22.23 seconds. Fresh API and actual-source mocked review passed afterward. `git diff --check` passed. Two existing Node frontend checks remain excluded; no browser rendering claim is made.

The local app was restarted at http://localhost:8080. Refresh the page and reprocess the PDF to replace old cached section/review results.
