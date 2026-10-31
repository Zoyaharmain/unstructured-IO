# Assign-schema latency: smaller responses and one-window review

Stage 3 was still requesting a verbose hierarchy: every source value was repeated
in evidence quotations, empty fields were represented twice, and logical-record
text repeated the source-block inventory. A typical three-batch document also
needed two network windows with two workers.

## Implemented

- Request a versioned `compact_fields_v1` provider response containing populated
  literal values and owning source IDs. The provider does not need to re-emit
  quotations and empty field arrays. Rebuild exact citations locally, then run the
  existing field, ownership, source and completeness validation before commit.
- Preserve explicit missing statuses; an unreported empty field stays `unmapped`,
  not presumed absent. Legacy verbose replies remain supported. The public JSON,
  field evidence and schema contracts remain unchanged.
- Remove duplicate text from logical-record prompt metadata while preserving
  record IDs, source IDs, block membership and structural hints. Original source
  text remains in the block inventory.
- Default production field workers to three (configurable 1–4). Three independent
  batches can run together, retaining request budgets and validation/fallback.
- Report wire and expanded response character counts in field-review metadata,
  alongside batch workers/count and processing seconds.

Main code: `local_api/services/llm_schema_mapping.py`,
`local_api/services/llm_section_review.py`.

## Actual live measurement with invented text

Used a newly fabricated synthetic resume fixture, not a redacted or transformed
candidate resume. Same model, source, request budget and registry in both runs;
strict budget of two provider calls total, one per format. Both reviews completed
and the extracted `data` objects are identical.

| Provider response | Schema-review time | Wire characters |
| --- | ---: | ---: |
| Verbose | 4.683 s | 3,681 |
| Compact | 2.750 s | 2,389 |

This is about 41% less time and 35% fewer output characters in this small controlled
live comparison. It does not establish a guaranteed time for a longer resume or a
universal provider speedup. Provider load, source length and validation retries vary.

Artifacts: `synthetic-live-timing.json`, `synthetic-verbose.json`,
`synthetic-compact.json`. The synthetic transport output was not mocked.

## Source safety and verification

The user-provided PDF timing check was blocked by automatic approval review because
it would send personal/employment data to the configured external LLM. That check
was not executed or bypassed. User approval was requested. All live measurements
reported here use unrelated invented text only.

Compact-response regressions verify identical validated schema output, rejection
of fabricated values and foreign-record citations, exact original record context,
legacy strictness and honest handling of unreported fields. Existing complete-role
restoration, concurrency/budget and fallback tests remain in the regression run.
Final offline selection: **809 passed, 2 skipped, 15 deselected**. The selection
includes unit, mocked-provider, API and cached local-model tests; external-provider
tests and two Node diagnostic tests are excluded. Node-dependent tests skip when
Node is unavailable. `git diff --check` passed.

The app has been restarted on http://localhost:8080 with the compact response path
and three-worker default. Regenerate the schema to use these changes. No wall-clock
guarantee or timing result for the user's actual PDF is claimed.
