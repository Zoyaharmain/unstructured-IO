# Repairs applied to the existing 350 documents

**This pass repairs the existing documents only. No unseen-resume batch was started. The result is not a claim that every source word, section label and relationship is now correct.**

## Implemented fixes

1. **Employer headers without business suffixes.** Short organization/location headers with parenthesized employment ranges now establish record boundaries even without Ltd/Inc/Technologies. Explicit `Job Role:` lines continue the employer record. Guards reject project/client/training/education headings, duty sentences, standalone role/date strings and bare years. Employer field references point to the original header; no employer name, title or date is invented.
2. **Repeated PDF table cells.** Matching previously paired every repeated text occurrence with every identical physical line, allowing both cells to inherit the first row. Physical lines and textual occurrences now pair one-to-one in source order when counts agree. Ambiguous cardinalities produce no guessed location. Existing cached line hints are cleared before refreshing geometry.
3. **Existing failed reviews.** Replayed saved responses through the strict current validator. Avishek M and Dipali Kothawade pass; source coverage and record integrity remain checked. These are offline recoveries, not new live-provider success. Jewel's saved responses remain invalid and its unchanged local result is retained. A requested live retry was blocked before sending anything, as described below.

## Applied across the 350-document inventory

Rebuilt PDF-location evidence from the preserved PDFs and regenerated record proposals for **all 350 distinct saved live documents**. Exact source text, source offsets and existing section decisions remain unchanged during the geometry/grouping repair. Separate successful provider replays update Avishek/Dipali's section decisions under the normal exact-coverage validator. Original artifacts were preserved; the new outputs are separate.

- **350/350** extracted-source integrity checks passed.
- **238 documents** have changed record proposals relative to their historical saved outputs. This is a change count, not an accuracy score.
- **700 original input files checked; zero changed** during the all-document repair.
- No paid provider request was sent. No human approval or gold promotion occurred.

Use [repaired-350/current-results.json](repaired-350/current-results.json) as the index of the new artifacts. It gives each document's original PDF hash, repaired artifact path/hash, historical live status, and explicit repair mode. Do not mistake the retained historical statuses for new provider reviews. The [review page](index.html) shows source IDs, pages, exact record text, unknown text and warnings for all 350; [remaining-review-queue.csv](remaining-review-queue.csv) provides the same triage summary as a spreadsheet.

## Concrete before/after evidence

| Document | Before | After |
|---|---|---|
| DeepaR | One job group, 42 meaningful employment blocks unlinked | Three source-supported job groups, zero unlinked duties |
| Dhiman Mishra | One job group, 49 meaningful employment blocks unlinked | Three source-supported job groups, zero unlinked duties |
| PUPPYKUMARI | Both B.S.E.B cells could resolve to the first PDF row | Separate 10th/B.S.E.B/2005 and 12th/B.S.E.B/2007 rows; B.C.A/S.M. U/2011 and M.C.A/G.G.S.I.P.U/2014 preserved |
| Avishek M / Dipali Kothawade | Historical live review failure | Saved response accepted offline under current exact validation; repaired outputs indexed separately |

A controlled comparison holds the refreshed PDF geometry constant on both sides and toggles only the employer-header patch: **1,029 → 939 unlinked employment blocks** across the same 350 documents. The [isolated comparison](isolated-header-effect.json) records every document. Mohit Kumar exposes two career-wide skill lines preceding the first employer; they remain visible and unlinked rather than being attached to that employer.

Comparing to all historical saved artifacts instead gives **1,055 → 1,199 unlinked employment/education blocks combined**. Historical batches used different grouping versions; current conservative geometry/grouping also exposes unsupported older associations. This larger total must not be hidden or presented as an improvement. Unlinked table headings, genuine career-wide text and uncertain fields require distinguishing from missing job associations; these are not automatically extraction failures. The controlled comparison above isolates the specific code fix without that version confound.

## Still unresolved — not marked fixed

The current repaired set retains **64 meaningful unknown spans in candidate/unknown-scope documents**, and **413 in out-of-scope documents**. It also flags **one document requiring an OCR reference**, **five with damaged glyphs**, **193 with unlinked record content**, and **243 with record-level warnings**. Counts overlap and include provisional/out-of-scope records; they are review signals, not independently confirmed semantic errors or error rates. See [remaining-summary.json](remaining-summary.json).

Jewel still requires a valid provider review or source-backed manual correction. Existing damaged glyphs, conflicting PDF text layers and the scanned Keerthi page cannot be corrected by guessing from category coverage. Employment and education associations remain automated proposals. These limitations are retained in the output; no flag was suppressed to make the totals look clean. No independent human-approved references were created.

## Jewel retained for local review

The user explicitly declined sending **JEWEL BIJOY.pdf** to external DeepSeek. No external retry was sent. Jewel remains pending for local source review with its preserved local result; no retry is scheduled or authorized. The [recorded decision](jewel-local-review-decision.json) and repaired output index reflect this status.

## Validation

**291 tests passed in 109.58 seconds** after the final production changes: [full regression log](final-tests/regression.log), [JUnit results](final-tests/tests.xml). Tests cover header recognition, responsibility/project/degree rejection, three-company job ownership, repeated-cell row mapping and ambiguous-match rejection, alongside the existing source coverage, atomic fallback, provider-contract and project regression checks. Provider credentials were removed and external sockets blocked in the test harness. `git diff --check` passed.

**Do not run another 300 yet.** These are implemented and applied repairs, with the remaining issues explicitly tracked; the existing 350 have not been certified correct.
