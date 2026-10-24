# Ten-resume repair investigation and approval plan

**Status: investigation complete; production unchanged; no provider calls, extraction/detection runs, mapping replays or ten-resume rerun. NO-GO for larger processing remains.** New diagnostic scripts, tests and reports are isolated in this directory. All conclusions below distinguish source-bound observations from human semantic labels.

## Exact size-limit causes

The configured limits were 600 review spans and 200,000 message-content characters. Counts below reconstruct the production message builders from saved artifacts with the current serialization, including the system instructions; they are character counts, not token counts or provider context-window claims.

| Resume | Initial review spans | Initial section prompt characters | Final audit prompt characters | Observed blocked stage |
|---|---:|---:|---:|---|
| Siva Mari | 469 | 373,608 | 429,029 | Section review, before any request |
| Vikrant Roy | 576 | 400,537 | 467,265 | Section review, before any request |
| Divya Balyan | 235 | 181,800 | 235,418 | Schema audit after successful section review |
| Sundar | 207 | 150,426 | 234,896 | Schema audit after successful section review |
| Sumit | 238 | 189,215 | 243,330 | Schema audit after successful section review |

Siva and Vikrant were **below the unit limit**; their messages exceeded the character gate. `local_api/services/llm_section_review.py::review_sections` constructs the entire message and rejects it before transport. `scripts/check_single_resume.py::audit_schema` similarly rejects oversized audit messages. These are deliberate fail-closed limits, not authentication errors, provider HTTP failures, or proof of missing source text. Merely increasing the limit is not the proposed fix.

Section prompts serialize spans, repeated whole source elements, coordinate/evidence metadata and record hints. The audit serializes source text plus the full schema response, including raw sections, metadata, nested values and their expanded field index. For Divya, the schema components alone include meta 78,558 characters, field_index 68,341, section_schemas 47,243, and data 9,799. These overlapping representations amplify payload size. `schema-payload-components.json` and `investigation.json` preserve the actual measurements.

## Source adjudication: Aditya education

Exact frozen source IDs and pages:

- `e12:507:567`, page 1: `Guru Gobind Singh Indraprastha University, Delhi | 2018 - 21 `, linked with `e12:567:606` (Master of Technology / Computer Science).
- `e20:90:150`, page 2: `Guru Gobind Singh Indraprastha University, Delhi | 2013 - 17 `, linked in education-2 with `e12:606:647` (Bachelor of Technology / Computer Science, page 1).

The final output keeps start years 2018 and 2013, leaves graduation_year unresolved, and explicitly warns `Abbreviated completion year in source; no century inferred.` `education_subfields.py::refine_education` intentionally implements that policy. The source does **not** contain literal `2021` or `2017` in those quoted ranges. The provider suggestion to populate expanded end years is **not a confirmed mapper defect under the existing literal-evidence policy**. No century expansion or ground-truth update is proposed. The cross-page degree/date association is a separate human-review question; existing IDs and quotes do not independently certify that association. The original range remains available in source evidence, so it is not silently erased.

## Source adjudication: Manjunath responsibilities

Confirmed saved-artifact behavior:

- Page 1 `e15:0:18`: `Translated complex`.
- `e17:0:18`: `regulatory updates`; `e18:0:13`: `into detailed`; `e19:0:11`: `field-level`.
- `e16:0:11`: `functional `; `e16:11:94` and `e16:94:129`: its remaining sentence.

All belong to experience-1 (PwC), but extraction inventory order puts e16 before e17–e19. Saved PDF-line coordinates place e15, e17, e18, e19 and the first e16 fragment on the same physical row, left-to-right. The mapper emits several incomplete fragments as separate source-supported responsibilities. **Fragmentation and a mismatch between inventory order and physical line order are confirmed; a universally safe joined sentence is not.** This needs a view ordered by page/row/x within one established record, with original offsets retained; concatenating adjacent element IDs would produce the wrong order here. Do not relabel the source inventory or silently rewrite raw extraction. Geometry uncertainty, columns, bullets and cross-page continuation require abstention/review.

