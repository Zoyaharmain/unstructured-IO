# Partial offline resume corpus audit

Stopped at the user’s request after **1,059 / 1,541** batch results. **482 files have no completed batch result. API calls: 0.**

Independent package preflight covered all 1,541 inputs; this is separate from extraction and model testing.

The run invokes production extraction, Sentence-BERT/K-means grouping and local boundary recovery directly. DeepSeek is disabled; the batch container has no network. Input files are read-only.

| Format | Files | Processed | Errors/timeouts/empty | With unassigned text |
|---|---:|---:|---:|---:|
| .doc | 4 | 0 | 4 | 0 |
| .docx | 303 | 302 | 1 | 225 |
| .pdf | 752 | 751 | 1 | 620 |

## Results

- Status counts: `{"error": 6, "processed": 1053}`.
- Source/reference invariant failures: **0**.
- All spans assigned locally: **208** documents.
- Documents with unassigned text: **845**.
- Median locally assigned text: **99.3%** (coverage, not accuracy).
- Documents below 95% local assignment coverage: **218**.
- Triage flags (may overlap): `{"few_sections": 19, "parser_token_disagreement": 22, "unassigned_text": 845, "very_little_text": 1}`.

## What was checked

Exact source-span coverage and text reconstruction; canonical section uniqueness and reconstruction; highlight offset validity; entry references; empty extraction; unresolved spans; unusually sparse output; and token overlap with a separate PDF parser. Parser disagreement is a diagnostic, not a missing-word accuracy score.

## Limits and review queue

This corpus has no manually labeled ground-truth sections or original transcriptions. Semantic section accuracy, precision/recall and word accuracy were **not measured**. A processed document can contain incorrect assignments, even if every span was assigned. The DeepSeek validation/recovery layer was intentionally not tested. Unsupported/corrupt/encrypted documents are reported rather than silently counted as passes.

Private filenames, extracted text and section results are kept in the ignored audit directory. Open `index.html` for a searchable per-file table, `review-queue.csv` for triage, and `documents/*.json` for exact extraction and assigned/unassigned spans. No private resume text is copied into this aggregate report.

## Reproduce

See `docs/BATCH_RESUME_AUDIT.md`. Rerunning the same command resumes unchanged inputs; changed production code or file metadata invalidates the cached result.

## Input preflight

Independent package inspection covered 1541 files; issues: `{"multipart_payload_saved_as_pdf": 1}`.

## Fixes completed and verification status

- Fixed PDF whitespace fragments becoming separate review items, and recognition
  of Skill Set/Skill Sets/Skillset headings. These fixes were active throughout
  the reported full-folder batch attempt.
- Four legacy DOC files failed in the batch because LibreOffice could not create
  its user profile. Added isolated temporary profiles; separate direct extraction
  checks succeeded for **all six DOC files** in the folder. Full grouping rechecks
  after this fix were not run before the user stopped the audit.
- One DOCX failed because an image relationship pointed to `../NULL`. Added narrow
  in-memory recovery without changing document text XML. Direct extraction passed
  on that file; full grouping recheck is pending. The six batch errors above are
  original results, not post-fix failures.
- One file named PDF contains a multipart upload payload, not a valid PDF. It
  remains an invalid-input issue; the original file was not modified.
- The regression suite passed **134 tests**, with 8 upstream parity cases
  deselected. The additional parser-deadline guard test also passed.

The updated deployment image was built locally without network access. The
running Resume Inspector was not restarted. The audit container is stopped;
no batch/retry processing continues.

## Read individual results

Open `.upstream/batch-validation/index.html` for the searchable table. Each
processed row opens a normal side-by-side source/section view, including Needs
review. `review-queue.csv` ranks failures and uncertain cases. Exact private
source spans and metadata remain in `documents/*.json`. These files contain
personal resume data and remain in the ignored private output directory.
