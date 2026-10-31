# Date warnings, desired-role mapping and processing overhead

## Corrections visible in the default JSON

Applied date representation changes now have an explicit `date_standardized`
warning stating that the system corrected the representation to ISO format.
Each retains the original value, normalized value, field path and deterministic
rule basis. A formatting correction is not independent verification of a date.
Missing/ambiguous dates are not guessed or described as corrected calendar dates.
All applied normalizations remain in `standardization_metadata.corrections`;
unapplied spelling suggestions remain separate warnings with `applied=false`.

Implementation: `local_api/services/standardization/validation.py`.

## The four source spans

Re-extracted the user-specified PDF locally. Its last two extracted elements contain
exactly the four spans reported by the user: TARGET ROLES, two title-list fragments,
and the geographic/remote continuation. Local detection incorrectly placed them in
education; the user's LLM-reviewed output had abstained on those same spans.

A general bounded source-context rule now recognizes target/desired-role headings
and assigns the heading and continuation to `personal_information`. It maps titles
to `contact.target_role` and the explicit trailing preferred scope to
`contact.work_preferences`. It does not treat these as current employment,
professional title, candidate identity or residential location. Existing schema
fields are reused; no candidate-specific production rules were added.

For this PDF the title value retains the complete list ending in
“AVP / Assistant Director – Operations”; preferred scope is
“India | UAE & Middle East | UK | Europe | Remote / Global”.
Residence remains null. All four original source intervals and source citations
validate; none of these four spans remains unassigned. This is one preference
section represented by four source spans, not four employment records.

Implementation: `local_api/services/target_preferences.py`,
`local_completion.py`, `record_subfields.py`, `schema_mapping.py`;
section-review instructions also identify these preferences explicitly.

`after-mapping.json` includes the reviewed source-to-schema mapping and
`after-standardized.json` includes its default consumer projection. These are
local-only outputs: other document-level mapping/completeness findings remain
visible. Resolving the four preference spans does not validate every employment
association or manufacture missing employment dates. Previous downloaded files
are not rewritten.

## Processing time

Initial live extraction took 0.47 seconds, local detection 1.22 seconds and local
mapping 0.20 seconds, without external review. The slow reviewed workflow had an
unnecessary rule forcing each repeated category into a separate provider call.
Modest sections can now share a request, subject to actual serialized-input and
context budgets, a 70-block packing bound and a 12-record packing bound. Complete
sections/record context and all validation gates remain intact. Provider failures
still retain successfully validated preceding batches. Tests force multiple
batches through real input budgets to verify partial-failure behavior.

On this actual section inventory the field-review plan changes from **6 batches
to 3**. This is a measured plan count, not a claim that a live provider completed
the whole resume in a fixed amount of time. No paid provider calls were needed to
resolve these four spans. Classification review still inspects the original source.

A bounded in-process cache reuses encoder vectors for repeated exact text during
recovery and repeated local detection. It retains at most 2,048 vectors with
hashed keys. It does not cache source IDs, classifications, schema assignments or
LLM output. Model/anchor files remain unchanged. The final offline benchmark took
1.3960 seconds for first detection+mapping and 0.5407 seconds for the warm repeat,
excluding model initialization and file extraction. The restarted API took 9.907 seconds on its first request including model loading,
and 0.632 seconds on the warm repeated request. These costs are recorded separately
in live-check-cold.json and live-check.json. Provider latency remains variable.

Implementation: `resume_sections.py`, `llm_schema_mapping.py`.

## Evidence and verification

**792 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider,
API and cached local-model regression selection. External-provider tests and
two Node diagnostic tests were excluded; Node-dependent checks skipped where
Node was unavailable. `git diff --check` passed.

- `extraction.json`, `before-sections.json`, `before-mapping.json`: baseline local run.
- `after-mapping.json`: four LLM-abstained spans reconstructed from the exact original
  intervals and successfully assigned with validated source-backed fields.
- `after-standardized.json`: default export with correction warnings/metadata.
- `checks.json`: local benchmark, packing counts and zero source-binding errors.
- `live-check.json`: restarted API smoke check with zero provider calls.
- New regressions cover target-role continuation across wide PDF rows, boundaries,
  incorrect education assignments, residence/current-title separation, exact source
  evidence, date-warning wording, vector-cache bounds and one-call mixed-section mapping.

App: http://localhost:8080. Regenerate sections and JSON to apply the improvements.
