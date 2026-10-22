# Controlled 30-Resume Schema-Mapping Pilot: Execution & Stop Condition Verification Report (DeepSeek LLM)

**Run Directory**: `reports/deepseek-schema-pilot30-20261022/`  
**Execution Timestamp**: 2026-10-22  
**Circuit Breaker Status**: **STOP CONDITION 1 TRIGGERED (IMMEDIATE HALT ENFORCED)**  
**Rollout Recommendation**: **NO-GO FOR FULL 350-RESUME ROLLOUT** (Remediation required before expanding beyond pilot).

---

## 1. Executive Summary & Circuit Breaker Enforcement

Execution of the controlled 30-resume schema-mapping pilot commenced on 30 previously unprocessed, unique resumes using `deepseek-flash` with native JSON mode (`response_format: {"type": "json_object"}`). All preflight checks, manifests, and immutable baselines were established prior to model calls.

During execution of Document 02 (`Ashfaq Rahman.pdf`), **Stop Condition 1 (Invalid JSON or Premature Closure)** was triggered:
- **Error**: `invalid_json` (`Expecting ',' delimiter` at character offset 26,463).
- **Cause**: The model generated valid JSON through the complete schema mapping (`data`, `evidence`, and `missing_information`), but in the trailing metadata envelope omitted the closing bracket `]` of the `"uncertainties"` list before initiating `"upstream_observations"`.
- **Enforcement**: In accordance with the zero-tolerance circuit breaker contract, the batch was **halted immediately**. No automated retries, heuristic repairs, or silent truncations were performed. The response was quarantined in `02/parse-failure.json`.

```mermaid
flowchart TD
    Start[Pilot Execution Initialized] --> Doc1[Doc 01: AbhishekTiwari.pdf]
    Doc1 --> Eval1[Parse OK: 128/130 Citations (98.46%), 7/7 GT (100%)]
    Eval1 --> Doc2[Doc 02: Ashfaq Rahman.pdf]
    Doc2 --> CheckJSON{Strict json.loads Validation}
    CheckJSON -- Syntax Error: Missing ']' in uncertainties array --> Halt[HALT IMMEDIATELY: Stop Condition 1 Triggered]
    Halt --> Quarantine[Quarantine Doc 02 to parse-failure.json]
    Quarantine --> StopBatch[Batch Halted at 2 Calls: No Further Calls]
```

---

## 2. Execution Metrics & Denominators

| Metric | Raw Model Output | Final Candidate Output | Gate Status |
| :--- | :---: | :---: | :---: |
| **Resumes Planned** | 30 | 30 | Target batch |
| **Resumes Attempted** | 2 | 2 | Halted on Doc 02 |
| **API Calls Made** | 2 | 2 | Exactly 2 single-shot calls (0 retries) |
| **Successful JSON Parses** | 1 (50.0%) | 1 (50.0%) | Doc 01 parsed cleanly |
| **Quarantined Resumes** | 1 (50.0%) | 1 (50.0%) | Doc 02 quarantined (`invalid_json`) |
| **Populated Schema Fields** | 130 | 130 | Evaluated on Doc 01 |
| **Valid Citation Fields** | 128 / 130 (98.46%) | 128 / 130 (98.46%) | Exceeds 90.0% threshold |
| **Critical-Field Ground Truth Agreement (Parsed)** | 7 / 7 (100.0%) | 7 / 7 (100.0%) | Exceeds 85.0% threshold |
| **Critical-Field Agreement (All Attempted)** | 7 / 13 (53.85%) | 7 / 13 (53.85%) | Reflects Doc 02 quarantine |
| **Unexpected Section Omissions** | 0 | 0 | Zero omitted sections on Doc 01 |
| **Total Tokens Consumed** | 28,304 | 28,304 | Well within 650,000 token budget |
| **Total Realized Spend** | **$0.01007 USD** | **$0.01007 USD** | ~1.0 cent |

---

## 3. Deep Dive: Document 02 JSON Parse Failure Audit

- **Document**: `Ashfaq Rahman.pdf` (1-page Full-Stack Engineer resume, 25 elements, 4,285 source characters).
- **Token Count**: 6,686 prompt tokens (2,560 cache hits, 4,126 misses), 7,688 completion tokens. Total: 14,374 tokens.
- **Finish Reason**: `stop` (the model was not truncated by token limits).
- **Exact Defect**:
  At character offset 26,463 in `02/response-content.txt`:
  ```json
  ... {"path":"/certifications/0","kind":"certification_association","detail":"AWS certification line shares a block with the education line; parsed as a certification with name only, no issuer or year asserted.","source_ids":["e23:86:131"]},"upstream_observations":[{"path":"/skills" ...
  ```
