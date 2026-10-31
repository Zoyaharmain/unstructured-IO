# Complete target-role lists and faster schema review

## Root cause and correction

The previous local recovery correctly found the complete TARGET ROLES list. The
field-review model could nevertheless select only its first literal title. That
value passed citation validation because it was genuinely in the source, despite
being incomplete. The reviewed value then replaced the full local value.

`recover_target_role_lists()` in `local_api/services/llm_schema_mapping.py` now
restores the complete list under a unique explicit desired-role heading after
provider parsing. Exact source citations are rebuilt and normal source/hierarchy
validation runs again before commit. Data and subschema values use the same full
list. Explicit heading context also overrides a partial local first-title guess
in `record_subfields.py`. Model instructions request the entire wrapped list.

The source-specific regression feeds the actual extracted PDF preference section
to the reviewed mapper, simulating a model response with only “Senior Program
Manager”. The accepted output restores:

> Senior Program Manager | Business Transformation Manager | Operations Transformation Manager | Change Management Lead | Continuous Improvement Manager | Governance, Risk & Controls Manager | AVP / Assistant Director – Operations

The preferred scope remains `India | UAE & Middle East | UK | Europe | Remote / Global`
in work_preferences, separate from residence. This source-specific verification
uses general production rules; no name, employer or candidate-specific lookup was
added. The artifact is a contact/preference-section regression, not a new complete
resume extraction.

## Schema latency

Independent field-review batches now run in bounded windows. Production defaults
to two workers (`DEEPSEEK_FIELD_WORKERS`, supported range 1–4); custom callers using
explicit ReviewSettings retain a default of one worker. For three batches, this
allows two waves rather than three sequential waits. The model/input/context limits,
shared request budget and source validation remain unchanged. Budgets are reserved
before dispatch. Results are consumed in source order. An already-running sibling
can finish after another fails; later windows are not dispatched. Successfully
validated batches remain available if another batch fails.

Paid completion POSTs no longer silently repeat HTTP errors or transport timeouts.
Previously the provider adapter could retry twice, despite the caller comment
claiming no automatic retries. Read-only model/connection checks still retry
transient failures. Explicit schema-validation repair attempts remain bounded and
budgeted. A failure is surfaced with the validated local fallback rather than
silently starting another paid attempt.

A controlled test with two 0.2-second mocked provider waits measured **0.4358 seconds
sequentially versus 0.2458 seconds with two workers**, with two attempts in both
cases and identical accepted records. This demonstrates scheduling overhead and
parallelism; it is not a measured live-provider speedup. Live latency still depends
on response length, provider load and configured timeout.

Field-review metadata now reports `batch_count`, `batch_workers` and
`processing_seconds` to make assignment latency visible.

## Validation

**800 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider,
API and cached local-model regression selection. External-provider tests and
two Node diagnostic tests were excluded; Node-dependent tests skip where Node
is unavailable. `git diff --check` passed.

New regressions cover truncated first-title responses, exact source evidence and
consistent data/subschema values, overlapping batch execution, shared budget
limits, one-batch provider failure with another validated success, concurrency
bounds and no repeated paid POST on a transient HTTP error.

- `checks.json`: actual-source truncation regression and controlled-delay benchmark.
- `source-backed-target-review.json`: reviewed contact/preference schema with complete
  target-role data and citations. Provider output was mocked; no paid calls.
- `live-check.json`: restarted local API smoke check for the complete title list,
  preferred locations, date warnings and zero external calls.

App restarted at http://localhost:8080. Regenerate sections/schema JSON; old saved
or downloaded JSON is unchanged.
