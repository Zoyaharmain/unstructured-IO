# Wrapped achievement and competency mapping

Reproduced with _SURESHBABUS.pdf offline (fast extraction). No provider calls or candidate-specific rules.

## Root cause

Both KEY ACHIEVEMENTS and CORE COMPETENCIES were already detected as headings with their content assigned to the correct sections. The loss occurred afterward:

1. Achievement entries were grouped by layout lane. Each wrapped bullet's long first line entered one record and its short continuation entered another. The mapper then attempted to cite a concatenation of unrelated lines and rejected it. Two provisional records had zero mapped achievement names.
2. Skills were parsed from physical rows rather than the whole source paragraph when a middle-dot list wrapped. The middle dot itself was not recognized as a delimiter. Partial phrases and unbalanced parenthetical fragments were skipped.

## General fixes

- Original ListItem source elements establish achievement record boundaries. All physical lines of one source bullet remain in that record, independent of layout lane. This applies when the achievement content is a source list, not arbitrary adjacent paragraphs.
- A middle-dot-delimited source paragraph is reconstructed from contiguous fragments of that original element before splitting skills. Middle dots are parsed as delimiters outside parentheses. Independent physical rows without delimiters are not concatenated.
- Heading-only cleanup now requires a heading with no inline body. Inline label/value content such as Languages: English, Hindi stays content. Exact source text and offsets remain authoritative.

## Before/after

- Achievement records: two lane-fragment groups with zero mapped names -> four complete source bullets with four mapped names. Unknown issuer/date values remain empty.
- all_skills values: 20 -> 36. This is recovered literal coverage, not a precision/accuracy percentage.
- No source fragments in needs_review in either local run; this confirms why placement coverage alone did not reveal the field-mapping loss.
- Final exact source and hierarchy checks pass. Before/after outputs and final frozen-code rebuilt sections/schema are retained privately alongside this report.

## Verification

111 affected regressions passed in 16.84 seconds. Four focused wrapped-content tests passed separately, including the newly added inline label/value regression. Genuine unsupported evidence remains rejected by the existing suite. Compilation/diff checks pass. No paid LLM re-evaluation was performed; remaining review statuses are retained.

## Follow-up: reviewed-path omissions

The earlier repair verified local-only mapping and did not establish the result after live LLM field review. The actual running API was subsequently tested with section and field review explicitly disabled: HTTP local paths produced four mapped achievements and 36 skills. Its output is retained in live-local/.

A confirmed integration gap remained: `recover_record_fields` excludes awards and skills. An otherwise accepted provider response could declare source-backed list fields not_stated/unmapped and replace the populated local values with empties. Added `recover_literal_lists` before final reviewed-payload validation:
- Preserve source-backed achievement names within an identical owner; recover omitted independent records only when original ListItem boundaries establish them.
- For explicit middle-dot skill lists, retain validated local literal items whose evidence belongs to the provider record.
- Leave populated achievement names and ambiguous declarations untouched; do not transfer evidence across records.
- Revalidate the complete modified candidate and retain repair metadata. This does not fabricate an LLM success or claim a fresh provider benchmark.

The real resume was passed through map_with_field_review with an offline mocked provider that returned empty awards/skills fields. Final output retained all four achievement names and 36 skills, with validated evidence. Artifact: mock-reviewed-schema.json. All provider invocations in this test used the injected mock, with zero network calls.

Two new generic reviewed-path regression tests plus existing ownership/citation/fallback tests: 103 passed in 15.95 seconds. No paid live model call has been made, and the exact unseen live response is not claimed to have been reproduced.

## Exact twelve-excerpt UI report

The user supplied twelve residual source excerpts from e9–e15. The saved reviewed output was checked against those exact source IDs. Eleven excerpts have skill citations; the twelfth is the CORE COMPETENCIES section heading. Combining all exact record-local quote intervals leaves no meaningful competency text uncovered in these excerpts. The original residual calculation only removed a block if one quote equalled the entire block; multiple valid field citations therefore left a misleading full-block residual list.

The frontend now derives coverage from the union of exact, unique-occurrence quotes per source ID. It displays mapped field paths, source headings/group labels as context, and only actual uncovered meaningful fragments as needing mapping. Original excerpts remain available in nested evidence details and JSON. Repeated quotes without occurrence offsets are conservatively left unresolved. Foreign citation IDs do not cover a block. Mapping statuses and source validation are unchanged.

Artifact: ui-source-coverage.json (12 excerpts, 11 with mapped fields, 1 heading, zero meaningful uncovered fragments). Seven focused frontend/reviewed-path/wrapped-list tests passed. The frontend regression also verifies genuinely unmapped text, foreign evidence, and ambiguous repeated occurrences stay visible. JS syntax and diff checks pass. No paid calls.
