# Product Readiness Report: End-to-End Resume Processing Pipeline

**Run Identifier:** `product-readiness-20261025-093847`  
**Date & Timestamp:** 2026-10-25T09:38:47-07:00  
**Repository:** `~/unstructured-IO`  
**Git Branch:** `main` (commit `096286a8`)  
**Auditor:** Antigravity Advanced Agentic Coding System  

---

## 1. Executive Decision: `NOT READY` (For Unattended Production Scaling)

### Decision Summary
The resume-processing product is **`NOT READY`** for general, unattended production deployment across arbitrary candidate resumes. It is structurally stabilized, offline-tested, and demonstrably safe for strictly controlled, human-supervised limited pilot evaluation (`LIMITED PILOT READY` with human-in-the-loop validation only).

### Concise Justification
1. **Critical Offline Semantic Gap**: The local offline model stack (Sentence-BERT + K-means / heuristic section classification) achieves only **58.5% character accuracy** and **0 / 15 (0.0%) entirely correct resumes** on the 15 gold-standard human-verified resumes ([`reports/ground_truth_15_evaluation.md`](file:///home/gopal/unstructured-IO/reports/ground_truth_15_evaluation.md)). Without LLM assistance, it regularly fragments multi-column layouts, misclassifies education/skills, and misses contact names.
2. **Schema Audit Gate Failure on Real Complex Resumes**: When the LLM review pipeline is activated, strict schema-audit quality gates correctly halted processing on Document 01 (`Abhishek.S.pdf`) due to source-missing required fields (`education[0].institution`, `education[2].institution`), leaving 4 of the 5 pilot resumes unattempted under the strict gate policy.
3. **Severe Annotation Deficit**: Of the 804 discovered resumes in the corpus, only **15 (1.87%)** have gold human-verified ground-truth annotations in [`ground_truth/gold/`](file:///home/gopal/unstructured-IO/ground_truth/gold/). Statistical confidence across arbitrary real-world resumes is unestablished.
4. **Missing Candidate Indexing/Search Feature**: While the HTTP API schemas define query contracts, persistent candidate search/indexing across processed resumes is not implemented in this codebase.
5. **Operational Strengths**: On the positive side, the codebase has achieved **100% test pass rate (472/472 tests)** across all offline tiers (unit, mock-provider, api-integration, extraction-slow, and local-model), with zero regressions, zero file corruptions, zero socket leaks, and 100% citation provenance enforcement.

---

## 2. Scope & Limitations

### What Was Evaluated
- **Full Offline Test Suite**: All 472 collected tests across 5 tiers: `unit` (241), `mock_provider` (129), `api_integration` (64), `extraction_slow` (13), and `local_model` (25).
- **Parity & Ingestion**: Direct Unstructured extraction vs Local FastAPI HTTP `/v1/partition` parity across `Jayesh Yadav-CV.pdf` and `digital-multipage.pdf` across 4 strategies (`fast`, `auto`, `hi_res`, `ocr_only`).
- **5-Resume Pilot Dataset**: End-to-end local execution of the 5 stratified resumes from [`reports/chunked-schema-pilot5-20261024/selection-manifest.json`](file:///home/gopal/unstructured-IO/reports/chunked-schema-pilot5-20261024/selection-manifest.json):
  1. `Abhishek.S.pdf`
  2. `IdaJose.pdf`
  3. `Priyotosh Kumar Singh.pdf`
  4. `PriyankaRoy[8y_0m].pdf`
  5. `Kaleru Abhiram.pdf`
- **Schema & Subschema Constraints**: `ResumeSchema`, `SectionSchema`, nested hierarchy, citation validation, unmapped block tracking, and document scope filtering.
- **Artifact Preservation**: Verification that historical reports, frozen manifests, and existing working-tree modifications remained untouched.

### What Was NOT Evaluated (Explicit Exclusions)
- **Live Provider API Calls**: Zero external or paid LLM calls were made during this audit (`DEEPSEEK_API_KEY` and `OPENAI_API_KEY` were held disabled, complying with strict safety rules).
- **Unverified Gold Labels**: No synthetic predictions were promoted to ground-truth labels.
- **Candidate Database/Search**: No multi-resume search index was evaluated because it is not implemented in the application layer.

---

## 3. Baseline

### Git & Working Tree State
- **Branch:** `main` (commit `096286a8`)
- **Initial Working Tree:**
  - Modified: [`pyproject.toml`](file:///home/gopal/unstructured-IO/pyproject.toml), [`tests/test_local_api.py`](file:///home/gopal/unstructured-IO/tests/test_local_api.py)
  - Untracked: [`tests/README.md`](file:///home/gopal/unstructured-IO/tests/README.md), [`tests/conftest.py`](file:///home/gopal/unstructured-IO/tests/conftest.py)
  - All pre-existing user modifications and untracked files were preserved intact.
- **Historical Parity Directory:** [`reports/api-parity/`](file:///home/gopal/unstructured-IO/reports/api-parity/) verified clean and unmodified.

### Initial Known Defects Diagnosed
1. **Slow Extraction TestClient Stall Perception**:
   - *Symptom:* The `extraction_slow` tier appeared to stall at `TestClient.post()` in [`tests/test_local_api.py:82`](file:///home/gopal/unstructured-IO/tests/test_local_api.py#L82), triggering 45s faulthandler dumps.
   - *Root Cause:* Each test ran extraction **twice** sequentially (synchronously in main thread, then in an AnyIO worker thread). For CPU-heavy strategies (`hi_res` with YOLOX ONNX layout detection taking ~27.5s total, and `ocr_only` with Tesseract tile encoding taking ~34.3s total), the test was compute-bound on CPU, not deadlocked. When allocated adequate runtime (>45s per test), all 13 tests pass cleanly.
2. **Read-Only Matplotlib Config**:
   - Sandboxed execution mounts `/home/gopal/.config` as read-only, prompting Matplotlib to emit non-fatal cache warnings.

---

## 4. Architecture Map

The resume processing pipeline consists of 6 discrete stages:

```
[Raw Document: PDF / Image / DOCX]
               │
               ▼
   [Stage 1: Ingestion & Extraction]
   (unstructured.partition.auto.partition / local_api.app: /v1/partition)
   - Elements, coordinates, page numbers, reading order, clean text
               │
               ▼
   [Stage 2: Section Detection & Boundary Layout]
   (local_api.services.resume_sections / Sentence-BERT + K-means / Anchors)
   - Category assignment, section headers, unassigned block identification
               │
               ▼
   [Stage 3: Section Recovery & Highlights]
   (local_api.services.section_recovery / section_highlights / source_accounting)
   - Unresolved text recovery, whitespace normalization, provenance retention
               │
               ▼
   [Stage 4: LLM Section Review & Schema Audit (Provider Stage)]
   (local_api.services.llm_section_review / review_chunking / review_resolution)
   - Chunked review with source quote bounds, quality gates (Mocked / Offline in test)
               │
               ▼
   [Stage 5: Schema & Subschema Mapping]
   (local_api.services.schema_mapping / section_subschemas / record_relationships)
   - ResumeSchema (contact, experience, education, skills, projects, certifications)
   - SectionSchema (nested record hierarchies, attribute values, source IDs)
               │
               ▼
   [Stage 6: Provenance & Audit Ledger Verification]
   (local_api.services.quality_assessment / source_validation / subschema_validation)
   - Field evidence mapping, missing required field ledger, unmapped block audit
```

### Core Implementation Files
- **API Entrypoint:** [`local_api/app.py`](file:///home/gopal/unstructured-IO/local_api/app.py)
- **Extraction Router:** [`local_api/routes/extraction.py`](file:///home/gopal/unstructured-IO/local_api/routes/extraction.py)
- **Section Router:** [`local_api/routes/sections.py`](file:///home/gopal/unstructured-IO/local_api/routes/sections.py)
- **Schema Mapping Router:** [`local_api/routes/schema_mapping.py`](file:///home/gopal/unstructured-IO/local_api/routes/schema_mapping.py)
- **Canonical Schema Models:** [`local_api/vendor/handoff_schema/models.py`](file:///home/gopal/unstructured-IO/local_api/vendor/handoff_schema/models.py)
- **Subschema Models:** [`local_api/schemas/subschemas.py`](file:///home/gopal/unstructured-IO/local_api/schemas/subschemas.py)
- **Test Harness Configuration:** [`tests/conftest.py`](file:///home/gopal/unstructured-IO/tests/conftest.py), [`pyproject.toml`](file:///home/gopal/unstructured-IO/pyproject.toml)

---

## 5. Change Log

### Files Modified & Verified
1. [`pyproject.toml`](file:///home/gopal/unstructured-IO/pyproject.toml):
   - Configured `pythonpath = ["src"]` to allow seamless local testing of both `src/pdf_hires` and root `local_api`.
   - Registered 6 official markers: `unit`, `api_integration`, `extraction_slow`, `local_model`, `mock_provider`, `provider`.
   - Default pytest invocation safely excludes live provider: `addopts = "--strict-markers -m 'not provider'"`.
2. [`tests/test_local_api.py`](file:///home/gopal/unstructured-IO/tests/test_local_api.py):
   - Fixed historical report pollution: `test_direct_extraction_parity` now writes temporary artifacts to pytest's `tmp_path / 'api-parity'` instead of mutating historical reports in `reports/api-parity/`.
   - Added `parity_snapshot()` and `test_parity_artifacts_refuse_historical_report_directory()` regression test to guarantee historical artifacts are never modified.
3. [`tests/conftest.py`](file:///home/gopal/unstructured-IO/tests/conftest.py) (Untracked preservation):
   - Added `pytest_collection_modifyitems` assigning exactly one primary tier per test item.
   - Added autouse fixture `disable_live_provider_by_default` stripping `DEEPSEEK_API_KEY`, `DEEPSEEK_REVIEW_ENABLED`, and `OPENAI_API_KEY` unless `@pytest.mark.provider` is explicitly active.
4. [`tests/README.md`](file:///home/gopal/unstructured-IO/tests/README.md) (Untracked preservation):
   - Documented exact commands and environment flags for all 5 safe offline test tiers.

---

## 6. Test Matrix

All 472 collected tests were executed across their respective tiers with complete recording:

| Tier Name | Marker Filter | Tests | Passed | Failed | Skipped | Deselected | Duration | Exit Code | Outcome |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Unit & Mock Provider** | `unit or mock_provider` | 370 | 370 | 0 | 0 | 102 | 35.23s | 0 | **PASS** |
| **API Integration** | `api_integration` | 64 | 64 | 0 | 0 | 408 | 21.11s | 0 | **PASS** |
| **Slow Extraction & OCR** | `extraction_slow` | 13 | 13 | 0 | 0 | 459 | 113.55s | 0 | **PASS** |
| **Local ML Section Model** | `local_model` | 25 | 25 | 0 | 0 | 447 | 18.58s | 0 | **PASS** |
| **Live Provider** | `provider` | 0 | - | - | - | - | - | - | **EXCLUDED** |
| **AGGREGATE OFFLINE** | *All offline tests* | **472** | **472** | **0** | **0** | **0** | **188.47s** | **0** | **100% PASS** |

- **Collection Health:** 472 items collected, 0 collection errors, 0 unregistered markers, 0 untiered tests.
- **Static & Diff Health:** `git diff --check` passed with 0 errors.

---

## 7. Real-Resume End-to-End Evaluation Matrix

The 5 stratified resumes from the frozen selection manifest ([`reports/chunked-schema-pilot5-20261024/selection-manifest.json`](file:///home/gopal/unstructured-IO/reports/chunked-schema-pilot5-20261024/selection-manifest.json)) were evaluated through the complete offline pipeline:

| Resume Filename | Pages / Elements | Sections Detected | Contact Extracted | Work Exp Records | Edu Records | Missing Required Fields | Unmapped Blocks | Processing Assessment |
|---|:---:|---|---|:---:|:---:|:---:|:---:|---|
| **`Abhishek.S.pdf`** | 1 pg / 36 elem | `education`, `experience` | Name: `""`<br>Email: `""`<br>Phone: `""` | 1 | 24 | 49 fields (`contact.*`, `experience[0].role`, 22 empty `education` records) | 30 / 36 | **Severe Local Fragmentation**: 2-column sidebar missed; 22 empty education records created. Caused previous live pipeline to fail schema audit gate. |
| **`IdaJose.pdf`** | 2 pg / 57 elem | `personal_info`, `summary`, `experience`, `skills`, `education` | Name: `"IDA JOSE"`<br>Email: `"idajose1603@gmail.com"`<br>Phone: `"+919400593192"` | 2 | 2 | 3 fields (`education[0,1].institution`, `education[1].degree`) | 27 / 57 | **Good Structural Alignment**: Clean contact & experience extracted. Minor institution missing in education. |
| **`Priyotosh Kumar Singh.pdf`** | 2 pg / 67 elem | `personal_info`, `skills`, `summary`, `education`, `experience`, `languages` | Name: `"Email"` *(heuristic error)*<br>Email: `"pg18-85@jkbschool.org"`<br>Phone: `"7059311404"` | 3 | 9 | 18 fields (`contact.full_name`, roles in experience, multiple edu degrees) | 13 / 67 | **Label Misclassification**: Captured label `"Email"` as candidate full name. Education records fragmented. |
| **`PriyankaRoy[8y_0m].pdf`** | 2 pg / 40 elem | `personal_info`, `skills`, `experience` | Name: `""`<br>Email: `"Priyankaroyp324@gmail.com"`<br>Phone: `"+91 9830642938"` | 2 | 0 | 2 fields (`contact.full_name`, `experience[1].company`) | 7 / 40 | **Omitted Section**: Education section heading not identified locally; 0 education records created. |
| **`Kaleru Abhiram.pdf`** | 3 pg / 80 elem | `personal_info`, `summary`, `skills`, `languages`, `experience`, `projects`, `education` | Name: `""`<br>Email: `"abhiramkaleru@gmail.com"`<br>Phone: `"+91 7993119262"` | 3 | 1 | 2 fields (`contact.full_name`, `projects[2].name`) | 50 / 80 | **High Unmapped Text**: 50 of 80 blocks remained unmapped into final schema attributes. |

---

## 8. Schema & Subschema Assessment

1. **Schema Compliance**: The canonical [`ResumeSchema`](file:///home/gopal/unstructured-IO/local_api/vendor/handoff_schema/models.py) model and [`SectionSchema`](file:///home/gopal/unstructured-IO/local_api/schemas/subschemas.py) serialize without ValidationError. Empty values fall back to empty strings `""` or `None` rather than fabricating missing information.
2. **Missing Required Fields**: The pipeline generates a dedicated ledger `meta.missing_required_fields` rather than inventing employers, job titles, or degrees.
3. **Record Boundaries**: Record relationships within `experience` and `education` are constrained by `record_subfields.py` and `education_subfields.py`. However, multi-column and dense tabular formats without clear visual boundaries frequently fragment single degrees into multiple empty records (e.g. 24 records in `Abhishek.S.pdf`).
4. **Candidate Scope Filter**: `document_scope()` successfully flags non-resume documents and prevents false extraction of candidate profiles from job descriptions or interview guides.

---

## 9. Evidence & Citation Assessment

1. **Strict Provenance**: All field values linked via `meta.field_evidence` are indexed to verified block `source_id` tokens (e.g., `e1:0:16`).
2. **Hallucination Prevention**: The mapping logic explicitly verifies that citations exist in the source inventory:
   ```python
   errors = validate_result(request.elements, request.sections)
   if errors:
       raise ValueError('Sections are not bound to the supplied source inventory')
   ```
   Fabricated quotes, foreign IDs, or out-of-order text mutations are rejected.
3. **Unmapped Blocks Audit**: Blocks that were not assigned to any schema field are recorded in `meta.unmapped_blocks`. In dense or multi-column resumes, unmapped block ratios remain high (up to 62.5% in `Kaleru Abhiram.pdf`), demonstrating that offline extraction alone loses significant semantic content unless reviewed by an LLM.

---

## 10. Accuracy Assessment & Ground Truth

| Dataset / Configuration | Resumes | Human Verified | Character Accuracy | Entirely Correct Resumes | Entirely Correct Sections |
|---|:---:|:---:|:---:|:---:|:---:|
| **Local Pipeline Only (Sentence-BERT + Heuristics)** | 15 (Gold) | **Yes** | **58.5%** | **0 / 15 (0.0%)** | 34 / 98 (34.7%) |
| **LLM-Assisted Pipeline (DeepSeek Review)** | 15 (Gold) | **Yes** | **99.92%** | **9 / 15 (60.0%)** | 86 / 98 (87.8%) |
| **Full Discovered Corpus** | 804 | **No (15 gold, 40 needs review)** | *Unmeasured across 789 resumes* | *Unmeasured* | *Unmeasured* |

### Key Accuracy Insights
- The local offline pipeline cannot independently serve as an enterprise-grade parser (58.5% accuracy).
- The LLM-assisted review stage provides a +41.4% accuracy boost, making it essential for viable extraction quality.
- However, because the LLM review stage is gated on schema audits that fail on imperfect multi-column resumes, production rollout cannot proceed until audit thresholds and fallback strategies are harmonized.

---

## 11. Operational Safety

- **Provider Isolation:** Zero live API calls were made during this audit. Environment variables `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, and `DEEPSEEK_REVIEW_ENABLED` were kept stripped.
- **Network Boundaries:** `HF_HUB_OFFLINE=1` was strictly enforced. Offline socket guard tests verified that unauthorized external connections fail closed.
- **Historical Reports & Fixtures:** 100% preserved. All historical runs under `reports/` and fixtures under `tests/fixtures/` retain their original SHA-256 hashes.
- **Parity Isolation:** Parity tests were safely redirected to ephemeral directories, preventing historical report overwrites.

---

## 12. Open Blockers & Risk Analysis

| # | Severity | Risk / Blocker | Impact | Recommended Action |
|---|:---:|---|---|---|
| **B1** | **HIGH** | Local Offline Pipeline Accuracy (58.5%) | Resumes processed purely offline suffer severe omissions and misclassifications. | Require LLM review for any production or customer-facing extraction. |
| **B2** | **HIGH** | Schema-Audit Gate Halts on Missing Fields | LLM pilot stops completely when resumes lack required fields (e.g. unstated institution or title). | Allow schema audit to classify unstated fields as `source_absent` rather than catastrophic pipeline failures. |
| **B3** | **MEDIUM** | Incomplete Gold Annotations (<2% Coverage) | Only 15 of 804 resumes have human-verified gold ground truth. | Expand human gold annotations to at least 50 stratified resumes across single/multi-column layouts. |
| **B4** | **LOW** | Missing Cross-Resume Search Implementation | The API has schema definitions for querying subschemas, but no global search/index. | Implement persistent database indexing in the next dedicated feature cycle. |

---

## 13. Readiness Gates Assessment

| Gate | Title | Status | Supporting Evidence |
|---|---|:---:|---|
| **Gate A** | **Test Integrity** | **PASS** | 472/472 offline tests pass across all 5 tiers with zero failures, zero errors, and zero skips. Clean pytest collection. |
| **Gate B** | **Pipeline Integrity** | **PASS** | Complete execution from PDF ingestion to serialized schema response. Unmapped blocks tracked without silent loss. |
| **Gate C** | **Schema Integrity** | **PASS** | `ResumeSchema` and `SectionSchema` validate successfully. Required/optional fields and empty fallbacks conform to contract. |
| **Gate D** | **Evidence & Provenance** | **PASS** | All field values retain verifiable source-span citations. Foreign, hallucinated, or ungrounded quotes are rejected. |
| **Gate E** | **Semantic Accuracy** | **PARTIAL** | 99.92% achieved with LLM on 15 gold resumes, but local offline accuracy is only 58.5% and 789 corpus resumes remain unannotated. |
| **Gate F** | **Operational Safety** | **PASS** | 0 provider calls, 0 secrets leaked, historical reports protected, offline network calls blocked. |
| **Gate G** | **Product Readiness** | **FAIL** | Not ready for unattended production due to B1 (low offline accuracy), B2 (schema gate halts on missing fields), and B3 (low annotation coverage). |

---

## 14. Ordered Next Steps

1. **Refine Schema-Audit Gate Policy**: Update `pipeline.json` and schema audit logic so that genuine source-absent fields (e.g. a candidate who did not list an institution or role) are marked `absent_in_source` rather than triggering a hard pipeline halt (`schema_audit_failed`).
2. **Authorize Controlled 5-Resume Pilot with LLM**: With the updated audit policy, execute the remaining 4 resumes from [`reports/chunked-schema-pilot5-20261024/selection-manifest.json`](file:///home/gopal/unstructured-IO/reports/chunked-schema-pilot5-20261024/selection-manifest.json) under a strictly capped budget (max 20 API calls).
3. **Expand Gold Ground Truth**: Annotate 35 additional diverse resumes (bringing gold count to 50) using [`scripts/audit_pilot_human_review.py`](file:///home/gopal/unstructured-IO/scripts/audit_pilot_human_review.py) to achieve statistically meaningful coverage.
4. **Implement Global Candidate Search**: In the next feature phase, build persistent database indexing on top of the validated `SchemaMappingResponse` outputs.

---

## 15. Handoff Note: Stable Reusable Interfaces

The following modules, schemas, and interfaces are fully stabilized, regression-tested, and ready to be imported for downstream features:

1. **`local_api.schemas.mapping.SchemaMappingResponse`**: The canonical contract for resume data, section subschemas, source accounting, and field evidence.
2. **`local_api.services.schema_mapping.map_schema`**: Pure, deterministic mapping service consuming `SectionResponse` and producing verified, citation-bound resume records.
3. **`local_api.services.subschema_validation.query_subschemas`**: Validated query engine for extracting specific subschema attributes by JSON path.
4. **`tests/conftest.py`**: Central test harness providing strict tier isolation, provider disabling, and regression safety.

