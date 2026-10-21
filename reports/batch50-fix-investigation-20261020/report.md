# Fixes for the 50-document diagnostic batch

The reported problems were real but represented different failure types. Production changes and offline regression checks are implemented. **The batch is not yet an accuracy-certified set of 50 candidate resumes.** No DeepSeek requests or API charges were made for this investigation. Original PDFs, saved provider responses, annotations and previous reports were preserved.

## What changed


| Problem | Cause and correction | Remaining limit |
|---|---|---|
| Non-resume documents | Content-based scope detection now recognizes an explicit hiring JD, interview preparation guide and website critique, in addition to the requirements form. | Four exclusions; the other 46 remain candidate-or-unknown until source review. Replacements were not silently selected. |
| Word fragments | Tokenizer and geometry cuts move to ordinary-word boundaries. Joined heading exceptions are restricted; PostgreSQL is protected. Provider offsets splitting ordinary words are rejected. | Old saved provider outputs remain unchanged. A future provider can still return invalid splits; bounded retry or explicit failure applies. |
| Missing PDF text | A local PDF-character recovery layer restores complete missing physical lines; partial overlaps are retained as uncertainty. | This cannot establish OCR fidelity or recover text absent from the PDF text layer. |
| Duplicate extraction | Only exact same-text/same-page/same-coordinate duplicates are collapsed; the duplicate objects and original indices are retained in provenance. | Genuine repeated text at different locations is preserved. |
| Detached or merged records | Reviewed employment groups use visible headers/page positions rather than lane identity. Education uses qualification rows and nearby institution/year/grade rows. | These are proposals, not independently verified record relationships; ambiguous layouts remain a limitation. |
| Frontend grouping mismatch | The readable display now uses reviewed JSON entries instead of rebuilding records with the old lane adapter. | Original source spans and additional ungrouped content remain visible. |
| Incorrect repeated-title geometry | Identical source words could match the wrong occurrence on a page. Line hints now check the element's own source region. | Existing saved artifacts are immutable; fresh geometry was computed in memory for this replay. |
| Keerthi provider failure | Saved response 1 omitted u19; response 2 used u15[20:36] for a 20-character span. Retry feedback now names missing IDs and required lengths. | Both historical responses remain invalid. No live provider success is claimed. Validation was not relaxed. |

## Dataset exclusions

- `Java Aws backend.pdf`: requirements form.
- `Java Developer & Angular_sanjeev.pdf`: explicit hiring job description. Its 39 pending spans are not candidate-history failures.
- `Divakar_Prep_guide.pdf`: explicit interview preparation guide. Its 138 pending spans are not candidate-history failures.
- `Assignment.pdf`: website critique, not a candidate resume.

These source-purpose decisions are automated evidence plus assistant inspection, not human gold approvals. No clean-50 accuracy denominator has been manufactured.

## Source extraction findings

- **GAURAVAGRAWAL:** recovered the page-2 Achievements heading and collapsed one exact overlapping awards-text duplicate.
- **Piyush Anand 1:** recovered four page-3 lines, including Tata Tele Services and the missing responsibilities. The original page was rendered and inspected.
- **SAIPREETHIJUNGA1_3:** recovered two page-4 bullets and two page-6 skills lines. Rendered pages 4 and 6 confirm the source text. Whole-document token comparisons had underreported this because the same words occur elsewhere.
- **Ajay Bandagi:** collapsed one exact overlapping duplicate region.

Total: **nine physical PDF lines recovered and two duplicate regions collapsed** in the offline source comparison. All other source text stays intact. Recovered inventories require fresh detection; old span IDs and cached classifications are not reused against them.

## Keerthi source check

The one-page scanned original was rendered and inspected against the fresh OCR. This exposes an additional extraction problem: source “web technologies” became “web technologics,” “Seeking” became “Secking,” and the Gmail address was read with “pmail.com.” The two-column Skills reading order is also interleaved. A valid provider response would not certify these OCR words. No contact details were guessed or automatically corrected. Keerthi therefore remains unresolved for both OCR fidelity and provider validation.

