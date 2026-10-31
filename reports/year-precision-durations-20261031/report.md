# Year-only experience durations

## Source finding and root cause

Read the supplied Ashfaq Rahman PDF locally with pdftotext. Its employment headers
state 2023–Present, 2020–2023 and 2018–2019. No start/end months are stated or lost
at these headers. The existing duration function explicitly rejected year-only
precision and returned insufficient_dates. This was a precision-policy limitation,
not a missing-month extraction bug.

## Implemented general policy

Valid year-only and mixed year/month ranges now produce explicitly labelled
annual-resolution estimates. Source date strings retain their supplied precision;
no January/December employment dates or missing months are added to JSON. Current
roles use the request's reference year, with the actual as-of date recorded.

| Source range | Output as of 31 October 2026 | Estimated months |
| --- | --- | ---: |
| 2023–Present | Approximately 3 years | 36 |
| 2020–2023 | Approximately 3 years | 36 |
| 2018–2019 | Approximately 1 year | 12 |

The month counts are conversions of coarse annual estimates, not known elapsed
months. Same-year ranges say “Less than 1 year (year precision)”. Exact duration
cannot be established from year labels alone. Invalid, future or missing dates
still remain uncalculated with explicit warnings.

Every estimated record has an applied duration_estimated_year_precision warning
and metadata duration_status=estimated_year_precision and duration_is_approximate=true.
These warnings remain visible in default JSON and its corrections metadata. Source
stated ranges are retained separately.

Coarse year-level intervals participate in the non-overlapping total using common
computational year boundaries, never asserted actual employment dates. For this
saved mapping the result is approximately **7.0 years**, with the 2019–2020 label
gap excluded and touching/overlapping year-label intervals counted once. Metadata
calculated_experience_is_approximate is true and a total-experience estimate warning
explains that real months, gaps and overlaps remain uncertain. Completeness means
all supplied records contributed at their available precision, not exact dates.

Month/day precision calculations are unchanged, including the prior September
2013–May 2024 result of 128 months / 10 years 8 months.

Implementation: local_api/services/standardization/dates.py, service.py,
contracts.py, consumer.py and export.py. No candidate-specific production rule.

## Verification

**836 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider, API
and cached local-model selection. External-provider tests and two Node diagnostic
tests were excluded; Node-dependent tests skip where Node is unavailable.
The new tests cover year-only/current roles, source immutability, mixed precision,
same-year labels, future/reversed dates, estimated totals and overlap resolution.
`git diff --check` passed.

The restarted API standardized Ashfaq's existing saved mapping in 0.105 seconds,
with all three durations populated and all three estimate warnings present.
The saved input file was verified unchanged. No external provider calls.
This is a duration-policy verification using a saved mapping, not a fresh full
semantic audit of all other fields in that mapping.

- ashfaq-year-estimates.json: actual default JSON from the restarted API.
- checks.json: runtime assertions, precision flags and zero-provider-call result.

App: http://localhost:8080. Regenerate JSON to use this policy. Previously downloaded
files remain unchanged.
