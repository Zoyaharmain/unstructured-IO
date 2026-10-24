# Resume field review — pending decisions, group 01

No new accuracy evaluation was run. All 230 worksheet rows remain unreviewed. The statement that the PDFs were inspected does not approve system predictions.

- v1 references, previous reports, fixtures and production mapping code are preserved.
- `ground_truth/field_level/v2` retains exactly Manjunath's six prior user-supplied expectations with their existing field/provenance objects. They are not new PDF-review approvals.
- Aditya still has zero verified field labels. No expected values were copied from predictions into ground truth.
- `decision-audit.json` records that the old JSON has 138 + 92 pending rows and CSV decisions/evidence are blank.
- Current outputs were read from `reports/project-url-fix-20261024/offline-replay/{03,02}/schema.json`; their `data` and `section_schemas` match the existing comparison predictions. They were not regenerated or rescored.
- Original PDF paths recorded in v1 are unavailable in this environment. Source text below comes from frozen extraction artifacts; compare it with your original PDFs. The six prior evidence intervals were checked against those saved elements, not independently against PDFs.

## Start with six fields

Open `group-01.html` in a browser. It displays the exact original saved record text, the current mapped value, parent, record ID and proposed evidence for:

| Row ID | Resume | Field |
|---|---|---|
| A001 | Aditya Vashisth | personal_information.full_name |
| A002 | Aditya Vashisth | personal_information.email |
| A003 | Aditya Vashisth | personal_information.phone |
| M002 | Manjunath Murugan | personal_information.email |
| M003 | Manjunath Murugan | personal_information.phone |
| M005 | Manjunath Murugan | personal_information.linkedin_url |

All belong to the current `personal_information` record named `personal_information`. That association is a prediction to inspect, not an automatic approval. Manjunath's name/location and English/French expectations are already retained with their prior provenance; no new sign-off is inferred for them.

## Save decisions durably

Choose one workflow:

1. **Browser:** enter your reviewer name, then choose Confirm displayed / Correct / Uncertain for each reviewed row. Confirm explicitly approves the displayed value, parent, record and source quote together. Correct lets you edit those details. Uncertain is retained as uncertainty, not converted to truth. Click **Download reviewed decisions (JSON)** or **CSV**, save the downloaded file, then provide its saved path. Pending rows are omitted. Downloads have timestamped names and do not update ground truth automatically. Closing the page before downloading loses browser edits.
2. **VS Code:** edit the new `aditya-vashisth/comparison-worksheet.json` or CSV and the corresponding Manjunath copy in this directory. Set the explicit decision, expected values, expected parent, expected record association, reviewer evidence and reviewer name, then save with Ctrl+S. Prefer editing one format and giving its path rather than independently editing both. Predictions and source suggestions must stay separate from your expected labels. Keep unsaved/pending rows unreviewed.
3. **Chat:** reply using the row IDs, e.g. `A001 correct`, `A002 corrected: ...`, or `M005 unsure: ...`. “Correct” must mean you approve the displayed tuple including source evidence and association. Those explicit decisions can then be saved to a new decision file. No rows are approved by silence.

The six-row JSON is `group-01.json`. Full editable JSON/CSV working copies contain all original rows, unique row IDs, blank expected fields and review-group IDs. The old v1 worksheets are not the editable copies for this session. The browser export uses the same reviewer field names plus document/row IDs, making it joinable to the full worksheets.

## Prioritized next groups

`review-plan.json` lists 51 small groups of at most six rows. After the introductory contact group, each field group stays within one document, parent and record:

1. Remaining personal information for Aditya and Manjunath, including professional title and any genuinely absent optional fields.
2. Employment headers: employer, job title, start/end date, duration and location, one position at a time. Duties and technologies are a separate small group. Review Aditya's TechTree title/source-prefix ownership carefully; this is an open question, not a new confirmed defect. Manjunath has four jobs whose associations need explicit review beyond the retained six expectations.
3. Education: institution, degree, specialization, years and grade, one qualification at a time. Aditya's printed `2018-21` / `2013-17` ranges need an explicit reviewer decision; do not infer full completion years from predictions. Manjunath's MBA and commerce qualifications require their own institution/date decisions.
4. Remaining skills, projects, certifications, languages, residual and unassigned source. Explicitly add source-backed rows for genuinely omitted fields/records; unreviewed optional fields are not verified absences.

This priority order does not approve any value or record. We will finish one small group before moving to the next. No additional batch, production/evaluation mapping replay, PDF extraction or API call was started. Regression tests exercise saved source fixtures offline without publishing new resume accuracy scores.

## Checks

56 offline regression tests passed: pending/approval separation, invalid evidence, v1/v2 preservation, group IDs, existing source/field refinement and defect tests. These are software checks, not field accuracy scores. The browser behavior test checks that a named reviewer and explicit decision are required, pending rows are omitted from downloads, wrong quotes are rejected, uncertainty stays unresolved and initial rows are unchanged.

`preservation.json` records the final hash check of pre-existing reports, v1 references, fixtures and production files. New working copies and v2 files are intentionally separate.
