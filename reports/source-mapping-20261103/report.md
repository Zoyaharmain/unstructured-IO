# Source-led resume mapping repairs — 3 November 2026

The supplied Jaydipsinh Chudasama.pdf was replayed locally from PDF extraction through section detection, schema mapping and standardized consumer export. No candidate data was sent to an external model. A second run deliberately supplied mocked field-review omissions and an incorrectly split award to verify deterministic recovery.

## Causes and changes

1. **Name/title boundary.** The PDF extraction joins a large name row and a smaller professional heading into one element. Local segmentation had correctly separated these, but the identity mapper joined adjacent fragments again. `physical_card_recovery.py::recover_physical_cards` uses distinct physical PDF rows and font sizes to mark the name and professional heading. `schema_mapping.py::map_schema` excludes the heading from identity joining and accepts the literal heading even without a job-title keyword. Field review restores this source-established name/title if omitted. This is typography/context logic; no candidate name or professional-heading string is embedded in production rules.
2. **Employers, departments and aligned dates.** A short employer plus a department/operations description was not recognized, and a right-aligned location/date column was rejected as unrelated. `record_subfields.py::employment_header_fields` handles the department qualifier; `dated_record_headers.py::split_employment_headers` ignores punctuation-only separators and permits a bounded right-hand location/date column when employer and role come from the same source element. `recover_split_employment_headers` repairs the entry boundaries and retains adjacent duties. Independent columns and client rows cannot establish an employer.
3. **Education grammar and dates.** `education_subfields.py::DEGREE` and `record_relationships.py` recognize plural Bachelor forms. Institution detection excludes activity prose such as student representation on a college team. Exact month/year ranges populate both education dates. School qualification names and grades are kept in separate fields.
4. **Shared school institution.** `education_context.py` establishes an institution-only reference for sibling Class 10/Class 12 qualifications split from the same original element. `SectionEntry.context_fields` is additive and defaults to empty. Qualification ownership remains disjoint. Source and hierarchy validators require the school context to be supported by a sibling record and allow its evidence only for the institution field. Compact-review expansion preserves that permission; record ownership IDs exclude context. Completeness checking recognizes the declared institution context without authorizing unrelated overlaps. Dates and grades cannot be inherited. The unstated Class 10 completion date remains null.
5. **Achievement heading and card boundaries.** Heading lookup tolerates a tightly bounded transposition in known section labels without changing source spelling. Explicit award headings can end an inherited education section. Existing wrapped/bulleted achievement grouping is preserved, while a styled award title owns its result prose and date. `awards.description` is now an optional schema field. `section_subschemas.py` maps the title, description and date separately. `physical_card_recovery.py::repair_physical_card_fields` prevents field review from splitting a confidently established card again.
6. **Total experience.** Restoring the internship dates removes the incomplete-timeline condition. The existing standardization union calculation now produces 6.2 years as of November 2026 across all four roles the source places in Professional Experience, including the NGO role. Overlaps are counted once and gaps excluded. This does not infer whether any role was paid. Existing duration/date/total-calculation warnings and original source evidence are retained.

## Verified output

- Name: JAYDIPSINH CHUDASAMA; professional title: INVESTMENT BANKING OPERATIONS.
- Northern Trust / Senior Financial Analyst / January 2025–Present.
- Northern Trust / Financial Analyst / July 2022–December 2024.
- Riansh Corporate Private Limited / Finance Intern / April 2021–January 2022.
- Girl Up Vriddhi (NGO at United Nations Program) / Vice-President and Project Manager / February 2020–January 2022.
- Three education records: Bachelors in Commerce, Class 12th and Class 10th. College dates July 2019–May 2022 and CGPA 9.8 are mapped. Both school records cite the same named school through explicit context; their grades remain separate. No Class 10 date is fabricated.
- One Sustainable Business Plan Competition award, with its original third-place description and August 2021 date.

See `corrected-consumer.json`, `live-extraction.json`, `live-mapping.json`, `live-check.json` and `mock-reviewed-mapping.json`. The live check used fresh upload -> extraction -> local detection -> schema -> consumer JSON with review_fields=false. The mock check exercised the review pipeline without contacting a provider. External provider variability itself is not verified by these runs.

## Validation and limits

New regressions in `tests/test_physical_card_recovery.py` cover typography, department-qualified employers, right-aligned dates, heading transposition, award split recovery, Bachelor variants, institution-only school context, disjoint ownership, missing dates, prohibited date borrowing and unrelated context rejection. Existing wrapped-achievement tests and an actual multi-column resume test pass.

The full suite is not claimed clean. Three tests require absent files under `.upstream/batch-validation/documents/` (Benjamin, Anita and the saved seven-job identity test). Three mapping assertions already fail against an isolated unchanged HEAD copy: explicit supplied field-boundary enforcement (`test_schema_mapping.py`), three-column employment alignment (`test_structural_grouping.py`), and date-first qualifications (`test_word_record_recovery.py`). The baseline comparison also confirmed the actual multi-column regression passes at HEAD; the newly introduced regrouping problem was corrected and that test passes again. These six existing failures are not hidden or relabelled as successful checks.

No universal semantic accuracy claim is made. Original resume text remains authoritative, unrepresented content stays visible, and unsupported fields remain empty. No new provider calls were added by these deterministic repairs. The application was restarted at http://localhost:8080.

Final full local selection: **918 passed, 6 pre-existing failures, 2 skipped, 15 deselected**, in 91.55 seconds. Two existing Node frontend checks were excluded. `git diff --check` passed.
