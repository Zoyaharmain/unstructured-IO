# Executed resume section validation

Validated using the real local Sentence-BERT model with a MiniLM `BertModel`
encoder and scikit-learn K-means, on CPU. Model ID, immutable revision and seed
corpus are in `local_api/data/section_model.json` and `section_anchors.json`.
No hosted inference or cloned extraction checkout is used.

## Python checks

```bash
HF_HOME="$PWD/.venv/model-cache" HF_HUB_OFFLINE=1 DO_NOT_TRACK=true \
NUMBA_CACHE_DIR=/tmp/extraction-package-numba MPLCONFIGDIR=/tmp/extraction-matplotlib \
OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/test_resume_sections.py \
  tests/test_verification_ui.py tests/test_text_extraction.py tests/test_local_api.py \
  -k 'not direct_extraction_parity' -q
```

**80 passed, 8 deselected in 21.91s.** The eight historical repeated extraction
model-parity cases were excluded. `pip check` reported no broken requirements.
Raw output: `reports/resume-sections-tests.txt`.

Real-model section tests cover:

- Correct grouping on a synthetic standard resume, including contact/name,
  summary, experience, projects, education and skills.
- Alternative headings such as Career overview and Employment history.
- Interleaved left/right columns, including a narrow sidebar beside a wide main
  column, without placing the tested sidebar skills inside experience.
- Long repeated text and multiple headings inside one source element, with exact
  source reconstruction after token-offset splitting.
- Uninterpretable text and combined headings left for review.
- Footer and page-separator elements retained for review without interrupting
  the active experience context.
- Actual DOCX creation, Unstructured extraction and section detection through HTTP.

Isolated tests cover ambiguous heading context termination, request confirmation,
text-size/empty-input validation and missing model/dependency error responses.
Tests assert that every source character is preserved with exact, nonoverlapping
span offsets, independent of the semantic labels.

An additional stress check revealed combined headings such as Education and
Certifications could initially be forced to one category. BERT classification of
component phrases now identifies distinct heading families, and a regression
requires these headings to remain in Needs review.

## Browser checks

Chromium verification passed with a real generated DOCX and live local API:

- Section detection disabled without extraction and until explicit confirmation.
- Actual BERT/K-means response produced personal information, summary, experience,
  projects, education and skills in separate cards on the synthetic fixture.
- All source text preserved in the response; valid section JSON downloaded.
- Locate source block selects the corresponding raw extraction element.
- Mobile 390-pixel width had no horizontal overflow.
- File changes cleared verification and previous section results.
- No browser page errors.

Evidence: `reports/resume-sections-browser-check.json`,
`reports/resume-sections-desktop.png`, `reports/resume-sections-mobile.png`.
Screenshots use a synthetic resume and were visually inspected on desktop.
Temporary browser tooling is outside deployment requirements.

## Scope of evidence

This is functional/development validation, not a held-out resume accuracy
benchmark. Seed purity and assigned-text coverage are not section precision or
recall. Some fixture wording resembles the semantic seeds. There is no claim
that every real-world resume is correctly segmented, that no label leakage can
occur, or that extraction confirmation automatically establishes word accuracy.
The UI exposes provisional assignments, review items and source evidence.
See [RESUME_SECTIONS.md](RESUME_SECTIONS.md) for the repository integration, algorithm,
thresholds, supported categories and limitations.

## Previous offline deployment check (before structural integration)

Built `unstructured-text-api:local`, image ID prefix `4ea7b156842d`, with the pinned
BERT encoder cached during construction. A temporary container ran as UID 10001
with `--network none -e HF_HUB_OFFLINE=1` and no project/source mounts.

It served the UI and sections JS, extracted a generated DOCX through the real
Unstructured package, rejected unverified section input with 422, then returned
personal information, summary, experience, projects, education and skills with
HTTP 200 after caller verification. Reconstructing every source element from
returned spans succeeded. A combined Education and Certifications heading was
retained in Needs review with both alternatives, rather than assigned to just one.

Runtime packages: Unstructured 0.27.27, sentence-transformers 5.7.0,
scikit-learn 1.9.1. Evidence: `reports/resume-sections-container-check.json`.
The observed 100% assignment coverage and seed purity on this synthetic fixture
are not claims of resume classification accuracy.

The temporary container/test server were stopped after validation. That image predates the structural integration; see the update below. Recreate existing containers (or restart the
local Uvicorn server) to load the update.

## Feature files

- `local_api/services/resume_sections.py`: BERT embedding, K-means, conservative
  boundaries, lane handling, lazy offline model and exact source conservation.
- `local_api/schemas/sections.py`, `local_api/routes/sections.py`: verified input,
  bounded schema, structured section/review response and HTTP integration.
- `local_api/data/section_model.json`, `section_anchors.json`: pinned model and
  named semantic seed examples.
