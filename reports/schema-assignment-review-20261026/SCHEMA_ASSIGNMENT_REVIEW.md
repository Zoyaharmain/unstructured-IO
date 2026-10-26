# Schema assignment review and repairs

Review date: 26 October 2026 (Asia/Kolkata).

The schema pipeline is improved, but it is not universally correct. This review covered detection, recovery, record grouping, typed mapping, hierarchical citations, coverage reporting, API contracts, and the schema UI. It re-evaluated the existing 15 labelled documents and ran the project test suite; it did not reprocess the entire historical corpus.

## Measured results

| Measurement | Before | After |
| --- | ---: | ---: |
| Section ownership accuracy, all 15 documents | 77.98% | 91.39% |
| Section ownership accuracy, 14 candidate resumes | 78.92% | 93.07% |
| Section ownership micro F1 | 78.58% | 92.73% |

These are non-whitespace extracted-character section labels, validated against source hashes. They are not OCR accuracy or field-value accuracy. The candidate-only baseline above is recalculated from character totals; the earlier recovery report's 80.30% figure does not reproduce from these totals.

6 documents improved, 8 were unchanged, and 1 regressed in section labels. The regression is the job description, whose candidate fields remain empty and whose candidate schema is not applicable.

| Document | Before | After | Change (percentage points) |
| --- | ---: | ---: | ---: |
| Pavan Bakku.pdf | 76.64% | 99.68% | +23.04 |
| Ajay Bandagi.pdf | 88.16% | 88.16% | +0.00 |
| AkshayPatni (1).pdf | 100.00% | 100.00% | +0.00 |
| Prasad PR.pdf | 88.68% | 88.68% | +0.00 |
| Anuradha Yadav.pdf | 84.34% | 84.34% | +0.00 |
| Java Aws backend.pdf | 32.09% | 8.77% | -23.32 |
| GAURAVAGRAWAL.pdf | 86.87% | 86.87% | +0.00 |
| Charansai P.pdf | 53.23% | 88.43% | +35.20 |
| Alvina _Fernandes.pdf | 94.98% | 100.00% | +5.02 |
| Nikhil Kumar.pdf | 100.00% | 100.00% | +0.00 |
| Rutuja Herekar.pdf | 82.84% | 82.84% | +0.00 |
| S  Abhinav.pdf | 90.94% | 95.61% | +4.67 |
| A Suribhotla.pdf | 99.71% | 99.71% | +0.00 |
| NagaVishnu.pdf | 67.04% | 87.52% | +20.48 |
| PUPPYKUMARI.pdf | 45.33% | 96.70% | +51.37 |

## Repairs

- Added structural heading recognition for achievements, independent projects, academic details, IT skills, and employment project/role sections.
- Prevented project names such as “Training App” and technology prose such as “Microsoft Projects” from opening unrelated sections during recovery.
- Restored professional engagement context after skills when explicit role, project, client, and preceding experience evidence exist. Clients are not inferred to be employers.
- Prevented dated awards and certificates from opening employment records.
- Preserved source entry IDs when empty records are removed. Legacy array indexes, field evidence, nested records, and record bindings now move together.
- Checked source candidates across all sections before declaring contact fields absent. Conflicting labels receive ambiguous status, and record coverage includes optional child fields with record-local evidence.
- Displayed unmapped and ambiguous field counts in the UI.
- Corrected the evaluator's measurement description and removed its forced human-verification flag. Each new evaluation saves inspectable sections and schema output.

Existing `/api/v1/resume/sections`, `/api/v1/resume/schema`, and `/api/v1/resume/schema/query` use these fixes. Optional configured DeepSeek section review remains available through the existing review flow; no external provider calls were made during this review. Source-bound schema mapping itself remains deterministic.

## Verification

- Full project suite: **490 passed** in 132.31 seconds, including in-process HTTP contracts, local models, extraction, and mocked provider behavior. The sandbox HTTP client hung at startup; the complete suite passed outside the sandbox.
- After the final phone-candidate guard change: focused mapping/hierarchy/source/model checks: **52 passed**, 3 API tests deselected (those had passed in the full suite).
- Added seven regression tests covering stable record identity, citation reindexing, wrong-section contacts, ambiguous labels, optional child statuses, heading boundaries, professional engagements, and project context.
- Existing partial human field references: **17/17 exact matches** against frozen extracted source. Source quotes were checked. Original PDF paths referenced by the older evaluator are unavailable on this machine, so this replay does not claim fresh PDF verification or whole-document field accuracy.
- JavaScript syntax, Python compilation, and `git diff --check` passed.

## Remaining limitations

Several resumes still contain incorrect or unresolved assignments. Mixed awards/certifications, heading-free content, complex education tables, and record association require further source review. A section can be correctly classified while individual fields remain unresolved. The 17 field references are partial; they cannot establish exhaustive field precision or recall.

The job description's section score fell from 32.09% to 8.77%; it is out of scope for a candidate resume schema, and its candidate fields remain empty. This regression is retained in the all-document metric rather than hidden. No historical source artifacts or human labels were changed. Existing saved outputs must be reprocessed to receive the new mappings.

## Reproduction and evidence

```bash
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/evaluate_field_level_accuracy.py --output-dir reports/schema-assignment-review-20261026/recheck
.venv/bin/python reports/schema-assignment-review-20261026/replay_verified_fields.py
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q
```

- [Before metrics](before/field_level_evaluation.json)
- [After metrics](after/field_level_evaluation.json)
- [Comparison](comparison.json)
- [Per-document sections and mappings](after/documents/)
- [Partial field-reference replay](verified-fields/summary.json)
