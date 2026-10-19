# Formal validation of 15 pilot documents

**Acceptance decision: NOT READY.** No production fixes, label changes, gold promotions, new DeepSeek requests or bulk processing were performed. This report is an assistant audit, not human approval.

## Scope and evidence

Inspected rendered pages for all 15 PDFs (43 pages), together with independent Poppler pdftotext -layout output and saved extraction/section/entry membership. Rendered original pages and complete diagnostic text are saved in each artifact-ID subdirectory. This is page-level inspection plus exact saved-span checks, not a certified word-for-word human transcription. PASS requires evidence for the complete relevant dimension; an absence of detected defects or parser agreement does not earn PASS.

All 15 source SHA256 hashes match the selected manifest and pilot copies. All 15 recovered extraction inventories and embedded local section results exactly match the saved earlier local artifacts. Every rendered page has saved extraction elements. This proves page presence and artifact linkage, not complete PDF text capture. No local, saved recovery, original draft, live-review draft or legacy gold JSON was missing. All 45 annotation extraction hashes match the saved inventories; independent source-PDF hashes/approval evidence are not uniformly recorded in annotations. See artifact-inventory.json and annotation-bindings.json.

## Per-document verdicts

| Document | Pages | Extraction fidelity | Block/relationship quality | Meaningful unassigned local → recovered |
|---|---:|---|---|---:|
| Pavan Bakku.pdf | 1 | INCONCLUSIVE | FAIL | 0 → 0 |
| Ajay Bandagi.pdf | 1 | FAIL | FAIL | 7 → 0 |
| AkshayPatni (1).pdf | 2 | INCONCLUSIVE | FAIL | 1 → 0 |
| Prasad PR.pdf | 2 | INCONCLUSIVE | FAIL | 3 → 0 |
| Anuradha Yadav.pdf | 2 | INCONCLUSIVE | FAIL | 14 → 0 |
| Java Aws backend.pdf | 2 | INCONCLUSIVE | FAIL | 5 → 0 |
| GAURAVAGRAWAL.pdf | 2 | FAIL | FAIL | 1 → 0 |
| Charansai P.pdf | 3 | INCONCLUSIVE | FAIL | 1 → 0 |
| Alvina _Fernandes.pdf | 3 | INCONCLUSIVE | FAIL | 0 → 0 |
| Nikhil Kumar.pdf | 3 | INCONCLUSIVE | FAIL | 1 → 0 |
| Rutuja Herekar.pdf | 3 | INCONCLUSIVE | FAIL | 13 → 0 |
| S  Abhinav.pdf | 4 | INCONCLUSIVE | FAIL | 3 → 0 |
| A Suribhotla.pdf | 4 | INCONCLUSIVE | FAIL | 1 → 0 |
| NagaVishnu.pdf | 5 | INCONCLUSIVE | FAIL | 81 → 0 |
| PUPPYKUMARI.pdf | 6 | INCONCLUSIVE | FAIL | 27 → 0 |

**Extraction: 0 PASS, 2 FAIL, 13 INCONCLUSIVE. Block/relationship quality: 0 PASS, 15 FAIL.** FAIL here requires an observed defect, not merely a missing human label. All 15 saved outputs have concrete broken record membership or document-scope evidence below. It does not imply every section or every span is wrong. The 13 extraction INCONCLUSIVE verdicts mean full word fidelity has not been independently established; they do not claim missing text was found in those files.

## Saved local versus saved recovery

No API request was needed for this comparison. The original live run made 16 requests; this audit made zero. All 15 live checkpoints say source_reextracted=false: recovery reused saved local extraction and detection.

- Raw needs_review blocks: 160 → 0. Meaningful needs_review spans: 158 → 0. The difference is two whitespace spans in NagaVishnu; this reconciles the earlier reported 158 with raw 160.
- Previously unassigned non-whitespace characters now assigned: 4,977. Characters whose category changed: 31,995. A changed category is not automatically a correction.
- Exact saved-source interval accounting passed 15/15: no omitted/overlapping/reworded extracted-source intervals. This cannot detect text missing before the interval inventory was built, PDF-level duplicates already extracted, or wrong semantic labels.
- At least four specific recovered spans in Rutuja are confirmed inappropriate for past employment (element64[0:123],65[0:14],70[0:35],71[0:51]); they were already Experience locally. This is a lower bound from enumerated evidence, not an exhaustive section-error count.
- Pavan Achievements remains Summary in both local and recovery; this is not a local-to-recovery regression. The older cached LLM output placed some of those bullets in Awards. Rutuja coursework remains Experience in local and current recovery, while older cached LLM classified some of it as Certifications. Confirmed source-based concern: loss of distinct achievements/training meaning; exact canonical labels need reviewer policy.
- Total semantic corrections/regressions and relationship precision/recall cannot be computed without independently approved span/record references. No numerical semantic accuracy is claimed. The prior 99.92% and 97.23% figures remain agreement with unproven references only.

