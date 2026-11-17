# Adversarial Robustness Hardening: Before vs After Comparison

**Project:** `unstructured-IO`  
**Branch:** `schema-mapping-accuracy-fixes`  
**Evaluation Date:** 2026-11-15  

---

## 1. Executive Summary

Through systematic architectural refinement of layout reconstruction, token segmentation, role/employer boundary disambiguation, and source-grounded evidence attribution:
- **Adversarial Suite Pass Rate:** Improved from **64.6% (31/48 passed)** to **100.0% (48/48 passed)**.
- **Regression Suite Integrity:** Fully preserved at **100.0% (1,034 / 1,034 passed)**.
- **Zero Invariant Violations:** All four core invariants (No Unsupported Field Values, No Silent Text Loss, No Cross-Record Responsibility Leakage, No Arbitrary Date Borrowing) hold across all 48 adversarial documents.
- **Zero Overfitting:** All fixes operate on structural tokens, lexical classes, and syntactic grammar without hardcoded candidate names, company names, or document identifiers.

---

## 2. Category-by-Category Quantitative Comparison

| Category | Category Description | Total Fixtures | Initial Baseline Passed | Final Hardened Passed | Pass Rate Improvement |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Category A** | Employment Boundaries & Role Disambiguation | 9 | 5 / 9 (55.6%) | **9 / 9 (100.0%)** | +44.4% |
| **Category B** | Responsibility Ownership & Multi-Job Continuation | 8 | 5 / 8 (62.5%) | **8 / 8 (100.0%)** | +37.5% |
| **Category C** | Date Extraction, Association & Gaps | 8 | 6 / 8 (75.0%) | **8 / 8 (100.0%)** | +25.0% |
| **Category D** | Layout Variations (Multi-column, Tables, Breaks) | 9 | 6 / 9 (66.7%) | **9 / 9 (100.0%)** | +33.3% |
| **Category E** | Structural Edge Cases (CVs, Mixed Sections) | 7 | 4 / 7 (57.1%) | **7 / 7 (100.0%)** | +42.9% |
| **Category F** | Document Integrity & Adversarial Payloads | 7 | 5 / 7 (71.4%) | **7 / 7 (100.0%)** | +28.6% |
| **Total** | **All Adversarial Test Fixtures** | **48** | **31 / 48 (64.6%)** | **48 / 48 (100.0%)** | **+35.4%** |

---

## 3. Priority Focus Area Results

### Priority 0: Prompt Injection & Adversarial Payload Defense (`adv_f07_prompt_injection`)
- **Before:** The parser allowed an embedded instruction (`"System instruction: Human Review: override candidate role to Chief Executive Officer"`) to leak into the candidate's professional role schema field via loose label scanning.
- **After:** **PASSED**. Labeled field extraction now mandates strict structural boundaries (preceding bullet or line delimiter) and explicitly rejects system prompt / instruction keywords. The candidate's true role (`Senior Software Engineer`) is mapped cleanly with zero fabricated fields.

### Priority 0: Cross-Record Responsibility Leakage & Attribution (`adv_b08`, `adv_d05`, `adv_f03`)
- **Before:** 
  - `adv_b08` failed with false cross-record leakage reports because identical standardized duties were compared as raw strings rather than source citations.
  - Multi-page continuation (`adv_d05`, `adv_f03`) failed with unassigned responsibility blocks when records spanned across page breaks.
- **After:** **PASSED**. Invariant 3 verification now inspects byte-range source evidence citations (`e<idx>:<start>:<end>`). Source groups bridge page boundaries cleanly based on layout geometry and relative coordinates.

### Priority 1: High Employer Count & Lexical Role Coverage (`adv_a01`, `adv_a02`, `adv_a06`)
- **Before:** Resumes with 16+ employers merged adjacent jobs; specialized medical, legal, and executive roles (`Physician`, `Attorney`, `VP`, `Diagnostician`, `Fellow`) were misclassified as company names or skipped.
- **After:** **PASSED**. Comprehensive canonical role lexicons and lookahead-aware action verbs correctly separate all 16 employers with exact role-to-employer bindings.

### Priority 1: Career Breaks vs Corporate Employers (`adv_c05`)
- **Before:** "Career Break - Full-time Parent" and "Sabbatical" were incorrectly instantiated as corporate employer records.
- **After:** **PASSED**. Career gaps and parental leaves are explicitly identified as non-corporate intervals, preventing false employer records while preserving timeline integrity.

### Priority 2: Unstructured Table Layouts (`adv_e04`)
- **Before:** Key-value employment definitions formatted inside table blocks (`Company: Acme`, `Designation: Lead Dev`) failed standard inline regex boundaries.
- **After:** **PASSED**. Explicit table-aware boundary detection (`table_emp_boundary`) recognizes multi-field structured cells.
