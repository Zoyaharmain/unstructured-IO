# 15-Resume Pilot Definitive Validation Report

**Validation Run Directory**: `ground_truth/validation_15_20261019/`  
**Date**: October 19, 2026  
**Auditor**: Antigravity Technical Audit Agent  
**Final Verdict**: **FAIL / NO-GO FOR CORPUS SCALING**

---

## 1. Executive Summary & Recommendation

Definitive validation of the 15-resume pilot establishes that the system **MUST NOT scale to the 1,500+ resume corpus at this stage**.

While the automated test suite executes cleanly (185/185 tests passing) and previous reports claimed high character accuracy, rigorous source-level audit against the authoritative original PDF pages reveals critical defects across extraction fidelity, document scoping, and record grouping:

1. **Extraction Defects Persist Upstream**:
   - `GAURAVAGRAWAL.pdf` (Page 2): The "Achievements" heading is completely missing from the extracted text, and the 247-character awards paragraph is duplicated into two identical elements.
   - `Ajay Bandagi.pdf` (Page 1): A 185-word work-experience bullet is duplicated into two identical elements (Elements 9 & 10), artificially inflating word count from 479 to 660 words.
   - `Prasad PR.pdf` (Page 1): The token-slicing logic in `local_api/services/resume_sections.py` naively cuts strings at token 200 without checking for subword continuations, bisecting `PGSQL` into `Databases: PGS` and `QL, MongoDB`.

2. **Semantic & Scoping Defects**:
   - `Java Aws backend.pdf` is an unfilled **Job Requirements Template** (e.g. `Job title: *`, `Experience range: (Min to Max years) *`). The pipeline forced this into candidate work experience and academic records, fabricating non-existent candidate history.
   - `Rutuja Herekar.pdf` (Page 3): Coursework and future study topics (`G E N E RA T I VE A I — F O U N DA T I O NA L K N O WL E D G E`, `Topics Studied`, `QA Applications I’m Building Toward`) were misclassified as past employment (`experience`) in both local and DeepSeek recovery outputs.
   - `PUPPYKUMARI.pdf` (Page 1): Multi-column tables with conflicting internal dates (`Role History` 2015–2020 vs `Career History` 2015–2021) caused catastrophic record grouping, turning headings and date strings into employers (`Emp: Role History`, `Emp: Aug 2021 to March 2024.`).

3. **Ground Truth Gap**:
   - The legacy "gold" annotations in `ground_truth/gold/` are **unverified automated drafts**. All 15 records in `verification_log.json` state `has_explicit_corrections: false`, `ground_truth/corrections/` is completely empty, and the reviewer field is an automated script placeholder. No human review was recorded.

**Recommendation**: **NO-GO**. Fix the 3 extraction/slicing defects, implement non-resume template filtering, and establish verified ground truth via the review interface before spending any additional API credits.

---

## 2. Phase 1 — Inventory & Baseline Provenance

All 15 target resumes were traced back to the Windows corpus directory:
`/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT/`

