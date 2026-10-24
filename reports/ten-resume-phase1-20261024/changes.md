# Phase 1 changes: D1 and D3 only

Production changes are limited to `local_api/services/record_relationships.py` and `scripts/single_resume_pipeline.py`. `tests/test_phase1_repairs.py` adds focused regressions. No edits to education normalization, extraction, detection, embeddings, schema fields, chunking, search, API configuration or ground truth. Prior reports are preserved.

## D1 — responsibility continuation

Before: `field_kinds('delivering high-integrity data feeds to downstream Fund accounting systems.', 'experience')` returned `['employer']` because of the generic suffix `systems`.

After: a leading **delivering clause with an object and a continuation preposition** (`to`, `for`, `through`, `across`, `within`) is classified as responsibilities before suffix matching. This is a source-shape guard, not a company dictionary or guessed missing text. The clause stays within its supplied record; no cross-job regrouping. Bare `systems`, `Delivering results`, `Delivering Systems`, `Delivering Systems Ltd`, explicit Company labels, BNP Paribas ISPL and Persistent Systems retain the tested prior/header behavior. The guard does not universally disambiguate every possible organization name; unusually sentence-shaped company names still need source review.

The real frozen BNP record retains the same employer/title/dates and source ownership. Its e24:0:75 continuation now populates one responsibility with its own exact quote. It is not merged into the preceding sentence; D2 paragraph reconstruction remains outside scope.

## D3 — semantic recovery fingerprint

Before: the fingerprint included legacy data and full entry dumps but ignored nested output. Hierarchy-only changes did not count as progress, while changing an entry explanation could count.

After: it includes parent categories; record IDs/source ownership; attribute names, item values and support status; exact source IDs/quotes; residual source evidence; section block IDs/offsets/text; entry IDs/block membership/field assignments; unresolved spans and legacy data. It excludes record review reasons, boundary explanations, block reasons, warnings, metadata counters and confidence. Field/status representation is derived from typed attributes; no generic removal of dictionary keys that could accidentally remove a real field value.

The retry loop itself, retry budget, failure handling, previous-valid-result retention, audit feedback and stop conditions were not changed. The fingerprint allows meaningful hierarchical progress to be recognized, but still cannot turn repeated mapping into a semantic correctness guarantee.

## Red-to-green process

The two original investigation tests reproduced **2 failures on unchanged production** before edits (`red-tests.txt`). The pre-fix field replay was captured while both production files were still unchanged.

Additional tests were written before acceptance. Their first run exposed an invalid new fixture lacking required page_number; that fixture was corrected and the erroneous logs retained. Corrected pre-fix testing used byte/hash-verified HEAD copies of the two unchanged files, without reverting live source: **11 failed, 12 passed, 1 deselected**. The deselected integration case intentionally imports installed code internally, so was not presented as a pre-fix check. Original two red tests already establish both defects independently. Completed post-fix runs and commands are in test-results.txt.

## Frozen local replay method

`prepare_baseline.py` reads each frozen final extraction and sections file, deep-copies via typed parsing, recomputes field evidence with `annotate_relationships`, then invokes the actual `map_schema`. It does not call PDF extraction, section detection, embeddings, local resegmentation, recovery, or any provider. Existing section categories, intervals, entry IDs and block memberships are asserted unchanged. Field evidence must be recomputed to test D1; mapping the old frozen `fields.employer` indices without annotation would not exercise the repaired classifier.

The before replay reproduces all ten frozen schema responses exactly. The after replay uses precisely the same frozen inventories. Before and after outputs are isolated under before/ and after/. Validation checks exact extracted-source accounting, hierarchy/quotes, record ownership, predefined field index agreement and the partial reference tuples. Raw PDFs are never re-extracted for this replay. The full regression suite separately exercises its existing test fixtures and local extraction/model code as part of the explicitly requested offline tests.

## Every meaningful output change

**Nine schema responses are exactly unchanged. Only Manjunath changes.**

- Section `experience`, entry `experience-2`: e24 leaves `fields.employer` and enters `fields.responsibilities`. Record ID and owned block indices remain unchanged.
- Legacy `data.experience[1].responsibilities` gains the existing literal continuation at index 1. No employer, role, date or other legacy value changes.
- Nested `experience-2.responsibilities` gains the same value with exact quote `delivering high-integrity data feeds to downstream Fund accounting systems.` in e24:0:75. Nested populated items: **113 → 114**. No existing nested item is removed.
- That fully represented source block leaves nested experience residuals: **29 → 28**. Raw source and record ownership remain present; nothing is deleted from the inventory.
- Subsequent responsibility positions shift by one, so legacy field-evidence paths and the derived field_index/JSON pointers shift accordingly. They were checked against the canonical hierarchy; these are insertion effects, not extra new facts.
- D3 changes no fixed-inventory mapper output. It changes feedback progress detection, covered by focused and existing bounded-loop tests.

Source-span accounting is identical for each document. Final unresolved meaningful spans remain **2** (one Vikrant, one Harmeet). Every record retains its parent and source ownership. The legacy and nested responsibility changes agree. All other schema differences are absent; recursive differences are saved in before-after-comparison.json.

The 17 partial reference tuples remain exact before and after: Group01 6/6, Group02 5/5, and older Manjunath expectations separately 6/6. Pending fields and uncertain A069 remain excluded. No labels were added. Precision, recall, F1 and population accuracy are unavailable from this partial positive reference set. One supported additional field item is evidence of the targeted correction, not a new overall accuracy estimate.
