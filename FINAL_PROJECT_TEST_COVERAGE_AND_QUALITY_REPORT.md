# Final project test coverage and quality report

**Verdict: NOT READY**

The pre-change suite returned **1,093 passed and 59 failed** in **1,150 seconds**. The largest failure class was **43 rejections for stale or missing source-ownership validation**. Those rejections prevented the affected replay tests from reaching their field-accuracy assertions. The audit fixed provider error logging and added eight focused test cases, all of which passed together. The final offline suite returned **1,099 passed and 59 failed**.

## Repository and scope

- Branch `schema-mapping-accuracy-fixes`, commit `f855b19f1e3cc8b6746bf88e661af41adc2bd50b`. The baseline includes the working tree’s 11 pre-existing source edits and seven untracked test and fixture files.
- The local API uses FastAPI, Starlette, Pydantic, Unstructured, Tesseract, Poppler, LibreOffice, Sentence-BERT and scikit-learn. The standalone Python PDF package includes a vendored port. The frontend uses plain JavaScript, HTML, CSS and local preview assets. No application database or repository-root CI workflow was identified.
- [Source inventory](reports/final-project-qa/python-source-inventory.tsv) lists source components, dependencies and direct test imports. [Scenario matrix](reports/final-project-qa/scenario-gap-matrix.tsv) tracks subsystem risks and missing scenarios. Direct imports can miss indirect execution.
- Python coverage measures executable statements and branches across `local_api` and `src/pdf_hires`, including application-owned vendored code. Operational scripts and frontend assets are outside those percentages.

## Baseline and execution disclosure

| Measure | Baseline |
|---|---:|
| Cases | 1,152 |
| Passed | 1,093 |
| Failed | 59 |
| Skipped, xfailed, or errors | 0 |
| Statements | 14,418 of 19,817 (72.76%) |
| Branches | 5,974 of 8,732 (68.42%) |

Two existing, unmarked tests explicitly reloaded credentials from `.env` and contacted DeepSeek in the first baseline despite clearing inherited credentials. Both passed and each asserted at least one live completion call. One used synthetic text and one used a real resume fixture. These calls were unintended. The default suite now deselects both live cases, test collection no longer loads those credentials, and the final run also blocks external Python socket connections. The live assertions remain in the suite for explicitly authorized runs. The host restarted during the first offline attempts, so the retained historical baseline includes the two live tests. Coverage differences from that run cannot be attributed solely to the new tests.

[Baseline coverage JSON](reports/final-project-qa/baseline-coverage.json) · [Baseline coverage XML](reports/final-project-qa/baseline-coverage.xml)

## Confirmed findings

| Severity | Finding | Resolution |
|---|---|---|
| High | The provider HTTP error handler read and logged an unrestricted response body. A synthetic regression reproduced the exposure. | The handler now closes the response and logs the HTTP status and normalized category. Completion and retry behavior is preserved. |
| High | Two live DeepSeek tests lacked the configured `provider` marker. Collection of one test module also loaded private configuration. | Both tests are marked and collection no longer reads the credential file. Collection confirms two deselected cases. |
| High | Forty-three baseline cases failed with `Stale validated ownership source`. Nine inspected ground-truth replays had no stored source digest. Some replay helpers also rebuild sections while carrying forward older validation state. | Preserve the fail-closed check. Rebuild affected fixtures from original paired extraction and validation artifacts or define a versioned migration. |
| High | Other baseline assertions fail in semantic grouping, education ownership, date alignment and hierarchy. | Compare each failing output against its source before changing parsing behavior. |
| Medium | The positive batch-audit fixture passes a namespace in place of an extraction element. Digest computation calls `model_dump()`, which the fixture lacks. | Convert the fixture to a public extraction schema before interpreting the test as a production failure. |

## Test quality and additions

The stronger ownership tests assert record identity, literal field values, offsets and transaction rollback. Source conservation alone leaves room for classification errors. Successful OCR calls and element counts establish that a path executes. They do not validate transcription or ordering. Saved replays with stale provenance currently fail before their semantic assertions, leaving a gap between nominal and effective coverage. Provider mocks verify local behavior under controlled failures. Browser layout and live provider conformance require separate evidence.

- **Section detection** uses the real cached model to compare equivalent input with and without the Education heading. It checks assignment reason, neighboring Projects content and preservation of the source.
- **Provider transport** tests response-body privacy, capped paid responses without retries, and bounded retry and cleanup for read-only requests.
- **Dates and durations** exercises all permutations of overlapping intervals with a duplicate and verifies the same four-year total.
- **Word conversion** tests timeout handling and cleanup of the temporary source and LibreOffice profile.
- **Frontend** uses the real PDF extraction endpoint’s response with shipped JavaScript in a simulated DOM. It checks loading, success, API rejection, malformed JSON and reset of the busy state. A separate Chromium smoke check passed real PDF extraction, corrupt-PDF error handling and upload controls at a 390-pixel viewport. Full responsive and browser workflow coverage remains open. [Smoke results](reports/final-project-qa/browser-smoke.json)

The heading and interval tests are metamorphic tests. No mutation, fuzzing, load testing or independent corpus-accuracy percentage was measured. Python compilation, JavaScript syntax checks, and `git diff --check` passed.

## Changed files

- Production fix in `local_api/services/llm_section_review.py`.
- Added tests to `test_llm_section_review.py`, `test_resume_sections.py`, `test_word_preparation.py` and `test_year_precision_durations.py`.
- Added `tests/test_upload_workflow_ui.py` and `tests/upload_workflow_ui.cjs`.
- Applied the live-provider markers in `test_generalized_semantic_hierarchy.py` and `test_structural_review_chunking.py`.

