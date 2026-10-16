> Historical source-based integration record. Current deployment uses the published
> package; see [DEPLOYMENT.md](DEPLOYMENT.md) and [PACKAGE_DEPLOYMENT_VALIDATION.md](PACKAGE_DEPLOYMENT_VALIDATION.md).

# Text extraction integration review

Inspected the existing project before editing: Python/setuptools project,
`src/pdf_hires` legacy port with CLI entry point `pdf-hires`, and FastAPI in
`local_api/app.py` exposing `/health` and `/v1/partition`. Existing tests and PDF
fixtures are retained. No database, queue, summarizer or hosted client is added.
The new `.venv` is in the project directory. Existing `/home/gopal/venv` had no
Unstructured installation and was left alone.

The authoritative source exists at `/home/gopal/unstructured`. No extraction
source has been copied or changed. Installation uses that checkout as an editable
dependency. The source's existing Apache license/NOTICE remain applicable.

Inspected paths and reused behavior:

- `unstructured/file_utils/filetype.py`: `detect_filetype()` uses magic/content,
  ZIP/Office inspection and secondary filename hints. The service first detects
  without client MIME or extension hints, and permits textual disambiguation only
  after establishing text content. `file_utils/model.py` supplies canonical MIME
  types, partitioner names and optional dependency registry.
- `unstructured/partition/auto.py`: `partition()` dispatches detected content via
  `_PartitionerLoader`, loading format-specific modules lazily. The adapter passes
  the detector's MIME type to avoid inconsistent second detection.
- `partition/pdf.py`: PDFMiner extracts embedded PDF text in fast mode;
  `partition_pdf_or_image()` chooses strategies and delegates layout and OCR.
  `partition/strategies.py` selects fast for extractable PDFs and OCR for scans;
  image auto uses hi_res. Upstream fallback rules remain in force.
- `partition/image.py`: shares the PDF/image OCR/layout path. OCR-only uses the
  installed upstream Tesseract agent; high resolution uses inference layout models.
- `partition/docx.py`: python-docx walks paragraphs/tables and returns elements;
  page metadata depends on rendered break information. `partition/doc.py` converts
  legacy files with LibreOffice in an upstream temporary directory, then calls DOCX.
- `partition/text.py`: encoding-aware text reads and original element classification.
  `partition/md.py` and `partition/html/partition.py` handle Markdown conversion and
  HTML structure; `partition/csv.py` uses the original tabular extraction path.
- `partition/pptx.py`: walks slides/shapes in upstream order and supplies slide page
  metadata. `partition/xlsx.py` reads sheets with the upstream table/cell logic.
- `documents/elements.py`: `Element.to_dict()` serializes category, text, ID and
  `ElementMetadata`, including page numbers where present. The new response schema
  exposes type/text/page_number/metadata; it joins texts in returned order.

Selected extras from the actual source pyproject: csv, doc/docx, image/pdf, md,
pptx, xlsx. These avoid all-docs extras such as audio/Whisper, EPUB and pandoc.
Upstream image/pdf dependencies include inference/PyTorch and google-cloud-vision
although local OCR uses Tesseract. CPU-only PyTorch is appropriate for this host.
NLP uses the source's pinned spaCy English model. Tesseract and Poppler are present;
LibreOffice is absent. No OS packages were installed.

Architecture: `local_api/routes/extraction.py` owns HTTP upload lifecycle;
`services/text_extraction_service.py` owns detector/partition integration;
`schemas/extraction.py` owns public models; `utils/file_validation.py` owns safe
names and typed service errors; `core/config.py` owns environment limits.
`local_api/errors.py` is the shared existing exception classifier. The old route
retains its response and dispatch behavior; its error logs now omit exception
messages and tracebacks to avoid exposing document contents.

PDF input also receives a pypdf readability check before upstream partitioning,
because upstream fast extraction can suppress malformed-file errors as an empty
result. This check validates the file; it does not implement text extraction.
The package disables upstream telemetry by default, and the new service rejects
configured OCR agents other than local Tesseract.
