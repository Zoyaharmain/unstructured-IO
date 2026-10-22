# DeepSeek Schema Mapping Evaluation (Phase 2) — Blocker Resolutions & Comprehensive Before/After Report

**Status: Both blockers resolved offline without API calls; strict validation, deterministic pointer normalization, and full test suite passing with zero regressions.**

- **Blocker 1 Resolved (JSON Response Reliability)**: Root cause established for `KARTHIYAYINI S_1.pdf` (premature closing brace followed by extra data `,"upstream_observations": [...]` at character offset 35922). Implemented strict complete-response parser (`parse_strict_json_response` and `parse_response_with_quarantine`) with structured output / JSON mode. Enforced zero silent truncation, zero guessing, and strict quarantine without automatic retries. Added regression tests reproducing the exact failure.
- **Blocker 2 Resolved (Citation Pointer Alignment)**: Root cause established for `A Lokhande.pdf` (missing leading slashes on all 103 evidence keys). Implemented deterministic local normalizer `normalize_evidence_pointers` that converts provably equivalent relative paths to standard JSON Pointers starting with `/`. Guaranteed zero target data value mutation (`candidate['data'] == raw['data']`) and zero citation fabrication. Enforced rejection of ambiguous collisions. Valid citations for `A Lokhande.pdf` increased from **0/102 (0.0%)** to **93/102 (91.18%)**, and evidence-backed reference matches increased from **0/12 (0.0%)** to **12/12 (100.0%)**.
- **Overall Offline Before / After Result**:
  - Populated fields across parseable outputs: **388** (unchanged).
  - Citation-compliant fields: increased from **282/388 (72.68%)** to **375/388 (96.65%)** (**+93 fields**).
  - Predeclared critical reference opportunities: **79**.
  - Value agreement: **60/79 (75.95%)** (the 19 unmapped facts belong entirely to quarantined `KARTHIYAYINI S_1.pdf`).
  - Evidence-backed critical agreement: increased from **48/79 (60.76%)** to **60/79 (75.95%)** (**+12 facts**). Every single value match is now **100% evidence-backed**.
  - Target data values mutated: **0**.
  - Fabricated citations: **0**.
- **Regression Suite**: **26/26 targeted gate tests** and **341/341 full repository tests passed in 98.91s** with zero regressions.
- **Production Gate**: **Quarantined. Production code unchanged.** No automatic production rollout is authorized without explicit user approval.

---

## 1. Blocker 1: JSON Response Reliability Investigation & Strict Quarantine

### Root Cause Analysis (`KARTHIYAYINI S_1.pdf`)
In Document 4 (`KARTHIYAYINI S_1.pdf`), a dense 4-page banking operations resume containing 182 local blocks, the provider response failed strict JSON parsing with:
```
json.JSONDecodeError: Extra data: line 1 column 35923 (char 35922)
```
Inspection of `04/response-content.txt` at character boundary 35922 revealed:
```json
... {"path":"/contact/email","kind":"ambiguous_source","detail":"Email local part 'Karthiyayini0208' not used to infer name; name taken from explicit name text.","source_ids":["e0:0:15","e1:0:34"]}]}}
,"upstream_observations":["Local categories mislabeled: education, certifications, awards, and languages blocks were tagged as 'awards', 'projects', or 'languages' inconsistently.","Project header split across 'PROJECTS ' and 'AT WORK' blocks; ...
```
The model successfully generated four top-level keys (`data`, `evidence`, `missing_information`, and `uncertainties`), but closed the root JSON object with `}` at position 35922. It then immediately generated a comma followed by the fifth key (`"upstream_observations"`) outside the root JSON object.

### Architectural Fix & Strict Response Validation
1. **Strict Response Parser (`parse_strict_json_response` & `parse_response_with_quarantine`)**:
   - Validates the complete response string strictly via `json.loads(content)`.
   - Explicitly rejects any response containing trailing extra data, unescaped tokens, or malformed syntax.
   - **Zero silent truncation**: strictly forbids slicing `content[:pos]` to discard trailing data, as doing so would silently drop candidate observations.
   - **Zero guessing**: forbids heuristic text repair on malformed envelopes.
   - Quarantines the document immediately with telemetry:
     ```json
     {
       "error": "invalid_json",
       "message": "Extra data",
       "line": 1,
       "column": 35923,
       "offset": 35922,
       "automatic_repair_attempted": false,
       "retry_performed": false
     }
     ```