## Remaining priorities

1. Restore authoritative saved-replay fixtures and resolve the semantic failures.
2. Expand labeled OCR and layout coverage across rotation, skew, mixed scripts and partial OCR output.
3. Verify partial and empty results, downloads, responsive layouts and errors in a browser.
4. Add deterministic CI jobs for local API, cached model and OCR execution. Run provider checks independently with synthetic documents.

## Final execution and coverage

Report generated **2026-11-18T23:50:23+05:30**. Six independently measured test batches ran with pytest 9.1.1 and coverage.py 7.17.3. Coverage combines branch data from all six Python processes. All eight new cases passed in these batches. Failure counts by module matched the baseline.

| Run | Selected | Passed | Failed | Skipped | Xfailed | Errors | Deselected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 1,152 | 1,093 | 59 | 0 | 0 | 0 | 0 |
| Final | 1,158 | 1,099 | 59 | 0 | 0 | 0 | 2 |

The final batches recorded **2080.05 seconds** of summed pytest process time. Two batches could run concurrently. End-to-end elapsed time was **1241.26 seconds**.

| Scope | Baseline statements | Baseline branches | Final statements | Final branches |
|---|---:|---:|---:|---:|
| Overall Python application | 14418/19817 (72.76%) | 5974/8732 (68.42%) | 14413/19814 (72.74%) | 5972/8732 (68.39%) |
| Local API backend | 11731/13075 (89.72%) | 5579/6726 (82.95%) | 11726/13072 (89.70%) | 5577/6726 (82.92%) |
| Standalone PDF package | 2687/6742 (39.85%) | 395/2006 (19.69%) | 2687/6742 (39.85%) | 395/2006 (19.69%) |
| API routes and app | 253/262 (96.56%) | 34/36 (94.44%) | 253/262 (96.56%) | 34/36 (94.44%) |
| Parsing and recovery | 8924/9646 (92.52%) | 4461/5222 (85.43%) | 8919/9643 (92.49%) | 4460/5222 (85.41%) |
| Standardization | 1036/1129 (91.76%) | 433/500 (86.60%) | 1036/1129 (91.76%) | 433/500 (86.60%) |
| Dates and experience | 206/246 (83.74%) | 89/114 (78.07%) | 206/246 (83.74%) | 89/114 (78.07%) |
| Mapping and evidence | 2285/2576 (88.70%) | 1149/1410 (81.49%) | 2285/2576 (88.70%) | 1149/1410 (81.49%) |
| Critical business logic | 3394/3717 (91.31%) | 1807/2110 (85.64%) | 3393/3717 (91.28%) | 1806/2110 (85.59%) |

The local API backend met the 80% statement target at 89.70%. Critical business logic missed the 90% branch target at 85.59%.

The Word conversion timeout test newly exercises two previously uncovered statements. For files with unchanged source, the branch comparison recorded three fewer branch destinations and no additional destinations. The provider handler itself changed, so its line coordinates are compared through module totals and HTML. The small decrease in overall coverage must be read alongside the change in suite selection and the narrower source path after the provider fix.

### Critical module targets

| Module | Final statement coverage | Final branch coverage | Missing statements | Missing branches |
|---|---:|---:|---:|---:|
| `services/text_extraction_service.py` | 137/148 (92.57%) | 55/66 (83.33%) | 11 | 11 |
| `services/resume_sections.py` | 399/417 (95.68%) | 159/174 (91.38%) | 18 | 15 |
| `services/resume_structure.py` | 642/676 (94.97%) | 393/450 (87.33%) | 34 | 57 |
| `services/schema_mapping.py` | 555/602 (92.19%) | 297/340 (87.35%) | 47 | 43 |
| `services/source_ownership.py` | 628/727 (86.38%) | 328/410 (80.00%) | 99 | 82 |
| `services/llm_section_review.py` | 353/380 (92.89%) | 101/120 (84.17%) | 27 | 19 |
| `services/llm_schema_mapping.py` | 766/883 (86.75%) | 374/486 (76.95%) | 117 | 112 |
| `services/standardization/dates.py` | 206/246 (83.74%) | 89/114 (78.07%) | 40 | 25 |
| `services/standardization/service.py` | 175/187 (93.58%) | 61/68 (89.71%) | 12 | 7 |

Use 85% statement and 90% branch coverage for the listed important and critical modules. Remaining misses include ownership transitions, date grammar and provider validation paths. The target is 80% of backend statements. The separate standalone PDF package is included in the overall application denominator.

### Frontend coverage

[Node V8 function observations](reports/final-project-qa/frontend-v8-summary.json) cover JavaScript assets loaded by path in the full test run. Tests that extract functions into anonymous scripts are not attributed to an asset in this report. These counts do not represent whole-frontend or browser coverage.

### Raw artifacts and failure details

- [Final HTML coverage](reports/final-project-qa/html/index.html) includes uncovered lines and branch destinations, and function-level reports.
- [Final JSON](reports/final-project-qa/final-coverage.json), [final XML](reports/final-project-qa/final-coverage.xml), [coverage by module](reports/final-project-qa/python-module-coverage.tsv) and [branch changes](reports/final-project-qa/branch-delta.tsv).
- [Test module inventory](reports/final-project-qa/test-module-inventory.tsv) includes test and outcome counts. The static review signals are triage evidence. They cannot distinguish weak from strong assertions by themselves.
- [Final failing cases](reports/final-project-qa/test-failure-inventory.tsv) lists test definitions without fixture parameter values, quoted résumé text or exception bodies.

**NOT READY.** Restore trustworthy replay coverage and resolve the remaining semantic failures before treating the suite as release evidence.
