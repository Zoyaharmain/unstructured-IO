# Group 01 revalidation and employment Group 02

Six explicit `correct` decisions accepted; zero rejected; zero uncertain in the submitted file. Reviewer name on every row: **Aditya Vashisth** (self-declared). Review timestamps are preserved exactly in validation-results.json. The file is the same one already imported into v3, so v4 retains these labels once and adds zero labels. Previous references and reports remain unchanged.

| Row | Resume | Field | Explicit expected value | Exact cited source |
|---|---|---|---|---|
| A001 | aditya-vashisth | full_name | Aditya Vashisth | e0:16:31: Aditya Vashisth |
| A002 | aditya-vashisth | email | avmsv1996@gmail.com | e20:164:184: avmsv1996@gmail.com |
| A003 | aditya-vashisth | phone | +91 7982016518 | e20:150:164: +91 7982016518 |
| M002 | manjunath-murugan | email | manjunathmurugan50@gmail.com | e1:0:77: manjunathmurugan50@gmail.com |
| M003 | manjunath-murugan | phone | 9176398910 | e1:0:77: 9176398910 |
| M005 | manjunath-murugan | linkedin_url | www.linkedin.com/in/profilemanjunathmurugan | e1:77:120: www.linkedin.com/in/profilemanjunathmurugan |

All six decisions explicitly name parent `personal_information` and record association `{"kind":"record_id","value":"personal_information"}`. Each parent/attribute is defined, the record exists under that parent in the saved current hierarchy, each citation belongs to that record, each quote occurs exactly in the cited block and contains its expected value. The six correct decisions match the saved mapped tuples and prior v3 references. No citation was inherited or inferred. JSON and CSV validation files record each decision and the reason for acceptance.

Validation is against the frozen extracted text and saved section intervals, which passed integrity checks. Original PDF paths are unavailable here; no fresh visual PDF verification or identity authentication was performed. Declared PDF hashes are provenance, not freshly checked PDF hashes. Presence of text and record membership supports these submitted personal fields, not correctness of unreviewed records.

v4 contains 12 reference fields: Aditya 3 and Manjunath 9. Six of Manjunath's fields retain their earlier explicit-user-expectation provenance unchanged; they are not newly approved PDF decisions. All 224 pending rows retain null expected values/parents/associations and empty reviewer evidence. No new accuracy score or whole-resume approval is implied.

## Next manual review: Group 02 employment

Open **group-02.html** in this directory. Review Aditya's Persistent Systems record (`experience-1`, parent `experience`) in six rows: A064 company, A065 role, A066 start date, A067 end date, A068 duration, A069 location. This keeps one employment record together. Saved header source `e12:647:706` reads:

> Engineering Lead | Persistent Systems | Apr 2022 - Present

Current values are Persistent Systems, Engineering Lead, Apr 2022, Present, Apr 2022 - Present, and an unresolved empty location. The page shows full saved record text, proposed field-specific evidence, current parent/record, and controls for corrections or uncertainty. These are predictions, not approvals. Do not infer a location from a different job or personal address, or interpret “Present” as a newly verified current-employment claim. The older personal-information Group 02 page remains preserved; this new session is specifically the requested employment review.

Every row starts pending. Enter your reviewer name, explicitly confirm/correct individual rows or mark uncertainty with notes, then download JSON (preferred) or CSV. Verified absence requires checking the original PDF and recording scope; an empty model field alone does not establish absence. Downloads are durable separate files; browser selections alone are not saved. Share the downloaded file path for validation. Session-specific filenames distinguish this Group 02 from the previous personal-field page. No labels from Group 02 are incorporated until you review and submit them.

No DeepSeek/API calls, production mapping changes, extraction/block detection, or previous 350-resume experiment were run. Work stops here for manual review.

## Offline validation checks

17 Python regression checks passed; the Group 02 JavaScript behavior check passed. Coverage includes repeated-import preservation, wrong parent/record/citation rejection, 224 pending rows left unreviewed, explicit form decisions, uncertain values left null, and session-tagged JSON downloads. See test-results.json for exact commands. Preservation hashes confirm 2,045 protected files unchanged.
