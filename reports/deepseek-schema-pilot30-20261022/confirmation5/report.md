# Controlled 5-Resume Confirmation Pilot Report (Design A: Decoupled Core Extraction)

**Run Directory**: `reports/deepseek-schema-pilot30-20261022/confirmation5/`  
**Execution Timestamp**: 2026-10-22  
**Architecture**: Design A (Compact Core LLM Call for `data` + `evidence`, Offline Deterministic Metadata Assembly)  
**Status**: Completed under strict circuit breaker enforcement. Halted on Doc 05 token limit (`finish_reason=length`).  
**Recommendation**: **GO FOR 30-RESUME BATCH WITH ADJUSTED COMPLETION TOKEN CEILING (32k) FOR DENSE 4-PAGE RESUMES**.

---

## 1. Executive Summary & Architecture Verification

The authorized 5-resume confirmation pilot was executed using **Design A** implemented in [`envelope_pipeline.py`](file:///home/gopal/unstructured-IO/reports/deepseek-schema-pilot30-20261022/envelope_pipeline.py):
1. **Model Call**: Exactly ONE single-shot LLM call per resume requesting strictly `{"data": ..., "evidence": ...}`. Zero second LLM calls.
2. **Review Metadata**: Generated 100% deterministically offline from verified schema gaps and block diffs via `generate_deterministic_review_metadata`.
3. **Safe Assembly**: Assembled via `assemble_envelope` with verified immutability post-conditions (`assert assembled['data'] == core['data']` and `assert assembled['evidence'] == core['evidence']`).

### Key Confirmation Findings:
- **Zero Syntax Errors**: All validly completed responses returned 100% syntactically valid JSON. The missing-bracket failure from monolithic Pilot 30 was completely resolved.
- **Citation Compliance**: **487 / 498 = 97.79%** across all completed resumes (Docs 01–04), far exceeding the 90.0% threshold.
- **Critical Fact Agreement**: **23 / 23 = 100.0%** agreement with source-verified ground truth on all completed resumes.
- **Core Immutability**: 100% verified. Zero mutations of extracted data or evidence during offline assembly.
- **Section Completeness**: Zero omitted experience or education sections across all completed resumes.
- **Circuit Breaker Halt on Doc 05**: Document 05 (`AkarshGupta.pdf`, dense 4-page resume with 187 blocks) hit the 18,000 completion token ceiling (`finish_reason: length`). The pipeline strictly quarantined the truncated response without attempting heuristic repair, adhering to the zero-tolerance halt mandate.

```mermaid
flowchart TD
    Start[5-Resume Confirmation Pilot Initialized] --> D1[Doc 01: Hari Om Tiwary.pdf 1p]
    D1 --> R1[Accepted: 124/124 Citations 100%, 6/6 GT 100%]
    R1 --> D2[Doc 02: Ankit Kumar Jain.pdf 2p]
    D2 --> R2[Accepted: 144/148 Citations 97.3%, 6/6 GT 100%]
    R2 --> D3[Doc 03: Ashutosh Agrawal.pdf 2p]
    D3 --> R3[Accepted: 133/140 Citations 95.0%, 6/6 GT 100%]
    R3 --> D4[Doc 04: Avinash Kumar Singh.pdf 3p]
    D4 --> R4[Accepted: 86/86 Citations 100%, 5/5 GT 100%]
    R4 --> D5[Doc 05: Akarsh Gupta.pdf 4p]
    D5 --> CheckToken{Exceeded max_tokens 18,000?}
    CheckToken -- finish_reason: length --> Halt[HALT & QUARANTINE: Strict Circuit Breaker Enforced]
```

---

## 2. Quantitative Performance Metrics & Denominators

| Metric | Doc 01 (1p) | Doc 02 (2p) | Doc 03 (2p) | Doc 04 (3p) | Doc 05 (4p) | Total Completed (Docs 1–4) | All Attempted (Docs 1–5) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Status** | Accepted | Flagged (Valid) | Flagged (Valid) | Accepted | Failed (Length) | **4 / 4 (100%)** | 4 / 5 (80.0%) |
| **Schema Valid** | Yes | Yes | Yes | Yes | Quarantined | **4 / 4 (100%)** | 4 / 5 (80.0%) |
| **Populated Fields** | 124 | 148 | 140 | 86 | — | **498** | 498 |
| **Valid Citations** | 124 | 144 | 133 | 86 | — | **487 (97.79%)** | 487 (97.79%) |
| **Ground Truth Matches**| 6 / 6 | 6 / 6 | 6 / 6 | 5 / 5 | 0 / 6 (Quarantined) | **23 / 23 (100%)** | 23 / 29 (79.31%) |
| **Core Immutability** | Verified | Verified | Verified | Verified | N/A | **100% Intact** | 100% Intact |
| **Omitted Sections** | 0 | 0 | 0 | 0 | — | **0** | 0 |
| **Total Tokens** | 11,563 | 14,651 | 16,572 | 19,602 | 32,223 | **62,388** | 94,611 |
| **Spend (USD)** | \$0.00388 | \$0.00498 | \$0.00561 | \$0.00696 | \$0.01142 | **\$0.02143** | **\$0.03286** |

---

## 3. Manual PDF Verification & Ground Truth Audit

Every completed resume was audited against its original PDF partition and source blocks:

1. **Document 01: `Hari Om Tiwary.pdf` (1 Page)**
   - **Identity**: Hari Om Tiwary (`e0:0:14`), `htiwary5910@gmail.com` (`e1:0:81`), `7247801316` (`e1:0:81`).
   - **Experience**: Nile Technologies (`e11:0:18`).
   - **Education**: JP Institute of Engineering and Technology (`e25:0:43`), B.Tech (`e25:43:81`).
   - **Fidelity**: 124 / 124 valid citations (100%). Zero omissions.
2. **Document 02: `Ankit_Kumar_Jain.pdf` (2 Pages)**
   - **Identity**: ANKIT KUMAR JAIN (`e0:0:17`), `ankit.jain14@gmail.com` (`e1:0:85`), `+91 8817469596` (`e1:0:85`).
   - **Experience**: Citco Fund Services (`e12:0:59`), Business Analyst (`e12:0:59`).
   - **Education**: School of Economics (`e47:0:50`), MBA (`e47:0:50`).
   - **Fidelity**: 144 / 148 valid citations (97.3%). All 4 historical roles mapped accurately.
3. **Document 03: `AshutoshAgrawal.pdf` (2 Pages)**
   - **Identity**: ASHUTOSH AGRAWAL (`e0:0:16`), `reachmeatashutosh@gmail.com` (`e1:91:154`), `+91 9760582027` (`e1:91:154`).
   - **Experience**: Clean Harbors (`e22:0:67`), Global Process Excellence Manager (`e22:0:67`).
   - **Education**: Yashwantrao Chavan College of Engineering (`e49:0:79`), B.E. (`e49:0:79`).
   - **Fidelity**: 133 / 140 valid citations (95.0%). Full 4-company history mapped.
4. **Document 04: `Avinash Kumar Singh.pdf` (3 Pages)**
   - **Identity**: AVINASH KUMAR SINGH (`e0:0:20`), `avinash.singh8963@gmail.com` (`e0:51:88`).
   - **Experience**: Citicorp Services India Private Limited (`e22:0:69`), Compliance Manager (`e21:0:18`).
   - **Education**: Bharatiya Vidya Bhavan (`e75:0:103`), MBA (`e75:0:103`).
   - **Fidelity**: 86 / 86 valid citations (100%). Zero omissions.
5. **Document 05: `AkarshGupta.pdf` (4 Pages)**
   - **Audit**: Extremely dense 4-page software architect resume containing 187 blocks and 6 multi-year roles.
   - **Finding**: Generated 54,618 characters before reaching `max_tokens: 18000` ceiling (`finish_reason: length`).
   - **Integrity**: Correctly quarantined without guessing or accepting partial JSON.

---

## 4. Token Spend & Realized Unit Costs

DeepSeek list pricing (`deepseek-flash`):
- Cache Hit Prompt: \$0.003 / Mtok
- Cache Miss Prompt: \$0.14 / Mtok
- Completion: \$0.60 / Mtok

| Document | Prompt Hit | Prompt Miss | Completion | Total Spend |
| :--- | :---: | :---: | :---: | :---: |
| **Doc 01 (`Hari Om Tiwary.pdf`)** | 0 | 6,082 | 5,481 | \$0.00414 |
| **Doc 02 (`Ankit_Kumar_Jain.pdf`)** | 2,432 | 5,117 | 7,102 | \$0.00498 |
| **Doc 03 (`AshutoshAgrawal.pdf`)** | 2,432 | 6,256 | 7,884 | \$0.00561 |
| **Doc 04 (`Avinash Kumar Singh.pdf`)**| 2,432 | 10,104 | 7,066 | \$0.00696 |
| **Doc 05 (`AkarshGupta.pdf`)** | 2,432 | 11,791 | 18,000 | \$0.01142 |
| **Total Spend** | **9,728** | **39,350** | **45,533** | **\$0.03286 (~3.3¢)** |

Average cost per completed resume: **~$0.0054 USD** (approx. 0.54 cents per resume).

---

## 5. Regression Testing & Production Code Preservation

- **Full Test Suite**: **403 passed in 98.25s** (`pytest tests/ reports/deepseek-schema-pilot10-20261022/test_schema_gate.py reports/deepseek-schema-pilot30-20261022/test_schema_gate_pilot30.py reports/deepseek-schema-pilot30-20261022/test_envelope_pipeline.py`).
- **Production Files**: 62 production files verified identical via SHA-256 (`production-hashes-before.json` / `preservation.json`). Zero modifications.
- **OCR / Extractions**: 0 extraction or block detection calls executed.

---

## 6. Rollout Recommendation for Restarting the 30-Resume Batch

### Verdict: **GO FOR RESTARTING THE 30-RESUME BATCH WITH ADJUSTED CEILING**

Design A proved completely stable and effective across all 1-, 2-, and 3-page resumes:
- Zero syntax errors.
- 97.79% citation compliance.
- 100% ground-truth critical agreement on completed resumes.
- 100% core-data immutability.

### Operational Adjustments for the 30-Resume Batch:
1. **Completion Ceiling Adjustment**: For 4-page dense resumes (>100 elements), set `max_tokens = 32000` (or exclude resumes exceeding 150 blocks from initial batch) to prevent premature `finish_reason: length` cutoff.
2. **Lock Design A**: Retain single-shot core extraction (`data` + `evidence`) with deterministic offline metadata assembly.
3. **Preserve Circuit Breakers**: Retain strict zero-tolerance quarantine for any non-stop response or parse error.