- **Root Cause**: The model emitted a closing brace `}` for the 5th element of `"uncertainties"`, but failed to close the array with `]` before outputting the comma and the next envelope key `"upstream_observations"`.
- **Policy Compliance**:
  1. The pipeline did **not** perform an ad-hoc heuristic repair (e.g. injecting `]`).
  2. The failure was captured deterministically by `parse_response_with_quarantine`.
  3. All artifacts (`response-content.txt`, `response-envelope.json`, `parse-failure.json`) were saved in `02/` and remain strictly immutable.

---

## 4. Performance on Document 01 (`AbhishekTiwari.pdf`)

Document 01 demonstrated the technical efficacy of the prompt and schema gate when JSON syntax is compliant:
- **Populated Fields**: 130 fields across contact, summary, experience, education, skills, and projects.
- **Citation Compliance**: 128 / 130 = **98.46%**.
  - Only 2 minor citation failures: `/skills/technical_skills/15` and `/skills/all_skills/15` (offset misalignment on developer tools block `e6:0:53`).
- **Ground-Truth Critical Facts**: 7 / 7 (**100.0%** agreement):
  - `contact.full_name`: `'Abhishek Tiwari'` (Block `e0:0:15`)
  - `contact.email`: `'abhisheksde1317@gmail.com'` (Block `e1:0:93`)
  - `contact.phone`: `'9555237663'` (Block `e1:0:93`)
  - `experience[0].company`: `'Crystaltech Services Private Limited'` (Block `e12:0:37`)
  - `experience[0].role`: `'Full Stack Software Engineer'` (Block `e12:37:65`)
  - `education[0].institution`: `'University of Allahabad'` (Block `e20:0:23`)
  - `education[0].degree`: `'Bachelor of Science'` (Block `e22:0:35`, with specialization `'Mathematics'` cleanly separated into `field_of_study`).
- **Section Fidelity**: All roles, education, and skills present in source blocks were mapped without omission.

---

## 5. Token Usage & Cost Audit

List pricing for DeepSeek API (`deepseek-flash`, verified 2026-10-22):
- **Cache Hit Prompt**: \$0.003 / 1,000,000 tokens
- **Cache Miss Prompt**: \$0.14 / 1,000,000 tokens
- **Completion**: \$0.60 / 1,000,000 tokens

### Realized Spend on Pilot 30 Execution

| Call / Document | Prompt Tokens | Cache Hits | Cache Misses | Completion Tokens | Total Tokens | Spend (USD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Doc 01 (`AbhishekTiwari.pdf`)** | 6,809 | 2,560 | 4,249 | 7,121 | 13,930 | \$0.004875 |
| **Doc 02 (`Ashfaq Rahman.pdf`)** | 6,686 | 2,560 | 4,126 | 7,688 | 14,374 | \$0.005198 |
| **Total Realized Spend** | **13,495** | **5,120** | **8,375** | **14,809** | **28,304** | **\$0.010073 (~1.0¢)** |

Cumulative token spend (28,304 tokens) remained well below the 650,000 token budget circuit breaker.

---

## 6. Regression Testing & Production Preservation

- **Full Test Suite**: 388 tests passing across unit, integration, and pilot regression suites (`pytest tests/ reports/deepseek-schema-pilot10-20261022/test_schema_gate.py reports/deepseek-schema-pilot30-20261022/test_schema_gate_pilot30.py`).
- **Targeted Test Added**: `test_reproduce_pilot30_doc02_missing_array_bracket_syntax_failure` reproduces the exact unclosed array syntax failure and confirms strict quarantine without guessing.
- **Production Code Preservation**: 62 production files verified unchanged via SHA-256 baseline (`preservation.json`). Zero modifications to production source code.
- **Immutability**: All model responses, request payloads, and error records remain immutable on disk.

---

## 7. Rollout Recommendation & Strategic Roadmap

### Recommendation: **NO-GO FOR 350-RESUME BATCH**

While individual resume citation compliance reaches 98.46% and critical-field extraction accuracy is 100% on valid outputs, **full batch rollout cannot proceed under a zero-tolerance JSON failure policy** until model response syntax reliability is stabilized.

### Key Risk & Remediation Path
- **Vulnerability**: In long monolithic responses (>7,000 completion tokens) containing all 5 envelope keys (`data`, `evidence`, `missing_information`, `uncertainties`, `upstream_observations`), the model occasionally drops closing syntax brackets in trailing arrays.
- **Proposed Architectural Remedies**:
  1. **Schema Envelope Decomposition**: Split mapping into a two-stage or modular invocation: Stage 1 maps core `data` + `evidence`; Stage 2 extracts residual `uncertainties` and `upstream_observations`. This eliminates extreme completion token pressure and keeps generation within concise schema bounds.
  2. **Strict JSON Schema Mode**: Migrate from generic `{"type": "json_object"}` to provider-enforced JSON schema grammar if supported by DeepSeek's API for the targeted endpoints.
  3. **Controlled Single-Call Retries**: Evaluate whether a single retry on syntax-quarantined documents with explicit error-feedback is acceptable under production governance.

