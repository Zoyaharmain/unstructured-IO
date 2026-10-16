> Historical source-based integration record. Current deployment uses the published
> package; see [DEPLOYMENT.md](DEPLOYMENT.md) and [PACKAGE_DEPLOYMENT_VALIDATION.md](PACKAGE_DEPLOYMENT_VALIDATION.md).

# Executed text extraction validation

Validated on 2026-10-15 with Python 3.12.3 in the project `.venv`.
Source: editable `/home/gopal/unstructured`, version 0.27.27.dev3.
No changes were made to extraction source. CPU-only torch/torchvision were
installed first, followed by the selected source extras and API/test requirements.
The upstream pinned spaCy English model 3.8.0 was initialized successfully.
Exact installed versions: `reports/text-extraction-requirements.txt`.
`python -m pip check`: no broken requirements found.

New suite: **30 passed in 8.08s**, with no skips. Real extraction covered PDF fast
and auto, DOCX, TXT, Markdown, HTML, CSV, XLSX, PPTX, scanned-PDF OCR and PNG OCR.
Also covered schema, optional elements, unsupported files and disguised binary
content, malformed PDF, valid blank PDF, upload limit, strategy checks, failures,
missing OCR dependency, safe metadata/filename, direct Python use, order, and
upload closure including on-disk spooling. Mocks were restricted to isolated
failure/order/dependency/lifecycle tests.

Existing route regression suite: **24 passed, 8 deselected in 12.50s**. The eight
repeated direct-extraction model-parity cases were excluded; this is not a claim
that the entire historical project suite was run.

Commands (with DO_NOT_TRACK=true, UNSTRUCTURED_DISABLE_NOTICE=1,
NUMBA_CACHE_DIR=/tmp/extraction-numba-cache,
MPLCONFIGDIR=/tmp/extraction-matplotlib, OMP_NUM_THREADS=2):

```bash
.venv/bin/python -m pytest tests/test_text_extraction.py -x -vv
.venv/bin/python -m pytest tests/test_local_api.py -k 'not direct_extraction_parity' -q
```

Raw outputs: `reports/text-extraction-tests.txt` and
`reports/text-extraction-legacy-tests.txt`.

Live Uvicorn verification on 127.0.0.1:8011 (8000 already occupied):

- GET /docs: HTTP 200.
- POST /api/v1/extract/text with real digital-multipage.pdf and strategy=fast:
  HTTP 200, 246 characters, 11 elements, reported pages [1, 2].
- Same PDF, strategy=hi_res: HTTP 200, 11 elements, nonempty text. Original layout
  model downloaded into `.venv/model-cache`; no replacement extraction model.

Actual responses are stored in `reports/text-extraction-http-response.json` and
`reports/text-extraction-hi-res-response.json`. Both use the synthetic fixture.

Environment issues encountered and resolved: sandbox TestClient requests hung,
so executed tests used local socket access; stale/unwritable editable-source Numba
caches required separate writable caches; default PyTorch resolution pulled CUDA
packages, so that install was cancelled in favor of CPU-only wheels. No CUDA
runtime was installed. The initial malformed-PDF test exposed upstream empty
success; the adapter now validates PDF readability before partitioning.

Remaining setup/limits:

- LibreOffice is absent: legacy DOC returns 503 until installed. No real DOC
  conversion was validated. Tesseract/English and Poppler are present; OCR tests ran.
- OCR defaults to English. Additional languages need language packs and service
  configuration changes. Page counts remain null because element metadata cannot
  establish complete page counts for blank/trailing pages.
- Model assets require a first download or pre-caching. The API has no remote
  document fetch or hosted extraction client. Upstream packages may declare
  hosted-client/cloud dependencies, but extraction here uses local partitioners.
- No hard processing timeout, expanded-archive limit, or worker isolation is
  implemented. Use container/resource and reverse-proxy limits for public traffic.
- The existing PDF port, its CLI and historical model-parity suite were not changed
  or fully rerun. Existing `/v1/partition` response behavior is preserved.

Setup, API contract, request/response examples and startup commands:
`local_api/README.md`. Source behavior review: `docs/TEXT_EXTRACTION_SOURCE_MAP.md`.

## Exact created or modified files

- `README.md`
- `local_api/README.md`
- `local_api/__init__.py`
- `local_api/app.py`
- `local_api/requirements.txt`
- `pyproject.toml`
- `.env.example`
- `docs/TEXT_EXTRACTION_SOURCE_MAP.md`
- `docs/TEXT_EXTRACTION_VALIDATION.md`
- `local_api/core/__init__.py`
- `local_api/core/config.py`
- `local_api/errors.py`
- `local_api/routes/__init__.py`
- `local_api/routes/extraction.py`
- `local_api/schemas/__init__.py`
- `local_api/schemas/extraction.py`
- `local_api/services/__init__.py`
- `local_api/services/text_extraction_service.py`
- `local_api/utils/__init__.py`
- `local_api/utils/file_validation.py`
- `reports/text-extraction-hi-res-response.json`
- `reports/text-extraction-http-response.json`
- `reports/text-extraction-legacy-tests.txt`
- `reports/text-extraction-requirements.txt`
- `reports/text-extraction-tests.txt`
- `tests/test_text_extraction.py`
