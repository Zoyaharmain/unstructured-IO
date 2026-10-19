# Fifteen-resume recovery investigation and live rerun

## What was actually wrong

The dashboard conflated local-versus-LLM disagreements with unassigned content. All 15 historical cached DeepSeek outputs already had zero unassigned spans. PUPPYKUMARI’s 301 uncertain spans were local/LLM disagreements, not missing assignments. Such disagreements still require human review; they were not erased.

Draft generation also projected reviewed spans onto old local boundaries by exact offset equality, losing split decisions; defaulted unresolved text to Experience; treated any standalone number as an artifact; invented generic work/education field values; and used filenames alone as cache identity. Production supplied all spans but omitted full original elements/layout and record context from its review prompt. Its successful review status meant valid decisions, not complete semantic recovery.

## Changes

- Full source elements, span evidence, coordinates, and record hints now accompany all assigned/unassigned spans.
- Source accounting validates contiguous exact coverage and gives each span an assigned, artifact or human-review outcome. Single-letter skills remain meaningful. No duplicate text is silently excluded.
- Invalid/incomplete decisions get bounded retries; meaningful unresolved content gets a full-context follow-up. DEEPSEEK_RECOVERY_ATTEMPTS is configurable from 0 to 3 (default 1). Network/auth/balance errors are not automatically retried. A failed follow-up preserves the last valid review.
- Draft projection uses the union of boundaries and containing intervals, preserves LLM splits, keeps unresolved content as needs_review, and separates disagreement counts.
- Unknown record fields stay blank; record proposals retain source header evidence rather than fabricated employer/title values.
- New cached drafts bind to extraction hashes; legacy cached results are explicitly marked as having incomplete configuration provenance and still require exact source validation.
- Bulk triage now uses final candidate coverage rather than stale local coverage. No bulk expansion was run.

## Live result

- 15/15 actual DeepSeek reviews completed; 16 classification requests.
- Meaningful unassigned spans: 158 locally → 0 after review.
- Exact extracted-source preservation: 15/15. Source PDF hashes match the original selection for 15/15.
- Actual usage: 395,564 input tokens and 12,227 output tokens. No cost was invented from assumed pricing.
- 155 tests passed; 8 upstream parity tests deselected.

| Resume | Local meaningful unassigned | After live review | Changed assignments | API calls | Artifacts |
|---|---:|---:|---:|---:|---:|
| Pavan Bakku.pdf | 0 | 0 | 27 | 1 | 0 |
| Ajay Bandagi.pdf | 7 | 0 | 9 | 1 | 0 |
| AkshayPatni (1).pdf | 1 | 0 | 1 | 1 | 0 |
| Prasad PR.pdf | 3 | 0 | 23 | 1 | 0 |
| Anuradha Yadav.pdf | 14 | 0 | 14 | 1 | 0 |
| Java Aws backend.pdf | 5 | 0 | 31 | 2 | 1 |
| GAURAVAGRAWAL.pdf | 1 | 0 | 12 | 1 | 0 |
| Charansai P.pdf | 1 | 0 | 56 | 1 | 0 |
| Alvina _Fernandes.pdf | 0 | 0 | 9 | 1 | 0 |
| Nikhil Kumar.pdf | 1 | 0 | 1 | 1 | 0 |
| Rutuja Herekar.pdf | 13 | 0 | 36 | 1 | 0 |
| S  Abhinav.pdf | 3 | 0 | 121 | 1 | 8 |
| A Suribhotla.pdf | 1 | 0 | 1 | 1 | 1 |
| NagaVishnu.pdf | 81 | 0 | 180 | 1 | 2 |
| PUPPYKUMARI.pdf | 27 | 0 | 335 | 1 | 6 |

## Classification and grouping limits

Against the unchanged existing gold files, non-whitespace character label agreement is 58.50% locally and 97.23% after review. 7/15 final resumes match every scored label; 15 improved relative to local and 0 regressed. These numbers are conditional on those reference labels, not independently verified accuracy.

The gold promotion script can mark drafts human_verified without explicit corrections, and its existing log records no explicit corrections for these 15. That does not prove nobody reviewed them, but independent human verification cannot be established from these files. Gold files were not modified. Original PDF word/OCR accuracy was not measured by source-span reconstruction.

Work/education entry counts before/after are included in the CSV, but count equality does not prove employer/title/date or degree/institution relationships. Production record grouping remains structure-based and these relationship proposals still require human verification. No relationship-accuracy improvement is claimed. The zero-unassigned result also does not resolve local/LLM disagreements; 678 remain visible in the new live-review drafts.

## Review files

- `ground_truth/recovery_pilot/live-review/index.html`: normal source-span/category/record review; unverified drafts, not gold.
- `ground_truth/recovery_pilot/live/documents/`: original extraction, local output and final reviewed output for the same 15 sources.
- `ground_truth/recovery_pilot/per-resume-report.csv`: per-resume source accounting, actual API calls, retries and grouping counts.
- `ground_truth/recovery_pilot/evaluation/`: conditional comparison against existing labels.
- `python scripts/check_pilot_recovery.py`: replay legacy caches without API calls.
- `DEEPSEEK_RECOVERY_ATTEMPTS=1` controls production retry budget.

No gold annotations were promoted or changed. No 1,500-resume expansion was started. This pilot is a development regression set, not an unbiased held-out performance benchmark.

## Comparison with the previous LLM output

The pre-existing cached LLM comparison reported 99.92% agreement and 9 exact resumes against these same reference files. The fresh context-rich review has 97.23% agreement and 7 exact resumes: a **2.69 percentage-point decrease against those labels**, not an accuracy improvement over the old LLM run. It improves over the local baseline, but this does not establish superior semantic accuracy over the previous LLM prompt. Reference provenance needs independent confirmation before judging the difference as a real quality regression or improvement. No labels were edited to favor the new result.

A final record-boundary check found generic Title fields (Organization, Designation, Duration) and embedded project labels being counted as employers after reassignment. These no longer start work records merely because they are Title elements; stale local context IDs no longer force separate jobs in reviewed output. Final entry boundaries were rebuilt from the same validated provider decisions without additional API calls; the pre-rebuild outputs are preserved under `ground_truth/recovery_pilot/before-entry-rebuild/`. Field identities and relationships remain proposed, with unknown values blank, and have not been independently scored.
