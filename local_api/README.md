> Resume sections are now available after text verification: see [section detection](../docs/RESUME_SECTIONS.md). The detector uses local Sentence-BERT and seeded K-means, keeps source spans, and separates uncertain text for review.

# Resume Inspector and local text extraction

Open `/` for the built-in Resume Inspector. Upload a PDF or DOCX, choose an
extraction strategy, and inspect the original beside the returned blocks. Counts
show extracted words, characters, blocks and pages with text metadata. Blocks
can be searched, filtered by type and selected to jump to their PDF page when
page metadata exists. Plain text can be copied and JSON can be downloaded.

The Word comparison tab accepts source text copied from the original resume.
It highlights missing reference words and extra extracted words in reading order.
Whitespace is normalized, punctuation is compared, and ignoring case is optional.
Repeated words are counted. Rearranged words may appear as missing and added.
Coverage measures agreement with your pasted reference; it does not establish
that every word in the original file is correct. Block boundaries are inspected
visually rather than assigned an invented accuracy percentage.

PDF preview uses the browser's PDF viewer; use Open ↗ if the browser cannot
embed it. DOCX preview is browser-rendered and may differ from Word's pagination
or layout. It runs in a sandboxed iframe with local JSZip/docx-preview assets;
no external viewer or CDN receives the resume. Neither uploads, references nor
results are stored by the UI (user-triggered downloads are saved locally).
The UI does not change the underlying Unstructured extraction behavior.

`POST /api/v1/compare/text` accepts JSON `reference`, `extracted`, and optional
`ignore_case` (false). Each text is limited to 100,000 characters and 5,000 words.
It returns matched/missing/extra counts, reference coverage and ordered diff
segments. Empty reference text and exceeded limits return 422.

The existing `/v1/partition` contract remains available. The modular endpoint is
`POST /api/v1/extract/text`; start both with:

```bash
cd /path/to/unstructured-IO
python3.12 -m venv .venv
# CPU-only layout dependencies avoid the default CUDA distribution on Linux:
.venv/bin/python -m pip install 'torch==2.14.1+cpu' 'torchvision==0.29.1+cpu' --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r local_api/requirements.txt -c local_api/constraints-tested.txt
NUMBA_CACHE_DIR=/tmp/unstructured-io-numba MPLCONFIGDIR=/tmp/unstructured-io-matplotlib \
  HF_HOME="$PWD/.venv/model-cache" DO_NOT_TRACK=true .venv/bin/uvicorn local_api.app:app --host 127.0.0.1 --port 8000
```

Resume Inspector: http://127.0.0.1:8000/. Interactive API: http://127.0.0.1:8000/docs. If port 8000 is occupied, use `--port 8011` and adjust request URLs. No API key or hosted extraction
service is used. `DO_NOT_TRACK=true` disables upstream telemetry. Model assets
may download on first use; pre-cache these for fully offline deployment.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/extract/text \
  -F file=@tests/fixtures/digital-multipage.pdf \
  -F strategy=fast -F include_elements=true