| Filename | SHA-256 Hash | Pilot Copy Match | Local Extraction Artifact | DeepSeek Checkpoint | API Calls | Tokens Consumed |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| `Pavan Bakku.pdf` | `9cd414d78c4fb79f01adea54f62150e573a07892987e008d5bc167962bc3c203` | MATCH | `b629db55549ed1bd9610.json` | `b629db55549ed1bd.json` | 1 | 15,172 |
| `Ajay Bandagi.pdf` | `6462281d67c91a043cf95f218aac2539d2479e9b78268a425d0746ebd2ae1cea` | MATCH | `f3b9f2a6333cad3718ac.json` | `f3b9f2a6333cad37.json` | 1 | 20,556 |
| `AkshayPatni (1).pdf` | `7f950f0e57892ba655f6601c90bced1679e30bd110c87444a82e937a36594cf4` | MATCH | `9a4498b27a2e14f9e3a0.json` | `9a4498b27a2e14f9.json` | 1 | 18,621 |
| `Prasad PR.pdf` | `2d77d7ff3f07aee3b3e230d7bc1be0600f6ee4f8f411ba71607a783350117d66` | MATCH | `6be5a73777f3dbd961a1.json` | `6be5a73777f3dbd9.json` | 1 | 16,587 |
| `Anuradha Yadav.pdf` | `204859ebcc79c85261b0c0ce7f4c568f696c738e411b43aa6a56ecbe3f545a90` | MATCH | `e8262488bf710cf48ccb.json` | `e8262488bf710cf4.json` | 1 | 14,464 |
| `Java Aws backend.pdf` | `432247fb426f43706e23ca6e54cf269229fae5e7837ca20da5d3e233c0919246` | MATCH | `820a109ff20c21202713.json` | `820a109ff20c2120.json` | 2 | 21,236 |
| `GAURAVAGRAWAL.pdf` | `6daeb2662c5b96d9f9ccce7903cf8a221f92576b2512f43bb22272eebfdc5ca1` | MATCH | `45575a74b9b03bde6e54.json` | `45575a74b9b03bde.json` | 1 | 16,652 |
| `Charansai P.pdf` | `10bc39f9b5bc75ea6aeb6e07875b144bc343e0d8689793132e0c1fef54eb7526` | MATCH | `035a657b54efa8e6417c.json` | `035a657b54efa8e6.json` | 1 | 31,298 |
| `Alvina _Fernandes.pdf` | `f2d65c3bb83b0f5b4a022b7a97ae2b8140db5b3e944747c32bf2cb4120ecda63` | MATCH | `1c7d6d6f5b430bc2fbec.json` | `1c7d6d6f5b430bc2.json` | 1 | 20,343 |
| `Nikhil Kumar.pdf` | `fa97a13c9e6ca3a32f641774d08a55e1db32066fa61d0f507ba918115796c702` | MATCH | `c7c6de90e08c54361783.json` | `c7c6de90e08c5436.json` | 1 | 28,098 |
| `Rutuja Herekar.pdf` | `bfddcaae34c3fb34e56847247d519b7a44fb408b0c82fb1f1a58df981ec4aa85` | MATCH | `b493159ea095e1581dbd.json` | `b493159ea095e158.json` | 1 | 28,149 |
| `S  Abhinav.pdf` | `ec99f7d2f97fa603cf338876c2457c156094bba5e9130777e58b1ec4fb0581ba` | MATCH | `6a158b8a966dcc161973.json` | `6a158b8a966dcc16.json` | 1 | 41,782 |
| `A Suribhotla.pdf` | `3780362c1613eb54fdf56f9189ef94d8cb84524458f31e3d36b763dd03dafc84` | MATCH | `455f5323879db82963ef.json` | `455f5323879db829.json` | 1 | 25,837 |
| `NagaVishnu.pdf` | `602d3ee77dd7fbe8e9dbe2c75a4087ec8d5dd5cfd4ebdd67f3957eb017a416ad` | MATCH | `07aefd82194f852b5b38.json` | `07aefd82194f852b.json` | 1 | 45,040 |
| `PUPPYKUMARI.pdf` | `43224b17f8fa5b07a9ef38676d499fe1ef85df0dbbbba3448a33fae9e2be2897` | MATCH | `08aaa025979276b8d070.json` | `08aaa025979276b8.json` | 1 | 63,956 |

- Total recorded API calls: **16**
- Total tokens consumed: **407,791**
- Checkpoints confirmation: All 15 checkpoints explicitly state `source_reextracted: false` (reused upstream pre-extraction).

---

## 3. Phase 2 & 3 — Source-Level Accuracy Audit & Known Risk Areas

### Risk Area 1: `GAURAVAGRAWAL.pdf` (Page 2)
- **Defect 1 (Missing Heading)**: The heading `Achievements` is clearly printed on page 2 in the PDF, but completely missing from the extracted elements list.
- **Defect 2 (Duplicate Extraction)**: The paragraph beginning `Awarded the Student Prize for the outstanding research award in MSc Management and Business Analytics...` occurs once in the PDF, but is extracted twice as Element 8 and Element 9 with identical coordinates (`[36.0, 680.0, ...]`).
- **Downstream Consequence**: Without the `Achievements` heading, the local classifier assigned these award bullets into `education`. DeepSeek reassigned the text to `awards`, but the duplicate text was preserved in the final output.
- **Severity**: **CRITICAL** (Extraction fidelity failure).

