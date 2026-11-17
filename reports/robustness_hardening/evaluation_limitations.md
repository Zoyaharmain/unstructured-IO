# Evaluation Limitations & Future Hardening Recommendations

**Project:** `unstructured-IO`  
**Branch:** `schema-mapping-accuracy-fixes`  
**Author:** Document Understanding & Production Reliability Staff Engineering  

---

## 1. Limitations of the Current Evaluation Methodology

While achieving 100% on the 48-fixture adversarial benchmark and 100% on the 1,034-test regression suite demonstrates substantial robustness, several intrinsic limitations remain:

### A. Synthetic vs Organic Document Artifacts
- **Limitation:** The 48 adversarial fixtures were procedurally synthesized using `pypdf`, `reportlab`, and `python-docx`. While they faithfully emulate multi-column geometries, em-dashes, mixed fonts, and adversarial payloads, they lack real-world physical scanning imperfections (skew, bleeding ink, low DPI noise, fax transmission artifacts, and handwritten annotations).
- **Mitigation:** Future evaluation pipelines should incorporate scanned image PDFs processed through OCR engines (e.g. Tesseract / EasyOCR / PaddleOCR) to test parser resilience under character recognition errors.

### B. Internationalization & Multilingual Layouts
- **Limitation:** The current canonical title and section anchor dictionaries are predominantly English-focused (with some European and Indian regional corporate forms: `Pvt Ltd`, `GmbH`, `LLP`, `BV`). Resumes featuring bilingual or non-Latin scripts (e.g., CJK, Cyrillic, Arabic) or jurisdiction-specific headings (e.g. German *Berufserfahrung*, French *Parcours professionnel*) rely primarily on BERT embedding similarities rather than structural lexicons.
- **Mitigation:** Expand multilingual anchor sets and evaluate against cross-lingual CV datasets.

### C. Creative Layout Geometries
- **Limitation:** Complex non-linear infographics, circular skill wheels, and magazine-style resumes with arbitrary reading paths may still confuse column lane clustering algorithms.
- **Mitigation:** Integrate 2D spatial layout models (LayoutLMv3 or similar visual document processors) as an optional fallback when geometry lanes exhibit high planar overlap.

---

## 2. Recommendations for Continuous Reliability

1. **Property-Based Fuzzing:** Introduce Hypothesis-based property testing that mutates whitespace, date formats, delimiter punctuation, and bullet unicode codepoints on existing fixtures to detect edge-case parsing regressions.
2. **Automated Invariant Gates:** Maintain the four core invariants (`no_unsupported_field_values`, `no_silent_text_loss`, `no_cross_record_leakage`, `no_arbitrary_date_borrowing`) as hard gating checks in CI/CD before any production release.
3. **LLM Fallback Isolation:** Maintain strict untrusted-data boundaries on all LLM repair prompts, ensuring LLM suggestions cannot introduce unsourced quotes or ungrounded entities.
