# Phase 2 files and behavior changes

## Production

- **New `local_api/services/review_chunking.py`:** pure deterministic planner, request-body budgeting, global source/document inventory bindings, record-aware packing, owned/context separation, safe source splitting, strict chunk response/audit acknowledgement validation, source-overlap record crosswalks and per-pass/document/run request accounting. No provider transport is implemented here.
- **`local_api/services/llm_section_review.py`:** configure new bounded policies, fall back from oversized whole requests to chunks, carry feedback before budgeting, atomically merge only complete validated source decisions, preserve entries on confirmation, report incomplete aggregate coverage/failures and share budgets through bounded follow-ups. Small fitting whole requests retain the historical protocol. Error codes distinguish request exhaustion and unreviewable units.
- **`scripts/check_single_resume.py`:** the actual CLI schema audit now uses compact canonical units and the same request budget/original document digest as section review. Its old parser helper remains available for compatibility tests, but the new audit adapter enforces explicit unit acknowledgements and record-local source references.
- **`scripts/single_resume_pipeline.py`:** pass feedback, budget and document binding into the review stage; expose aggregate provider coverage and budget events. Phase 1's fingerprint and existing bounded stopping/failure behavior remain.

No edits to the Phase 1 continuation classifier, education normalization, extraction/detection/embedding code, source schema fields, mapping rules or search. No server restart or .env edits. No previous 350-run logic executed.

## Tests

- New `tests/test_review_chunking.py`: 24 focused mocked-provider checks for deterministic ownership, source fidelity, source ordering, record boundaries, columns, cross-page records, oversized records/spans, invalid/unknown/context IDs, gaps/overlaps/conflicts, incomplete/duplicate audit acknowledgements, cross-record citation rejection, rollback, feedback/output accounting, per-pass/document/shared-global budget exhaustion and ownership crosswalks.
- `tests/test_llm_section_review.py`: the old max_units=2 rejection case becomes an invalid zero-unit-budget rejection; valid small budgets are now covered as successful multi-chunk cases. Malformed-response and source-conservation assertions remain.
- `tests/test_flagged_review_resolution.py`: a historical whole-response replay explicitly sets large **test-only** token-policy budgets to match its existing large character budget. This prevents replaying historical uN decisions into a new global-ID chunk contract. All expected source/education/work ownership assertions remain intact. Production defaults were not raised.

Initial new-fixture issues and one historical protocol regression were retained in logs, corrected and rerun. No failing production invariant was skipped or weakened. Exact commands/results appear in test-results.txt. The final full run covers all tests with no exclusions.
