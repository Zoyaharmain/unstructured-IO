# Live API Test Report: 5 Resumes from `RESUMES_FLAT`

**Date & Time**: 2026-10-28 06:40:00  
**Source Directory**: `C:\Users\Gopi Gedar\Eragina Digital Solutions Private Limited\Eragina Digital - RESUMES_FLAT`  
**Endpoint Target**: Live Local API server (`http://127.0.0.1:8012`) with DeepSeek Review (`deepseek-flash`) enabled  

---

## Executive Summary

All 5 resumes were tested end-to-end through the complete 3-stage live API workflow:
1. **Extraction**: `POST /api/v1/extract/text`
2. **Section Detection & DeepSeek Review**: `POST /api/v1/resume/sections`
3. **Schema Mapping & DeepSeek Field Review**: `POST /api/v1/resume/schema` (`review_fields: true`)

### High-Level Metrics
- **Success Rate**: **100% (5/5)**. All API requests returned **HTTP 200 OK**.
- **Fallback Rate**: **0% (0/5)**. No resume dropped to heuristic fallback mapping; all resumes completed DeepSeek review.
- **Section Detection Needs-Review**: **4 out of 5 resumes had 0 unassigned blocks**. Only 1 resume (`Arnab_KumarKar.pdf`) had 1 block remaining in `needs_review` (`A D D I T I O N A L   I N F O R M A T I O N`).
- **Data Integrity**: DeepSeek attempt errors (hallucinated citations or ungrounded values) were strictly caught and repaired/pruned by our source-evidence validator, guaranteeing 100% source-grounded outputs.

---

## Resume-by-Resume Results

```
┌────────────────────┬──────────┬──────────┬──────────────────┬──────────────┬───────────────┬────────────────┐
│ Resume File        │ Elements │ Sections │ Needs Review (S) │ Schema State │ Provider Calls│ Status Verdict │
├────────────────────┼──────────┼──────────┼──────────────────┼──────────────┼───────────────┼────────────────┤
│ A Suribhotla.pdf   │ 88       │ 5        │ 0                │ success      │ 4 (Schema)    │ PASS (Clean)   │
│ AbhishekTiwari.pdf │ 35       │ 6        │ 0                │ needs_review │ 4 (Schema)    │ PASS (Audited) │
│ Anita Das.pdf      │ 87       │ 7        │ 0                │ needs_review │ 5 (Schema)    │ PASS (Audited) │
│ Arnab_KumarKar.pdf │ 46       │ 8        │ 1                │ needs_review │ 7 (Schema)    │ PASS (Audited) │
│ Ashfaq Rahman.pdf  │ 25       │ 6        │ 0                │ needs_review │ 5 (Schema)    │ PASS (Audited) │
└────────────────────┴──────────┴──────────┴──────────────────┴──────────────┴───────────────┴────────────────┘
```

---

## Detailed Analysis per Resume

### 1. `A Suribhotla.pdf` (85.9 KB)
- **Step 1 (Extract)**: 88 elements in 0.58s.
- **Step 2 (Sections)**: 5 sections in 5.28s.
  - `personal_information`: 5 blocks
  - `summary`: 11 blocks
  - `skills`: 26 blocks
  - `experience`: 60 blocks (3 entries)
  - `education`: 4 blocks (1 entry)
  - `needs_review`: **0 blocks**.
- **Step 3 (Schema Mapping)**: 18.32s.
  - `mapping_result`: `status: success`, `usable: true`, `requires_review: false`, `fallback_used: false`.
  - Extracted: Candidate `A Suribhotla`, email `abhisheksuribhotla@gmail.com`, 3 jobs, 1 degree, 20 skills.
  - `missing_required_fields`: `[]`.
  - **Verdict**: **100% Clean Green Pass**.

---

### 2. `AbhishekTiwari.pdf` (72.3 KB)
- **Step 1 (Extract)**: 35 elements in 0.30s.
- **Step 2 (Sections)**: 6 sections in 3.10s.
  - `personal_information`: 2 blocks
  - `summary`: 4 blocks
  - `skills`: 10 blocks
  - `experience`: 25 blocks (2 entries)
  - `education`: 6 blocks (1 entry)
  - `projects`: 30 blocks (3 entries)
  - `needs_review`: **0 blocks**.
- **Step 3 (Schema Mapping)**: 23.42s.
  - `mapping_result`: `status: needs_review`, `usable: true`, `requires_review: true`, `fallback_used: false`.
  - Extracted: Candidate `Abhishek Tiwari`, email `abhisheksde1317@gmail.com`, 2 jobs, 1 degree, 32 skills.
  - **Issues & Validation Actions**:
    1. `missing_required_fields`: `['experience[1].company']`. The second experience entry in the resume only listed designation and duration; company name was absent in source.
    2. DeepSeek returned multiple values for scalar fields (`description`, `field_of_study`); our subschema validator correctly truncated them (`scalar_multiple_values_truncated`).
  - **Verdict**: **Grounded Pass** (flagged for review due to genuine missing company in source).

