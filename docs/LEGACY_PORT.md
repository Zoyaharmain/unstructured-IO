# Unstructured PDF hi_res port

A PDF-only source port of the supplied `unstructured-main.zip`. Layout detection, PDFMiner merging, OCR, element classification, XY-cut ordering and metadata handling are retained from upstream. The full `unstructured` distribution is **not** required or installed by this project. `unstructured-inference` remains the original external model/inference dependency.

## Setup and run

Python 3.11–3.13 is required; validation used Python 3.12 on Linux. Upstream inference's Windows dependency marker supports Python 3.12 only; use Linux/WSL for the validated setup.

```bash
cd /home/zoya_harmain/unstructured-IO
# Debian/Ubuntu system dependencies:
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-eng libmagic1
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements-tested.txt .
export DO_NOT_TRACK=true
pdf-hires 'tests/fixtures/Jayesh Yadav-CV.pdf' -o elements.json
# Equivalent:
python -m pdf_hires input.pdf --model yolox --languages eng --dpi 200 -o elements.json
```

`requirements-tested.txt` is a constraints snapshot of the validated environment, including transitive dependencies, rather than a minimal requirements list. `pyproject.toml` declares compatible upstream ranges. Omit `-c requirements-tested.txt` to resolve those ranges afresh, but rerun comparisons after dependency changes.

First use needs access to the original model downloads, or a populated cache. Default YOLOX: Hugging Face `unstructuredio/yolo_x_layout`, `yolox_l0.05.onnx`. The validated model SHA-256 and package versions are in [reports/environment.json](reports/environment.json). Upstream NLP uses spaCy `en_core_web_sm==3.8.0` with its original download URL and checksum. Tesseract requires the requested language packs. `--infer-table-structure` retains upstream table inference and can require additional model downloads. No substitute model is selected by this interface when inference dependencies are missing.

```python
from pdf_hires import extract_pdf, partition_pdf

rows = extract_pdf('input.pdf', languages=['eng'], hi_res_model_name='yolox')
# Or original-style Element objects:
elements = partition_pdf('input.pdf', strategy='hi_res', languages=['eng'])
# In-memory PDFs are supported:
# rows = extract_pdf(file=open('input.pdf', 'rb'), languages=['eng'])
```

Each JSON element has upstream `text`, `type`, `element_id`, and `metadata`, plus a one-based document-wide `reading_order`. Page numbers are in `metadata.page_number`; coordinates, coordinate system and dimensions are in `metadata.coordinates`. Values are preserved without rounding. Upstream can omit coordinate metadata for non-geometric objects such as PageBreak. Additional original PDF settings can be supplied through the Python API or CLI `--settings settings.json`.

## Validation

```bash
DO_NOT_TRACK=true HF_HUB_OFFLINE=1 python -m unittest discover -s tests -v
python scripts/compare_upstream.py \
  --upstream-source .upstream/unstructured-main \
  --upstream-python /path/to/original-environment/bin/python \
  --port-python .venv/bin/python \
  --settings tests/settings.json \
  'tests/fixtures/Jayesh Yadav-CV.pdf' \
  'tests/fixtures/Jayesh Yadav-CV 1.pdf'
```

The comparison script uses separate processes, imports the original directly from the extracted archive, and asserts the full Unstructured package is absent in the port process. It compares entire ordered serialized elements with no text normalization, numeric tolerance or metadata exclusions. The additive reading_order is validated and removed before comparison. Both runs use identical absolute PDF paths and settings.

Observed exact matches: Jayesh (49 elements, both identical copies), generated two-page digital PDF (11), scanned PDF (6), and rotated upstream fixture (3). All four interface/integration tests pass. This is evidence for these four unique PDFs and settings, not a claim of universal equivalence. See [reports/comparison/summary.json](reports/comparison/summary.json), [reports/additional/summary.json](reports/additional/summary.json), and [docs/JAYESH_FINDINGS.md](docs/JAYESH_FINDINGS.md). The Jayesh detached-bullet boundary and reading-order problem is reproduced.

## Source, scope and differences

- [docs/PLAN.md](docs/PLAN.md): implementation plan and dependency/execution map.
- [docs/source-manifest.json](docs/source-manifest.json): every included upstream module, original SHA-256, and extraction edits.
- [docs/provenance.json](docs/provenance.json): archive version and checksum. The supplied Windows path contained `unstructured-main.zip`; a file named `unstructured-main(3).zip` was not available.
- `src/pdf_hires/_vendor/`: extracted source under an independent Python namespace. Internal OCR class paths therefore start with `pdf_hires._vendor`, rather than `unstructured`; use those names for explicit OCR-agent environment settings.
- Chunking decorator removed; public API rejects chunking and strategies other than hi_res. Upstream text-classification helpers are retained, while the TXT entry point and HTML partitioner/export entry point are excluded. Shared element/serialization helpers and PDF debugging/form routines remain because they support the PDF path. No new classification, section rules, clustering, corrections or BERT are added.
- Model assets and system executables are external, as upstream. Optional PaddleOCR/Google Vision, table inference, forms, encrypted PDFs, image payloads and alternate layout models were not all exercised. Their retained code is not a guarantee of equivalence for those configurations.
- Upstream notices and telemetry code are retained; `DO_NOT_TRACK=true` opts out of telemetry. Additional `UNSTRUCTURED_DISABLE_NOTICE=1` hides the original usage notice.

To reproduce the source extraction:

```bash
python -m zipfile -e /path/to/unstructured-main.zip .upstream
python scripts/extract_sources.py .upstream/unstructured-main
```

The clean network install could not be completed in this session because PyPI DNS resolution failed. Validation instead used an isolated environment populated with the machine's existing dependency files, excluding the full Unstructured distribution and its editable hooks; the project itself was installed and its wheel built successfully. GitHub DNS resolution also failed, so the local repository could not be published.

Apache-2.0: see [LICENSE.md](LICENSE.md) and [NOTICE](NOTICE). Resume fixtures are user-supplied regression documents; the project license does not grant rights to their personal content.
