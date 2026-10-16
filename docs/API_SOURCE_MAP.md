> Historical source-based integration record. Current deployment uses the published
> package; see [DEPLOYMENT.md](DEPLOYMENT.md) and [PACKAGE_DEPLOYMENT_VALIDATION.md](PACKAGE_DEPLOYMENT_VALIDATION.md).

# Authoritative source and API dependency map

Inspected before API edits:
- Source checkout: /home/zoya_harmain/unstructured (Git HEAD 0b7f806e0f6ef540df22fad5627756a72663eb11).
- Target checkout: /home/zoya_harmain/unstructured-IO (origin https://github.com/Zoyaharmain/unstructured-IO.git).
- local_api/app.py and local_api/requirements.txt do not exist in the source; HTTP implementation belongs to the target.

The API imports unstructured.partition.auto.partition directly from an editable installation of the source checkout. It does not call the earlier namespaced port. No authoritative extraction source is modified.

Execution path:
1. unstructured/partition/auto.py: partition() → detect_filetype(), decide_table_extraction(), _PartitionerLoader.get() and augment_metadata(). PDF dispatch passes strategy, OCR languages, model and metadata to partition_pdf().
2. unstructured/file_utils/filetype.py and model.py: file detection and PDF partitioner/dependency registry.
3. unstructured/partition/pdf.py: partition_pdf() metadata/chunking/telemetry decorators → partition_pdf_or_image(). Original strategy selection stays in partition/strategies.py.
4. fast: extractable_elements(), _partition_pdf_with_pdfminer(), _process_pdfminer_pages(), _partition_pdf_with_pdfparser().
5. hi_res: _partition_pdf_or_image_local() → unstructured_inference.inference.layout.process_file_with_model/process_data_with_model (default YOLOX ONNX) → pdf_image/pdfminer_processing.py extraction/merge → pdf_image/ocr.py Tesseract OCR → clean_pdfminer_inner_elements() → document_to_element_list().
6. ocr_only: _partition_pdf_or_image_with_ocr() → page rendering → OCRAgent → _process_uncategorized_text_elements().
7. partition/common/common.py normalize_layout_element(), partition/text.py element_from_text(), partition/text_type.py: original element creation/classification.
8. partition/utils/sorting.py sort_page_elements() and xycut.py: original reading order.
9. partition/common/metadata.py apply_metadata(), lang.py language metadata, documents/elements.py and coordinates.py: original metadata, identifiers and geometry.

Dependencies: install source checkout with its [pdf] extra to retain declared compatible versions. This installs the core and PDF-related libraries without all-docs extras. Layout inference is unstructured-inference; ONNXRuntime runs YOLOX. PDFMiner, pypdf, pikepdf, pdf2image/Poppler and Pillow process PDFs; unstructured-pytesseract plus system Tesseract supplies OCR. Optional table inference needs original table model downloads. Source NLP loads en_core_web_sm 3.8.0 with its original checksum. The API adds FastAPI, Starlette, python-multipart, Uvicorn; tests add HTTPX and pytest. No hosted inference or new extraction models are used.

HTTP scope: one PDF upload, four strategies, original ordered serialized elements. Only PDF dependencies/features are exposed. The installed source package contains its original shared modules and other format source files; this API never dispatches to those formats.
