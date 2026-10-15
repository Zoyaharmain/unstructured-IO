# Implementation plan

1. Inspect the supplied archive and trace partition_pdf(strategy="hi_res").
2. Extract the PDF import closure into an independent namespace, including dynamically loaded OCR agents and data files. Keep original processing functions; remove unrelated format entry points and chunking from the public interface.
3. Preserve original compatible dependency ranges; pin the comparison environment and record model hashes. Retain Apache-2.0 notices.
4. Provide a PDF-only Python API and CLI with explicit reading-order indices.
5. Compare archive upstream and port in separate processes, on identical absolute input paths and settings. Compare full ordered element dictionaries and individual text/type/coordinate/metadata fields. Inspect Jayesh output for block issues without corrections.

# Dependency map

- partition/pdf.py: metadata and strategy decorators → PDF complexity checks → PDFMiner text extractability → hi_res local path.
- unstructured-inference: models/base.py default yolox → models/yolox.py ONNX model + preprocessing/NMS → inference/layout.py PDF page layout and block detection. External library retained, not substituted.
- PDF: pdfminer.six, pypdf, pikepdf, pdf2image/Poppler, Pillow, pi-heif. PDFMiner configuration, rotation handling, deduplication, annotations, widgets, URI links retained.
- partition/pdf_image/pdfminer_processing.py: inferred/extracted layout merge and inner-block cleanup; inference_utils.py supplies geometry helpers.
- partition/pdf_image/ocr.py → dynamically loaded partition/utils/ocr_models/*: default Tesseract via unstructured-pytesseract/system tesseract; optional PaddleOCR and Google Vision retain upstream adapters.
- Optional table structure: unstructured-inference tables model and OCR cells (Transformers/Torch model assets); no new models introduced.
- partition/common/common.py normalize_layout_element + documents/elements.py/mappings.py: upstream class mapping; partition/text.py element_from_text + text_type.py/NLP for extracted-text classification.
- partition/utils/sorting.py + xycut.py: upstream XY-cut ordering, shrink factor and environment overrides unchanged.
- partition/common/metadata.py + lang.py + documents/coordinates.py: filename, filetype, page, pixel coordinates, hierarchy/IDs, language and last-modified metadata.
- Shared support: cleaners, NLP tokenization and word lists, table formats, serialization, logging/configuration, PDFMiner patches, telemetry decorators.

The final source manifest records exact files and extraction edits. The API rejects alternate strategies and chunking so missing dependencies cannot silently select another strategy.
