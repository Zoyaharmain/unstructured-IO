# Resume Inspector and local extraction API

Open `/` for the local Resume Inspector: PDF/DOCX preview, ordered blocks, plain text,
counts, JSON download, and word comparison against pasted source text. `/docs`
continues to provide interactive API documentation. The **Resume sections** tab
adds structure-led boundaries and local Sentence-BERT/K-means grouping automatically after extraction; see
[section detection and limitations](docs/RESUME_SECTIONS.md).

The modular text endpoint **POST /api/v1/extract/text** is documented in
[local_api/README.md](local_api/README.md), including supported formats, strategy
validation, direct Python usage, configuration, and setup. The existing
`/v1/partition` contract below remains available.

The HTTP API calls `unstructured.partition.auto.partition()` from the pinned published `unstructured==0.27.27` package installed in site-packages. No local Unstructured checkout is required. [Deployment instructions](docs/DEPLOYMENT.md) include a Docker image with system dependencies and cached models. The raw text endpoint preserves upstream extraction behavior. Optional resume section grouping combines explicit heading/layout boundaries with local Sentence-BERT and seeded K-means automatically after extraction. The default view combines all relevant text into one block per canonical section (for example Work History becomes Experience). PDF typography supports merged-heading and page-layout recovery; employer/role detail and exact source references remain expandable. Extraction stays local. An optional [DeepSeek review layer](docs/LLM_SECTION_REVIEW.md) validates all assigned and unassigned text together and applies source-linked placement corrections; it is disabled until configured.

## Install and run

Python 3.12 on Linux/WSL is the validated environment. Install the published package using the API requirements below.

```bash
cd ~/unstructured-IO
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-eng libmagic1
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install 'torch==2.14.1+cpu' 'torchvision==0.29.1+cpu' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r local_api/requirements.txt -c local_api/constraints-tested.txt
export DO_NOT_TRACK=true
uvicorn local_api.app:app --host 127.0.0.1 --port 8000
```

The API requirements pin the published extraction package and selected format extras.
`local_api/constraints-tested.txt` records validated dependency versions; the root
`requirements-tested.txt` is a historical PDF-port snapshot, not API setup.
Missing optional dependencies return HTTP 503. Upstream strategy fallback behavior
remains unchanged. No Unstructured API key is required.

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/partition \
  -F 'file=@tests/fixtures/Jayesh Yadav-CV.pdf' \
  -F strategy=hi_res -F languages=eng -F hi_res_model_name=yolox
```

## Contract

`GET /health` returns `{"status":"ok"}`. It is a liveness endpoint, not a model-download readiness check.

`POST /v1/partition` accepts multipart `file` plus `strategy` (`auto`, `fast`, `hi_res`, `ocr_only`; default `auto`). Optional form fields: repeated `languages` (default `eng`), `hi_res_model_name`, `infer_table_structure`, `include_page_breaks`, `starting_page_number`, `pdf_image_dpi`, `metadata_last_modified`, and `password`.

The maximum uploaded file size is exactly 25 MiB (26,214,400 bytes), inclusive. The server counts file bytes rather than trusting Content-Length. Multipart parsing spools the upload before the endpoint checks this file limit; configure a reverse proxy/request limit separately if an early transport-level cap is needed.

Responses contain exactly:

```json
{
  "filename": "resume.pdf",
  "requested_strategy": "hi_res",
  "element_count": 0,
  "page_numbers": [],
  "text": "",
  "elements": []
}
```

`elements` contains every original `Element.to_dict()` in extraction order, including empty elements, text, IDs, coordinates and metadata. No fields are normalized or removed. Order in the array is the original reading order. `text` joins original element text with two newlines; `page_numbers` is the unique sorted set of page numbers actually present. An empty extraction is successful. `requested_strategy` records the request; the original library may select a different strategy under its own fallback rules.

Errors use structured JSON `{"detail":"clear message"}` without stack traces or exception contents:

| Status | Condition |
| --- | --- |
| 400 | Missing file or empty filename |
| 413 | File exceeds 25 MiB |
| 422 | Invalid parameters/strategy, empty/unsupported/invalid input, unprocessable malformed or encrypted PDF |
| 503 | Required optional dependency unavailable |
| 500 | Unexpected internal processing failure |

Tracebacks are logged server-side for diagnosis. Non-PDF documents are passed to the original auto detector and document-specific partitioner, rather than rejected at the HTTP layer.

## Models and dependencies

Default `hi_res` layout model: original YOLOX ONNX through `unstructured-inference`. First use downloads `unstructuredio/yolo_x_layout/yolox_l0.05.onnx` into the Hugging Face cache. OCR uses system Tesseract and `unstructured-pytesseract`; install each requested language pack. Original NLP uses spaCy `en_core_web_sm==3.8.0` with the source library's own download/checksum handling. Optional table structure inference requires its original additional model assets. No model replacements are provided. Offline operation requires cached assets.

`reports/environment.json` and `requirements-tested.txt` describe the earlier source-port test environment; the API-specific environment and results are recorded separately in `reports/api-environment.json` and API test reports.

## Tests and parity

```bash
DO_NOT_TRACK=true HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 \
  python -m pytest tests/test_local_api.py -v
```

The tests compare API outputs with direct calls to the installed `unstructured.partition.auto.partition()` using the same upload bytes, filename and settings. Complete equality of ordered serialized elements tests text, boundaries, types, IDs, reading order, coordinates and all metadata. No fields are excluded or rounded. Explicit `hi_res` comparisons include Jayesh's resume; the other three strategies and a non-PDF document are also exercised. Results and remaining limitations are in `docs/API_VALIDATION.md`.

## Repository layout and provenance

- `local_api/app.py`: HTTP handling, upload limit, error mapping, response envelope. Extraction remains in the source library.
- `tests/test_local_api.py`: HTTP contract/error tests and direct extraction parity tests.
- `docs/API_SOURCE_MAP.md`: inspected paths, functions and dependency trace.
- `reports/api-parity/`: direct extraction outputs and API responses from parity tests.
- `src/pdf_hires/`: earlier separate PDF-only port retained from the preceding task. The HTTP API does **not** import it. Its historical documentation is in `docs/LEGACY_PORT.md` and earlier comparison reports; those results are distinct from API parity.

The API layer is maintained in this repository; extraction is supplied by the published package. The historical source review remains documented, but deployment does not depend on that source checkout. Source code, model assets and dependencies retain their upstream licenses. See `LICENSE.md` and `NOTICE`. User-supplied resume fixtures are included for regression tests; the project license grants no additional rights to their personal content.