### Risk Area 2: `Java Aws backend.pdf` (Non-Resume Template)
- **Defect**: This document is an unfilled corporate requisition template containing prompt fields:
  - `Project /Customer Name or Strategic Requirement *`
  - `Job title: *`
  - `Experience range: (Min to Max years) *`
  - `Education and Work Experience Requirements: This section is used to describe what knowledge, skills and abilities are required...`
- **Downstream Consequence**: The system forced this template into candidate schemas, fabricating fictional records:
  - `Employer: "Experience range: (Min to Max years) *"`, `Title: "Candidate Role"`
  - `Employer: "6 - 9 years of working experience as a Software Engineer"`, `Title: "Candidate Role"`
  - `Institution: "Education and"`, `Degree: "Academic Qualification"`
- **Severity**: **CRITICAL** (Document classification / scoping failure).

### Risk Area 3: `PUPPYKUMARI.pdf` (Page 1)
- **Defect**: Page 1 contains two distinct tables with contradictory employment dates:
  - Table 1 (`Role History`): `Software Developer [June 2015- Jan 2020]`
  - Table 2 (`Career History`): `Cordova Learning Solutions: June 2015 to Aug 2021`
- **Downstream Consequence**: Logical record grouping collapsed, producing corrupt entities where table headers and date ranges were extracted as employers:
  - `Emp: Role History`, `Title: Candidate Role`
  - `Emp: Career`, `Title: Candidate Role`
  - `Emp: Aug 2021 to March 2024.`, `Title: Candidate Role`
- **Severity**: **CRITICAL** (Record relationship construction failure).

### Risk Area 4: `Rutuja Herekar.pdf` (Page 3)
- **Defect**: Page 3 contains an academic self-study section:
  - Heading: `G E N E RA T I VE A I — F O U N DA T I O NA L K N O WL E D G E`
  - Body: `Oracle OCI Generative AI Professional - Structured coursework and hands-on labs...`
  - Subheadings: `Topics Studied`, `QA Applications I’m Building Toward`
- **Downstream Consequence**: Both the local classifier and DeepSeek assigned this entire block to `experience` (past work employment).
- **Severity**: **HIGH** (Semantic classification failure).

### Risk Area 5: `Pavan Bakku.pdf` (Page 1)
- **Defect**: The section `KEY ACHIEVEMENTS` (3 performance bullets) immediately follows `PROFESSIONAL SUMMARY`.
- **Downstream Consequence**: The pipeline merged `KEY ACHIEVEMENTS` into `summary`. In earlier pilot iterations, it was labeled `awards`, causing reference drift.
- **Severity**: **MEDIUM** (Section boundary granularity).

### Risk Area 6: Subword Token 200 Slice (`Databases: PGS` / `QL, MongoDB`)
- **Document**: `Prasad PR.pdf` (Element 4, Page 1).
- **Source PDF Text**: `Databases: PGSQL, MongoDB`.
- **Root Cause Traced**: In `local_api/services/resume_sections.py` (line 132):
  ```python
  cuts = sorted(set(recovery_cuts + hint_cuts + [0] + [offsets[i][0] for i in range(200, len(offsets), 200)] + ...))
  ```
  Element 4 is a long skills block exceeding 200 subword tokens. The tokenizer splits `PGSQL` into subwords:
  `Token 198: 'PG'` (offset 784-786)  
  `Token 199: '##s'` (offset 786-787)  
  `Token 200: '##q'` (offset 787-788)  
  The slice cut at `offsets[200][0] = 787` fell between `##s` and `##q`. The code did not verify whitespace or token continuation, blindly slicing `PGSQL` into `Databases: PGS` (offset 773-787) and `QL, MongoDB` (offset 787-798).
- **Severity**: **HIGH** (Algorithmic segmentation failure).

---

## 4. Phase 4 — Automated Regression Tests

