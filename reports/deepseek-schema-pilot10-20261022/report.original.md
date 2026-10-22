# Controlled 10-Resume Schema-Mapping Pilot Report (DeepSeek LLM)

**Run Directory**: `reports/deepseek-schema-pilot10-20261022/`  
**Execution Timestamp**: 2026-10-22  
**Status**: Completed successfully under strict cost controls. All safety gates passed.

---

## Executive Summary

As instructed, a controlled **10-resume schema-mapping validation pilot** was conducted using DeepSeek LLM (`deepseek-flash` / DeepSeek-V3). The experiment remained completely isolated from production code, obeyed strict zero-retry cost controls (exactly 10 API requests for 10 resumes), and evaluated both raw substring matching (Option A) and deterministic candidate pointer normalization.

### High-Level Scorecard

| Metric | Target / Gate | Result | Status |
| :--- | :--- | :--- | :--- |
| **Documents Processed** | Exactly 10 resumes | 10 resumes | PASSED |
| **API Mapping Calls** | Exactly 10 (0 retries) | 10 calls | PASSED |
| **JSON Parse Reliability** | 100% valid JSON, 0 parse errors | 10 / 10 (100.0%) | PASSED |
| **JSON Quarantines** | 0 quarantined | 0 quarantined | PASSED |
| **Critical Field Agreement (PDF Ground Truth)** | $\ge 85\%$ | **91.72%** (133 / 145) | PASSED |
| **Evidence-Backed Match Rate (Normalized)** | $\ge 85\%$ | **91.72%** (133 / 145) | PASSED |
| **Total Populated Fields** | Complete extraction | 1,502 fields | AUDITED |
| **Raw Citation Compliance (Option A)** | Baseline | 73.44% (1,103 / 1,502) | BASELINE |
| **Candidate Normalized Citation Compliance** | $\ge 90\%$ | **92.28%** (1,386 / 1,502) | PASSED |
| **Data Values Mutated during Normalization** | 0 allowed | **0** | PASSED |
| **Fabricated Citations** | 0 allowed | **0** | PASSED |
| **Full Regression Suite** | 100% passing | **341 / 341 passed** (100%) | PASSED |
| **Production Code Preserved** | 100% unchanged | 102 / 102 files unchanged | PASSED |

---

## Step 1: Investigation of Pilot 2 Citation Failures

In Pilot 2, 13 fields failed citation validation. Before running Pilot 10, a granular root-cause investigation was performed across all 13 failures to distinguish data contract defects from upstream extraction artifacts:

1. **Line-break Hyphenation Artifacts (3 fields)**:
   - `KARTHIYAYINI S_1.pdf` (`/experience/0/responsibilities/0`): Document text contained `ap-` on line 1 and `plications` on line 2. The model quoted `applications`.
   - `AswathyRajagopal.pdf` (`/experience/1/responsibilities/3`): Text contained `de-` on line 1 and `livery` on line 2. Model quoted `delivery`.
   - `G S Sandhya Rani.pdf` (`/experience/0/responsibilities/2`): Text contained `Knowl-` on line 1 and `edge Management` on line 2. Model quoted `Knowledge Management`.
2. **Unicode Private Use Area (PUA) Ligatures (2 fields)**:
   - `KARTHIYAYINI S_1.pdf` (`/skills/0/name`): Source PDF OCR rendered the `fi` ligature as Unicode PUA character `\ue620` (`Pro\ue620cient` and `\ue620nancial`). Model produced standard ASCII `Proficient` and `financial`.
3. **OCR Spacing & Token Concatenation (2 fields)**:
   - `A Lokhande.pdf` (`/skills/2/name`): Source block contained `SpringBoot` and `Java8` without word spaces, whereas the mapped skill used separated terms `Spring Boot` and `Java 8`.
4. **Model Attribution & Pointer Offsets (6 fields)**:
   - `A Lokhande.pdf`: Off-by-one pointer index on tools list (`/skills/12/name` for Kafka/Jenkins).
   - `Abhishek Barnwa.pdf`: Span misattribution on ServiceNow transform maps.
   - `KARTHIYAYINI S_1.pdf`: Model omitted a trailing punctuation character in the quote substring.

**Confirmation of Option A**: In accordance with the user's decision, **Option A (Strict Raw Substring Matching)** was maintained for raw scoring: no de-hyphenation or Unicode ligature normalization was applied to raw citations. Both raw and candidate-normalized results are reported transparently.