A more narrowly confirmed field-assignment defect occurs in experience-2 (BNP Paribas ISPL):

- `e23:0:78`, page 2: `Drove BA scope for the pricing platform transformation with the Product Owner,`.
- `e24:0:75`, page 2: `delivering high-integrity data feeds to downstream Fund accounting systems.` (the exact block, including whitespace, is in source-evidence.json).

`record_relationships.py::field_kinds` returns **employer** for the e24 text because of the generic word `systems`; the ACTION pattern in `record_subfields.py` does not recognize this continuation. `annotate_relationships` therefore excludes it from responsibility evidence. It remains in the same employment record's source ownership and in residual_blocks, but does not populate responsibilities. This is a **confirmed continuation misclassification and structured-field omission, not lost extracted text**. The proposed repair should prioritize a source-supported action/continuation within an established job over a generic organization suffix, while retaining actual company headers such as Persistent Systems. It must not promote every sentence containing “systems” to employment history.

## Defects, gaps and hypotheses

| ID | Finding | Status | Proposed minimum action |
|---|---|---|---|
| D1 | e24 continuation classified as employer | Confirmed reproducible functional defect | Narrow action/continuation guard, with company-header counterexamples |
| D2 | Responsibilities split/reordered across extracted elements | Confirmed representation problem; full joins need further source adjudication | Add a record-local ordered view with quote chains, or mark ambiguous fragments for review; do not blindly join inventory neighbors |
| D3 | Feedback fingerprint ignores section_schemas | Confirmed code-level blind spot, reproduced by unit test; no saved incident proves it caused premature stop here | Include semantic nested field/value/record/evidence state, excluding counters/reasons-only changes |
| G1 | Whole-document review/audit cannot handle selected long payloads | Confirmed capability gap; existing rejection is correct | Budgeted source-preserving chunk planner plus validator and aggregate coverage state |
| S1 | Expand Aditya abbreviated completion centuries | Advisory suggestion, not confirmed defect | Keep current uncertainty and seek explicit labels/policy before normalization |
| S2 | Other provider findings and true job/degree grouping | Unverified suggestions beyond these source checks | Manual adjudication; no inferred accuracy labels |
| G2 | Cross-candidate search | Confirmed missing capability in inspected routes | Document scope; no search implementation in this phase |

## Recovery invariant and termination

All **15 saved pass artifacts across ten documents** were revalidated against their unchanged extraction inventories: exact source slices, interval coverage/no overlap, hierarchy/citations and repeated-record ownership passed. Each document used one or two feedback passes, within its configured limit. The source-block accounting invariant holds **for the frozen extracted inventories**, not all words that might exist in the PDFs.

`single_resume_pipeline.py::run_feedback` has a fixed `range(1 + recovery_attempts)`, with shared invalid-response/feedback budget, early failure exits, stagnation stopping and prior-valid-output retention. `review_sections` applies decisions atomically and calls the interval coverage gate; malformed, omitted, overlapping or duplicated assignments are rejected. Existing local recovery may rerun detection across the whole inventory, and provider review can change previously assigned spans: there is no semantic lock protecting already-correct placements. Conservation does not prove semantic correctness. Existing stagnation behavior for Manjunath/Chandan must not be reinterpreted as repair success.

D3 is verified independently: changing only hierarchical record output leaves the current fingerprint unchanged. It is a latent weakness, not evidence that the existing saved stops lost newly improved hierarchy. Proposed tests must verify hierarchy-only progress changes the fingerprint while warning/counter-only changes do not keep the loop alive.

## Source-preserving chunking design — not implemented

