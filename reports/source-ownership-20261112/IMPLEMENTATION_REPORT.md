# Resume ownership implementation and evaluation

The ownership architecture and evaluation tooling are implemented. This is **not production-ready**: semantic regressions remain, and independent unseen-resume accuracy is **not established**. Raw extraction code and existing ground-truth files were not changed. No branch was merged or pushed.

## Reproduced root causes

| File / function | Original failure mechanism | Change |
| --- | --- | --- |
| `local_api/services/resume_sections.py`, `SectionEngine._detect` | Upstream Title/Header could stop strong semantic context; Footer/PageBreak could suppress meaningful headings or numeric content; ListItem could suppress exact section aliases. | Require semantic/source evidence; exact heading semantics override weak upstream types. Source-supported page artifacts are distinguished from body text. |
| `local_api/services/resume_structure.py`, `entry_groups` / `reviewed_employment_groups` | Role boundaries depended on style/context, nearby anchors could merge, and vertical tolerance could pull a preceding duty into a later role. | Separate role evidence, preserve reading-lane order, abstain on ambiguous merged columns. |
| `local_api/services/schema_mapping.py`, `map_schema` | A preceding iteration's `refs` closure widened the next record's evidence; implicit previous-employer/client inheritance copied complete source headers. | Explicit primary ownership; company-only context with field-specific evidence. Parent titles, dates and duties are excluded from child refinement. |
| `local_api/services/schema_mapping.py`, `map_schema` | When only one job had no duties, arbitrary Projects text was copied into it. | Remove the cross-section fallback. Repair must explicitly reassign existing source IDs. |
| `local_api/services/llm_section_review.py`, `make_messages` | Existing provider contract accepted section assignments only, despite supplying record hints. | Add a separate bounded structural stage with source-only create/split/merge/assign/review/employer-link operations. |
| `local_api/services/source_accounting.py`, `account_source` | Complete text coverage and section assignment did not establish primary role ownership or semantic accuracy. | A frozen source ledger and explicit ownership graph complement coverage accounting. |
| `local_api/services/record_relationships.py`, `annotate_relationships` | Re-annotation could erase external uncertainty and replace accepted structural fields. | Preserve review reasons and validated ownership. Mapping cannot silently heal away accepted abstentions. |
| `local_api/services/record_subfields.py`, `employment_header_fields` | Redundant action-word filtering dropped organization literals; parenthesized role specializations became clients; a rewritten component could crash a position lookup. | Preserve source-supported organization/role literals; only explicitly labeled client parentheses become client evidence; guard source-position lookup. |

Exact architecture entry points: `source_ownership.snapshot`, `role_boundary_operations`, `apply_operations`, `materialize`, `validated_ownership_state`, `finalize_ownership`; `employer_context.valid_employer_context` and `valid_record_context`. See [architecture and lifecycle](../../docs/RESUME_OWNERSHIP.md).

## Architecture and integrity

The existing extractor, section detector, recovery stack and mapper are retained. The new frozen ledger stores source IDs, exact Unicode intervals, raw text, original types, page, coordinates, normalized bounding boxes where available, extraction order and lane. A digest binds source text and metadata. Each source interval has one primary owner at most. Shared company evidence is explicitly field-specific and does not widen other fields' evidence.

Provider operations cannot invent source text, source IDs or arbitrary record IDs. Validation is atomic and checks source coverage, owner membership, section compatibility, entity kinds and employer context. Local unsupported employer links become Needs Review; invalid provider links reject the entire transaction. Accepted ownership is checked against its persisted ledger before mapping and cannot be replaced by heuristic recovery. Missing dates and ambiguous associations remain unresolved.

## Dataset audit and independent evaluation preparation

The local inventory contains 434 unique source-byte hashes. 252 have tracked historical references. Frozen manifests contain 352 development documents, 45 reserved validation candidates and 37 reserved held-out candidates. Unmatched candidates are not certified unseen: independence attestation, duplicate/version review and independent annotation remain required. Per-resume external/pretraining use is not documented and is not claimed absent.

Audit evidence identifies prior selections, processing, tests, annotations and development reports. Used resumes stay in development; renamed byte-identical sources cannot cross splits. Existing gold and regression fixtures are not unseen data. The held-out evaluator requires explicit invocation, independent human review plus distinct adjudication, original-document hash binding and a fresh exposure check.

The blind export was exercised on a development extraction: 94 unlabeled source spans, exact source hash retained, no predicted sections or record ownership. Its unverified template was rejected by the validation CLI. See [annotation guidelines](../../docs/RESUME_ANNOTATION_GUIDELINES.md) and [audit summary](../../evaluation/resume-ownership-v1/audit-summary.json). LLM drafts are never automatically promoted to independently verified ground truth.

## Actual verification

The latest complete repository-wide run attempted all 96 modules and completed 96; 1004 passed, 24 failed, 0 errors, 0 timed-out modules. Ordinary provider exclusions/credential fixtures remained active. Earlier in-sandbox API timeouts were environmental; the isolated health test passed outside the sandbox, and subsequent complete runs were performed there.

After the final contract/type regressions, latest JUnit observations cover **1034 distinct test cases: 1010 passed, 24 failed, 0 errors, 0 skipped**. This combines the complete run with the later focused JUnit results by test identity, not by summing overlapping runs. The focused ownership/evaluation/schema contract run passed 81 cases; four additional upstream-heading-type cases passed separately. Complete logs, JUnit and [per-case latest results](latest-test-observations.json) are retained. The [collection coverage check](test-coverage-check.json) confirms an observation for every one of the 1,034 currently collected cases, with no stale or unobserved cases.

