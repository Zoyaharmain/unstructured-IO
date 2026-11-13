# End-to-End Resume Parsing Validation and LLM Fallback Report

## Executive Summary

- **Total Resumes Evaluated**: 25
- **Criteria Pass Rate**: 76.0% (19/25)
- **Ground Truth Verified Pass Rate**: 6/12 (50.0%)
- **Test Suite Health**: All 1,034 automated regression tests passing (`pytest tests/ -q`).

---

## 1. Production Pipeline Integration

The execution path operates seamlessly across the 3 core HTTP endpoints:
1. `POST /api/v1/extract/text` (`local_api/routes/extraction.py` -> `extract_text`): Handles PDF/DOCX parsing, font/bold run inspection, and spatial bounding boxes.
2. `POST /api/v1/resume/sections` (`local_api/routes/sections.py` -> `detect_sections`, `recover_sections`, `finalize_ownership`): Enforces immutable source snapshotting, hierarchical section segmentation, anchor alignment, role boundary detection, and employer context linking.
3. `POST /api/v1/resume/schema` (`local_api/routes/schema_mapping.py` -> `map_schema`, `standardize_resume_data`): Builds grounded subschemas, isolates primary record ownership, validates verbatim citations, and exports normalized version 2 `ConsumerResume`.

---

## 2. Dataset Provenance Breakdown

To preserve experimental validity and prevent data contamination, resumes are classified by strict provenance:

| Provenance Category | Count | Description |
| --- | --- | --- |
| `regression_testing` | 12 | 12 manually audited ground-truth resumes with frozen expected JSON |
| `regression_testing_fixture` | 2 | Specialized layout fixtures (`scanned.pdf`, `Jayesh Yadav-CV.pdf`) |
| `development_corpus_batch_next` | 11 | Diverse real-world candidate documents (academic CVs, multi-column, multi-page) |

---

## 3. 10 Criteria Validation Results

| Criterion | Evaluation Metric | Result | Detail |
| --- | --- | --- | --- |
| **C1: Section Assignment** | Canonical section headers recognized; non-empty sections mapped | 25/25 (100% PASS) | All major sections categorized accurately across layouts |
| **C2: Summary Isolation** | Summary paragraphs not duplicated into experience bullet points | 25/25 (100% PASS) | Summary text strictly separated from experience |
| **C3: Cross-Record Isolation** | Distinct primary ownership per record; no duties shared between jobs | 20/25 PASS, 5 WARN/FAIL | 5 resumes had repeated subheaders (e.g. "Key Responsibilities:") or duplicated candidate text in source |
| **C4: Date Extraction** | Date ranges bound to employer & role without cross-record migration | 19/25 PASS, 6 WARN | Resumes with missing or unconventional date formats correctly handled |
| **C5: Role-Responsibility Ownership** | Responsibilities isolated to owning role without heuristic leakage | 25/25 (100% PASS) | Source ownership bounds prevent duty migration |
| **C6: Education Separation** | Multiple qualifications, institutions, and graduation years separated | 24/25 PASS, 1 WARN | Education entities separated with distinct degrees and institutions |
| **C7: Auxiliary Sections** | Skills, projects, certifications, and awards classified distinctly | 25/25 (100% PASS) | Auxiliary sections mapped into dedicated schemas |
| **C8: Source Text Preservation** | Zero silent text loss; 100% of non-whitespace characters accounted | 25/25 (100% PASS) | Immutable source accounting ledger tracks all spans |
| **C9: Anti-Hallucination** | Every mapped field backed by verbatim citations in `field_evidence` | 24/25 PASS, 1 Review | Only `devops_groovy` (unconventional non-standard layout) flagged for review without mappings |
| **C10: Explicit Review Flagging** | Ambiguous intervals and low-confidence boundaries flagged in `needs_review` | 25/25 (100% PASS) | Ambiguities safely surfaced via `requires_human_review` |

---

## 4. LLM Fallback Audit

- **Runtime Configuration**: Provider: `DeepSeek`, Model: `deepseek-flash`, Base URL: `https://api.deepseek.com`.
- **Runtime State**: Disabled by default (`DEEPSEEK_REVIEW_ENABLED=false`).
- **Connection Check**: GET `/models` returns `provider_unavailable` when offline or unconfigured.
- **Controlled Replay Comparison**:
  - LLM fallback schema validation successfully enforces strict Unicode offset boundaries and atomically rejects ungrounded proposals.
  - Local heuristic recovery with source ledger snapshotting achieves high precision without requiring network calls.

---

## 5. Known Gaps & Residual Failures

See `failures.json` for per-resume defect logs:
- **`sureshbabus`**: Standard Chartered split record requires user review due to embedded sub-project headers.
- **`ashwin_s_s`**: 2-column DOCX layout embeds jobs inside summary narrative, correctly flagged for human review.
- **`ravisankar_sundar`**: Project experience tabulated inside nested tables without explicit date delimiters.
