# Employment field completeness — 3 November 2026

## Finding

The previous saved local output did contain the two jobs, but its duty arrays had wrapped fragments, duplicate prefixes and incomplete tool categories. More importantly, `repair_dated_employment_scope` checked job ownership and identity fields but did not check responsibility/technology content when a provider retained the correct source IDs. A model could own an entire job's source blocks while returning only part of its description. Source ownership is necessary evidence; it does not establish that every identifiable field was populated.

A second boundary gap concerned combined employer/title rows followed by a date in another extracted element. The source-local scope logic previously required dates in the same element. Wrapped multiline headers also required distinct handling to avoid reading location/client metadata as employer text.

## Implementation

- `employment_details.py::duties_from_source` reconstructs literal duty paragraphs within confidently established employment cards. It removes label-only material, routes tool rows to technology fields, retains descriptions following tools inside a mixed paragraph, joins only supported wrapped continuations and preserves source order. No paraphrasing or invented responsibility text is used.
- `physical_bullet_starts` uses original PDF line coordinates and retained narrow list-marker coordinates to recover separate bullets inside merged paragraphs. Empty marker spans remain audit artifacts; they are not classification/review work.
- `record_subfields.py::refine_record` reads labels from complete source runs so physical line cuts cannot truncate tool lists. General technology-category labels (Agile/DevOps, cloud/data platforms, ETL/data integration, database/BI tools, etc.) reuse the technology field registry. These are field-label rules, not candidate/employer/tool-value constants.
- `employment_scope.py::recover_employment_scope` supports a complete literal employer/title row and a bounded adjacent date/location row, as well as a single dated job. It retains source and established records outside the employment chapter, abstains on unrecognized dates or competing undated identities, and records literal header evidence. `schema_mapping.py` uses that evidence rather than allowing a location row to become an employer.
- `repair_dated_employment_scope` now checks responsibility and technology **value coverage**, even when ownership IDs are correct. `covered_by_values` measures meaningful source characters represented by actual values; an oversized quotation alone cannot hide an omission. Incomplete duty content is restored from the validated source paragraphs. A complete reviewed segmentation remains intact. Existing strict citation/ownership validation still runs afterward.
- Multiline split-header parsing distinguishes a pure role row from a combined company/title row and rejects competing role evidence rather than treating a department or city as a new employer.

## Actual PDF verification

A fresh localhost upload of Girish Morab.pdf passed extraction -> local section detection -> schema mapping -> standardized consumer export:

- Four genuine employment records remain.
- PayPal has **7** responsibilities, including program leadership, portfolio execution, cross-functional collaboration, executive engagement, resource optimization, end-to-end program management and tracking/governance/RAID management.
- Trianz has **9** responsibility/impact items, including migration, portfolio ownership, account turnaround, pre-sales, four governance themes and the complete insurance/reinsurance impact statement.
- PayPal has its four explicitly listed technologies. Trianz has all **11** explicit technology values across its four tool categories.
- Name, phone/email and job-seeking text are not included as employment descriptions. The two jobs retain their original companies, roles, dates and calculated durations.
- There are zero empty review blocks; 24 empty source spans remain in the audit inventory.

`corrected-consumer.json` is the fresh actual-document export. `live-check.json` contains the assertions' results, and `live-extraction.json`, `live-sections.json` and `live-mapping.json` retain source/evidence traceability.

A separate actual-source mocked review kept every source ID and every identity field but deliberately retained only the first duty and first tool in each of the two jobs. The pipeline restored all 7 PayPal duties, 9 Trianz duties and 11 Trianz technologies. See `mock-reviewed-mapping.json`. This directly tests the previously unchecked omission, rather than only testing fake job boundaries. No candidate content was sent to an external model during these checks.

## Validation

New and extended tests cover full and partial duty/tool omissions despite complete ownership, overbroad evidence quotations, preservation of complete granular values, adjacent date elements, multiline headers, single-job resumes, wrapped paragraphs, physical bullet markers, identity ambiguity, chapter-local source conservation and source audits after header/body segmentation. Focused header/employment regression selection: 29 passed.

Full local unit/mock-provider/API-integration/local-model selection: **929 passed, 6 pre-existing failures, 2 skipped, 15 deselected**, in 123.42 seconds. The six existing failures are the same three absent private fixtures and three unchanged-HEAD mapping assertions documented in `../source-mapping-20261103/report.md`. Two existing Node frontend checks remain excluded. `git diff --check` passed.

The app was restarted at http://localhost:8080. Refresh and reprocess the PDF to replace cached output. External-provider variability was not tested live; the deterministic repair paths were tested with deliberate mocked omissions. No universal classification guarantee is claimed for genuinely ambiguous text.