```

Multipart fields: `file` required, `strategy` default `auto`, `include_elements`
default `true`. Supported extensions: PDF, DOCX, DOC, TXT, MD, HTML, CSV, XLSX,
PPTX, PNG, JPG, JPEG. Content detection uses Unstructured's detector; client MIME
types do not override it. For ambiguous text, the validated filename supplies a
secondary format hint. The reported MIME type is the detected type, so a renamed
file may be processed as its actual format.

Example response shape (text and elements depend on the document):

```json
{
  "success": true,
  "filename": "sample.txt",
  "file_type": "text/plain",
  "strategy": "auto",
  "text": "Example document text",
  "elements": [{"type": "Title", "text": "Example document text", "page_number": null,
                "metadata": {"filename": "sample.txt", "filetype": "text/plain"}}],
  "metadata": {"total_elements": 1, "page_count": null, "page_numbers": []}
}
```

`strategy` records the requested strategy. Unstructured controls automatic
selection and its own fallback behavior. The service preserves element order,
text, types and metadata, removes local directory metadata, and uses a sanitized
upload filename. `include_elements=false` returns `elements: null` while retaining
combined text and counts. `page_numbers` contains only reported page numbers;
`page_count` is null because blank and trailing pages may have no elements.

| Format | Strategies | Implementation/dependencies |
| --- | --- | --- |
| PDF | auto, fast, hi_res, ocr_only | Original PDF partitioner, PDFMiner, inference/OCR extras |
| PNG/JPEG | auto, hi_res, ocr_only | Original image partitioner; fast rejected |
| DOCX/DOC | auto | python-docx; DOC additionally needs LibreOffice |
| TXT/HTML/MD | auto | Original text/HTML partitioners; Markdown extra |
| CSV/XLSX | auto | pandas; XLSX extra includes openpyxl and encryption support |
| PPTX | auto | python-pptx |

`auto` normally uses fast text extraction for text PDFs; scanned PDFs require
OCR. Image auto selects the upstream high-resolution path. `fast` uses embedded
PDF text and returns no OCR text on scanned pages. `ocr_only` uses upstream
Tesseract integration. `hi_res` loads the upstream layout model and costs more
memory/time; it can download YOLOX ONNX weights. NLP classification also needs
the upstream pinned spaCy `en_core_web_sm` 3.8.0 model. Table inference is not
requested by this endpoint. Heavy layout/OCR models are loaded only as upstream
requires them. Explicit hi_res/ocr_only requests check their core dependencies.

Linux system setup (run separately if missing):

```bash
sudo apt-get install libmagic1 poppler-utils tesseract-ocr tesseract-ocr-eng
# Only needed for legacy .doc:
sudo apt-get install libreoffice-writer
```

OCR defaults to English. Additional language support requires installing the
relevant Tesseract language packs and extending the service configuration. The
upstream image extra declares google-cloud-vision, but this API uses the default
local Tesseract agent; do not configure a remote OCR agent.

Export `MAX_UPLOAD_BYTES` to change the default 25 MiB limit (see `.env.example`).
The file limit is counted while reading, after Starlette multipart spooling;
use a reverse proxy body limit for transport-level protection. Uploads close on
success and failure, deleting spooled temporary files. The service uses in-memory
streams; legacy DOC conversion uses upstream-managed temporary directories.
No user path is opened and no URL input is accepted. Application error logs record
exception classes without exception messages or document text; upstream logging
is independently controlled by its libraries. For untrusted public workloads,
run document processing in a resource-limited worker/container: this synchronous
API has no hard CPU, expanded-archive, model-memory, or processing-time quota.

Errors: 400 missing file/name; 413 upload too large; 415 unsupported extension or
content; 422 incompatible strategy, empty/corrupt input; 503 missing dependency;
500 unexpected processing failure. Error bodies are `{"detail":"message"}`.

Direct Python use:

```python
from pathlib import Path
from local_api.services.text_extraction_service import extract_text
result = extract_text(Path('sample.pdf').read_bytes(), 'sample.pdf', strategy='fast')
print(result.text)
```

Tests use real generated Office/image documents and existing PDF fixtures:

```bash
NUMBA_CACHE_DIR=/tmp/unstructured-io-numba MPLCONFIGDIR=/tmp/unstructured-io-matplotlib \
  DO_NOT_TRACK=true OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/test_text_extraction.py -v