## Evidence for each document

### Pavan Bakku.pdf

Pages inspected: 1. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-1 contains all four employment headers; education-2 contains only 2008–2012, separated from degree/institution. KEY ACHIEVEMENTS e12 and bullets e13 remain Summary.

Expected: Separate S&P Global/Skata/NCR/OSI records and keep education dates with the degree; explicitly decide Achievements taxonomy.

Evidence files: [b629db55549ed1bd9610/all-pages.jpg](b629db55549ed1bd9610/all-pages.jpg), [b629db55549ed1bd9610/extracted.txt](b629db55549ed1bd9610/extracted.txt), [b629db55549ed1bd9610/independent.txt](b629db55549ed1bd9610/independent.txt), [b629db55549ed1bd9610/relationships.txt](b629db55549ed1bd9610/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Ajay Bandagi.pdf

Pages inspected: 1. Severity: HIGH. Extraction FAIL; block/relationship quality FAIL.

Extraction e9/e10 repeat the same 185-word responsibilities paragraph, visible once. experience-1 contains Vigocare and Godavari; experience-2 contains their dates alone.

Expected: Remove only source-proven duplication in a new extraction version; bind each employer/title/date/responsibility record.

Evidence files: [f3b9f2a6333cad3718ac/all-pages.jpg](f3b9f2a6333cad3718ac/all-pages.jpg), [f3b9f2a6333cad3718ac/extracted.txt](f3b9f2a6333cad3718ac/extracted.txt), [f3b9f2a6333cad3718ac/independent.txt](f3b9f2a6333cad3718ac/independent.txt), [f3b9f2a6333cad3718ac/relationships.txt](f3b9f2a6333cad3718ac/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### AkshayPatni (1).pdf

Pages inspected: 1–2. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-1 includes NAV and BNP headers while experience-2 mixes continuation lines with the Northern Trust header. experience-3 contains only two bullet markers.

Expected: Keep three roles distinct, including BNP continuation across page break; artifacts must not become employment records.

Evidence files: [9a4498b27a2e14f9e3a0/all-pages.jpg](9a4498b27a2e14f9e3a0/all-pages.jpg), [9a4498b27a2e14f9e3a0/extracted.txt](9a4498b27a2e14f9e3a0/extracted.txt), [9a4498b27a2e14f9e3a0/independent.txt](9a4498b27a2e14f9e3a0/independent.txt), [9a4498b27a2e14f9e3a0/relationships.txt](9a4498b27a2e14f9e3a0/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Prasad PR.pdf

Pages inspected: 1–2. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

Education-1 combines Liverpool, IIIT-B and JSS; education-2 holds the MSc degree alone. e4 PGSQL [784:789] is cut at 787 into PGS/QL in both outputs; both pieces remain Skills.

Expected: Keep three degree/institution/date/grade relationships distinct; prevent boundaries inside a skill word. Raw extraction has intact PGSQL.

Evidence files: [6be5a73777f3dbd961a1/all-pages.jpg](6be5a73777f3dbd961a1/all-pages.jpg), [6be5a73777f3dbd961a1/extracted.txt](6be5a73777f3dbd961a1/extracted.txt), [6be5a73777f3dbd961a1/independent.txt](6be5a73777f3dbd961a1/independent.txt), [6be5a73777f3dbd961a1/relationships.txt](6be5a73777f3dbd961a1/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Anuradha Yadav.pdf

Pages inspected: 1–2. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-1 merges JPMorgan, Xiaomi and Profinch headers; experience-2 holds many detached responsibility lines. Trainee internship requires explicit association.

Expected: Retain three dated employments and associate the Profinch trainee statement separately without invented dates.

Evidence files: [e8262488bf710cf48ccb/all-pages.jpg](e8262488bf710cf48ccb/all-pages.jpg), [e8262488bf710cf48ccb/extracted.txt](e8262488bf710cf48ccb/extracted.txt), [e8262488bf710cf48ccb/independent.txt](e8262488bf710cf48ccb/independent.txt), [e8262488bf710cf48ccb/relationships.txt](e8262488bf710cf48ccb/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Java Aws backend.pdf

Pages inspected: 1–2. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

Both rendered pages are a blank requirements template. Recovered Experience contains Job title: *, No. of Positions: * and a required bachelor degree. There is no recovered Education section.

Expected: Identify as non-candidate document; request an explicit exclusion decision. Do not represent required qualifications as earned credentials.

Evidence files: [820a109ff20c21202713/all-pages.jpg](820a109ff20c21202713/all-pages.jpg), [820a109ff20c21202713/extracted.txt](820a109ff20c21202713/extracted.txt), [820a109ff20c21202713/independent.txt](820a109ff20c21202713/independent.txt), [820a109ff20c21202713/relationships.txt](820a109ff20c21202713/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### GAURAVAGRAWAL.pdf

Pages inspected: 1–2. Severity: HIGH. Extraction FAIL; block/relationship quality FAIL.

Page 2 Achievements heading is absent from extraction; e40/e41 duplicate the same awards passage visible once. experience-2 contains all three date ranges alone; education-2 combines both degree date ranges.

Expected: Version extraction to restore heading/remove proven duplicate; keep dates with TCS/client roles and each degree; GPA 8.5 belongs to the bachelor degree.

Evidence files: [45575a74b9b03bde6e54/all-pages.jpg](45575a74b9b03bde6e54/all-pages.jpg), [45575a74b9b03bde6e54/extracted.txt](45575a74b9b03bde6e54/extracted.txt), [45575a74b9b03bde6e54/independent.txt](45575a74b9b03bde6e54/independent.txt), [45575a74b9b03bde6e54/relationships.txt](45575a74b9b03bde6e54/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Charansai P.pdf

Pages inspected: 2–3. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-1 contains Engineering Manager, Principal Technologist and Senior WebLogic Administrator headers together. experience-2 combines Oracle and CGI project/domain headings.

Expected: Separate three employment records and relate Oracle/CGI responsibilities to the correct roles; determine dates only from source.

Evidence files: [035a657b54efa8e6417c/all-pages.jpg](035a657b54efa8e6417c/all-pages.jpg), [035a657b54efa8e6417c/extracted.txt](035a657b54efa8e6417c/extracted.txt), [035a657b54efa8e6417c/independent.txt](035a657b54efa8e6417c/independent.txt), [035a657b54efa8e6417c/relationships.txt](035a657b54efa8e6417c/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Alvina _Fernandes.pdf

Pages inspected: 1–3. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-1 combines Morgan Stanley and Nomura; experience-2 has their two date ranges alone. The one BMS record is split across education-1 (degree), education-2 (years), education-3 (college/grade). Spot Award is genuinely repeated in PDF pages 1 and 3.

Expected: Keep two job records and one complete BMS record. Do not automatically deduplicate the genuine repeated award mention.

Evidence files: [1c7d6d6f5b430bc2fbec/all-pages.jpg](1c7d6d6f5b430bc2fbec/all-pages.jpg), [1c7d6d6f5b430bc2fbec/extracted.txt](1c7d6d6f5b430bc2fbec/extracted.txt), [1c7d6d6f5b430bc2fbec/independent.txt](1c7d6d6f5b430bc2fbec/independent.txt), [1c7d6d6f5b430bc2fbec/relationships.txt](1c7d6d6f5b430bc2fbec/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Nikhil Kumar.pdf

Pages inspected: 1–3. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

education-1 combines BPUT degree and both CBSE qualifications; education-2 contains years 2013/2008/2006. experience-2 groups dates/locations from different employments.

Expected: Bind each of three education rows and three work records independently; distinguish employer GENPACT from client Citi Bank.

Evidence files: [c7c6de90e08c54361783/all-pages.jpg](c7c6de90e08c54361783/all-pages.jpg), [c7c6de90e08c54361783/extracted.txt](c7c6de90e08c54361783/extracted.txt), [c7c6de90e08c54361783/independent.txt](c7c6de90e08c54361783/independent.txt), [c7c6de90e08c54361783/relationships.txt](c7c6de90e08c54361783/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### Rutuja Herekar.pdf

Pages inspected: 1–3. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

Page 3 e64 coursework, e65 Topics Studied, e70 QA Applications I’m Building Toward and e71 prompt-regression plans remain Experience in local and recovered output. Education-1 merges MSc2021 and BSc2018.

Expected: Classify training/plans without claiming past employment; maintain two degree/year records, with institution absent rather than invented.

Evidence files: [b493159ea095e1581dbd/all-pages.jpg](b493159ea095e1581dbd/all-pages.jpg), [b493159ea095e1581dbd/extracted.txt](b493159ea095e1581dbd/extracted.txt), [b493159ea095e1581dbd/independent.txt](b493159ea095e1581dbd/independent.txt), [b493159ea095e1581dbd/relationships.txt](b493159ea095e1581dbd/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### S  Abhinav.pdf

Pages inspected: 1–4. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-2 combines multiple Career Commencement blocks, including IRIS and BNY Mellon, while experience-3 contains detached heading fragments. education-1 combines BTech, XII and X.

Expected: Separate seven chronological employments including two distinct BNY periods; keep four academic qualifications separately; absent years stay unknown.

Evidence files: [6a158b8a966dcc161973/all-pages.jpg](6a158b8a966dcc161973/all-pages.jpg), [6a158b8a966dcc161973/extracted.txt](6a158b8a966dcc161973/extracted.txt), [6a158b8a966dcc161973/independent.txt](6a158b8a966dcc161973/independent.txt), [6a158b8a966dcc161973/relationships.txt](6a158b8a966dcc161973/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### A Suribhotla.pdf

Pages inspected: 2–4. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-1 contains Virtusa/title/client but its Jan2022–Present date is in experience-2, which also includes later employer headers. experience-3 holds detached project/responsibility lines across employers.

Expected: Keep Virtusa/HSBC, Keolis/L&T Metro and Concentrix/Uber roles, dates, clients and responsibilities associated.

Evidence files: [455f5323879db82963ef/all-pages.jpg](455f5323879db82963ef/all-pages.jpg), [455f5323879db82963ef/extracted.txt](455f5323879db82963ef/extracted.txt), [455f5323879db82963ef/independent.txt](455f5323879db82963ef/independent.txt), [455f5323879db82963ef/relationships.txt](455f5323879db82963ef/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### NagaVishnu.pdf

Pages inspected: 1–5. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-2 merges Unlimited Innovations and Cognizant. education-1 has the BE header, but its CGPA8.07 is in education-2 with SSC. Project grouping fragments six named projects into 25 entries.

Expected: Keep three employments, six explicit named projects plus Other Project Details, and three education records linked correctly; repeat responsibility bullets genuinely present in different projects must remain.

Evidence files: [07aefd82194f852b5b38/all-pages.jpg](07aefd82194f852b5b38/all-pages.jpg), [07aefd82194f852b5b38/extracted.txt](07aefd82194f852b5b38/extracted.txt), [07aefd82194f852b5b38/independent.txt](07aefd82194f852b5b38/independent.txt), [07aefd82194f852b5b38/relationships.txt](07aefd82194f852b5b38/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

### PUPPYKUMARI.pdf

Pages inspected: 1–6. Severity: HIGH. Extraction INCONCLUSIVE; block/relationship quality FAIL.

experience-2 combines multiple employer names and project material; experience-3 isolates Designation/Duration columns. education-3 contains four degree names; education-2 contains institutions/years. PDF itself conflicts: Software Developer June2015–Jan2020 vs Cordova June2015–Aug2021; Sr Consultant Current vs later Coforge Technical Lead.

Expected: Preserve and flag both source claims; human must choose conflict treatment. Bind four career table rows and four education rows; separate project/client/role records across pages2–6.

Evidence files: [08aaa025979276b8d070/all-pages.jpg](08aaa025979276b8d070/all-pages.jpg), [08aaa025979276b8d070/extracted.txt](08aaa025979276b8d070/extracted.txt), [08aaa025979276b8d070/independent.txt](08aaa025979276b8d070/independent.txt), [08aaa025979276b8d070/relationships.txt](08aaa025979276b8d070/relationships.txt). The relationships file expands the exact entry membership for both saved configurations; it is not reconstructed by a new model run.

## Known-issue conclusions

1. **GAURAVAGRAWAL — confirmed extraction FAIL:** page2 Achievements is visible but absent from saved extraction; e40/e41 repeat one visible awards passage. Neither zero-unassigned bookkeeping nor reference-label agreement detects this.
2. **Java Aws backend — confirmed scope FAIL:** both pages are requirements, with blank candidate fields. Current recovery has Experience/Skills/Certifications, not Education. Do not claim it fabricated a recovered degree record: the real defect is candidate-semantic interpretation of requirements. Explicitly exclude or classify non-resume in a new approved pilot version.
3. **PUPPYKUMARI — confirmed source conflict and relationship FAIL:** conflicting dates are in the PDF; no automated repair can establish the true dates. Current grouping separates table columns and mixes employers/projects. Repeated responsibilities on different project pages are genuine source repetition and must not be silently removed.
4. **Rutuja — confirmed section FAIL:** explicit structured coursework and future QA applications remain Experience. Both MSc and BSc share a single recovered education entry. Institutions are not stated in that list.
5. **Pavan — confirmed boundary/grouping FAIL:** KEY ACHIEVEMENTS remains inside Summary, and four employments share one entry; degree date is detached. An explicit Achievements-to-Awards policy still requires human approval.
6. **PostgreSQL/PGSQL — confirmed saved block split:** searched every exact PostgreSQL and PGSQL occurrence in the 15 saved inventories against both configurations. The detected internal split is Prasad e4 PGSQL[784:789] at787. Both fragments belong to Skills. Source extraction contains intact PGSQL; canonical joined text can look correct while block boundaries remain broken. No exact PostgreSQL occurrence was found split in this pilot. See skill-splits.json.
7. **Ajay — additional confirmed extraction FAIL:** identical e9/e10 each repeat 185 whitespace-separated words of the same page1 job responsibilities. Page1 shows that passage once. The independent Executive token mismatch may involve word joining and is not separately declared a missing word.

## Ground truth and human decisions

All 15 legacy gold files exist and claim human_verified=true, but the verification log reports no explicit corrections, corrections/ is empty, and no source-bound independent approval bundle was found. This does not prove nobody ever looked at them; it prevents establishing independent gold provenance. No labels were promoted or edited in this audit.

Required human decisions: approve/correct every section and span boundary; identify true layout artifacts versus repeated source content; link each employer/title/date/client/responsibility and degree/institution/year/grade within an approved record; resolve or preserve source contradictions; decide canonical treatment of achievements and coursework; explicitly decide Java template exclusion; verify every page and source-text omission/duplicate finding. These audit observations cannot substitute for those approvals.

## Discrepancies in the other open validation report

The pre-existing ground_truth/validation_15_20261019/report.md is preserved. Its hash table differs from current source/selection hashes for 12 documents, starting with Prasad; it labels Anuradha a clean one-page extraction although the source and saved elements have two pages; it treats PGSQL slicing as extraction failure although raw PGSQL is intact; it claims Pavan block PASS despite merged roles; and it implies recovered Java academic records although the current saved recovery has no Education section. Do not adopt its 185/185 assertion as this audit’s result. This report uses independently read sources and newly recorded test outcomes.

## Automated tests

**Full regression: 185 passed, 0 failed, no deselections (117.96s). Targeted: 176 passed, 9 deselected (35.51s).** An earlier attempt failed collection because src/ was absent from the import path; a sandbox attempt did not complete. See [TEST_RESULTS.md](TEST_RESULTS.md) for exact commands, failures/limitations and coverage, with raw logs and JUnit XML. No source fixes were made to obtain a passing result. The runners remove DEEPSEEK_API_KEY, disable review, set Hugging Face/Transformers offline, and block non-loopback socket connections. Test fixtures are separate from the corpus; fixture processing does not rerun the pilot models or remaining collection.

## Priority and acceptance recommendation

1. P0: repair/version source extraction for Ajay and GAURAV; verify against original page images and preserve this baseline.
2. P0: repair record membership across layout lanes and table rows; equal entry counts are not association accuracy. All 15 have demonstrated grouping/scope defects.
3. P0: establish independent source-bound human approvals; exclude the requirements template and select an explicitly versioned replacement if 15 actual resumes are required.
4. P1: prevent subword block boundaries and distinguish coursework/plans from employment; decide Achievements taxonomy.
5. P1: preserve contradictory dates and genuine repetitions as source evidence; require review rather than inventing resolutions.
6. P1: add real saved-PDF acceptance cases for these defects in a future authorized implementation task. Existing unit regressions alone cannot certify this pilot.

**Recommendation: the pilot does not pass acceptance testing. Keep bulk processing and paid API review paused.** No exhaustive word/section/relationship accuracy percentage is justified by the current ground truth.

## Preservation check

All **4,143 protected pre-existing files** (pilot/corpus source PDFs, annotations, caches, saved outputs and previous reports included in the snapshot) matched the SHA256 snapshot after audit and tests: zero changed, zero missing. See preservation-check.json. Only this new validation directory was written by the audit.