## Record relationship checks

The saved decisions were replayed with source geometry; no new section labels were obtained from an LLM. Examples:

| Resume | Old record grouping | Revised proposal |
|---|---|---|
| Pavan Bakku | One combined employment group; two education groups | Four jobs; one qualification |
| NagaVishnu | Two employment groups merged employers; grade ownership was wrong | Three employer anchors and three qualification anchors; responsibility ownership still requires review |
| Prasad PR | Dates detached from PWC; degrees/institutions combined | Three jobs with PWC dates attached; three qualification groups |

In NagaVishnu, the shared Accomplishments list following several employment headers is not independently proven to belong to the last employer. This remains an explicit human-review decision.

The before/after member texts for every document are available in [the readable comparison](index.html). These changes address grouping causes; they do not prove every role, employer, responsibility, grade or year is correct. Source-backed human review is still required, especially for overlapping dates, shared institution headings, multi-column layouts, and mixed project/employment history.

## What actually ran

1. Offline source/geometry replay for the existing 50 hash-bound PDFs, with networking forbidden. No extraction model, provider request or gold promotion in this replay.
2. Fresh local extraction + BERT/K-means + local recovery for **four** PDFs only: GAURAVAGRAWAL, Piyush Anand 1, SAIPREETHIJUNGA1_3 and Keerthi_SAPresume. All four completed with zero interval errors. Three still have local unassigned text. No API was used.
3. Tokenizer/geometry-unit checks for all five previously word-split-flagged documents: **zero ordinary internal-word cuts** in the revised local unit inventories. This checks local cuts, not the correctness of old saved provider labels.
4. Targeted tests for scope evidence, word boundaries, strict range rejection, precise retry feedback, same-row dates, employer/responsibility membership, degree/institution/year/grade membership, missing-line recovery, same-region duplicates, and repeated PDF title matching.

The fresh four-document run preceded the final geometry refinements; the final offline replay and regression tests cover those refinements. No fresh 50-document LLM run was performed.

## Review and next step

Open [index.html](index.html) to compare old and revised employment/education memberships against the linked originals. This is a read-only comparison, not an approval interface. Use the existing human-review workflow to record source-backed corrections and explicit approvals; no automatic gold promotion occurred.

Before another paid batch: confirm the scope exclusions and replacement candidates, inspect the revised record memberships, and correct/approve Keerthi's confirmed OCR discrepancies against the image. A live Keerthi retry is still needed to establish whether the improved repair prompt succeeds with the provider. Do not interpret zero pending spans as accuracy.

Artifacts: [per-document CSV](final-offline-audit/per-document.csv), [replay summary](final-offline-audit/summary.json), [fresh local results](fresh-local/current-results.json), [word-cut checks](word-cut-checks.json), and [source hash checks](source-bindings.json).

Reproduce the offline replay without API calls (choose a new output directory):

```bash
.venv/bin/python -B scripts/audit_batch50_repairs.py \
  --run reports/pilot-50-review-20261020-batch1 \
  --output "reports/batch50-offline-recheck-$(date +%Y%m%d-%H%M%S)"
```

Preservation: 332 original-run files checked, zero changed; 50/50 original corpus PDFs match the frozen source hashes. No bulk processing occurred.

## Verification status

The final full regression run is recorded in `complete-tests/regression.log` and `complete-tests/tests.xml`; its source hashes are checked before/after. Earlier test runs in this directory are intermediate checks and are not substituted for the final run. No API calls were made, and no gold annotations were created.

**Final regression: 224 passed, zero failed, in 88.00 seconds.** All 45 snapshotted source/test files remained unchanged during this final run. External connection attempts: zero. [Test log](complete-tests/regression.log), [JUnit results](complete-tests/tests.xml), [source/network verification](complete-tests/verification.json).