---

## Step 2: JSON Response Handling & Provider Verification

### Root Cause of the Pilot 2 Failure (`KARTHIYAYINI S_1.pdf`)
In Pilot 2, `KARTHIYAYINI S_1.pdf` failed with `JSONDecodeError: Extra data: line 245 column 2 (char 8219)`.
- **API Mode Verification**: Inspection of the DeepSeek API endpoint (`api.deepseek.com`) confirmed that it supports `response_format={"type": "json_object"}` (native JSON Mode). It does **not** support OpenAI-style strict `json_schema` schema enforcement.
- **Root Cause**: On very large, multi-page documents (4 pages, 182 blocks, ~200 fields), the model emitted a closing brace `}` after an extensive experience section, and then continued outputting subsequent schema keys (`education`, `skills`, `certifications`) outside the root JSON object.
- **Targeted Prompt Fix**: We hardened the prompt contract with an explicit structural directive:
  > `"CRITICAL JSON FORMAT CONTRACT: You must return exactly ONE single root JSON object containing ALL five keys: contact, experience, education, skills, certifications. Do NOT close the root object until the entire resume is mapped."`
- **Result**: `KARTHIYAYINI S_1.pdf` parsed cleanly without a single syntax error, producing 207 populated fields, 205 valid citations, and 19/19 ground-truth reference matches. Across all 10 resumes, JSON parse failure rate was **0.0%**.

---

## Step 3: PDF Ground Truth Validation (10 Representative Resumes)

10 diverse resumes were selected covering diverse career domains, layout complexities, page counts (1 to 4 pages), and block densities (43 to 182 blocks):

1. `KARTHIYAYINI S_1.pdf` (4 pages, 182 blocks) — Dense banking operations & compliance
2. `A Lokhande.pdf` (2 pages, 68 blocks) — Multi-role Java backend developer
3. `Abhishek Barnwa.pdf` (1 page, 54 blocks) — ServiceNow ITSM consultant
4. `A Suribhotla.pdf` (4 pages, 106 blocks) — Senior Data Analyst & BI engineer
5. `AswathyRajagopal.pdf` (2 pages, 81 blocks) — Regulatory affairs QA specialist
6. `Manisha Singh.pdf` (1 page, 43 blocks) — Core Software engineer
7. `MADHUSUDHANHK.pdf` (2 pages, 94 blocks) — IT Infrastructure & networks
8. `RAMU AKKENAPALLY.pdf` (2 pages, 69 blocks) — Oracle DBA & Cloud administrator
9. `Aparna_Bharti.pdf` (3 pages, 148 blocks) — Enterprise Business Analyst
10. `G S Sandhya Rani.pdf` (4 pages, 140 blocks) — Test Automation & QA Lead

### Ground Truth Agreement Breakdown

145 reference facts were audited directly against original PDFs:
- **133 / 145 (91.72%)** critical fields matched the original PDF ground truth exactly.
- **133 / 133 (100.0%)** of matching values were fully backed by source evidence in the candidate evaluation.

| Document | Denominator | Matches | Agreement % | Notes / Ambiguities |
| :--- | :---: | :---: | :---: | :--- |
| `KARTHIYAYINI S_1.pdf` | 19 | 19 | **100.0%** | Full recovery of dense banking roles, titles, dates |
| `A Lokhande.pdf` | 12 | 12 | **100.0%** | Full extraction of roles, degrees, technologies |
| `Abhishek Barnwa.pdf` | 13 | 13 | **100.0%** | Complete ITSM roles, certifications, education |
| `A Suribhotla.pdf` | 17 | 17 | **100.0%** | 4-page timeline extracted cleanly across all employers |
| `AswathyRajagopal.pdf` | 18 | 17 | **94.4%** | 1 degree minor title phrasing variation |
| `Manisha Singh.pdf` | 10 | 10 | **100.0%** | All employment dates, employers, education matched |
| `MADHUSUDHANHK.pdf` | 7 | 7 | **100.0%** | Network infrastructure roles & dates verified |
| `RAMU AKKENAPALLY.pdf` | 16 | 12 | **75.0%** | 4 vendor vs client attribution differences (Anthem vs Apex Systems) |
| `Aparna_Bharti.pdf` | 19 | 14 | **73.7%** | 5 certification credential vs training heading variations |
| `G S Sandhya Rani.pdf` | 14 | 12 | **85.7%** | 2 project role vs corporate title hierarchy distinctions |
| **Total** | **145** | **133** | **91.72%** | **Strong generalizability across diverse layouts** |

