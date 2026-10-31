# Visible correction metadata and date-derived totals

Default standardized exports now include `warnings` and `standardization_metadata`.
The latter includes `corrections`: applied changes with field paths, original and
normalized values, rule basis and explanation. Full source audit remains optional.
Spelling suggestions have `applied=false`; they are not reported as applied corrections.
The existing safe technology aliases and deterministic formatting changes are logged.
Normalization accounting now visits individual fields within equal-length record lists,
so a whitespace/date change is attributed to its specific record and field.

`data.total_experience_years` now uses the union of dated employment intervals,
excluding gaps and counting overlaps once. Explicit current roles end at the
request's reference/current date, recorded in metadata. The original numeric claim
is preserved as `data.stated_total_experience_years`; summary wording such as “14+”
remains unchanged. Reprocessing the exported data preserves the original numeric claim.
Totals are decimal years rounded to one decimal, not a years.months notation.

Incomplete, invalid or rejected employment records prevent presenting a partial
total as complete: `total_experience_years` is null, while metadata retains the
partial calculation and an incomplete-total warning. Unsupported dates are not inferred.

Local date-range mapping now retains an immediately following parenthesized elapsed
claim, preserving literal evidence. The grounded-review prompt requests this too.
Duration discrepancy checks recognize years/yrs and months/mos, including “and”.
An explicit mismatch is logged as an applied system correction and remains a review
finding because the underlying source dates may themselves require verification.

## Source check and runtime verification

Read the user-specified PDF locally with `pdftotext -layout`. It states September
2013–May 2024 with “10 yrs 9 mos”, and June 2024–Present. Under the existing elapsed
calendar-month policy, these yield 128 and 28 months as of 31 October 2026:
**13.0 years total**, with the gap excluded. The source summary claims 14+ years.
No candidate-specific production rule was added. This checks the dates visible in
that PDF; it does not silently rewrite old saved extraction/mapping files or repair
missing dates in an earlier extraction.

The restarted API was tested using a synthetic payload with these date patterns:
`api-smoke.json` contains the actual default response. It has a 13.0-year calculated
total, the retained 14-year numeric claim, a 10-year-8-month corrected duration,
visible applied corrections, and the 2026-10-31 as-of date. No provider calls.

Regression tests: `tests/test_correction_metadata.py` plus existing standardization,
source mapping, mocked-provider, API and cached local-model regression suites.
**785 passed, 2 skipped, 15 deselected** in the final offline selection.
`git diff --check` passed.
The offline selection excludes external-provider tests and two Node diagnostic tests;
Node-dependent tests skip when Node is unavailable.

App: http://localhost:8080. Regenerate/export JSON to obtain the new fields.
