# Jayesh summary.statements investigation

## Confirmed live failure and limits

The running server logged diagnostic a52339b616f3476c8dfe94112a8b0e98:
source_evidence_validation / unsupported_value, field statements, at
/section_schemas/1/records/0/attributes/0/items/3/value (fourth statement),
on provider attempt 2. Attempt 1 failed overlapping_records in another section.

The submitted fourth statement, evidence quotes, and the ten-placement-change
SectionResponse were not persisted. The UI message and server log alone cannot
recover them. No file containing that live response was found. Consequently,
identifying its exact literal text/reference or claiming an exact live replay
would be unsupported. The controlled reproductions below are explicitly not
captures of the failing provider response.

## Request and error path

- local_api/static/schema.js:23 posts elements and the CURRENT sectionResult
  to /api/v1/resume/schema with review_fields enabled.
- local_api/routes/schema_mapping.py:71 map_existing_sections dispatches to
  llm_schema_mapping.map_with_field_review (:351).
- messages (:61) derives e{source_element_index}:{start}:{end} IDs from the
  supplied post-review blocks. parse_review (:79) reconstructs record owners
  and attributes and calls subschema_validation.validate_hierarchy (:13).
- validate_hierarchy (:41-45) first requires each evidence source_id to belong
  to the record and each quote to be an exact substring of that block.
  Then a string must occur case-insensitively in one quote OR be supported by
  source_fragments.contiguous_support (:50), which checks contiguous ranges
  and compares normalized whitespace. There is no separate statements-only
  validator: it uses this shared string validator.
- unsupported_value at :47 establishes that quote ownership/text checks
  PASSED, but submitted quotes did not support the string. It does not prove
  the string is absent from the entire source.
- map_with_field_review retains local output on failure (:460), records the
  diagnostic, and returns fallback_used. schema-status.js:11 supplies the UI
  warning; schema.js:38 adds the category/field and renders details.

Expected evidence format is an array of {source_id, quote}, with literal
source substrings. Multi-block statements require ordered, contiguous quotes.

## Offline results using the existing 55-element fixture

Tests use reports/single-jayesh-feedback-live-20261022/{extraction,sections}.json
and tests/fixtures/Jayesh Yadav-CV.pdf remains unchanged. Exact source statement:

“Experienced in client- facing fund onboarding, data integration into Arcesium
systems, and cross-functional collaboration with Legal, Compliance, Product,
and Engineering teams.”

It passes with exact partial quotes from e2:439:551, e2:551:662, e2:662:772.
reproduction.json contains only this relevant sentence and its quote fragments.
A CONTROLLED variant replacing client- facing with client-facing fails at
items/3/value with unsupported_value. Hyphen deletion is not whitespace
normalization; under the current literal-source contract rejecting that altered
value is correct. An invented fourth statement is also rejected. Neither
variant is asserted to be the unsaved live statement.

## Placement changes

llm_section_review.review_sections (:318-344) preserves the original element
index and adds split offsets to the original start. Mere reassignment preserves
IDs; splitting/refine_rows can change span boundaries and therefore IDs.
messages() generates fresh IDs afterward, so it does not reuse pre-review IDs.

The available saved provider response replays 18 changes, NOT the unsaved live
10 changes. Offline replay verifies exact extraction ranges and complete source
coverage; some non-summary spans merge/split, but all element-2 summary spans
and their IDs remain unchanged. No evidence demonstrates that the live ten
placements corrupted summary citations. A stale/foreign reference would
normally fail invalid_or_cross_record_quote before unsupported_value.

## Changes and before/after behavior

No validator was disabled and no source text or mapping value was changed.
No demonstrated validator defect justifies accepting the controlled rewrite.

- subschema_validation.py now attaches sanitized evidence analysis for an
  unsupported string: item index, quote count/lengths, source IDs, and whether
  the literal or whitespace-matched value exists in its record.
- schema_diagnostics.py allowlists these fields, excluding arbitrary text;
  development receives them, production retains its safe reference-only
  response while the server retains the sanitized details.
- static/schema.js displays the one-based field item and evidence analysis.
- tests/test_jayesh_statement_evidence.py covers the literal statement,
  unsupported rewrite, invented statement, placement/offset preservation,
  and rejection of private diagnostic metadata.

Before: opaque statements warning with no distinction between wrong quote and
absent source value. After: the warning remains for unsupported evidence, with
item/reference and source-match diagnostics in development. The exact live root
cause still requires that request's diagnostic/response; it cannot be honestly
inferred from an unrelated saved provider output.

Verification: 81 relevant offline tests passed, plus 4 API diagnostic tests.
JavaScript syntax and git diff --check passed. Zero paid provider calls.
