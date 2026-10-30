# Standardized resume output and calculation provenance

Extended the existing uncommitted standardization layer without replacing source-bound fields or schemas. No provider/network calls were made.

## Contract

Consumers use `standardized_data`; original `data`, `section_schemas`, source evidence, raw sections and mapping diagnostics remain source-bound. Normalized experience records carry raw_start_date, raw_end_date, raw_duration, ISO dates/precision, is_current, duration, duration_months, duration_is_approximate, duration_as_of and duration_status.

Standardized duration contains calculated time only, never a date-range string. Present/Current resolves to the explicit as-of date for calculation; it is not evidence that the job ended. Raw end marker is preserved. Month precision uses inclusive calendar-month coverage, marked approximate. Example JAN 2022–JUN 2022 is six covered months. Exact-day start/end use completed calendar units, so a one-day job is not reported as one month. Metadata records both policies.

Year-only, ambiguous numeric, invalid/reversed/future or incomplete dates have null calculated duration and an actionable warning. Short years use a documented century inference and a warning; reference_date is injectable for reproducibility. Arbitrary unknown date text is preserved rather than guessed. Aggregate experience remains a calendar-month coverage estimate with overlapping intervals merged; incomplete coverage is flagged by calculated_experience_complete. It is not an exact day-level aggregate.

Warnings include source field path, original value, proposed value, basis, applied flag and verification status. Curated dictionary spelling/alias matches are candidates, not proof. Responsibility text, names and location suggestions are not silently rewritten. A uniquely similar location repeated in the same document can produce an advisory suggestion; original location remains unchanged. Unknown locations are explicitly not externally verified. No paid geography/spelling lookup was performed.

The mapping route attaches prior pipeline field_evidence to standardization_metadata. These IDs identify the source basis of derived values; they do not turn a derived duration or spelling suggestion into an original quote. Standalone `/api/v1/resume/schema/standardize` is also available for previously extracted JSON. Its formatting/validation results do not independently re-verify an uploaded schema's facts.

UI duration fields show calculated time, granularity/as-of information, and retain the original date range inside source evidence. Standardization notices show suggestions and their basis.

## Attached JSON example

`A_Madhavi.standardized.json` preserves the uploaded JSON and adds the standardized fields. Reproducible as of 2026-10-29:

| Source period | Approximate inclusive-month duration |
|---|---|
| Aug 2022–Present | 4 years 3 months |
| Jan 2022–June 2022 | 6 months |
| May 2021–Dec 2021 | 8 months |
| Jan 2017–May 2021 | 4 years 5 months |

A different elapsed-month convention would produce different figures; this output explicitly identifies the chosen coverage policy. Closed dates retain source granularity rather than inventing exact days.

## Validation

47 affected tests passed, covering existing standardization, duration variants, current roles, year-only/ambiguous/invalid/future dates, exact-day calculation, protected source preservation, advisory location variants, and the local standardize endpoint. JS syntax and Python compilation pass. An unrelated pre-existing trailing blank line in tests/test_resume_sections.py was reported by whole-workspace diff checking and was left untouched.

No claim is made that every possible misspelling, name or location can be automatically proven correct. Evidence-free assertions remain unverified.

## Primary-output correction

The initial example/download retained source-bound `data` as the primary object, which made the original range appear unchanged despite an additional standardized_data object. Corrected consumer export:

- `data` now contains canonical values, including calculated duration and duration_months, without raw_* duplicates.
- Original values and citations are preserved under `source_evidence`, clearly separated from the primary result.
- UI JSON preview and default schema download use the canonical export (`.standardized.json`). Internal mapping responses retain source-bound data for validator compatibility.
- `/schema/standardize` additionally returns canonical `data` and source_evidence while preserving its existing standardized_data property for API compatibility.
- A_Madhavi.standardized.json has been rewritten in this consumer format. The previous combined source-bound file is preserved as A_Madhavi.source-bound.json.

Verified as of 2026-10-29: first primary job duration is 4 years 3 months / 51 inclusive covered months, is_current=true, duration_as_of=2026-10-29. This is approximate calendar-month coverage, not exact elapsed days.

49 affected tests passed, including exact equivalence between Python export and browser-download transformation, primary duration placement, source immutability, and preservation of the original date range only in source evidence. JS syntax and changed Python compilation passed. No paid calls.

## Experience layout cleanup

The technologies array was empty; the duration/precision properties following it were sibling fields, not technology items. The canonical export now orders business fields together: company, role, location, dates, current status, calculated duration/months, responsibilities and technologies. Duplicate ISO dates, date precision, approximation/as-of/status details move to standardization_metadata.experience_calculations with a record_path. No technology values are synthesized or removed. Internal source and standardized models retain all information; only the consumer layout changes. Browser, Python export, standalone standardize API, and the example file use the same layout. Three export regressions pass, including matching browser/Python output, source preservation and technology/calc separation; the combined affected suite passes 25 tests. No paid calls.