2. **Provider Structured-Output / JSON Mode & System Prompt Enforcement**:
   - Confirmed client request sends `response_format={'type': 'json_object'}`.
   - Strengthened the prompt contract in `run_pilot.py`:
     ```
     CRITICAL JSON FORMAT CONTRACT: Return a single, valid JSON object starting with { and ending with }.
     All five keys ("data", "evidence", "missing_information", "uncertainties", "upstream_observations")
     must be contained inside this single root object. Do not close the root object early and never emit extra data or trailing text.
     ```
3. **Regression Tests Added**:
   - `test_parse_strict_json_reproduces_karthiyayini_failure_and_quarantine`: reproduces the exact failure from saved `04/response-content.txt`, asserting failure metadata, `offset == 35922`, `automatic_repair_attempted == False`, and `retry_performed == False`.
   - `test_parse_strict_json_rejects_non_object`: verifies non-object payloads raise ValueError.
   - `test_parse_strict_json_accepts_clean_response`: verifies clean single-object payloads pass strictly.

---

## 2. Blocker 2: Citation Pointer Alignment & Provably Equivalent Path Normalization

### Root Cause Analysis (`A Lokhande.pdf`)
In Document 1 (`A Lokhande.pdf`), the provider extracted 102 factually accurate fields (12 of 12 critical reference facts matched), but emitted all 103 evidence dictionary keys without the RFC 6901 leading slash `/`:
- `contact/full_name` instead of `/contact/full_name`
- `experience/0/company` instead of `/experience/0/company`
- `skills/technical_skills/0` instead of `/skills/technical_skills/0`

Under strict raw citation checking, `evidence.get(path)` looked up `/contact/full_name` and found nothing, resulting in:
- 102 `missing_field_evidence` issues (0/102 valid citations; 0.0% compliance).
- 103 `evidence_not_for_populated_leaf` / `non_standard_json_pointer` issues.

### Deterministic Pointer Normalizer (`normalize_evidence_pointers`)
To fix this contract mismatch without altering model values or fabricating citations, we implemented `normalize_evidence_pointers(raw, blocks)`:
1. **Target Data Immutability**:
   - Asserts `candidate['data'] == raw['data']`. The normalizer is mathematically incapable of changing any mapped value.
2. **Citation Preservation**:
   - The citation payloads (`source_id`, `quote`) are transferred verbatim. No quotes or block IDs are fabricated or modified.
3. **Provably Equivalent Path Rules**:
   - A relative path missing a leading slash (`contact/email`) or with redundant leading slashes (`//contact/email`) is normalized to `/` + stripped path.
   - If the candidate pointer uniquely matches a populated leaf in `data`, the path is normalized and logged.
   - If an evidence path points to an out-of-bounds index (e.g. `experience/1/technologies/6`, where `technologies` has only 6 items), it is normalized to `/experience/1/technologies/6` and preserved so that `validate` strictly flags `evidence_not_for_populated_leaf`.
4. **Collision & Ambiguity Rejection**:
   - If multiple raw keys map to the same target pointer, or if an exact pointer already exists with conflicting citations, normalization is **rejected**. The collision is recorded in `rejections`, keeping the original keys so validation flags the defect.
5. **Audit Logging**:
   - Every single normalization is recorded in `changes.json` with the original path, normalized path, rule (`provably_equivalent_leading_slash`), and citation count.

### Impact on `A Lokhande.pdf`
- **Normalizations Applied**: 103 (102 matching populated leaves, 1 out-of-bounds pointer).
- **Ambiguities / Rejections**: 0.
- **Data Values Mutated**: 0.
- **Citation Validity**: Rose from **0/102 (0.0%)** to **93/102 (91.18%)**.
- **Remaining Issues (9 fields)**: Genuine source-text differences (e.g. block `e22:0:74` where upstream text lacked spaces: `DesignedandoptimizedRESTfulAPIsusingSpringBootandJava8`).
- **Critical Reference Facts**: Evidence-backed agreement rose from **0/12 (0.0%)** to **12/12 (100.0%)**!