1. **Immutable global inventory.** Bind original document SHA, extraction-content hash and pipeline/config hashes. Use global source IDs `eN:start:end`; never renumber them per chunk. Keep page, lane, offsets, heading and record identity. Create a signed-by-hash local manifest, not a new human reference.
2. **Owned targets vs read-only context.** Every original span/allowed subinterval is owned by exactly one chunk. Include overlapping heading, employer/title/date and adjacent continuation context as read-only references with original IDs. Context cannot generate duplicate decisions. Do not claim the entire resume is present when it is not. Record uncertainties are carried with their actual source quotes, not model-generated summaries.
3. **Record/section-aware packing.** Prefer complete established section records; pack adjacent jobs/degrees/projects separately with their own parent and record anchors. Keep same-job cross-page continuations together where evidence supports ownership. Layout columns and uncertain records remain explicitly uncertain. Oversized single records can be partitioned by source-backed bullets/rows with the same record anchors in each child chunk. They must never become independently invented employment records.
4. **Full serialized budgeting.** Measure the final messages after system instructions, target IDs, context, evidence and recovery feedback. Enforce existing character and unit caps, plus a conservative output/token allowance. Strip repeated derived representations from provider prompts only: retain the original response files and canonical inventory. Do not just slice strings. For one oversized span, split only at existing allowed source offsets; keep exact global subintervals. If no safe subdivision fits, retain it unresolved/local and flag the chunk unreviewable.
5. **Section response contract.** Accept decisions for owned global targets only; require exhaustive contiguous coverage for each target. Reject unknown/context-only IDs, gaps, overlap, unsupported cuts and contradictory assignments. Merge in source order, validate the union against the original inventory, then rebuild the global sections/records and map once. No concatenation of independently generated job lists. Preserve an old/new ownership crosswalk if record IDs change; do not silently rematch manual labels.
6. **Atomic aggregate state.** A failed chunk must not cause partial content loss or a false complete status. Prefer a whole-pass atomic commit of all valid chunks. If partial review is explicitly supported later, retain previous validated placements for failed chunks, mark them unreviewed, expose exact coverage and set aggregate status partial. No “complete” flag unless every owned target was validly reviewed. Invalid/conflicting output never overwrites a prior valid result.
7. **Schema audit chunks.** Use compact canonical parent/record/attribute/value/evidence units instead of sending data + field_index + metadata repeatedly. Include required unresolved fields, record-local residual source, the record anchors and parent context. Cover populated fields, missing-field candidates, residuals and all raw source in an explicit audit-coverage ledger. Split a large field list by item while preserving list index and the exact record; if one large item is split, maintain item/chunk references and require a combined coverage check. Record-local audits cannot prove cross-record grouping: add bounded boundary/association audits from original anchors or explicitly mark those checks incomplete. Never infer a clean document merely because a subset of fields had no findings.
8. **Global budgets and stopping.** Chunk requests multiply call counts. Introduce per-document/per-pass/global request budgets and bounded retries; record every attempt and exact reviewed ranges. The previous 40-request authorization must not be reused as approval for this new design. Stop deterministically on budget exhaustion, oversized context, repeated fingerprints or validation errors, retaining all source and unresolved diagnostics. New paid scope/budget needs separate approval.

## Exact proposed changes and required tests

No listed production file has been changed. Approval should cover small independent patches, not all proposals as one unreviewable change.