```

The API imports the published `unstructured==0.27.27` package from site-packages.
No sibling source checkout, editable install, Git dependency, or developer home
path is required. `pip install .[api]` also installs this pinned package, but adds
the legacy PDF port dependencies. For API-only deployment, use the requirements
above or the Dockerfile. See [deployment instructions](../docs/DEPLOYMENT.md).

Use the writable cache directories above with a read-only package installation or when
old Numba caches come from a different dependency version. Cache directories must
be writable by the runtime user.

Initial source-based integration results (historical): [../docs/TEXT_EXTRACTION_VALIDATION.md](../docs/TEXT_EXTRACTION_VALIDATION.md).

Current package-based verification is recorded in [../docs/PACKAGE_DEPLOYMENT_VALIDATION.md](../docs/PACKAGE_DEPLOYMENT_VALIDATION.md).

### Map existing blocks into the resume schema

After `/api/v1/extract/text` and `/api/v1/resume/sections`, POST the same `elements`
and complete section response to `/api/v1/resume/schema`. The response uses the
user-provided handoff's ResumeSchema, with missing fields, source evidence and
record warnings. Mapping makes no provider calls. The UI includes **Map to schema**
and a JSON download. See [integration instructions](../docs/SCHEMA_MAPPING_API.md)
for the exact request sequence and schema-definition endpoints.

### Drop a resume and review with DeepSeek

From the repository root, run:

```bash
.venv/bin/python scripts/start_resume_inspector_local.py --port 8012
```

Open http://localhost:8012. The launcher loads `DEEPSEEK_*` settings from `.env`
without printing the key; exported process settings take precedence. Set
`DEEPSEEK_API_KEY` and `DEEPSEEK_REVIEW_ENABLED=true` in `.env` to enable review.
The existing Docker launcher also loads `.env` through Docker's environment file.

Dropping or choosing a PDF/DOCX starts extraction, DeepSeek section review, and
schema mapping automatically. The three progress cards show each stage. Schema
fields include source evidence, missing fields and ambiguous mappings. A failed
DeepSeek review is shown explicitly while preserving local results. Use the
mode selector for local-only processing, or the connection button to check the
provider key/model without sending a document. Uploads in DeepSeek mode send
extracted resume text to that provider. A completed review is not proof of
correctness; compare the fields and cited text with the original document.

The individual CLI requires `--llm-review` to use DeepSeek; `--local-only`
explicitly disables it regardless of `.env`.

### DeepSeek field and subschema mapping

DeepSeek mode now performs two separate stages: section placement, followed by
record/field mapping into the imported `ResumeSchema` contract and its child
schemas. The default low-level `/api/v1/resume/schema` behavior remains local;
set `review_fields: true` to explicitly request configured DeepSeek field review.
The frontend sets this flag automatically in DeepSeek mode. The CLI's
`--llm-review` also includes field mapping before its advisory schema audit.

The field review validates exact source quotes and record ownership before
committing changes. It can repair employer/role separation and record boundaries.
Both `data` and `section_schemas` are derived from the same validated field items;
`meta.reviewed_sections` contains the matching reviewed entry ownership. A field
query can also opt into review with `review_fields: true`; use the returned
`field_index` for repeated queries without making additional provider calls.

Empty reviewed attributes distinguish `not_stated`, `ambiguous`, and `unmapped`.
A `not_stated` URL, issuer, grade, or date must not be fabricated just to fill the
schema. Unexplained omissions, invented values, foreign citations, and overlapping
record ownership are rejected atomically. Invalid candidates receive bounded
correction attempts under the configured request budget. Provider failures retain
local output and expose `meta.field_review.status = failed` to the UI.

### Schema failure diagnostics and processing outcomes

Schema responses include `meta.mapping_result.status`: `success`, `needs_review`,
`fallback_used`, or `failed`. `usable: true` means source-bound output is available
for inspection; it does not certify semantic correctness. A failed DeepSeek
response retains `meta.field_review.status: failed` and the original diagnostic,
while validated local output is shown as an amber `fallback_used` result.
Missing required fields in an otherwise valid result mean `needs_review`; they
are not automatically response-validation exceptions. Invalid source input is a
422 `failed` result without a usable fallback.

Production (the default) returns a diagnostic category and reference ID. Server
logs contain the correlated, sanitized exception type, code, field/path and
validation message. They exclude exception inputs, resume text and API keys.
For development, start with:

```bash
.venv/bin/python scripts/start_resume_inspector_local.py --port 8012 --development
```

Alternatively set `RESUME_APP_ENV=development`. The UI then displays the sanitized
reason and field/path. Do not diagnose a historical rejection from the generic
fallback message alone: earlier builds discarded the exception category.

### Logical resume blocks

Each section response includes derived `logical_blocks` alongside its original
`blocks`. Summary, contact and skills each form one complete section block.
Experience, education, projects and certifications use the existing record
owners to provide one complete block per job, qualification, project or
certificate. Other record sections follow their available entry boundaries.
Unowned meaningful text and overlapping ownership are explicitly provisional;
no employer or qualification association is invented. Unowned layout-only
markers remain in the original source inventory rather than becoming records.

Logical blocks contain `logical_id`, `kind`, `text`, `block_indices`, original
`source_ids`, and relationship-review findings. They are recomputed from the
current record inventory, including after field review. Their text concatenates
adjacent spans without inserting characters and uses newlines between separate
source elements. This is grouping, not an abstractive summary: original wording,
duplicates, offsets, source IDs and evidence checks remain intact.

The UI displays logical records first and keeps fragment inspection collapsed.
Field-mapping prompts receive complete logical context plus the original source
blocks; citations must still reference original source IDs and exact quotes.
Logical IDs are not valid evidence references. Grouping adds no provider calls.
