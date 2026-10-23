# Full-folder hierarchical schema mapping

**All 1,541 supported files were attempted locally.** Hierarchy outputs: **1,535**. Remaining pending/unmapped files: **6**. No DeepSeek requests or provider tokens were used.

Source folder: `/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT`. Formats: {'.docx': 453, '.pdf': 1082, '.doc': 6}. There are **1,482 distinct source hashes**; duplicates were still represented as separate files as requested.

## Processing

{'reused_saved_blocks': 1053, 'fresh_local_pipeline': 487, 'normalized_pdf_same_local_pipeline': 1}

The saved blocks for 1,053 files were reused only when their source-file hash matched and current source/hierarchy validation passed. The other files went through the existing local extraction, Sentence-BERT/K-means, recovery and schema stages. Reused blocks retain their original segmentation decisions; this is not a fresh segmentation rerun of those files. The corpus checkpoint runner and immutable manifest are in `scripts/map_resume_corpus.py` and `manifest.json`.

One PDF, `EWM_Resume_Shailesh.pdf`, initially failed content-type detection because its PDF header follows a 137-byte wrapper. A derivative in `normalized-inputs/` passed through the unchanged local pipeline. All three pages' independently parsed text matched before/after prefix removal. Original/derivative hashes and preparation details are in `wrapped-pdf-preparation.json`; original-attempt failure evidence remains in the raw checkpoint. Final results include the recovered mapping explicitly.

## Verification and limits

All **1,535 serialized mapping outputs** were reloaded and passed exact extracted-source interval checks, deterministic hierarchy validation, record-local source evidence checks and exact-quote validation. Populated child items: **95,768**. Unresolved attribute slots: **143,370**. The latter count is not a count of facts missing from the original documents.

All **1,541 original file hashes** were checked again: changed files **0**. Reused saved-artifact hashes were checked again: changed artifacts **0**. Existing extraction, detection and schema implementation code was not modified for this bulk run. Only a separate offline batch runner and its regression tests were added. Runner regression tests: **2 passed** (saved-block reuse/idempotent resume, changed-source rejection).

**These are provisional mappings requiring review.** Exact citations and schema validity do not establish correct names, associations, field completeness or original-PDF word accuracy. The local mapper's known completeness limitations remain. This run contains no new LLM verification and is not a readiness/accuracy certification. Non-resume material may be present; document-scope diagnostics are retained per file.

## Pending/unmapped files

| File | Error | HTTP-style status |
|---|---|---:|
| AmarnathSahu.doc | ExtractionError | 503 |
| MrutyunjaySamal.doc | ExtractionError | 503 |
| Padma Devandla.doc | ExtractionError | 503 |
| Power Platform Developer.doc | ExtractionError | 503 |
| Santosh Solanki.doc | ExtractionError | 503 |
| Santosh Solanki_1.doc | ExtractionError | 503 |

Legacy Word failures with status 503 require the missing LibreOffice `soffice` converter. **The user explicitly requested leaving these six DOC files pending.** They have no completed hierarchy output. No converter was installed and originals were not converted in place. They can be processed later if the user chooses to supply the dependency or supported copies.

## Results to use

- `final-summary.json`: final counts, including the recovered PDF.
- `final-per-resume.json` and `per-resume.csv`: every file, final status and mapping path.
- `review-queue.csv`: failures first, followed by unresolved-field counts.
- `final-failures.json`: outstanding files.
- `documents/<id>/mapping.json`: each ordinary mapped output; the recovered PDF uses `wrapped-pdf-local-recheck/schema.json`.
- `validation.json`: post-serialization source/hierarchy validation outcomes.
- `results.jsonl`, `per-resume.json`, `summary.json`: original checkpoint outcomes, retaining the PDF's initial failure.

To query one result, load its `section_schemas` using `SectionSchema.model_validate`, validate it against the paired `source.json` sections, then call `query_subschemas(hierarchy, 'education.institution')` or another predefined field path. Keep record IDs when joining employer/title or degree/institution results. The live source-bound query endpoint remains documented in `docs/SCHEMA_MAPPING_API.md`.
