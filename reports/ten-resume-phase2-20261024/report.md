# Phase 2 offline implementation and replay

**Completed offline. No live DeepSeek/API calls. NO-GO for production scaling or semantic certification.**

The actual section-review stage now supports deterministic source-owned chunks and strict global merge validation. The CLI schema-audit stage uses compact record-bound units and exhaustive acknowledgement coverage. Both share per-pass, per-document and run request budgets. Source IDs, offsets, layout and established anchors remain traceable; failed/unreviewable chunks cannot claim complete coverage. Phase 1 and education/mapping policy are preserved.

## Verified frozen-input replay

The baseline is the Phase 1 after/ output built from the original ten frozen extraction/section inventories. These are already processed development/stress inputs, not ten fresh human labels. Mock placement confirms frozen categories; mock audits acknowledge all units with no findings. Thus the following are structural orchestration results, not DeepSeek performance or accuracy measurements.

| Resume | Mock section requests | Mock audit requests | Aggregate stage statuses |
|---|---:|---:|---|
| Aditya vashisth.pdf | 2 | 2 | complete / complete |
| _ManjunathMurugan.pdf | 1 | 2 | complete / complete |
| Chandan Kumar BV.pdf | 1 | 1 | complete / complete |
| Siva Mari.pdf | 5 | 6 | complete / complete |
| Divya Balyan.pdf | 2 | 3 | complete / complete |
| Vikrant Roy.pdf | 5 | 6 | complete / complete |
| Sundar.pdf | 2 | 3 | complete / complete |
| Santhosh KR -  SAP EWM.pdf | 2 | 2 | complete / complete |
| Sumit.pdf | 3 | 4 | complete / complete |
| HarmeetSingh cv.pdf | 2 | 2 | complete / complete |

All ten complete both mocked stages, using **56 synthetic requests** total. Siva Mari and Vikrant Roy now fit multi-chunk section/audit plans; Divya, Sundar and Sumit fit the compact audit plans. Maximum measured chunk request: **99,862 serialized characters/bytes**, under the 200,000-character and 100,000-input-policy bounds, with 16,000 output tokens reserved against the configured 128,000 local context guard. Largest owned-target count: 406 (limit 600). These numbers use mock-only configuration; a real provider plan must be regenerated with its approved current configuration and verified context/token behavior.

No legacy data, nested values/quotes, field index, parent assignment, source interval, established entry membership or residual coverage changes in any of the ten outputs. Two meaningful unknown spans remain. Source-accounting reason strings and unresolved-block confirmation/provenance annotations change because the production review path records the synthetic review; full recursive differences are in output-differences-verified.json. Record crosswalks are saved in each review state and are source-overlap diagnostics, not automatic reference-label alignment.

Reference comparison remains **Group01 6/6, Group02 5/5, older Manjunath expectations separately 6/6**. Only those 17 partial tuples are scored. Pending rows and uncertain A069 stay excluded; precision/recall/F1 and whole-resume semantic accuracy remain unavailable. Empty mock audit findings do not resolve the original 101 provider concerns.

## Tests, preservation and limits

- Final full offline suite: **458 passed**, no failures/skips; **24 chunk-contract tests** passed. The larger focused/compatibility runs also passed; overlapping counts are explained in test-results.txt.
- Test transports were mocked; offline guard logs record zero external socket attempts. Initial failures and their fixes remain visible; no failing source invariant was removed.
- Preservation: **16,036 prior files checked, zero changed**. Original PDFs, frozen runs, ground truth and prior 350 artifacts remain untouched. Only the approved chunking/integration/test files changed relative to the Phase 1 snapshot.
- No extraction/detection/embeddings for the ten-input replay; the full regression suite independently exercises its normal fixtures and cached model tests. No server or larger batch started.
- Remaining limitations: byte-based token-policy calibration, indivisible oversized fields/context, provisional upstream record ownership, adjacent-only association audit scope, D2 paragraph reconstruction and incomplete human semantic labels. See limitations.md.

## Review files and stop boundary

- design.md — contracts, budgeting and integration.
- changes.md — exact production/test changes.
- test-results.txt — commands, actual outcomes and retained failure history.
- source-coverage-ledger-verified.json — owned/checked units, identities and shared budget events; detailed plans/messages in replay-verified/.
- before-after-comparison-verified.json / output-differences-verified.json — source/mapping/record comparisons.
- reference-comparison-verified.json — provenance-separated partial tuples.
- request-measurements-verified.json — serialized chunk envelope guards.
- preservation-check.json — immutable-artifact checks.
- readiness-assessment.md / limitations.md — NO-GO for scaling; conditions for a separately approved small provider pilot.

**Stopped here.** Any paid evaluation needs explicit new document scope, current settings and a new request cap. The old 40-call approval is not reused, and these 56 mocks are not a paid authorization.