Replaying the 24 failing full-suite cases against HEAD core implementations in memory reproduced 15 failures; 9 passed on the original core. This is a scoped baseline replay, not a claim that all remaining failures predate the change. Compatibility gaps remain and require review. In particular, retaining incomplete roles changes some record counts, suppressing unsupported date inheritance can leave total experience unknown, and the old Projects-to-only-job copying expectation intentionally remains unsatisfied. Existing expectations were not edited to make these changes pass.

The configured DeepSeek transport was tested with generated fiction: seven accepted create/assign operations, two experience records, zero source-validation errors, and remaining uncertainty retained. This checks protocol/integrity, not real-resume accuracy. Earlier real development responses with invalid entity assignments were atomically rejected. Automatic approval review blocked an additional real-resume transmission because document-specific approval was missing; the final provider protocol check used generated fiction instead.

## Measured results and limits

| Metric | Development evidence | Independent unseen test |
| --- | --- | --- |
| Section macro F1 | 76.7784% on 15 previously used section-labeled documents | Not established |
| Non-whitespace section character accuracy | 89.5958%; 81,352 scored characters | Not established |
| Record-boundary F1 | Not measured: complete independent role references unavailable | Not established |
| Responsibility ownership accuracy | Not measured: independent responsibility-to-role references unavailable | Not established |
| Cross-record leakage | Not measured; source-integrity checks are not semantic leakage accuracy | Not established |
| Unresolved-span rate | 22.8545% on nine unlabeled development documents | Not established |

The nine-document diagnostic batch contains six PDFs and three DOCX files, including table and column layouts; all nine processed and preserved source coverage. Although disjoint from historical batch selections, these examples are development diagnostics, not claimed unseen test evidence. Existing section labels retain their recorded legacy `human_verified` provenance; they were not independently re-certified here. Pipeline failures in section evaluation are scored as abstentions instead of being omitted from the denominator. That run reports 0 pipeline failures and 0 unavailable sources.

Reference evaluation is independent of parser segmentation: humans may choose different exact source intervals. Responsibility `unit_id` joins cross-line/page fragments for ownership scoring. Only human reference `ignore` spans are excluded from section accuracy. Abstentions lower ownership accuracy, while cross-record leakage counts actual wrong-role assignments. Null metrics remain null until appropriate reference labels exist.

## Remaining failing observations

- `tests.test_assignment_format_generalization::test_parenthetical_institution_candidate_is_not_declared_as_a_subject`
- `tests.test_assignment_format_generalization::test_wrapped_day_month_year_and_repeated_current_connector_keep_literal_offsets`
- `tests.test_assignment_format_generalization::test_wrapped_numeric_source_range_does_not_degrade_to_year_only`
- `tests.test_batch50_repairs::test_unlocated_date_is_not_guessed`
- `tests.test_batch_failure_repairs::test_actual_flattened_table_recovers_seven_distinct_employer_records`
- `tests.test_block_completion::test_labelled_responsibility_does_not_drop_first_last_or_split_prose_commas`
- `tests.test_existing350_repairs::test_three_organizations_without_company_suffix_keep_distinct_duties`
- `tests.test_flagged_review_resolution::test_noise_does_not_trigger_semantic_retry_or_needs_review_status[2-Footer]`
- `tests.test_multiline_headers_and_date_alignment::test_anita_das_resume_schema_mapping_and_standardization`
- `tests.test_multiline_headers_and_date_alignment::test_benjamin_resume_schema_mapping_and_standardization`
- `tests.test_nov5_five_resume_regressions::test_01_a_lokhande_employers_and_clean_responsibilities`
- `tests.test_nov8_five_resume_regressions::test_05_bhavyashree_ry_narrative_employment_responsibilities_education_cert`
- `tests.test_phase1_repairs::test_no_broad_delivering_or_systems_rule[delivering systems]`
- `tests.test_phase1_repairs::test_no_broad_delivering_or_systems_rule[systems]`
- `tests.test_readiness_audit::test_artifacts_require_specific_source_evidence[2 | P a g e-NarrativeText-False-False]`
- `tests.test_saved_hierarchical_defects::test_engineered_responsibility_is_not_lost_as_a_title`
- `tests.test_saved_hierarchical_defects::test_rachana_header_and_full_title`
- `tests.test_schema_mapping::test_record_boundaries_do_not_merge_or_borrow_fields`
- `tests.test_standardization_v2::test_unparseable_dates_do_not_leak_non_iso_strings_or_invent_century`
- `tests.test_structural_grouping::test_employment_three_column_alignment`
- `tests.test_twelve_ground_truth_replays::test_ground_truth_semantic_validation[abhishek_tiwari]`
- `tests.test_twelve_ground_truth_replays::test_ground_truth_semantic_validation[arnab_kumar_kar]`
- `tests.test_twelve_ground_truth_replays::test_ground_truth_semantic_validation[ashwin_s_s]`
- `tests.test_word_record_recovery::test_three_date_first_qualifications_are_three_populated_records`

The implementation is ready for code review and further development/validation work. It is not a production acceptance result. Independent held-out annotation, resolution of semantic compatibility failures and validation on genuinely independent resumes remain necessary.
