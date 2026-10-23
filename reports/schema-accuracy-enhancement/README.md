# Resume schema assignment enhancements

The local section detector now preserves exact known headings across PDF word cuts,
recognizes irregular letter spacing and common heading variants, and gives explicit
section structure precedence over weak semantic heading matches. Record labels such
as Objective and Tools and Technology stay inside their job/project context.
Programming-language lists are distinguished from spoken languages. Explicit paragraph
ownership survives PDF line-hint changes between layout lanes.

Job grouping uses available source geometry and avoids treating responsibility
fragments marked as Title by the PDF extractor as separate employers.

A shared record-local mapper supports explicit label aliases for contact details,
employment, education, projects, certifications, awards, publications, volunteering,
languages, and references. It handles common date formats and unambiguous three-part
employment headers. Conflicting scalar labels are cleared; reversed date ranges and
multiple date ranges are flagged. Candidate names are not taken from contact-only rows.
Legacy schema and nested attributes share these refinements. Each populated nested
value retains exact source evidence within its own record.

## Verification

- 154 relevant regression tests passed.
- 200 saved source documents passed replay checks for schema validity, record-local
  evidence, and unchanged requests. This measures compatibility, not field accuracy.
- On the 15 existing human-labeled documents (81,352 scored non-whitespace characters),
  local section ownership accuracy increased from 54.26% to 70.83% (+16.58 percentage points).
- 6 documents improved, 0 regressed, and 9 were unchanged. Per-document results,
  confusion matrices, and per-category precision/recall/F1 are included in the JSON files.

## Measurement limits

This 15-document set was used during development, so its score is not an unseen
benchmark or an overall accuracy guarantee. Two of the 15 documents have entirely
correct section ownership; 13 still contain section errors. Complex tables, mixed
columns, unheaded sections, and ambiguous associations still need review.
The human labels cover section ownership, not subfield values or OCR correctness;
subfield accuracy remains unmeasured. Field-completion counts must not be reported
as accuracy. No source files or ground truth were rewritten and no provider calls
were made by this evaluation.

## Repeat the evaluation

```bash
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 /home/zoyaharmain/venv312/bin/python scripts/evaluate_local_schema_accuracy.py --source ground_truth/recovery_pilot/source --truth ground_truth/gold/gold_resumes.jsonl --output reports/schema-accuracy-enhancement/recheck.json
```

Reprocess resumes through section detection and schema mapping to refresh saved output.