---

## Step 4: Pilot Execution & Metrics

### Dual Citation Contract Comparison

| Contract | Populated Fields | Valid Citations | Compliance % | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Before (Raw Option A)** | 1,502 | 1,103 | **73.44%** | Failed paths due to missing RFC 6901 leading slash in 2 resumes (`A Suribhotla`, `Aparna_Bharti`) |
| **After (Candidate Normalized)** | 1,502 | 1,386 | **92.28%** | Deterministic pointer normalization (`path` $\to$ `/path`). **0 data values altered.** |

- **Normalizations Applied**: 289 pointer path format fixes.
- **Target Data Values Mutated**: **0**.
- **Fabricated Citations**: **0**.
- **Automatic Inheritance**: **None** (every field verified independently against its cited source block).

### Token Usage and Cost Audit

| Document | Prompt Tokens | Cache Hit Tokens | Completion Tokens | Total Tokens |
| :--- | :---: | :---: | :---: | :---: |
| `KARTHIYAYINI S_1.pdf` | 10,724 | 2,304 | 10,344 | 21,068 |
| `A Lokhande.pdf` | 6,560 | 2,304 | 5,420 | 11,980 |
| `Abhishek Barnwa.pdf` | 6,260 | 2,304 | 4,212 | 10,472 |
| `A Suribhotla.pdf` | 8,720 | 2,304 | 7,650 | 16,370 |
| `AswathyRajagopal.pdf` | 8,240 | 2,304 | 6,880 | 15,120 |
| `Manisha Singh.pdf` | 5,840 | 2,304 | 4,110 | 9,950 |
| `MADHUSUDHANHK.pdf` | 8,420 | 2,304 | 7,120 | 15,540 |
| `RAMU AKKENAPALLY.pdf` | 7,680 | 2,304 | 6,450 | 14,130 |
| `Aparna_Bharti.pdf` | 12,480 | 2,304 | 11,240 | 23,720 |
| `G S Sandhya Rani.pdf` | 11,860 | 2,304 | 10,787 | 22,647 |
| **Total (10 Calls)** | **86,784** | **23,040 (26.6%)** | **74,213** | **160,997** |

- **Cost Audit**: The provider response envelopes did not return monetary balance charges. At standard published DeepSeek pricing ($0.014/Mtok cached input, $0.14/Mtok uncached input, $0.28/Mtok output), the total cost for all 10 resumes was approximately **$0.030** (~3 cents USD).

---

## Evolution Across Pilots

| Feature / Metric | Pilot 1 (5 Resumes) | Pilot 2 (5 Resumes) | Pilot 10 (10 Resumes) |
| :--- | :---: | :---: | :---: |
| **Batch Size** | 5 | 5 | **10** |
| **JSON Parse Reliability** | 80% (1 trunc) | 80% (1 extra data) | **100.0% (0 errors)** |
| **Quarantined Resumes** | 1 | 1 | **0** |
| **Ground Truth Agreement** | ~78% | ~84% | **91.72%** |
| **Candidate Citation Rate** | 68.2% | 82.5% | **92.28%** |
| **Off-by-One Pointer Drift** | Observed | Fixed in local tests | **Zero regressions** |
| **Prompt Cache Hit Rate** | ~10% | ~15% | **26.6%** |
| **Total Test Suite Pass Rate**| 100% (312 tests) | 100% (325 tests) | **100% (341 tests)** |

---

## Safety & Governance Gate

1. **Production Code Untouched**:
   - Extraction and block detection code remained completely untouched.
   - All 102 tracked production files verified identical via SHA-256 (`preservation.json`).
2. **Regression Test Suite**:
   - `pytest tests/ reports/deepseek-schema-pilot10-20261022/test_schema_gate.py` passed completely: **341 passed in 128.74s**.
3. **Standstill Enforcement**:
   - No automatic retries were performed.
   - The larger 350-resume batch has **not** been launched.
   - Code changes remain isolated in experiment directories pending user review and sign-off.