- `local_api/static/sections.js`: gated section tab, evidence, source navigation
  and section JSON export. Existing index/app/styles were extended to integrate it.
- `local_api/app.py`: mounts the new section router alongside existing endpoints.
- `local_api/requirements.txt`, `constraints-tested.txt`, `pyproject.toml`: package
  versions and inclusion of model/anchor JSON data in distributions.
- `scripts/warm_models.py`, `Dockerfile`: preload the pinned BERT assets during
  deployment preparation and include them for offline runtime.
- `tests/test_resume_sections.py`: real-model and isolated regression coverage.
- `docs/RESUME_SECTIONS.md`, this report, README/API/deployment guidance and
  `.env.example`: usage, repository interpretation, setup and explicit limitations.
- `reports/resume-sections-*`: executed tests, browser/offline evidence and
  screenshots of synthetic documents.

## Repository structural integration update

Reviewed `Gopi088/knowledge-graph-resume` at commit
`48376b8d8a0f64d1ab59b405ded3d9f38fc9ae48`. The current implementation adds
structure-led heading boundaries, exact-offset inline/merged-heading splits,
record-field protection and source-referenced entry groups. BERT/K-means remain
active for semantic classification and evidence; there is no TF-IDF fallback.

The 80-test run above includes regression coverage for letter-spaced and inline
headings, repeated words, empty spans, project Technologies/Achievement fields,
separate job/project entries, merged PDF heading prefixes and body phrases that
must not become headings. Chromium also verifies returned entry groups render.

Both sample PDFs from that repository were uploaded to the live API with `fast`
extraction, then grouped with the real offline BERT/K-means model. Each contains
125 whitespace-delimited words in the PDF text layer and in extracted text, with
zero missing/extra tokens under multiset comparison. Both returned personal
information, summary, experience, projects, education, certifications and skills.
Every extracted element reconstructed exactly from returned spans. Evidence:
`reports/repository-resume-integration-check.json` (counts only, no resume text).

This comparison is against the PDFs' text layer, not visual ground truth. It does
not establish correct extraction or grouping on other resumes. Merged source
paragraphs without visible entry boundaries remain a single entry; the parser
never fabricates multiple jobs/projects from semantic similarity alone.

The final deployment image was rebuilt as `unstructured-text-api:local`, image ID
prefix `68baeb7a21d5`, and passed the offline container check as UID 10001 with
`--network none` and `HF_HUB_OFFLINE=1`. Checks include real DOCX extraction,
BERT/K-means section grouping, exact source reconstruction, compound-heading
abstention, merged heading recovery and entry references. The updated evidence
is `reports/resume-sections-container-check.json`. The temporary test container
was removed. Existing running containers were left unchanged; recreate them
from the rebuilt image to load the update.

## Readable reference-block integration

The actual pinned repository `semantic_blocks.py` is now vendored unchanged.
`readable_resume.py` adapts its `prepare_blocks()` / `group_sections()` ownership
paths into source-linked readable trees. The UI displays normal paragraphs and
employer → role → responsibilities groups; source cards are collapsed evidence.

Additional regression fixtures cover two employers with multiple roles, wrapped
responsibility lines, slash-wrapped employer names, short dated role titles,
opening identity/headline/contact grouping, and strict context termination at
Profile Snapshot. Every displayed source span has one owner; repeated words and
rows ignored by the repository's normalized output are retained from source.

The user-supplied JSON was privately flattened into source lines using its own
section keys. The detector returned six section families with two employers and
three named roles. The headline stayed with personal information; the first
wrapped summary line stayed in summary. This checks grouping of the supplied
reference, not extraction accuracy against an original PDF, which was not
attached in this turn. No personal resume content is copied into project reports.

Chromium checks use a synthetic DOCX: two employers, three named roles, original
section labels, repeated-word retention, collapsed source evidence, source
navigation, JSON export, no browser errors, and no horizontal overflow at 390px.
Evidence: `reports/resume-readable-browser-check.json`,
`reports/resume-readable-desktop.png`, `reports/resume-readable-mobile.png`.

Final readable integration regression run: **83 passed, 8 deselected in 24.14s**.
The same eight historical repeated model-parity cases were excluded; extraction,
section ownership and HTTP/UI regressions passed. Raw output is in
`reports/resume-readable-tests.txt`. Aggregate-only checks for the supplied JSON
are in `reports/resume-reference-group-check.json`.

The final image `unstructured-text-api:local` (`8496327dec30`) passed the readable
hierarchy smoke check with `--network none`, `HF_HUB_OFFLINE=1`, UID 10001 and no
source mounts. It served the packaged UI, used real offline BERT inference and
the pinned repository grouping module, produced two employers with three named
roles and no placeholder roles, reconstructed every supplied source element,
and extracted a real generated DOCX. Evidence:
`reports/resume-readable-container-check.json`. Recreate existing containers to
load this image; the temporary smoke-test container was removed after checking.
