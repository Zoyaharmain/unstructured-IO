# Local Unstructured extraction API

The HTTP API calls `unstructured.partition.auto.partition()` directly from the authoritative local checkout at `~/unstructured`. It exposes the original extraction behavior, including existing block-detection mistakes. No section detection, clustering, correction rules, hosted API, or LLM is used.

## Install and run

Python 3.12 on Linux/WSL is the validated environment. Keep the source checkout available: its editable installation is the extraction library used by the server.

```bash
cd ~/unstructured-IO
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-eng libmagic1
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e "$HOME/unstructured[pdf]" -e '.[api,api-test]'
export DO_NOT_TRACK=true
uvicorn local_api.app:app --host 127.0.0.1 --port 8000
```

The API dependencies are also listed in `local_api/requirements.txt`; tests add `local_api/requirements-test.txt`. Installing the authoritative `[pdf]` extra supplies the original PDF dependency ranges. Other document formats route through their original partitioners; install the corresponding extras in the source checkout when needed. Missing dependencies that upstream reports as failures produce HTTP 503. Upstream strategy fallback behavior remains unchanged.

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

The tests compare API outputs with direct calls to `unstructured.partition.auto.partition()` using the same upload bytes, filename and settings. Complete equality of ordered serialized elements tests text, boundaries, types, IDs, reading order, coordinates and all metadata. No fields are excluded or rounded. Explicit `hi_res` comparisons include Jayesh's resume; the other three strategies and a non-PDF document are also exercised. Results and remaining limitations are in `docs/API_VALIDATION.md`.

## Repository layout and provenance

- `local_api/app.py`: HTTP handling, upload limit, error mapping, response envelope. Extraction remains in the source library.
- `tests/test_local_api.py`: HTTP contract/error tests and direct extraction parity tests.
- `docs/API_SOURCE_MAP.md`: inspected paths, functions and dependency trace.
- `reports/api-parity/`: direct extraction outputs and API responses from parity tests.
- `src/pdf_hires/`: earlier separate PDF-only port retained from the preceding task. The HTTP API does **not** import it. Its historical documentation is in `docs/LEGACY_PORT.md` and earlier comparison reports; those results are distinct from API parity.

The source checkout's `local_api/` directory was absent; the API layer was implemented in this target repository under the user-provided contract. The extraction library itself was not modified. Source code, model assets and dependencies retain their upstream licenses. See `LICENSE.md` and `NOTICE`. User-supplied resume fixtures are included for regression tests; the project license grants no additional rights to their personal content.
