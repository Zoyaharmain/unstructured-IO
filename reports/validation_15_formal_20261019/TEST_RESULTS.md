# Offline test results

These runs used existing tests unchanged. No DeepSeek calls were made. The audit runner removes the key from its environment, disables provider review, uses offline model caches and rejects external socket connections. Completed full and targeted runs recorded zero attempted external connections. Fixture extraction tests exercise local processing, not the remaining corpus.

## Commands and outcomes

1. Initial full run:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 300 .venv/bin/python -B reports/validation_15_formal_20261019/run_tests_offline.py
```

Collection stopped: 1 error, `ModuleNotFoundError: pdf_hires` in tests/test_interface.py. No tests passed in that invocation. The package is present under src/, so the next invocation supplied the source path without installing or editing production files. Log: tests.log.

2. Sandbox full run with source path:

```bash
PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 timeout 240 .venv/bin/python -B reports/validation_15_formal_20261019/run_tests_offline.py
```

The sandbox run stalled after progress dots and produced no completed test summary. It is NOT counted as passing. Log: tests-with-src.log. The completed run below was executed outside that sandbox with the same external-network guard and offline configuration.

3. Full regression suite, outside sandbox:

```bash
PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 timeout 240 .venv/bin/python -B reports/validation_15_formal_20261019/run_tests_offline.py
```

**185 passed, 0 failed, 0 deselected, in 117.96 seconds.** Saved log: tests-host.log; JUnit: tests.xml. Includes the legacy interface and direct extraction parity cases.

4. Targeted regression run, outside sandbox:

```bash
PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 timeout 90 .venv/bin/python -B reports/validation_15_formal_20261019/run_targeted_offline.py
```

**176 passed, 0 failed, 9 deselected, in 35.51 seconds.** Selected `not direct_extraction_parity and not actual_pdf_stream`. Log: targeted-tests.log; JUnit: targeted-tests.xml. These 176 are a subset of the 185, not additional independent cases.

## Full-suite coverage

| Module | Passed cases |
|---|---:|
| test_llm_section_review |43|
| test_local_api |32|
| test_text_extraction |30|
| test_resume_sections |24|
| test_human_pilot_review |18|
| test_verification_ui |8|
| test_resume_ground_truth |7|
| test_batch_resume_audit |5|
| test_ground_truth_workflow |5|
| test_word_preparation |5|
| test_interface |4|
| test_llm_batch_audit |2|
| test_section_layout_recovery |2|

## Do passing tests cover the observed defects?

- The LLM tests use mocked responses to check interval coverage, error handling and recovery protocol. They do not establish semantic correctness of the saved live results.
- Human-review tests verify unsupported/wrong employer/title/date and degree/institution/year associations are rejected, legacy human_verified flags are insufficient, and bulk generation requires approvals. These are synthetic integrity cases, not independent approved labels for these PDFs.
- `test_canonical_text_merges_wordpiece_spans_without_inserting_spaces` verifies rejoined text and source preservation. It does NOT prohibit splitting PGSQL internally into two blocks; therefore that observed defect can coexist with a pass.
- Structure tests exercise employer wrapping, two-column layouts and generic grouping, but do not assert all exact source-backed role/date/degree memberships in these 15 saved outputs. The lane-based grouping failures remain demonstrated in the saved entry membership.
- PDF form/source-line tests and extraction parity tests check selected fixtures and parity with the installed extractor. Parity is not proof of original-PDF transcription. They do not assert GAURAV page2 Achievements or Ajay's exact paragraph occurs once.
- No existing real-document acceptance assertion establishes correct rejection of this Java requirements template, correct treatment of Rutuja's future coursework/plans, or resolution of PUPPYKUMARI's contradictory dates.

No failing assertion was changed or defect fixed during this audit. Passing 185 software tests does not imply 15 accurate resumes.
