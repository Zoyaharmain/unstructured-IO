# Final ten-resume pipeline evaluation

**Decision: NO-GO for production scaling. The pipeline executes and preserves extracted-source evidence, but these ten outputs are not all semantically verified or fully LLM-reviewed.** This report summarizes the completed saved run; preparing it made no new API calls and changed no production mapping logic.

## Run outcome

- Selected and attempted: **10 distinct resumes** (two development controls, eight generalization cases).
- Pipeline outputs produced and final source-interval/hierarchical-citation validation passed: **10/10**. This means structural integrity, not original-PDF word accuracy or correct semantic grouping.
- DeepSeek section reviews completed: **8/10**. Siva Mari and Vikrant Roy exceeded configured review limits; their local outputs were retained and no partial document was sent.
- Final schema audits completed: **5/10**. Divya Balyan, Sundar and Sumit exceeded the schema-audit input limit after successful section review; the remaining two never reached audit.
- Actual provider requests: **22 across eight resumes**, within the 40-request cap. All 22 received provider responses; receiving a response does not mean its assignments were accepted. Aditya's first placement response was rejected as `invalid_assignments`, and the second pass succeeded.
- Model: **deepseek-flash**. Recorded run duration: **196.71 seconds**.
- Recorded usage: **864,070 prompt + 24,440 completion = 888,510 tokens**. Prompt cache hits: 122,624; misses: 741,446. Verified billed cost is unavailable; no tariff or estimated amount is invented.
- Input, baseline, code and prior-artifact preservation gate: **passed**, as recorded by execution-summary.json.

## Per-resume result

“Missing fields” means the mapper's required legacy-field diagnostics, not independently confirmed information omitted from the PDF. Audit concerns are provider suggestions requiring source review, not human ground truth. Zero concerns for an audit that did not run does not imply correctness.

| Resume | API calls | Feedback passes | Final section review | Final schema audit | Advisory concerns | Missing fields | Unresolved meaningful spans |
|---|---:|---:|---|---|---:|---:|---:|
| Aditya vashisth.pdf | 3 | 2 | complete | complete | 18 | 0 | 0 |
| _ManjunathMurugan.pdf | 4 | 2 | complete | complete | 12 | 0 | 0 |
| Chandan Kumar BV.pdf | 4 | 2 | complete | complete | 14 | 4 | 0 |
| Siva Mari.pdf | 0 | 1 | failed | not_run | 0 | 27 | 0 |
| Divya Balyan.pdf | 1 | 1 | complete | failed | 0 | 5 | 0 |
| Vikrant Roy.pdf | 0 | 1 | failed | not_run | 0 | 44 | 1 |
| Sundar.pdf | 1 | 1 | complete | failed | 0 | 6 | 0 |
| Santhosh KR -  SAP EWM.pdf | 4 | 2 | complete | complete | 24 | 9 | 0 |
| Sumit.pdf | 1 | 1 | complete | failed | 0 | 9 | 0 |
| HarmeetSingh cv.pdf | 4 | 2 | complete | complete | 33 | 5 | 1 |

All ten produced validated JSON output. None receives whole-resume semantic approval from that result. The final audits contain **101 advisory concerns across five resumes**. Required-field diagnostics total **109** across the ten; do not interpret that as 109 confirmed mapping errors.

## What the reference labels establish

Only the two development controls have partial field-level references:

| Resume / provenance | Exact matches | Denominator and scope |
|---|---:|---|
| Aditya: Group 01 personal information | 3/3 | Explicit saved reviewer decisions |
| Aditya: Group 02 employment header | 5/5 | Explicit saved reviewer decisions for Persistent Systems record |
| Manjunath: Group 01 personal information | 3/3 | Explicit saved reviewer decisions |
| Manjunath: earlier expectations | 6/6 | Prior user-supplied expected text; narrower provenance, not new PDF-review approval |

**11/11 explicit Group01/02 fields matched; six prior expectations separately matched 6/6.** Across all available partial expected fields, the value/selector exact-match result is 17/17. There were no incorrect/missing/incorrect-parent/incorrect-record classifications among these 17 comparisons. This is not “100% accuracy for ten resumes.” Aditya's uncertain employment location A069 remains excluded, as do all pending rows. Reference selectors are compared as supplied; record IDs are segmentation-dependent and do not independently certify every employer/role/date relationship.

Field precision, recall and F1 remain **unavailable** because references are partial and do not enumerate all correct fields, missing fields and false positives. Main-section accuracy, precision, recall and F1 are also **unavailable**: none of these ten has a complete matching source-bound section reference. The separate 15-document ownership benchmark cannot be reused as field labels or transferred blindly onto new extraction offsets. Exact-resume semantic correctness and population-level accuracy are unmeasured.

## Recovery and source accounting