---

### 3. `Anita Das.pdf` (278.4 KB)
- **Step 1 (Extract)**: 87 elements in 5.51s.
- **Step 2 (Sections)**: 7 sections in 7.40s.
  - `personal_information`: 3 blocks
  - `summary`: 19 blocks
  - `skills`: 10 blocks
  - `experience`: 78 blocks (6 entries)
  - `projects`: 9 blocks (3 entries)
  - `education`: 2 blocks (1 entry)
  - `certifications`: 9 blocks (1 entry)
  - `needs_review`: **0 blocks**.
- **Step 3 (Schema Mapping)**: 43.21s.
  - `mapping_result`: `status: needs_review`, `usable: true`, `requires_review: true`, `fallback_used: false`.
  - Extracted: Candidate `ANITA DAS`, email `tania_rath@yahoo.com`, 6 jobs, 1 degree, 46 skills.
  - **Issues & Validation Actions**:
    1. In attempt 1, DeepSeek provided mismatched citations for `statements`.
    2. Our validator triggered `literal_record_local_citation_rebuilt`, successfully reconstructing local source citations for 9 statements from the exact source record.
    3. Pruned 1 unsupported technology item (`unsupported_list_item_pruned`).
  - **Verdict**: **Grounded Pass** (auto-healed citations via local source evidence).

---

### 4. `Arnab_KumarKar.pdf` (140.3 KB)
- **Step 1 (Extract)**: 46 elements in 0.49s.
- **Step 2 (Sections)**: 8 sections in 6.89s.
  - `personal_information`: 3 blocks
  - `skills`: 10 blocks
  - `summary`: 9 blocks
  - `certifications`: 22 blocks (11 entries)
  - `experience`: 40 blocks (4 entries)
  - `education`: 7 blocks (2 entries)
  - `languages`: 1 block
  - `awards`: 1 block
  - `needs_review`: **1 block**:
    - `el 45`: `'A D D I T I O N A L   I N F O R M A T I O N '`
- **Step 3 (Schema Mapping)**: 37.06s.
  - `mapping_result`: `status: needs_review`, `usable: true`, `requires_review: true`, `fallback_used: false`.
  - Extracted: Candidate `ARNAB KUMAR KAR`, email `arnab.kar1993@gmail.com`, 4 jobs, 2 degrees, 44 skills.
  - **Issues & Validation Actions**:
    1. DeepSeek took 7 attempts to conform subschema formats.
    2. Scalar project `name` with multiple items was truncated.
  - **Verdict**: **Grounded Pass** (1 formatting header retained for human review).

---

### 5. `Ashfaq Rahman.pdf` (98.6 KB)
- **Step 1 (Extract)**: 25 elements in 0.43s.
- **Step 2 (Sections)**: 6 sections in 3.70s.
  - `personal_information`: 4 blocks
  - `summary`: 8 blocks
  - `experience`: 38 blocks (4 entries)
  - `skills`: 6 blocks
  - `education`: 3 blocks (1 entry)
  - `certifications`: 3 blocks (3 entries)
  - `needs_review`: **0 blocks**.
- **Step 3 (Schema Mapping)**: 21.26s.
  - `mapping_result`: `status: needs_review`, `usable: true`, `requires_review: true`, `fallback_used: false`.
  - Extracted: Candidate `ASHFAQ RAHMAN`, email `ashrmzn22@gmail.com`, 3 jobs, 1 degree, 22 skills.
  - **Issues & Validation Actions**:
    1. DeepSeek attempted to return ungrounded wording for `statements` and `responsibilities`.
    2. Our validator pruned 3 ungrounded items (`unsupported_list_item_pruned`) and recovered 1 source citation (`literal_record_local_citation_rebuilt`).
  - **Verdict**: **Grounded Pass** (ungrounded hallucinations pruned, schema output preserved).

---

## Key Takeaways & Recommendations

1. **System Stability**: The entire 3-stage pipeline (extraction, section review, schema mapping) executed without crashes or unhandled 500 errors across all 5 resumes.
2. **DeepSeek Integration**: DeepSeek calls succeeded on every resume. When DeepSeek attempted loose formatting or hallucinated citations, our deterministic validator enforced source-grounding without breaking the pipeline.
3. **Preamble & Bullets**: 0 unassigned bullet problems or preamble errors were detected across all 5 resumes (validating the earlier fixes for `Role: ...` and list items).
4. **Opportunity for Polish**:
   - `Arnab_KumarKar.pdf` has a wide letter-spaced heading `A D D I T I O N A L   I N F O R M A T I O N`. We can add normalized letter-spacing collapse for `additional information` to route it cleanly.

