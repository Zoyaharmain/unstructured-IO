# Pipeline repairs after the ten-resume benchmark

The confirmed extraction, grouping, validation and fallback bugs have been repaired. Existing schemas, original documents, fixtures and paid-run artifacts are preserved. **No additional paid calls were made.** These results are offline checks and saved-response replays, not a new DeepSeek accuracy benchmark.

## Verified results

- All **10/10** source-bound local results pass source coverage and hierarchy/evidence validation under the final mapper.
- The same original-source employer subset improves from **7/30 to 27/30** in local mapping. This is employer-core recovery, not overall accuracy or precision; it tolerates punctuation and city suffixes and does not certify every field.
- Both Sateesh Word files now retain Velocity IT and Netafim and produce **two jobs and four named projects**.
- Bhargava's flattened Word tables now yield **seven distinct employer records**, with employer and client names separated.
- Ashwini now has **three employment records and eight project groups**, rather than promoting project client roles, duration labels and responsibility headings into jobs/projects.
- Saved Fairoz responses now retain the **two validated employment mappings** when the projects response fails. The result is explicitly partial, with the projects fallback and original diagnostics visible.
- Saved Abdul responses now produce **four jobs**, retaining orphan duties as source content rather than an extra identity-less experience record.
- The running local API returned HTTP 200 with the corrected two-job/four-project Word result and **zero provider calls**. See runtime-verification.json.

## Causes and code changes

| Cause | Repair |
|---|---|
| Word text-box contents were invisible to the paragraph partitioner. | `word_preparation.materialize_textboxes` exposes original paragraph/table XML in a private input copy at the shape anchor. Alternate Choice/Fallback representations are not duplicated. Uploaded bytes remain unchanged. |
| Word table paragraphs were flattened, concealing record boundaries. | `annotate_table_paragraphs` supplies exact offset cut points only when the full original table paragraphs match the extracted text. Text and element indices are unchanged; unmatched/ambiguous tables are not guessed. `text_extraction_service.extract_text` applies both Word preparations. |
| Heading/field formatting was mistaken for identity. | `resume_structure.heading_boundary` composes known same-schema headings, keeps numbered project titles as content, and splits embedded numbered project boundaries. `entry_groups` keeps duration, client, role and responsibility subfields inside their project. |
| Company/role information in explicit alternate syntax was left unresolved. | `record_subfields.employment_header_fields` handles source-literal employment statements, employer/date headers and labelled company/client headers. Short and hyphenated month dates remain literal; no four-digit year is invented. Paired date/role rows establish structural proposals. |
| Technology markers, client-role lines and incidental business words in duties became employers. | `record_relationships.field_kinds` respects typed field markers, explicit employment headers and established record context. Leading client markers do not establish employers. `refine_record` retains validated employer boundaries and does not replace an already established employer/location split. Capability/client-only evidence cannot establish a provider company field. |
| One invalid batch discarded previously validated sections. | `llm_schema_mapping.map_with_field_review` retains successful batches and uses validated local sections only for failed batches. Transport/budget failure stops further requests while retaining previous valid batches. Partial results require review and expose failed/reviewed categories. All-batch failure still reports failed. |
| A saved response omitted one terminal closing brace. | `repair_terminal_json_closer` can insert exactly one missing closing delimiter only at a parser error followed entirely by closing delimiters. It does not reconstruct words, values or strings. Full schema, ownership and evidence validation still follows; ambiguous/truncated responses remain rejected. |
| Empty/duty-only experience records appeared as jobs. | `parse_review` leaves their source spans residual/unmapped rather than manufacturing an entity. Required review remains visible. |
| Audit record keys disagreed with actual schema IDs. | `review_chunking.audit_plan` resolves legacy contact, summary and skill units to existing record IDs. `audit_visible_sources` preserves the real owner of each boundary-context quote. Absence findings for empty legacy/unresolved fields may honestly have no citation; populated values and foreign quotes retain strict checks. |
| Production diagnostics lost their recovered/unresolved state. | `schema_diagnostics.client_diagnostic` now includes the safe recovery flag. `schema-status.js` distinguishes partial review from whole-result fallback and does not show resolved history as an active failure. |

## Verification artifacts

- `final-current/`: fresh offline extraction/detection of the same ten files.
- `final-schemas/` and `local-final-summary.json`: final source-bound rebuilds and subset checks using the frozen mapper.
- `verify_final_local.py`: repeatable offline verification of those inventories.
- `replay_saved_fields.py` and `replay/`: saved provider-response replay for Fairoz and Abdul. A replayed transport count is not a new API call.
- `replay_saved_audits.py` and `audit-replay.json`: 8 of 14 available saved audit chunks validate under corrected keys/contracts. Remaining invalid responses stay rejected. Chunks never requested during the old failed run remain unverified; this is not a new completed 10-resume audit.
- `tests/test_batch_failure_repairs.py`: generic synthetic cases and actual-source regressions for these failures, including negative cases for invented values, foreign citations, malformed JSON, client/employer confusion and field headings creating fake records.

## Remaining limits

Local-only mapping still misses three checked employer occurrences in the two PDFs A Lokhande and A Suribhotla. Those remain review items rather than invented values. Some project names or roles are not explicitly established by their source; record numbers and client names are not silently converted into descriptive project names.

A new paid run has not been authorized or performed after these repairs. The previous 98-request benchmark remains historical. No claim of 100% correctness, complete field accuracy, or readiness for every unseen layout is made. Complex floating Word layouts can still require reading-order review. Refresh the UI and reprocess original documents; old exported JSON is retained and does not update automatically.

## Final test results

The final frozen implementation passed **654 tests in 119.71 seconds**. Source/hierarchy checks passed for all ten rebuilt documents. JavaScript syntax, changed Python module compilation and `git diff --check` passed. The localhost runtime check used `review_fields:false`; no additional paid calls were made.
