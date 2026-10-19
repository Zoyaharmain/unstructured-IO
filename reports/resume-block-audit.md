# Offline resume corpus audit

**Partial audit stopped by request: 482 files have no completed batch result. No model tests were resumed to generate this report.**
Completed **1059 / 1541** resumes. API calls: **0**.

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

## Detected resume blocks

| Section | Documents with a detected block |
|---|---:|
| Personal information | 979 |
| Summary | 898 |
| Experience | 1005 |
| Projects | 272 |
| Education | 886 |
| Skills | 881 |
| Certifications | 508 |
| Awards and achievements | 217 |
| Publications | 16 |
| Volunteering | 5 |
| Languages | 304 |
| Interests | 69 |
| References | 1 |

A detected block means the local pipeline assigned text to that category. It does not verify correct ownership or completeness. A category not detected may simply be absent from the original resume. Canonical sections and their source spans are counted separately.

Open `block-detection.csv` for a yes/not_detected/not_evaluated matrix per resume, `section-blocks.csv` for heading, source-span, word, entry and page details per detected section, and the HTML table for normal block-by-block text.
