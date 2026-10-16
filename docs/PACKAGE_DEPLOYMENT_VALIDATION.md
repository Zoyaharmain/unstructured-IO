# Package deployment validation

The previous editable installation of Unstructured 0.27.27.dev3 was replaced by
the published **unstructured==0.27.27** wheel. The API code imports the same public
partition functions, now installed in site-packages. No extraction algorithms
were copied or replaced. No sibling checkout is required.

Verified package provenance:

- Partition module: `.venv/lib/python3.12/site-packages/unstructured/partition/auto.py`.
- Installed version: 0.27.27.
- `direct_url.json`: absent (no editable/local/Git dependency).
- `pip check`: no broken requirements found.

Machine-readable evidence: `reports/package-provenance.json`.
Installed dependency snapshot: `reports/package-deployment-requirements.txt`.
The deployment constraints are in `local_api/constraints-tested.txt`.

Executed against the published wheel:

```bash
DO_NOT_TRACK=true UNSTRUCTURED_DISABLE_NOTICE=1 \
NUMBA_CACHE_DIR=/tmp/extraction-package-numba MPLCONFIGDIR=/tmp/extraction-matplotlib \
OMP_NUM_THREADS=2 .venv/bin/python -m pytest \
  tests/test_text_extraction.py tests/test_local_api.py \
  -k 'not direct_extraction_parity' -q
```

**54 passed, 8 deselected in 12.50s.** This includes real Office, PDF and OCR
extraction, errors, cleanup, schemas, and legacy route checks. The provenance
regression no longer expects a hardcoded developer source directory; it checks
the installed package location and version. Eight repeated historical model
parity cases were excluded. Raw output: `reports/package-deployment-tests.txt`.

Deployment additions:

- `Dockerfile`: Python 3.12, published package dependencies, CPU PyTorch,
  Tesseract/English, Poppler, libmagic, LibreOffice, model preparation, unprivileged
  runtime, health check, and Uvicorn binding to 0.0.0.0:8000.
- `.dockerignore`: allowlist includes only API source and model setup script.
- `scripts/warm_models.py`: calls the installed library's own model loaders to
  prepare spaCy and optionally YOLOX during image construction.
- `docs/DEPLOYMENT.md`: container and non-container deployment commands.
- `local_api/requirements.txt` and pyproject API extras pin the published library;
  `local_api/constraints-tested.txt` records validated package versions.
- `requirements-tested.txt` now explains that its older PDF-port snapshot is not
  the API deployment input. Current API documentation no longer instructs users
  to install a sibling source tree.

Restart existing Uvicorn processes after changing packages. A running process
can retain already imported modules from the previous installation.

## Built container and offline verification

`docker build -t unstructured-text-api:local .` completed successfully.
Validated image ID prefix: `9b52b3b65ee9`.

Started with `--network none -e HF_HUB_OFFLINE=1`, without source or project mounts.
Only synthetic digital/scanned test fixtures were copied into the running
container for requests. The runtime user was UID 10001. The module loaded from
`/usr/local/lib/python3.12/site-packages/unstructured/partition/auto.py`; the
previous developer source directory did not exist inside the container.

Successful HTTP checks:

| Check | Result |
| --- | --- |
| / followed to /docs | 200 |
| /docs | 200 |
| /health | 200 |
| Digital PDF, fast | 200; 246 characters; 11 elements |
| Digital PDF, hi_res | 200; 246 characters; 11 elements |
| Scanned PDF, ocr_only | 200; 158 characters; 6 elements |
| Generated DOCX, auto | 200; expected sentence extracted |
| Generated legacy DOC, auto | 200; expected sentence extracted |

LibreOffice conversion was exercised in the container, where its system
installation is included. This does not install LibreOffice on the host.
Machine-readable evidence: `reports/package-container-verification.json`.
The temporary verification container was stopped after testing; the built image
remains available locally as `unstructured-text-api:local`.
