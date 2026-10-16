# Deploy the text extraction API

The API now uses the published **unstructured==0.27.27** Python package.
Previously `.venv` held an editable install pointing to `/home/gopal/unstructured`.
That install was replaced with the published wheel. API imports resolve inside
`.venv/lib/python3.12/site-packages/unstructured/`; neither deployment nor tests
require the sibling source checkout. The library still runs extraction locally.

Use `local_api/requirements.txt` for the API, with
`local_api/constraints-tested.txt` for validated dependency constraints. The root
`requirements-tested.txt` is an older PDF-port snapshot. Historical reports may
refer to earlier source-based experiments; they are not deployment instructions.

## Docker (Linux amd64 CPU)

From the project root:

```bash
docker build -t unstructured-text-api:local .
docker run --rm --name unstructured-text-api \
  -p 127.0.0.1:8011:8000 -e MAX_UPLOAD_BYTES=26214400 \
  unstructured-text-api:local
```

Open http://127.0.0.1:8011/ for Resume Inspector; interactive API docs are at `/docs`.
The UI and locally served preview assets are included in the image; no frontend
build, Node runtime or external CDN is needed.

```bash
curl http://127.0.0.1:8011/health
curl http://127.0.0.1:8011/api/v1/extract/text \
  -F file=@tests/fixtures/digital-multipage.pdf -F strategy=fast
```

The image copies only the API and the model-preparation script and section model configuration. It installs the
published Python packages and system Tesseract/English, Poppler, libmagic, and
LibreOffice for DOC conversion. It runs as an unprivileged user, binds to 0.0.0.0
inside the container, exposes port 8000, and includes a liveness health check.
No local source directory, `.venv`, personal documents, credentials or `.git` are
included in the build context. No database or hosted extraction API is involved.

The build preloads the original spaCy and YOLOX models and the pinned Sentence-BERT section encoder using the installed
library. Internet access is needed at build time. Models remain in the image;
local English OCR and normal PDF extraction need no runtime asset download.
For enforced offline model loading, also pass `-e HF_HUB_OFFLINE=1` at runtime;
PDF fast/hi_res, scanned OCR, DOCX and DOC were verified with networking disabled.
Additional table/model/language features would require their own assets.
For an image without the layout-model preload, build with
`--build-arg PRELOAD_HI_RES=false`; first hi_res use then requires model access.
CPU inference dependencies make this a large image. Allow adequate image storage
and RAM, and configure resource/request limits for your deployment workload.

## Without Docker

Use Python 3.12 on Linux, install OS tools, then install Python dependencies:

```bash
sudo apt-get update
sudo apt-get install libmagic1 poppler-utils tesseract-ocr tesseract-ocr-eng \
  libreoffice-writer libgl1 libglib2.0-0
python3.12 -m venv .venv
.venv/bin/python -m pip install 'torch==2.14.1+cpu' 'torchvision==0.29.1+cpu' \
  --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r local_api/requirements.txt -c local_api/constraints-tested.txt
HF_HOME="$PWD/.venv/model-cache" .venv/bin/python scripts/warm_models.py --hi-res --sections
HF_HOME="$PWD/.venv/model-cache" NUMBA_CACHE_DIR=/tmp/unstructured-io-numba \
  MPLCONFIGDIR=/tmp/unstructured-io-matplotlib \
  .venv/bin/uvicorn local_api.app:app --host 0.0.0.0 --port 8000
```

The CPU package constraints were validated on Linux amd64 with Python 3.12.
Other architectures/platforms need compatible PyTorch wheels and revalidation.
For public traffic, put the API behind your platform's HTTPS/reverse proxy,
set a request body limit, and configure CPU/memory limits. The API's file-size
limit is checked after multipart spooling; processing has no hard time quota.
Start with one worker because each worker can load its own model copies.

To confirm that the source checkout is not used:

```bash
.venv/bin/python -c 'import unstructured.partition.auto as m; print(m.__file__)'
```

The path should end in `site-packages/unstructured/partition/auto.py`.
Do not reinstall with `pip install -e ../unstructured` in deployment.

## Tests

```bash
.venv/bin/python -m pip install -r local_api/requirements-test.txt -c local_api/constraints-tested.txt
DO_NOT_TRACK=true NUMBA_CACHE_DIR=/tmp/unstructured-io-numba \
  MPLCONFIGDIR=/tmp/unstructured-io-matplotlib OMP_NUM_THREADS=2 \
  .venv/bin/python -m pytest tests/test_text_extraction.py tests/test_local_api.py \
  -k 'not direct_extraction_parity' -q
```

The package provenance regression verifies site-packages loading, pinned version,
and absence of editable/direct-URL provenance. Current executed results are in
[PACKAGE_DEPLOYMENT_VALIDATION.md](PACKAGE_DEPLOYMENT_VALIDATION.md).

Resume section grouping loads the pinned Sentence-BERT model from local cache
only. The image preloads it even with PRELOAD_HI_RES=false. Its request schema
requires extraction verification; see [RESUME_SECTIONS.md](RESUME_SECTIONS.md).