The saved traces show real recovery execution, not merely a design claim. All ten ran local recovery; five used a second feedback pass. Every run terminated within the two-pass limit.

- Aditya retried after an invalid placement response, then stopped at the configured budget with 18 audit concerns.
- Manjunath and Chandan stopped because the source/legacy mapping fingerprint did not change, while audit concerns remained.
- Santhosh and Harmeet stopped at the recovery budget with remaining audit concerns.
- Siva Mari and Vikrant stopped on section-review document limits, retaining validated local output.
- Divya, Sundar and Sumit stopped on schema-audit input limits.

Initial detection recorded 120 unresolved meaningful spans in total; final accounting recorded **two**, one each for Vikrant Roy and HarmeetSingh. These are snapshots of potentially different span segmentations: **do not claim exactly 118 spans were correctly recovered by subtraction**, or attribute all change to the LLM. All ten final extracted inventories passed conservation checks; no extracted-text gaps/overlaps were detected. This does not prove that extraction captured every original-PDF word or that reassigned text belongs to the right semantic record.

## Remaining defects and concerns

1. **Provider size limits prevent complete verification.** Two resumes did not receive LLM review, and three additional resumes did not receive schema audit. A bounded source-preserving strategy for long inputs needs design and tests before larger testing; silently dropping content or simply forcing categories is not acceptable.
2. **Recovery does not guarantee semantic repair.** Bounded retries and stagnation stopping work, but unresolved field/grouping diagnostics persist. Repeating a deterministic mapper cannot by itself repair unsupported or incorrectly associated fields.
3. **Field/grouping concerns remain.** Aditya's audit flags shortened education year ranges (`2018 - 21`, `2013 - 17`) with missing graduation years. Manjunath's audit flags responsibilities fragmented across source lines. These are concrete provider-raised examples for manual adjudication; this report does not promote those interpretations into confirmed human labels. Full field paths, exact source IDs and wording are in each schema-audit.json.
4. **Source support is weaker than semantic correctness.** A value can have a real quote inside an incorrectly grouped job or education record. Valid record-local citations are necessary but not an exhaustive association score.
5. **Field mapping remains local.** DeepSeek performs section placement and advisory audit in this execution path. It does not directly rewrite the final hierarchical fields.
6. **Cross-candidate search is missing.** The existing parent.child lookup and record filter expose structured fields within a supplied resume; they are not a persistent multi-candidate index, ranking system or combined skill/experience search engine. Search precision/recall is unavailable.

## Tests and preservation

The preflight recorded **410 full-suite tests passed, zero failures/skips**, plus **168 overlapping focused tests** and **four separate preflight checks**. These are the recorded offline tests from before the provider execution; this final-report step did not rerun tests. Initial sandbox TestClient hangs and successful reruns outside the sandbox with provider keys removed and external sockets blocked are retained in ../regression-tests.txt. The preflight preservation check covered 15,775 files with zero changed; the completed execution independently reports its input/baseline/code/prior-artifact preservation gate passed. These are recorded checks, not a new preservation scan performed by this report writer.

## Readiness and next actions

| Subsystem | Conclusion |
|---|---|
| Extraction and evidence | Ten final outputs pass extracted-source conservation/citation checks; original-PDF word accuracy remains unmeasured |
| Main sections | Eight LLM reviews complete; semantic section accuracy unavailable |
| Recovery | Real bounded loop verified; unresolved content and audit concerns remain |
| Child-schema mapping | Typed, source-bound output passes; partial references match, broader completeness unknown |
| Record associations | Only limited reviewed tuples tested; other grouping relationships need adjudication |
| Search | Per-resume field lookup exists; candidate-search readiness not established |
| Overall | **NO-GO for larger production processing or complete-system correctness claims** |

Next, manually adjudicate the cited field/grouping concerns, especially education year ranges and fragmented responsibilities; preserve ambiguous values. Design and test handling for review/audit size limits with full source accounting. Apply narrowly scoped fixes with regression evidence, then evaluate the same frozen ten offline first. Obtain approval before further paid calls. Expand explicitly saved labels before measuring broader semantic accuracy or launching a larger batch. No fixes, extra provider calls, or larger experiment were performed while preparing this report.

## Evidence files

- execution-summary.json and calls.json: actual provider execution, timings and usage.
- per-resume-results.json: final structural validation outcomes.
- sub-schema-evaluation.json: all 17 partial expected-field comparisons and provenance.
- main-section-evaluation.json: why semantic section scores are unavailable.
- reprocessing-accounting.json and stage-traces.json: exact spans, recovery invocations and stopping conditions.
- search-evaluation.json: existing lookup results and candidate-search limitation.
- 01–10/schema.json, sections.json, schema-audit.json, pipeline.json and pass directories: document outputs and diagnostics.
- ../architecture-audit.md, ../regression-tests.txt, ../selection-manifest.json: architecture, recorded tests and frozen scope.