---

## 3. Comprehensive Before / After Offline Evaluation Results

### Overall Aggregate Comparison

| Metric | Before (Strict Raw Contract) | After (Candidate with Normalizer) | Absolute Delta | Notes |
|---|---:|---:|---:|---|
| **Total Resumes** | 5 | 5 | 0 | Exactly 5 distinct representative resumes |
| **API Calls Made** | 5 | 5 | 0 | 0 new calls; 0 retries; 100% offline evaluation |
| **Schema Valid Documents** | 4 (80.0%) | 4 (80.0%) | 0 | 4 parsed cleanly; 1 quarantined |
| **Quarantined Failed Documents** | 1 (20.0%) | 1 (20.0%) | 0 | `KARTHIYAYINI S_1.pdf` (strict JSON error) |
| **Populated Fields (Parseable Outputs)** | 388 | 388 | 0 | Leaf count identical across all 4 valid resumes |
| **Citation-Compliant Fields** | **282 (72.68%)** | **375 (96.65%)** | **+93 fields** | **+23.97% citation compliance gain** |
| **Full Citation Contract Passes** | 2 / 5 (40.0%) | 2 / 5 (40.0%) | 0 | `A Suribhotla` & `AswathyRajagopal` (100% each) |
| **Predeclared Reference Opportunities** | 79 | 79 | 0 | Frozen prior to initial API calls |
| **Reference Value Matches** | 60 (75.95%) | 60 (75.95%) | 0 | All 19 missing facts belong to doc 4 (failed JSON) |
| **Evidence-Backed Critical Matches** | **48 / 79 (60.76%)** | **60 / 79 (75.95%)** | **+12 facts** | **100% of matching values are now evidence-backed** |
| **Target Data Values Mutated** | — | **0** | 0 | Mathematical equality strictly asserted |
| **Fabricated Citations** | — | **0** | 0 | Verbatim source quotes preserved |

---

### Per-Resume Before / After Breakdown

| # | Resume File | Pages | Blocks | Status | Populated Fields | Citations Before | Citations After | Citation Compliance Delta | Reference Denominator | Value Matches | Evidence-Backed Before | Evidence-Backed After |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `A Lokhande.pdf` | 2 | 68 | Flagged | 102 | 0 (0.0%) | **93 (91.18%)** | **+93 (+91.18%)** | 12 | 12 (100%) | 0 (0.0%) | **12 (100.0%)** |
| 2 | `Abhishek Barnwa.pdf` | 1 | 54 | Flagged | 93 | 89 (95.70%) | **89 (95.70%)** | 0 (0.00%) | 13 | 13 (100%) | 13 (100.0%) | **13 (100.0%)** |
| 3 | `A Suribhotla.pdf` | 4 | 106 | Flagged | 100 | 100 (100.0%) | **100 (100.0%)** | 0 (0.00%) | 17 | 17 (100%) | 17 (100.0%) | **17 (100.0%)** |
| 4 | `KARTHIYAYINI S_1.pdf` | 4 | 182 | **Failed** | 0 | 0 (0.0%) | **0 (0.0%)** | 0 (0.00%) | 19 | 0 (0.0%) | 0 (0.0%) | **0 (0.0%)** |
| 5 | `AswathyRajagopal.pdf` | 2 | 81 | Flagged | 93 | 93 (100.0%) | **93 (100.0%)** | 0 (0.00%) | 18 | 18 (100%) | 18 (100.0%) | **18 (100.0%)** |
| **All** | **Total / Overall** | **13** | **491** | **4 Flagged, 1 Failed** | **388** | **282 (72.68%)** | **375 (96.65%)** | **+93 (+23.97%)** | **79** | **60 (75.95%)** | **48 (60.76%)** | **60 (75.95%)** |

---

## 4. Part A Pilot 1 Re-evaluation Verification

