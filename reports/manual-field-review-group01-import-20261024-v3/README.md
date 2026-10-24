# Group 01 imported; Group 02 ready

Validated the exact supplied download `group-01-reviewed-2026-10-24T09-54-57.555Z.json` (SHA256 `97bc43d9eb17fee99e31bf94cfe0553ea6b6375252df8b4a3be91e265a962979`). The unmodified received bytes are retained in `received-group-01.json`.

## Imported decisions

All six rows contained an explicit `correct` decision, reviewer name, timezone-aware review timestamp, expected value, parent, record association and exact nonempty source quote. Each belongs to the Group 01 whitelist; no unknown/duplicate IDs occurred. Each confirmation exactly matches the displayed tuple and each quoted block was checked against the frozen extraction-bound source spans. The declared reviewer name is retained as provided; this is not independent identity authentication or a fresh PDF recheck.

| Row | Resume | Explicitly approved field |
|---|---|---|
| A001 | Aditya Vashisth | personal_information.full_name |
| A002 | Aditya Vashisth | personal_information.email |
| A003 | Aditya Vashisth | personal_information.phone |
| M002 | Manjunath Murugan | personal_information.email |
| M003 | Manjunath Murugan | personal_information.phone |
| M005 | Manjunath Murugan | personal_information.linkedin_url |

The new immutable reference version is `ground_truth/field_level/v3`. Aditya now has 3 explicit field labels. Manjunath has 3 newly approved labels plus his 6 unchanged prior user expectations. The older six retain their original provenance and are not relabeled as Group 01 approvals. Each new label points to the exact decision file/hash, reviewer/timestamp, row ID, parent, record selector, source quote and frozen extraction/section hashes.

V1, v2, their worksheets, predictions and prior reports remain unchanged. Working copies here contain **6 explicit decisions and 224 pending rows**. The pending rows have no inferred expected values or approvals. Original PDF paths recorded in the historical references are unavailable in this environment, so quote validation used the frozen source elements; source provenance states that limit explicitly. No API calls, production changes, mapping replay, or new accuracy score were made.

## Group 02

Open **group-02.html** in a browser. It displays original saved record text, current mapped values, parent/record context and proposed evidence for five Aditya fields:

| Row | Field | Current mapped value |
|---|---|---|
| A004 | location | unresolved |
| A005 | linkedin_url | linkedin.com/in/aditya-vashisth |
| A006 | github_url | github.com/av525 |
| A007 | portfolio_url | unresolved |
| A008 | professional_title | Engineering Lead |

All current parent/record assignments are `personal_information` / `personal_information`. All five start unreviewed. Empty mapped values are not evidence of absence.

Use Confirm displayed, Correct, Verified absent, or Uncertain as appropriate. **Verified absent requires an empty expected-value list, an explicit original-PDF check, record/parent association and a written scope note**. The exported absence record identifies the document's declared source hash; it does not fabricate an absence quote. Any optional context quotes must still match their original blocks. Uncertainty is kept separate from verified labels.

After reviewing, click **Download reviewed decisions (JSON)** or CSV. Save the downloaded file and provide its path. Browser selections alone are not durable. Unreviewed rows are omitted from the download, not counted as correct/incorrect. Files have a `group-02-reviewed-...` name. Downloads do not automatically change ground truth.

Editable full JSON/CSV copies are in the two document subdirectories. `group-02.json` is the small group's initial, still-pending worksheet. `review-plan.json` retains the future group order.

## Validation

- 13 offline import regression tests passed, including duplicate/foreign rows, missing reviewer/timestamp, wrong quotes, unsupported values, incorrect confirmation tuples, omitted-row counts and pending-row preservation.
- Group 02 browser behavior checks passed: no implicit decisions, no inferred absence, required absence scope/checkbox, pending rows omitted, initial worksheet state unchanged.
- `summary.json` records import counts; these are review-progress counts, not prediction-accuracy metrics.
- `preservation.json` records hashes of protected v1/v2 references, prior working reports, production files, fixtures, latest prediction artifacts and the original download. No protected file changed.
