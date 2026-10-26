# Resolved history grouping and duplicate scalar representation

The user supplied recovered history entries:
- 34f5d305991144828237dd909fa73c4f: invalid_or_cross_record_quote, soft_skills.
- ab2683ea165541b69a0a650eefd979ec: scalar_multiple_values, name.

Both displayed entries are recovered diagnostics. They are not sufficient to
establish a current failure, the final status, or whether a scalar name was a
literal duplicate versus distinct conflicting names. No live provider body was
retained and no paid request was made to reproduce it.

Changes:
- static/schema.js groups all recovered diagnostics under one closed processing
  history group, explicitly explaining final validation and directing users to
  current status for remaining findings. Detailed original diagnostics remain
  inspectable, and active failures remain separate and open.
- llm_schema_mapping.repair_literal_citation now recognizes identical scalar
  duplicate items for eligible fields such as certificate name. It retains all
  distinct citations, deduplicates only exact values of the same type, and
  executes full existing schema/evidence validation. Different values retain
  the existing truncation audit and require-review status; no arbitrary name
  conflict is falsely labeled a lossless correction.

Regression tests cover the actual JavaScript history renderer with a minimal
DOM, multiple recovered entries grouped/collapsed, active failure visibility,
identical certificate-name duplicates, and distinct names requiring review.
Validation remains enabled. Original fixtures and other existing changes are
preserved. No paid provider calls were made.

Verification: 98 focused tests plus 4 API tests passed (102 total). JavaScript
syntax and git diff --check passed. Backend auto-reload confirmed in server
logs; browser refresh loads the updated history grouping.