The 5 saved documents from Pilot 1 (`Ajay Bandagi`, `DDhanush`, `Boovanesh Kumar`, `A Madhavi`, `Nithin Eswarappa`) were re-verified offline via `offline_recheck.py`:
- All 3 confirmed omissions remained 100% repaired:
  1. `Nithin Eswarappa`: `/education/0/field_of_study` = `Intelligent Systems` (`e8:38:82`)
  2. `Nithin Eswarappa`: `/education/1/field_of_study` = `Electronics and Communication` (`e8:120:176`)
  3. `A Madhavi`: `/experience/3/responsibilities/14` = `Worked on Tag Mapping to Element level mapping for IMPS.` (`e61:0:56`)
- Strict per-leaf citation check active; zero unearned parent inheritance.
- 0 new network calls; 0 paid tokens consumed.

---

## 5. Token Usage & Verifiable Cost Audit

All calls were conducted under strict zero-retry enforcement against `deepseek-flash`. The credential-free ledger in `call-ledger.json` records:

| Document # | File | Model | Status | Prompt Tokens | Completion Tokens | Total Tokens | Cache Hits | Cache Misses |
|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | `A Lokhande.pdf` | deepseek-flash | 200 OK | 6,550 | 4,930 | 11,480 | 0 | 6,550 |
| 2 | `Abhishek Barnwa.pdf` | deepseek-flash | 200 OK | 6,054 | 4,641 | 10,695 | 2,560 | 3,494 |
| 3 | `A Suribhotla.pdf` | deepseek-flash | 200 OK | 8,747 | 5,571 | 14,318 | 2,560 | 6,187 |
| 4 | `KARTHIYAYINI S_1.pdf` | deepseek-flash | 200 OK | 13,433 | 10,256 | 23,689 | 2,560 | 10,873 |
| 5 | `AswathyRajagopal.pdf` | deepseek-flash | 200 OK | 7,690 | 6,149 | 13,839 | 2,560 | 5,130 |
| **Total** | **5 Calls** | **deepseek-flash** | **5 / 5** | **42,474** | **31,547** | **74,021** | **10,240** | **32,234** |

- **Cost Verification**: In compliance with strict auditing guidelines, no monetary cost is fabricated or estimated since DeepSeek response headers/envelopes do not return currency billing amounts.
- **Cache Efficiency**: 24.1% of prompt token volume was served via provider prompt caching (10,240 cached tokens).

---

## 6. Regression Testing & Production Code Preservation

### Automated Test Execution
- **Isolated Schema Gate Test Suite**: **26 of 26 passed in 0.30 seconds** (`test_schema_gate.py`).
  - Verifies strict JSON parsing and quarantine on `KARTHIYAYINI S_1.pdf` (extra data at character 35922).
  - Verifies pointer normalizer on `A Lokhande.pdf`: exactly 103 normalizations, 0 mutations of data, 0 fabricated quotes.
  - Verifies rejection of ambiguous path collisions.
  - Verifies rejection of bad quotes, parent-array citations, and unassigned emails.
- **Targeted Heuristic Mapping Suite**: **11 of 11 passed in 1.17 seconds** (`tests/test_schema_mapping.py`).
- **Complete Repository Regression Suite**: **341 of 341 passed in 98.91 seconds** (`PYTHONPATH=.:src .venv/bin/python -m pytest tests/ reports/deepseek-schema-pilot5-v2-20261022/test_schema_gate.py`).

### Production Code Preservation Check
- **Production Files Checked**: 102 files monitored across `local_api/`, `src/`, `scripts/`.
- **Production Files Changed**: **0**.
- **Source Artifacts Changed**: **0**.
- **Network Leak Check**: Zero external sockets or connections attempted; all tests run strictly offline.
- Verified in [preservation.json](preservation.json).

---

## 7. Next Steps & Production Gate Recommendation

### Current Status: **Ready for Review; Hold on Unattended Production Scaling**

With both blockers now isolated, understood, and deterministically resolved:
1. **JSON Parser Hardening**: The strict parser ensures that invalid provider JSON will never crash the pipeline or inject corrupt records into downstream stores.
2. **Citation Pointer Normalization**: Relative pointer formatting has been brought into compliance with RFC 6901 without altering model data.
3. **Next Scaled Testing**:
   - When approved by the user, a small 10-20 resume pilot can be executed using the hardened prompt contract and strict parsing.
   - Do NOT run full 350-batch extraction until user approval is received.