- **Command**: `PYTHONPATH=.:src .venv/bin/pytest tests/ -v`
- **Result**: `185 passed in 107.06s` (Exit Code 0).
- **Test Gap Assessment**:
  1. No test verifies that `SectionEngine.units()` avoids slicing inside words or subword tokens (`##`).
  2. No test catches upstream duplicate elements emitted by `text_extraction_service`.
  3. No test validates that non-resume job templates are rejected rather than parsed.
  4. No test checks record grouping against multi-column tables.

---

## 5. Phase 5 — Ground Truth Gap & Audit Findings

The legacy annotations in `ground_truth/gold/` cannot serve as ground truth:
1. `verification_log.json` records 15 approvals with `has_explicit_corrections: false`.
2. `ground_truth/corrections/` is completely empty.
3. Reviewer name is a static script-generated placeholder string.
4. Reported evaluation scores (e.g. 99.92%) represent **model-to-model agreement**, not ground-truth accuracy.

---

## 6. Phase 6 — Per-Resume Scorecard

| Resume File | Source Provenance | Extraction Fidelity | Block Assignment | Recovery Quality | Ground Truth Status | Overall Readiness | Key Findings & Blocker Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Pavan Bakku.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Key Achievements merged into summary; unverified gold |
| `Ajay Bandagi.pdf` | PASS | **FAIL** | PASS | **FAIL** | INCONCLUSIVE | **FAIL** | Elements 9 & 10 duplicate 185-word bullet |
| `AkshayPatni (1).pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean linear extraction; unverified gold |
| `Prasad PR.pdf` | PASS | **FAIL** | PASS | PASS | INCONCLUSIVE | **FAIL** | Token 200 subword split slices `PGSQL` |
| `Anuradha Yadav.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean 1-page extraction; unverified gold |
| `Java Aws backend.pdf`| PASS | PASS | **FAIL** | **FAIL** | INCONCLUSIVE | **FAIL** | Job requirements template; fabricated candidate records |
| `GAURAVAGRAWAL.pdf` | PASS | **FAIL** | PASS | **FAIL** | INCONCLUSIVE | **FAIL** | Missing Achievements heading; duplicate awards element |
| `Charansai P.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean extraction; bullet markers stripped; unverified gold |
| `Alvina _Fernandes.pdf`| PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean extraction; unverified gold |
| `Nikhil Kumar.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean extraction; unverified gold |
| `Rutuja Herekar.pdf` | PASS | PASS | **FAIL** | **FAIL** | INCONCLUSIVE | **FAIL** | GenAI coursework misclassified as past employment |
| `S  Abhinav.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean multi-page extraction; unverified gold |
| `A Suribhotla.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Clean extraction; isolated bullets omitted; unverified gold |
| `NagaVishnu.pdf` | PASS | PASS | PASS | PASS | INCONCLUSIVE | **INCONCLUSIVE** | Genuine cross-project bullet repetition; unverified gold |
| `PUPPYKUMARI.pdf` | PASS | PASS | **FAIL** | **FAIL** | INCONCLUSIVE | **FAIL** | Conflicting table dates; headings/dates turned to employers |

**Summary Counts**:
- Total Resumes Evaluated: **15**
- Source Provenance Passed: **15 / 15**
- Extraction Fidelity Passed: **12 / 15** (3 Failed: Ajay Bandagi, GAURAVAGRAWAL, Prasad PR)
- Block / Record Assignment Passed: **12 / 15** (3 Failed: Java Aws backend, Rutuja Herekar, PUPPYKUMARI)
- Resumes with Confirmed Defects: **6 / 15** (40.0%)
- Resumes with Independently Verified Ground Truth: **0 / 15** (15 Inconclusive)
- Overall Readiness: **6 FAIL, 9 INCONCLUSIVE, 0 PASS**

---

## 7. Cost & Scaling Readiness

- **Current Usage**: 16 API calls, 407,791 tokens across 15 resumes (average **27,186 tokens/resume**).
- **Projected Token Cost for 1,500 Resumes**:
  $$1,500 \times 27,186 \approx 40,779,000 \text{ tokens } (\sim 40.8\text{M tokens})$$
- **Scale Risk Assessment**:
  Running the full corpus now would consume ~40.8M tokens without resolving the underlying extraction duplications, subword bisections, or record hallucinations. LLM review cannot repair missing source headings or duplicated extraction elements.