| Proposed file(s) | Purpose | Required tests before acceptance |
|---|---|---|
| local_api/services/record_relationships.py; if needed record_subfields.py | D1 continuation versus employer evidence | e24 red regression; delivering/continuation variants; genuine company headers, role headers, Systems as proper name, ambiguous text and no cross-job transfer |
| scripts/single_resume_pipeline.py | D3 semantic hierarchy progress | Existing red test; hierarchical values, record IDs/ownership and citations; reasons/counters ignored; bounded cycles; valid result/audit feedback retained after failure |
| New local_api/services/review_chunking.py | Shared pure planner, inventory bindings, owned/context targets and budgets | Full union conservation, exact source/quote fidelity, order, pages/columns, cross-page jobs, oversized record/span, unknown/context IDs, duplicate/gap/overlap rejection, impossible chunk and no mutation |
| local_api/services/llm_section_review.py; review_validation.py if required | Use chunk contract and aggregate validated review state | Mocked providers only: all-success, one failure, contradictory overlap, refused chunk, invalid offsets, partial status, global request cap and no call beyond frozen hashes |
| scripts/check_single_resume.py | Compact chunked audit request and coverage ledger | All mapped/list/unresolved/residual targets included; record-local citations; invalid findings; budget exhaustion; no clean result on incomplete audit |
| local_api/services/source_fragments.py and/or a new record-local paragraph helper; schema_mapping.py only after source tests justify it | D2 geometry-backed view/paragraph handling | Same-row nonsequential IDs, multiline bullets, two columns, cross-page employer changes, no guessed spaces/rewrites inside quotes, ambiguous geometry remains review; legacy/nested agreement |
| tests/test_record_subfields.py, test_structural_grouping.py, test_single_resume_check.py, test_llm_section_review.py, test_section_subschemas.py; new test_review_chunking.py | Permanent approved regression coverage | Move/copy these isolated red cases into the production suite once implementing; preserve counterexamples and existing expected behavior |

Do not change education_subfields.py to invent a century. Do not add cross-candidate search or change routes as part of these fixes. Minimize the first patch to D1 and D3; stage chunking separately, then stage paragraph reconstruction only after boundary evidence is approved.

## Verification plan after approval

1. Snapshot hashes again and confirm no changes to frozen inputs, prior reports, PDFs, ground truth or previous 350 experiment. New directories only.
2. Make the narrowly approved changes after the red tests demonstrate the defect; retain explicit uncertainty. Run focused pure tests, mocked-provider chunk tests and the relevant full offline suite with provider credentials removed and external connections blocked. Do not weaken failing tests.
3. Replay mapping on **the same ten frozen extraction/section inventories** into a new directory; no PDF extraction, embeddings, API calls or 350 rerun. Compare to the original saved schema outputs: exact 17 reference tuples separated by provenance, all populated values/quotes, legacy/nested differences, record membership and parent changes, unresolved fields/spans and residual coverage. Classify change explanations rather than treating assignment increases as accuracy improvement.
4. Exercise the new chunk planner and recovery with deterministic mocked/replayed responses for those saved inventories. Previously paid whole-document responses cannot be blindly reused for new chunk contracts. There are no saved provider responses for Siva/Vikrant; report those mocks as synthetic structural tests, not fresh LLM verification.
5. If an approved grouping change must rebuild entries, use saved source/layout and explicit before/after record crosswalks; do not rerun PDF extraction or assume IDs are stable. A new full local detection run would be a separately described verification step, not silent reuse of frozen sections.
6. Publish before/after metrics only within verified label scope, red-to-green regression results, source-accounting outcomes, semantic changes requiring review, request/size simulation and remaining risks. Request a fresh explicit approval for any subsequent paid chunked run and its updated call cap. No larger batch on structural checks alone.

## Tests executed in this investigation

- New proposed-behavior tests: **2 failed, 5 passed**. The two failures intentionally expose D1 and D3 on unchanged production code. They are retained as visible red regressions, not marked xfail or hidden.
- Existing bounded-feedback tests: **3 passed, 7 deselected** using `pytest tests/test_single_resume_check.py -k feedback`. Provider responses are mocked; no live calls. This is focused verification, not a new full-suite claim.
- Prior 410-pass full suite and provider usage (22 requests / 888,510 tokens) were inspected as historical evidence; not rerun or billed again.
- Exact commands/results, source evidence, size diagnostics and preservation hashes are saved alongside this report. No new human labels or overall accuracy score.

**Approval checkpoint:** approve the proposed scope/order before production edits. All provider calls and the ten-input replay remain stopped until the relevant next phase is approved.
