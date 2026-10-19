# Test the resume corpus without APIs

`scripts/batch_check_resumes.py` calls the local production functions directly:
Unstructured extraction → Sentence-BERT/K-means → local boundary recovery. It never
imports/calls the DeepSeek reviewer or HTTP routes. Provider keys are removed from
the worker environment, Hugging Face is offline and Python network connections
are blocked. For stronger isolation, use Docker's `--network none` as below.
The Docker image must already contain the cached models and extraction dependencies.
No `.env` or API key is passed to this run.

From the project root, run:

```bash
resume_folder='/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT'
./scripts/run_offline_resume_audit.sh "$resume_folder" --timeout 120

.venv/bin/python scripts/report_resume_audit.py .upstream/batch-validation
```

PDFs use fast embedded-text extraction, with local OCR if it returns no text.
Word documents use auto extraction. This exercises those selected paths, not every
available OCR/layout strategy for every file. Use `--limit 10` for a pilot or
`--no-ocr-fallback` to test embedded text only. `--timeout` bounds each document;
the timer is Unix-specific and native libraries can delay Python signal delivery.
The same command resumes matching checkpoints, including recorded failures. Use a
new output directory for a fresh run. Model initialization failures abort the run
rather than counting every file as a processing failure.

With all dependencies installed locally, Docker is optional:

```bash
.venv/bin/python scripts/batch_check_resumes.py "$resume_folder" --workers 2
```

Keep the output private: it contains filenames and full extracted resumes. The
ignored output directory has restricted permissions. The aggregate Markdown/JSON
reports in `reports/` contain counts only. Open `.upstream/batch-validation/index.html`
in a browser for the searchable table, or inspect `review-queue.csv`. Each table row links to a normal side-by-side
source/section view; per-document JSON files retain exact source evidence. Each includes both assigned sections and Needs review.

A processing/invariant pass is not a claim that all sections are semantically
correct. Unassigned text and parser disagreements require inspection. Annotated
reference resumes are needed to measure accuracy; DeepSeek is deliberately absent
from this test, so its final validation stage is not covered.

## Fixes found during the corpus run

- PDF line-boundary spaces are kept on adjacent source spans, so whitespace does
  not become an independent Needs review item. Character offsets and source
  reconstruction remain exact.
- `Skill Set`, `Skill Sets` and `Skillset` are recognized as Skills headings.
- Legacy Word conversion uses a unique temporary LibreOffice profile per document,
  avoiding unwritable/shared user profiles under Docker and concurrent workers.
- A DOCX relationship to a missing `NULL` image can be removed from the in-memory
  package. Text XML remains unchanged and the repair count is exposed in element
  metadata as `removed_null_image_relationships`. Other missing parts are not
  silently removed. Uploaded/source files are never modified.

After fixing a processing failure, add `--retry-failed` to recheck failures while
retaining prior processed results. This is explicitly an incremental repair audit,
not a fresh full-corpus rerun after code changes. `retained_from_prior_revision`
identifies retained results. Omit this option (or use a new output directory) when
you need to validate changed grouping behavior across the entire corpus.

## Inspect detected section blocks

The report generator also writes `block-detection.csv`: one row per resume with
separate yes/not_detected/not_evaluated columns for Experience, Education, Skills,
Projects and every other supported category. `section-blocks.csv` lists each
canonical section's source heading, source-span count, word count, entry count,
source pages and a text preview. The HTML detail view shows the full section text.
These reports are derived from saved results; generating them does not resume
model testing or call an API. Detection means text was assigned to that category;
correctness remains unverified without comparison against the original resume.
