# DeepSeek Schema Mapping: 309-Resume Execution & Audit Report

**Date:** 2026-10-23  
**Status:** **Execution Halted at Document 309 / 350** (Per User Instruction)  
**Architecture:** Design A (Single-shot LLM call for core `data` + `evidence`; deterministic offline review metadata assembly)  
**Safety Protocol:** Strict Zero-Repair Parsing, Dynamic 32k/18k Token Ceiling, Per-Batch Quality Gates  
**Production Integrity:** **62 / 62 Production Files Unchanged** (100% SHA-256 match)  
**Regression Test Status:** **403 / 403 Tests Passing**

---

## 1. Executive Summary

Execution of the full 350-resume DeepSeek schema mapping rollout was halted at **Document 309** per user instruction. No further API calls were made. The remaining 41 resumes (indices 310–350) remain untouched in [`manifest.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/manifest.json).

Across the 309 resumes attempted, the pipeline processed **300 schema-valid resumes (97.09%)** and quarantined **9 resumes (2.91%)** due to provider JSON syntax anomalies. The candidate citation compliance achieved **94.11%** (45,135 / 47,960 valid citations), and Gate 30 reference fact agreement reached **98.58%** (139 / 141 facts).

### Overall Rollout Ledger

| Metric | Measured Value | Denominator / Basis | Percentage |
| :--- | :--- | :--- | :--- |
| **Total Resumes in Manifest** | 350 | Full Dataset | 100.0% |
| **Resumes Attempted** | **309** | Manifest | **88.29%** |
| **Completed Extractions** | **300** | Attempted (309) | **97.09%** |
| ↳ Clean Accepted | 16 | Attempted (309) | 5.18% |
| ↳ Flagged (with Review Metadata) | 284 | Attempted (309) | 91.91% |
| **Quarantined Documents** | **9** | Attempted (309) | **2.91%** |
| **Unprocessed Resumes** | **41** | Manifest (350) | **11.71%** |
| **Candidate Citation Compliance** | **45,135 / 47,960** | Populated Fields | **94.11%** |
| **Strict Raw Citation Compliance** | **42,322 / 47,960** | Populated Fields | **88.24%** |
| **Gate Ground-Truth Value Agreement** | **139 / 141** | Reference Facts | **98.58%** |
| **Gate Evidence-Backed Agreement** | **133 / 141** | Reference Facts | **94.33%** |
| **Token Ceiling Truncations** (`finish_reason=length`) | **0 / 309** | Attempted | **0.00%** |
| **Total Prompt Tokens** | 3,470,417 tokens | Actual API Usage | — |
| **Total Completion Tokens** | 2,535,478 tokens | Actual API Usage | — |
| **Total Tokens Consumed** | **6,005,895 tokens** | Actual API Usage | — |
| **Actual API Spend** | **\$3.726 USD** | DeepSeek V3 Pricing | \$0.0121 / resume avg |

---

## 2. Batch-by-Batch Gate Results & Decisions

Batches 1 through 6 were fully completed, evaluated, and approved by the automated quality gates. Batch 7 was halted at resume 309 (29 of 70 attempted).

| Batch Name | Resumes Range | Attempted | Quarantined | Citation Compliance | Cumulative Tokens | Gate Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`batch01_gate30`** | Docs 001–030 | 30 / 30 | 1 / 30 (3.33%) | 4,147 / 4,482 (**92.53%**) | 521,737 | **PASS** |
| **`batch02_50`** | Docs 031–080 | 50 / 50 | 1 / 50 (2.00%) | 7,133 / 7,413 (**96.22%**) | 1,448,002 | **PASS** |
| **`batch03_50`** | Docs 081–130 | 50 / 50 | 4 / 50 (8.00%) | 6,737 / 7,168 (**93.99%**) | 2,425,004 | **PASS** |
| **`batch04_50`** | Docs 131–180 | 50 / 50 | 0 / 50 (0.00%) | 6,923 / 7,592 (**91.19%**) | 3,351,933 | **PASS** |
| **`batch05_50`** | Docs 181–230 | 50 / 50 | 1 / 50 (2.00%) | 7,224 / 7,533 (**95.90%**) | 4,321,633 | **PASS** |
| **`batch06_50`** | Docs 231–280 | 50 / 50 | 1 / 50 (2.00%) | 7,693 / 8,288 (**92.82%**) | 5,348,751 | **PASS** |
| **`batch07_70`** | Docs 281–309 | 29 / 70 | 1 / 29 (3.45%) | 5,278 / 5,484 (**96.24%**) | 6,005,895 | **HALTED** (at doc 309) |

*The persistent record of batch approvals is stored in [`batch-decisions.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/batch-decisions.json).*

---

## 3. Quarantined Resumes Inventory (9 Documents)

In accordance with the **Zero Heuristic Repair** policy, all 9 responses containing provider syntax defects were quarantined with full diagnostics saved to their respective directories. Zero outputs were silently patched, trimmed, or accepted partially:

