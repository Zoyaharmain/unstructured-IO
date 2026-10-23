# Two-resume field-reference evaluation - v1

No API/DeepSeek calls were made. Exactly Aditya and Manjunath were replayed locally;
the full350 experiment was not rerun. No production mapping logic was changed.

## Findings and label provenance

The user reports checking both PDFs, but no new field-by-field corrections or
approval notes were supplied. A PDF review statement does not approve the predicted
JSON. The existing `ground_truth/needs_review/Aditya_vashisth.json` explicitly says
`human_verified: false` and contains section annotations; it is not a verified
field-level reference. No candidate-specific Manjunath approval file was found.

Separate versioned references were created in
[ground_truth/field_level/v1](../../ground_truth/field_level/v1/README.md).
Manjunath's reference contains only six expected fields explicitly supplied in the
earlier conversation, with that narrow provenance, independent exact source offsets,
parent section and record selector. This is not a new PDF-review sign-off. Aditya's
reference has zero verified fields and is explicitly pending. Predictions are saved
separately; none was copied into the references as an expected value.

| Resume | Explicit expected fields | Exact matches | Discrepancies | Field exact-match rate |
|---|---:|---:|---:|---|
| Manjunath | 6 | 6 | 0 | 6/6 (100%), only those prior user expectations |
| Aditya | 0 | Not scored | Not established | null |

The six Manjunath fields are personal_information.full_name = Manjunath MURUGAN;
personal_information.location = Noisy-le-Grand, France; language = English and
its proficiency = Full Professional Proficiency (C1); language = Français and its proficiency = Débutant (cours intensif en cours). Language records are matched
by their language value, not array position. Full exact Unicode expected values
and per-field comparisons are in [Manjunath evaluation](manjunath-murugan/evaluation.json).

No incorrect, missing, incorrectly grouped or incorrectly associated field is
established by these six labels. That does not mean the remaining fields are correct
or complete. Precision, recall and F1 remain null because exhaustive positive,
negative and omission labels are unavailable. These two development resumes and
six narrow expectations cannot validate employment, education, project or
certification accuracy, nor support a population-level readiness claim.

## Review worksheets and pending decisions

- [Aditya worksheet](aditya-vashisth/comparison-worksheet.html): 138 field/residual rows.
- [Manjunath worksheet](manjunath-murugan/comparison-worksheet.html): 92 field/residual rows.

Each folder also contains `comparison-worksheet.json`, `comparison-worksheet.csv`,
`source-text.txt`, `prediction.json`, `sections.json` and `evaluation.json`.
Worksheets show the source record text, current output, predicted record context,
exact evidence, unresolved attributes and residual/unassigned material. Predictions
and quoted source text are review aids, not approvals. JSON/CSV has blank decisions,
expected values, correct parent, record association and reviewer-evidence fields.
Add rows for omitted fields or records. Browser edits in HTML are temporary; use
JSON/CSV for durable decisions. Absence of a decision is never a negative label.

[Review priorities](review-priorities.json) records outstanding questions, not new
confirmed defects: Aditya's abbreviated completion years, partial TechTree title,
certification cardinality/duplicates and project associations; Manjunath's job,
date, duty and education associations beyond the six supplied fields. The current
mapper explicitly flags both Aditya education completion years for review.
No new regression test or production fix was invented for an unconfirmed finding.
Existing source-based defect and URL tests remain unchanged.

## Source identity and latest outputs

The originals are in `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/`:

| PDF | SHA-256 | Latest post-fix hierarchical output |
|---|---|---|
| `Aditya vashisth.pdf` | `fe64256cc650e0d0ab5f040d346205787f3459ca0ef38609552ef2baa830b7f2` | `reports/project-url-fix-20261024/offline-replay/03/schema.json` |
| `_ManjunathMurugan.pdf` | `a0a6ce21e0843824a33c748fd29b4b64d6747311a721ae43b2812e007128351d` | `reports/project-url-fix-20261024/offline-replay/02/schema.json` |

Original bytes match the frozen selection hashes. Reused fixtures are
`tests/fixtures/hierarchical_defects/02.json` and `03.json`; existing regressions
are in `tests/test_saved_hierarchical_defects.py`. Replay uses original saved
extraction and reviewed placements, rebuilds source rows/record groups with the
current production mapper, and validates source ownership and nested evidence.
It does not rerun extraction, model section detection or DeepSeek.

## Verification and reproducibility

- **285 relevant offline tests passed**; see [regression-tests.txt](regression-tests.txt).
- Both replayed `data` and `section_schemas` exactly match the latest post-fix outputs.
- Both outputs pass schema and source/evidence validation. These are structural
  checks, not field correctness metrics.
- **3,973 protected files unchanged**, including original PDFs, frozen runs,
  prior350 artifacts, references and reused fixtures; see [summary.json](summary.json)
  and `preservation-before.json`.
- Socket connections and provider entry points were prohibited. Zero provider
  calls and zero incremental provider cost. No old reports or existing gold labels
  were edited.

New work consists of `scripts/evaluate_manual_two_fields.py`, two separate reference
JSON files and their README under `ground_truth/field_level/v1`, and this new report
folder. Existing tests, fixtures and production mapper files were not changed.

Executed from `/home/zoyaharmain/unstructured-IO`:

```bash
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 /home/zoyaharmain/venv312/bin/python scripts/evaluate_manual_two_fields.py --references ground_truth/field_level/v1 --output reports/manual-field-review-20261024-v1
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 /home/zoyaharmain/venv312/bin/python reports/hierarchical-defect-replay-20261023-231542/run-regressions.py
```

The evaluator refuses to overwrite an existing run. A future run must use a new
output directory. Keep v1; create v2 only from explicit reviewer decisions.

## Next step

Record the two PDF reviews in the worksheets, including expected parent and record
associations and any missing fields. Then create the next reference version and
score those decisions offline. No larger evaluation or paid batch is recommended
on the basis of the current label coverage. This phase stops here.
