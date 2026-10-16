# Resume section detection: local Sentence-BERT and K-means

## Repository integration

The structural approach now follows the requested
[knowledge-graph-resume repository](https://github.com/Gopi088/knowledge-graph-resume),
reviewed at commit `48376b8d8a0f64d1ab59b405ded3d9f38fc9ae48`.
Relevant modules are `resume-kg-poc/backend/app/pipeline/preprocessing.py`,
`segmentation.py`, `semantic_blocks.py`, `document_blocks.py`, `embeddings.py`,
and `clustering.py`. This supersedes the earlier paper-based rationale.

The repository's actual `semantic_blocks.py` module is now included, unchanged,
in `local_api/vendor/resume_semantic_blocks.py`. Provenance and the reviewed
revision are recorded in `local_api/vendor/README.md`. The API calls its
`prepare_blocks()` and `group_sections()` functions through
`local_api/services/readable_resume.py`. No extraction checkout or graph stack
from the repository is required at runtime.

Unstructured remains the text extractor. Explicit heading/layout boundaries
establish section ownership; Sentence-BERT/K-means supply semantic evidence and
classify unsupported headings or unanchored content. Inside explicit sections,
body vocabulary cannot override ownership just because it resembles another
category. Personal header names/headlines adjacent to an explicit email address
remain together. Missing BERT assets produce a setup error rather than TF-IDF.

## Readable output matching the supplied reference

The default section view displays normal text blocks, not individual extraction
cards or JSON. It retains headings such as **Profile Snapshot**, **Core
Competencies** and **Work History**. Work history uses the repository's hierarchy:

```text
Work History
  Employer
    Role and employment dates
      Responsibilities and their continuation lines
    Earlier role and dates
      Earlier responsibilities
  Next employer
    Role and responsibilities
```

The supplied reference JSON has many line-sized `details` entries and empty
responsibility lists. Its section boundaries inform the view; those fragments
are grouped under actual employer and role owners rather than reproduced as
separate jobs. The adapter additionally repairs slash-wrapped employer names and
short dated role titles that the repository otherwise leaves in responsibilities.
The readable text preserves repeated words and source spelling; it does not
invent missing names or silently replace source text with normalized fields.

`readable_blocks` is a recursive tree of `kind`, `title`, `block_indices` and
`children`. Indices point into the section's immutable `blocks` array. Every
non-heading span and subsequent heading has exactly one readable owner. The first
heading is shown in the card title. Ignored/unknown repository rows remain in a
fallback readable group. The API checks this partition before returning.
Derived employer/role titles label the hierarchy; original source wording remains
available in full. Display joins wrapped lines with spaces; source offsets and
characters are untouched. Expand **Inspect original text and grouping evidence**
for individual source spans, scores, reasons and navigation to the document.

## What was implemented

`POST /api/v1/resume/sections` groups previously extracted elements. It does not
change the raw Unstructured extraction endpoint or its element order/text.
The Resume Inspector has a new **Resume sections** tab. The user must confirm
that extracted words were checked against the original before detection is
available. API requests require `extraction_verified: true`; false or missing
confirmation returns 422. This is caller attestation, not proof of OCR accuracy.

The section families are personal information, summary, experience, projects,
education, skills, certifications, awards/achievements, publications,
volunteering, languages, interests and references. Only detected sections appear.
Uncertain spans are returned separately in **Needs review**.

The implementation uses two learned techniques:

1. **Sentence-BERT embeddings:** the pinned
   [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
   model uses a compact distilled `BertModel` encoder, not original BERT-base.
   Runtime checks its `model_type == 'bert'`. This model is a general sentence
   encoder, not a resume-fine-tuned classifier. Revision is recorded in
   `local_api/data/section_model.json`; remote model code is disabled.
2. **Seeded K-means:** separate heading/content clustering fits normalized BERT
   embeddings of curated examples in `section_anchors.json`. Per-category means
   initialize 13 centroids. Majority labels of seed examples name the clusters.
   Models fail initialization if distinct category labels cannot be established.
   This is anchor-guided clustering, not anonymous clusters automatically named
   by K-means or per-resume discovery of an unknown number of sections.

Explicit known-heading aliases supplement BERT/K-means. No LLM, hosted inference,
DBSCAN, NER or unrelated classification model is used. Labeled semantic seed examples and structural
constraints are essential: K-means alone does not supply category names or
resume boundaries. Regex recognizes structural formatting, inline heading delimiters and entry boundaries; body keyword matches do not establish section headings.

## Boundary and preservation behavior

- Lines are separated without altering their text. Lines over 200 wordpieces are
  split with tokenizer offsets before encoding, below the encoder's context
  limit. Output text remains exact; it is not silently truncated or regenerated.
- Known standalone headings, including letter-spaced headings such as `S K I L L S`,
  establish boundaries. `Skills: Python SQL` is split at an exact source offset:
  the heading, delimiter, whitespace and body all remain in the source ledger.
- Merged PDF elements beginning with an exact capitalized heading and a
  capitalized value (for example `Summary Backend Developer...`) are also split
  with exact offsets. This conservative formatting heuristic recovers boundaries
  in the reference repository's sample PDFs. It can still misread similarly
  capitalized prose; results need review. Lowercase continuations such as
  `Experience building APIs` are not split by this rule.
- Record fields such as `Technologies:`, `Tools:`, `Role:` and `Achievement:`
  do not start another section or trigger semantic conflict against their owner.
- Each section also returns `entries`, which reference its existing `blocks` by
  zero-based `block_indices`. Explicit Title elements, project/company labels and
  short dated headers can start entries in Experience, Projects and Education.
  Entries never cross layout lanes or heading contexts. No visible boundary means
  one continuation group, rather than guessed employer/project records. These
  groups remain provisional: company and role headings on separate lines can
  require review. The legacy `entries` field remains available; the UI uses the richer repository-derived `readable_blocks` hierarchy.
- Strong heading assignments establish context for following content in the same
  layout lane. Context is recorded with its source element index. For inferred semantic headings, very strong
  semantic conflict leaves a span for review. Explicit known headings keep ownership
  even when a responsibility mentions skills, projects or achievements.
- Clearly separated column positions are clustered with K-means on normalized X
  coordinates. Each lane maintains its own heading context, so interleaved source
  order does not automatically mix sidebar skills and main-column experience.
- Generic compound heading phrases are independently embedded. Distinct strong
  BERT/K-means section labels, such as Education and Certifications, result in a
  review item and terminate the old context instead of choosing just one label.
- A short opening name may use adjacent BERT-recognized contact details as
  context. An explicit email next to the opening identity is also structural contact evidence.
- Original Footer/PageBreak elements are retained for review, keeping page
  separators out of experience/project text without interrupting continuation.
- Each output span records its source element index, exact start/end offsets,
  page, layout lane, cluster space/ID, semantic candidate, similarity, margin and
  assignment reason. Heading-context scores describe the semantic candidate;
  they are not probabilities that the inherited section is correct.
- Before returning, all spans are checked for contiguous, nonoverlapping coverage
  and exact reconstruction of every input element. Text goes into either a
  proposed section or Needs review; nothing is silently dropped or duplicated.

Similarity gates are explicit development defaults: heading match .72 with .09
margin; standalone content .44 with .07 margin; strong context conflict .65 with
.12 margin. Compound components require .85/.12. These are not thresholds
validated against a representative held-out resume benchmark. Seed-cluster purity
is a development diagnostic, not resume accuracy. Assigned text percentage is
coverage, not correctness. Results remain provisional even without review items.

## API and deployment

Example JSON (normally sent by the UI using the actual extraction response):

```json
{
  "extraction_verified": true,
  "elements": [
    {"type": "Title", "text": "Projects", "page_number": 1, "metadata": {}},
    {"type": "NarrativeText", "text": "Personal project: created an expense tracker.", "page_number": 1, "metadata": {}}
  ]
}
```

The response contains `status`, `sections`, `needs_review`, `metadata` and
`warnings`. Each section contains `category`, `label`, `source_heading`, source-mapped `blocks`, legacy `entries`, and hierarchical `readable_blocks`.
Metadata reports model/revision, anchor hash, algorithm, coverage counts and
`all_source_text_preserved`. Download section JSON from the UI to inspect it. Each span also has Locate source
block, which selects the original raw element and navigates to its PDF page when
page metadata is available. On desktop the original preview remains sticky while
scrolling long section results.

Limits: 1–1,000 elements, 100,000 total characters, 2,000 generated text units;
no nonempty text or missing verification gives 422. Missing packages/cached model
give a generic 503 with a setup command; unexpected failures give a generic 500.
Application logs omit document contents and exception messages. Model loading is
lazy, cached per process and serialized; inference is serialized per model to
avoid concurrent CPU/memory spikes. Raw extraction works without loading BERT.

Installed Python dependencies: `sentence-transformers==5.7.0`,
`scikit-learn==1.9.1` plus their declared dependencies. The existing CPU PyTorch
installation is reused. Versions are recorded in API requirements/constraints.
Prepare local assets with the same HF_HOME used by the server:

```bash
HF_HOME="$PWD/.venv/model-cache" .venv/bin/python scripts/warm_models.py --sections
```

Runtime loads the pinned model with `local_files_only=True`: no request sends
resume text to a hosted model or triggers a model download. The Dockerfile
preloads BERT in addition to its existing assets. Rebuild/recreate the image or
restart Uvicorn for the new feature. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Evaluation limits

Correct word extraction is necessary but does not prove correct reading order,
columns, headings or section semantics. Unknown headings, merged columns in a
single element, nested headings, unfamiliar layouts, multilingual resumes and
OCR errors can still produce incorrect assignments, including context mistakes.
The detector abstains in several ambiguous cases; it cannot guarantee that all
wrong assignments will be identified. It is an inspectable baseline requiring
human review, not a validated universal resume parser.

The development fixtures exercise standard and synonym headings, personal
preamble, interleaved columns, long/combined blocks, ambiguous/combined headings,
source preservation, API gating/dependency errors, and real DOCX extraction.
Some examples intentionally resemble the semantic seeds. Passing them is not an
independent measurement of generalization. Product accuracy requires an annotated,
representative held-out resume corpus and section/word boundary precision/recall,
including explicit cross-section leakage and abstention rates. No such product
accuracy claim is made from the reference repository or this small test suite.

Executed results are recorded in [RESUME_SECTIONS_VALIDATION.md](RESUME_SECTIONS_VALIDATION.md).