| Doc # | Filename | Batch | Error Code | Failure Diagnostic | Token Usage | Diagnostic File |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **016** | `Ananya Guha Resume.pdf` | `batch01_gate30` | `invalid_json` | Extra trailing bracket `'}'` at char index 19,876 | 13,032 | [`resumes/016/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/016/parse-failure.json) |
| **046** | `ANANDKUMAR.pdf` | `batch02_50` | `invalid_json` | Extra trailing bracket `'}'` at char index 33,639 | 24,082 | [`resumes/046/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/046/parse-failure.json) |
| **102** | `Dheeraj_Kumar.pdf` | `batch03_50` | `invalid_json` | Extra trailing bracket `'}'` at char index 38,155 | 27,249 | [`resumes/102/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/102/parse-failure.json) |
| **104** | `Dinesh KR.pdf` | `batch03_50` | `invalid_json` | Extra trailing bracket `'}'` at char index 17,764 | 12,683 | [`resumes/104/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/104/parse-failure.json) |
| **110** | `Dnyaneshwar NarayanIngale.pdf` | `batch03_50` | `invalid_json` | Missing `','` delimiter at char index 12,896 | 10,753 | [`resumes/110/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/110/parse-failure.json) |
| **127** | `Girish Morab.pdf` | `batch03_50` | `invalid_json` | Extra trailing bracket `'}'` at char index 51,972 | 34,917 | [`resumes/127/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/127/parse-failure.json) |
| **214** | `Manuj Mehrotra.pdf` | `batch05_50` | `invalid_json` | Extra trailing bracket `'}'` at char index 21,399 | 15,110 | [`resumes/214/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/214/parse-failure.json) |
| **259** | `Pandi Perumal cv.pdf` | `batch06_50` | `invalid_json` | Malformed property name without quotes at char index 35,465 | 28,906 | [`resumes/259/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/259/parse-failure.json) |
| **295** | `Prem Kumar.pdf` | `batch07_70` | `invalid_json` | Malformed property name without quotes at char index 10,819 | 8,795 | [`resumes/295/parse-failure.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/resumes/295/parse-failure.json) |

*Full machine-readable failure details are cataloged in [`failed-resumes.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/failed-resumes.json).*

---

## 4. Architectural Findings & Key Learnings

1. **Dynamic Token Ceiling Eliminates Truncation**:
   In previous pilots with fixed token ceilings (8,192 tokens), large multi-page resumes hit `finish_reason=length`. The dynamic ceiling rule (32,000 for dense resumes $\ge 3$ pages, $\ge 75$ blocks, or $\ge 7,500$ chars; 18,000 for standard) achieved a **100% completion rate without a single length truncation** across all 309 documents, even for massive resumes consuming up to 53,262 tokens (`RAJASUBRAMANIAN (1).pdf`).
2. **Strict Core Data Immutability**:
   Design A separates single-shot LLM extraction (`data` + `evidence`) from deterministic offline review metadata generation. Throughout all 300 parsed resumes, `candidate['data'] == raw['data']` held 100% of the time, guaranteeing zero offline hallucination or heuristic tampering with candidate values.
3. **Provider Grammar Drift**:
   All 9 quarantined documents were caused by provider-side syntax drift (primarily appending an extraneous closing curly bracket after finishing a valid JSON object, or occasionally omitting a comma delimiter). DeepSeek's `json_object` mode ensures valid JSON starts, but does not strictly constrain grammar or token termination at the API level. Quarantining these documents without repair preserves audit trail integrity.
4. **Cost Efficiency**:
   The entire 309-resume execution consumed **6,005,895 tokens** for a total API cost of **\$3.726 USD** (\$0.0121 / resume), proving the operational viability of DeepSeek V3 for large-scale production schema mapping.

---

## 5. Artifact Ledger

All intermediate files, ledgers, and metrics are preserved immutably in [`reports/deepseek-schema-full350-20261022/`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/):
- **Call Ledger:** [`call-ledger.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/call-ledger.json) (309 recorded API calls)
- **Manifest:** [`manifest.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/manifest.json) (350 resumes partitioned into 7 batches)
- **Batch Decisions:** [`batch-decisions.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/batch-decisions.json) (Batch gate evaluation records)
- **Summary Metrics:** [`summary.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/summary.json)
- **Field Citations Ledger:** [`field-validation.csv`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/field-validation.csv) (47,960 validated field citations)
- **Quarantined Failures:** [`failed-resumes.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/failed-resumes.json) (9 detailed failure entries)
- **Gate Reference Facts:** [`reference-evaluation.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/reference-evaluation.json) (141 scored ground-truth facts)
- **Code Preservation:** [`preservation.json`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-full350-20261022/preservation.json) (SHA-256 hashes of 62 production files)

---

## 6. Code Integrity & Verification

- **Production Files Verified**: 62 of 62 production files in `local_api/` and `src/` have matching SHA-256 hashes against `production-hashes-before.json` (**0 files modified**).
- **Regression Suite**: 403 / 403 unit and integration tests passing.
- **Rollout Status**: Completed 309 of 350 (88.29%). If desired in the future, the final 41 resumes can be resumed with a single invocation of `run_full350.py --resume`.
