# 100-document pipeline and DeepSeek review report

**This is an automated development/diagnostic batch, not an accuracy certification.** No independent human-approved reference labels were used. The known pilot relationship defects remain relevant.

## Batch result

Selected **100 documents with 100 distinct SHA256 hashes** from `/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT`. Selection: original15 +85 seeded stratified distinct PDF hashes from existing processed pool. Document scope must be checked individually; selected files are not automatically confirmed candidate resumes. This sample is not an unbiased corpus accuracy estimate.

Local completion: **100/100**. Provider attempted: **100/100**. Structurally valid provider reviews: **100/100**. Failed documents: **0**. Skipped: **0**.

All-local-before-review sequencing: **True**. Local completion `2026-10-21T13:45:23.990763+00:00`; review start `2026-10-21T13:45:23.992606+00:00`. Times are UTC evidence. The preflight credential/model GET sends no resume and is not a review request.

### Review statuses

- llm_reviewed_all_assigned: **88**
- llm_reviewed_needs_review: **4**
- llm_reviewed_out_of_scope: **8**

Classification requests: **107**. Actual input **3,844,712** + output **94,007** = **3,938,719 tokens**. Multi-call documents: 7; recorded invalid-response attempts: 2; failed follow-ups retaining a valid first result: 0. Actual token counts are reported; no price/cost estimate is invented. Provider prompt caching does not mean a local cached response was substituted.

Raw unassigned: **1529 → 497**. Meaningful unassigned: **1344 → 417**. Unassigned whitespace/page noise: **185 → 80**. All source artifacts, including noise, remain preserved. Counts can change when provider decisions split spans or move assigned content back to unknown; this is not automatically a regression.

Exact extracted-source interval checks: **100/100 passed**. This-run local/review/source-hash bindings: **100/100 passed**. Missing/overlapping output source intervals: 0 in validated artifacts. These checks do not prove original-PDF word coverage or semantic correctness.

## Per-document results

Raw / meaningful counts are shown separately. “All assigned” is a coverage status only.

| Document | Local raw / meaningful | Final raw / meaningful | Requests | Review status |
|---|---:|---:|---:|---|
| A Suribhotla.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ANUTOSHTRIVEDI.pdf | 9 / 9 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ARUNSUNDARVENKATARAMANI.pdf | 23 / 14 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ajay Bandagi.pdf | 7 / 7 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AkshayPatni (1).pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AkshitaKothari.pdf | 19 / 17 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Alvina _Fernandes.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AmmeyUtpatt.pdf | 12 / 10 | 27 / 0 | 1 | llm_reviewed_all_assigned |
| AmrikaBhattacharjee.pdf | 28 / 26 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ananya Guha Resume.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ankit _ agarwal (1).pdf | 0 / 0 | 1 / 1 | 2 | llm_reviewed_needs_review |
| AnupGurnani[7y_0m].pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Anuradha Yadav.pdf | 14 / 9 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Anuradhika.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Assignement.pdf | 14 / 12 | 42 / 35 | 1 | llm_reviewed_out_of_scope |
| Assignment.pdf | 25 / 25 | 0 / 0 | 1 | llm_reviewed_out_of_scope |
| AsthaSaraogi.pdf | 11 / 11 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Avinash Kumar Singh.pdf | 52 / 42 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AvipsaChatterjee.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| CHIGULLA PRASHANT.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ChaitanyaSareddy.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Chandan_.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Charansai P.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| DEEPAK SINGH CHAUHAN.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| DeepaR.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Deepak Malik.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Devops Groovy.pdf | 24 / 19 | 24 / 19 | 1 | llm_reviewed_out_of_scope |
| Dhanraj G Badhe.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Dhiman Mishra.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Dinesh Patnaik.pdf | 36 / 33 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Divakar_Prep_guide.pdf | 153 / 136 | 154 / 137 | 1 | llm_reviewed_out_of_scope |
| Dnyaneshwar NarayanIngale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Dr Shraddha Mishra.pdf | 36 / 27 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GAJENDRASRATHORE.pdf | 12 / 12 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GAURAVAGRAWAL.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GaneshSirigidi.pdf | 9 / 9 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Gauri Shah.pdf | 4 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ghodake Ratnaganga .pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Girish Morab.pdf | 56 / 42 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GopalPrasad K.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Gopalakrishna.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GowthamSelvaraj.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Harini Sasidharanbai.pdf | 9 / 9 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Janardhan.pdf | 6 / 6 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Jasmin_Pandya (1).pdf | 3 / 3 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Java Aws backend.pdf | 5 / 5 | 46 / 41 | 1 | llm_reviewed_out_of_scope |
| Java Developer & Angular_sanjeev.pdf | 8 / 8 | 40 / 39 | 1 | llm_reviewed_out_of_scope |
| K_Yugandhar__CV.pdf | 6 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kadam A.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Keerthi_SAPresume.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Keshav - resume.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| KhalidPathan.pdf | 37 / 32 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Khushal Narain Lulla.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Krishnadev_S.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kulwant._Singh.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kunal Gosavi.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Lanchana K.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| LohithaBhusarapu.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MA Faisal.pdf | 13 / 13 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Maaz Abdullah.pdf | 49 / 49 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Madan Kumar Singh.pdf | 16 / 16 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MadhukaranAkshayKumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MahaleCharushilaUttam.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mangesh Dhage (1).pdf | 14 / 13 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Manuj Mehrotra.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MaritaNikitaDcruze.pdf | 56 / 56 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Md Fazeel Ahmed.pdf | 10 / 10 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| MeghanaPalthepu.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Microsoft_.Net AWS Backend Infra Developers  .pdf | 7 / 7 | 16 / 15 | 1 | llm_reviewed_out_of_scope |
| MohitKumar.pdf | 7 / 7 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mukkadala Ramya Pavani.pdf | 36 / 23 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NagaVishnu.pdf | 83 / 73 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nageswar Reddy.pdf | 52 / 39 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nikhil Kumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nimisha Susan Varghese.pdf | 9 / 9 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Nisha Singh.pdf | 43 / 38 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NitinKumar.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PUPPYKUMARI.pdf | 27 / 27 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pavan Bakku.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Piyush Anand 1.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Piyush.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Poonam_Muley.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pradyum Raj_1.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PrajwalS.pdf | 76 / 74 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prasad PR.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prasad_Potdar.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prescilla Thomas.pdf | 98 / 66 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rajan Dattatraya Dudhale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rakesh.pdf | 144 / 127 | 144 / 127 | 1 | llm_reviewed_out_of_scope |
| Ravi RS.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ravi_RS.pdf | 33 / 33 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| RevatiSubhashChorg.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rutuja Herekar.pdf | 13 / 13 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| S  Abhinav.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| S gaotam.pdf | 24 / 24 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAI KUMAR CHOWDRY.pdf | 6 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAIPREETHIJUNGA1_3.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SANDHYABR.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SARVAGYA.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SHAIK RUSUM MOHAMMAD RASOOL.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |

## Failures and provider uncertainty

**Ankit _ agarwal (1).pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Assignement.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 35 meaningful spans remain. Local-result retained: False.

**Assignment.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 0 meaningful spans remain. Local-result retained: False.

**Devops Groovy.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 19 meaningful spans remain. Local-result retained: False.

**Divakar_Prep_guide.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 137 meaningful spans remain. Local-result retained: False.

**Jasmin_Pandya (1).pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: ['invalid_assignments']. 1 meaningful spans remain. Local-result retained: False.

**Java Aws backend.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 41 meaningful spans remain. Local-result retained: False.

**Java Developer & Angular_sanjeev.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 39 meaningful spans remain. Local-result retained: False.

**KhalidPathan.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Microsoft_.Net AWS Backend Infra Developers  .pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 15 meaningful spans remain. Local-result retained: False.

**Nimisha Susan Varghese.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Rakesh.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 127 meaningful spans remain. Local-result retained: False.

Jasmin_Pandya (1).pdf validation causes: gap_or_overlap.

Maaz Abdullah.pdf validation causes: gap_or_overlap, unsupported_word_boundary.

## Source, section and relationship concerns

The following are explicit diagnostics, not automatic ground truth. Exact repeated passages may be genuine repetitions. Independent text-parser differences may be reading order, spacing, broken words or missing source text; check the PDF before declaring an omission. Word-boundary splits are concrete source-boundary observations; canonical joined text may still be intact. Relationship flags identify suspicious grouping, not an exhaustive association score.

### A Suribhotla.pdf

Source SHA256: `620ab3d24d19d580d53bb5973d7d5d029b1cc9aed359d427215990aedd818a55`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 31,723.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ANUTOSHTRIVEDI.pdf

Source SHA256: `e32145dc06b21fc56903196401fa57a773655f7706fa74031116d0d37d3aea7b`. Source pages present: [1, 2]. API calls 1; tokens 31,099.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group; experience-1: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ARUNSUNDARVENKATARAMANI.pdf

Source SHA256: `23f55a652af4a503dd5d7c51b6385df2f9c269310e8cb9445d7bb9f53a87d738`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 72,673.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 52 meaningful section blocks have no record ownership; source review required Proposed groups: 3.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ajay Bandagi.pdf

Source SHA256: `6462281d67c91a043cf95f218aac2539d2479e9b78268a425d0746ebd2ae1cea`. Source pages present: [1]. API calls 1; tokens 19,690.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AkshayPatni (1).pdf

Source SHA256: `7f950f0e57892ba655f6601c90bced1679e30bd110c87444a82e937a36594cf4`. Source pages present: [1, 2]. API calls 1; tokens 25,044.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: education-1: qualification_not_established Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AkshitaKothari.pdf

Source SHA256: `b5122c176b141c5a81b24b7d44544816b2af0b19f846f93d2623145d7452badf`. Source pages present: [1, 2]. API calls 1; tokens 25,494.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Alvina _Fernandes.pdf

Source SHA256: `655dd07fd73e7a35e8663fbee6b2b8204bef1890fbbca42e63afdfbc8c19c386`. Source pages present: [1, 2, 3]. API calls 1; tokens 26,464.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmmeyUtpatt.pdf

Source SHA256: `07821a296523d0d353dbe7de3a82fe2713deb7c67025a7cf0508e83dc743dd38`. Source pages present: [1, 2]. API calls 1; tokens 45,459.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 5.

Education: education-1: qualification_not_established; education-2: qualification_not_established Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmrikaBhattacharjee.pdf

Source SHA256: `e042840e69bb458a11e4d782de7309db979eceef01fe84ec1b7ae9012cead558`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 57,841.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ananya Guha Resume.pdf

Source SHA256: `808f9ed3c7c79527b24e30863a1691d023ca3fb051eece68a11c69ce7b40f8ea`. Source pages present: [1, 2]. API calls 1; tokens 22,606.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ankit _ agarwal (1).pdf

Source SHA256: `f83463b281e1f7597c751a24fbb4d1379b36a6e0acbcca8fa293e1bc78ed9f50`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 68,502.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-8: employer_not_established_from_supported_fields; experience-9: employer_not_established_from_supported_fields Proposed groups: 9.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AnupGurnani[7y_0m].pdf

Source SHA256: `122acdd99f6a0ee553537bc746d2e5d8d32531c41e52a0598237e4e020902917`. Source pages present: [1, 2]. API calls 1; tokens 28,051.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Anuradha Yadav.pdf

Source SHA256: `60484622d8466a2e242f2cc097d78747f051cb7174484ae06bfe6bb0375aca5a`. Source pages present: [1, 2]. API calls 1; tokens 18,791.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Anuradhika.pdf

Source SHA256: `117e559c970205e2079477f5449e1bb983a95dea10565054dfdeb59252b249c0`. Source pages present: [1, 2]. API calls 1; tokens 32,343.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Assignement.pdf

Source SHA256: `2813113fdc6690cfc532461220ebcda4ce7eea97c8e0857fbe8b2e15d9f431f1`. Source pages present: [1]. API calls 1; tokens 10,616.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_website_critique.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Assignment.pdf

Source SHA256: `010745684c449b883e813e1f81362c77825882c541977ba91a88e990f4cc2e79`. Source pages present: [1]. API calls 1; tokens 7,659.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_website_critique.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AsthaSaraogi.pdf

Source SHA256: `83e6affd3c36a2b7b17f82e0096b156d65f5cfaa0a986a3d6fca35ee15493435`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 69,368.

Section/source flags: extraction_duplicate_candidates_require_source_check; education_relationship_concerns.

Repeated-passage candidates: 2; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: education-1: qualification_not_established Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Avinash Kumar Singh.pdf

Source SHA256: `1144f7ec741d4d3314d3979ea712f4de08c4202d925df793560fced19f0e2923`. Source pages present: [1, 2, 3]. API calls 1; tokens 45,735.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 8.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AvipsaChatterjee.pdf

Source SHA256: `05580c10b818064a1881e8b1b2a75eb080c956a825c15076e9ac116e14ca7839`. Source pages present: [1]. API calls 1; tokens 16,315.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 2 meaningful section blocks have no record ownership; source review required; experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### CHIGULLA PRASHANT.pdf

Source SHA256: `e0470ff9f6a67fb6bf726a8f931516d379aa0546a863fcd14fb6d91fd3dfc132`. Source pages present: [1, 2, 3]. API calls 1; tokens 39,337.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ChaitanyaSareddy.pdf

Source SHA256: `8238d23e03b0beabf2356a8bd53ee9b98a50ca1a6c702b4e65439ca3df64cdd0`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 46,846.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields Proposed groups: 2.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Chandan_.pdf

Source SHA256: `6e0e105d369589a86215b50a12eb41da9498fca10d92de64a4605a05a7d5a3e8`. Source pages present: [1, 2, 3, 4, 5, 6, 7]. API calls 1; tokens 58,689.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Charansai P.pdf

Source SHA256: `cc435e0166b283e4e32650b799ee526b1a3bc0dcb1c0819ebecda40ae90437e3`. Source pages present: [1, 2, 3]. API calls 1; tokens 39,344.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### DEEPAK SINGH CHAUHAN.pdf

Source SHA256: `558f959872acf59d155317b916b5428cb4b65758145490e078550a8bcf5d7eae`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 31,466.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields Proposed groups: 6.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### DeepaR.pdf

Source SHA256: `5bce56951525b124f6021414b32dd206bc299f819e72ce2ab3a0fe2753a62f36`. Source pages present: [1, 2]. API calls 1; tokens 24,237.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 42 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Deepak Malik.pdf

Source SHA256: `20a95d0318f6fe4fad437cb38e6cf8884c3074a0959e607960a7f2f452c0f73c`. Source pages present: [1, 2]. API calls 1; tokens 24,310.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Devops Groovy.pdf

Source SHA256: `5ee46d04d0f25744dfca5bea017f7b6efa293872df39081ab67509b637017b21`. Source pages present: [1]. API calls 1; tokens 6,611.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_job_description.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dhanraj G Badhe.pdf

Source SHA256: `5da61283511fdcd74aac8cc1b95fda4b314a22f96c8c36e95b5c4d0e4e107155`. Source pages present: [1, 2, 3]. API calls 1; tokens 38,527.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dhiman Mishra.pdf

Source SHA256: `743b5cb037c69a20776200c737bf2ce7cf6c6d254bfd6c3e4483dcff8f775e76`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 36,558.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 49 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dinesh Patnaik.pdf

Source SHA256: `f29e599cca3a10fdaae4a5de0c971e47e83b4b342c40f331c2400a695110e9dc`. Source pages present: [1]. API calls 1; tokens 23,905.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields Proposed groups: 4.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Divakar_Prep_guide.pdf

Source SHA256: `28f6fb290df57439f44528c7958ec85e721d944b42a1ff66a6418765bdf9d265`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 41,981.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_interview_preparation_guide.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dnyaneshwar NarayanIngale.pdf

Source SHA256: `850ec405810adb1222c4dd3766940847fb75497d187f177df4dd0b740db40526`. Source pages present: [1, 2]. API calls 1; tokens 20,545.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields Proposed groups: 3.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dr Shraddha Mishra.pdf

Source SHA256: `31bb5f4bd5709d9273e78191f84d6e45be66b3e182d7edf93c08c027603c85c3`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 78,705.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-5: multiple_dated_employment_headers_in_one_group; experience-1: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields Proposed groups: 6.

Education: 9 meaningful section blocks have no record ownership; source review required Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GAJENDRASRATHORE.pdf

Source SHA256: `be67d2f315b68262c0f83f886c51a1d5b1d3b2319b7d4a87d227a82233846818`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 70,153.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 8 meaningful section blocks have no record ownership; source review required; experience-3: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields; experience-8: employer_not_established_from_supported_fields Proposed groups: 8.

Education: 2 meaningful section blocks have no record ownership; source review required Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GAURAVAGRAWAL.pdf

Source SHA256: `9bbcb0781eecdd553e6ce120b8a33e889436fd65c5c445854112345b84b08ac6`. Source pages present: [1, 2]. API calls 1; tokens 21,864.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields Proposed groups: 4.

Education: 3 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GaneshSirigidi.pdf

Source SHA256: `7f2dc62d0fe141c7b89a393b966c92be1ea1bf8297ba53fd54a287b95f0c5423`. Source pages present: [1, 2]. API calls 1; tokens 25,954.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Gauri Shah.pdf

Source SHA256: `85b8f7a571b208dd2c3325950cf31e3f4b6e26b0994a909ffcf6022f3dda6b30`. Source pages present: [1, 2]. API calls 1; tokens 24,727.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ghodake Ratnaganga .pdf

Source SHA256: `c0b2b7f0284b2ae86b49126ea626e9d785c19c256e3a04d21e070796ff96d89a`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 58,219.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields; experience-9: employer_not_established_from_supported_fields; experience-10: employer_not_established_from_supported_fields Proposed groups: 10.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Girish Morab.pdf

Source SHA256: `b9e510607779fa6d259accdfd7c3c99b2f54598bc870d9e1cb564f55d0d7fab0`. Source pages present: [1, 2, 3]. API calls 1; tokens 60,056.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 18 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GopalPrasad K.pdf

Source SHA256: `863a82d120c468c8e3c88fa7c43a80aa16c9485e8a570b8dcee8d9dc5bc69c4b`. Source pages present: [1, 2, 3]. API calls 1; tokens 51,435.

Section/source flags: independent_pdf_text_difference_requires_source_check; employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 8; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Gopalakrishna.pdf

Source SHA256: `cc7fdbd297b9246c06b2beb8736997ba0b1291606a3c5b8c8467455ee3be0302`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 62,401.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 3 meaningful section blocks have no record ownership; source review required Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GowthamSelvaraj.pdf

Source SHA256: `2e96285ea903ae02b62cc1fcbbd3b74bcf172ca5d1fcf0c5873f7790b455847e`. Source pages present: [1]. API calls 1; tokens 21,049.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Harini Sasidharanbai.pdf

Source SHA256: `ca3547c50ae7421b006861b9bf0fe9450bac95177c201c188231aca372609d13`. Source pages present: [1, 2]. API calls 1; tokens 23,534.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Janardhan.pdf

Source SHA256: `45015e8c69532793329955826c103211ad5041fb378d5a338d034258bcdf527e`. Source pages present: [1, 2]. API calls 1; tokens 37,272.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields Proposed groups: 6.

Education: 3 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Jasmin_Pandya (1).pdf

Source SHA256: `47a2ccde8e20a10c29255d2c23ba4ce1aae340daaef5f3687091e924d58a382a`. Source pages present: [1, 2, 3]. API calls 2; tokens 72,643.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: employer_not_established_from_supported_fields Proposed groups: 6.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Java Aws backend.pdf

Source SHA256: `a829c05aa18916dce49096991a37e28a470d28c3effd5a7132f7e6b15af6f218`. Source pages present: [1, 2]. API calls 1; tokens 13,084.

Section/source flags: employment_relationship_concerns; out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Java Developer & Angular_sanjeev.pdf

Source SHA256: `0001fd97e8314265a495d8d70aa83ec1196240c3be2518eba5dd90758e82066e`. Source pages present: [1]. API calls 1; tokens 10,936.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_job_description.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### K_Yugandhar__CV.pdf

Source SHA256: `5b385603648a26deb25a1274bee4c05e664bfe9a4b8473708eb015469efe181a`. Source pages present: [1]. API calls 1; tokens 23,548.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-2: employer_not_established_from_supported_fields Proposed groups: 2.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kadam A.pdf

Source SHA256: `ea195de3d818a37c3589602b5cff84683089edfde7b5268a9c7389b8f957c806`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 25,729.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields; experience-9: employer_not_established_from_supported_fields; experience-11: employer_not_established_from_supported_fields Proposed groups: 11.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Keerthi_SAPresume.pdf

Source SHA256: `ad5e648e21102bce534924ab7c5a0e196ed0b56663189d05fce6e9f83c823750`. Source pages present: [1]. API calls 1; tokens 7,853.

Section/source flags: independent_pdf_text_empty_requires_visual_or_ocr_reference; employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Keshav - resume.pdf

Source SHA256: `84a04f3a1d2b30daaa95784801dbdf4f8c3cf8e0bbfd3f048cdc115651ff8cd2`. Source pages present: [1]. API calls 1; tokens 11,666.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### KhalidPathan.pdf

Source SHA256: `a12eb0d5cf74a50c893cae0707a7d5826f2628aa7e6606c4a337d4df11faa3b1`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 115,762.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; 1 meaningful section blocks have no record ownership; source review required; education-1: multiple_qualifications_in_one_source_span Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Khushal Narain Lulla.pdf

Source SHA256: `6ebae0c3da8a6bddb82ceecd7dd00bf7a8515dfda685f70f4fc7297a8af16ce1`. Source pages present: [1]. API calls 1; tokens 14,130.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 3 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields Proposed groups: 1.

Education: 2 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Krishnadev_S.pdf

Source SHA256: `46511b668f2663bce892111ee9c68bb15f1e429435a6e24dbd90f456a1cf82e5`. Source pages present: [1, 2, 3]. API calls 1; tokens 39,538.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kulwant._Singh.pdf

Source SHA256: `7c04045cda7528b50c3a136468d772ea89cc8cc8bf0af599d8eb80df1506f09f`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 50,436.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kunal Gosavi.pdf

Source SHA256: `ca7b3534805e9dddada5e424ab4e4c64d6dff4cd8b6378aca2c5c5ea4db17d64`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 45,790.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Lanchana K.pdf

Source SHA256: `8633132a4cab4928dd5c2f78b509f9e4d6c3a6a5f61064d7c33fbc6093e901e3`. Source pages present: [1, 2, 3]. API calls 1; tokens 35,800.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 2 meaningful section blocks have no record ownership; source review required Proposed groups: 5.

Education: 2 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### LohithaBhusarapu.pdf

Source SHA256: `632c6a037df53d8760cac6e6c68cc4b582e195fd03fe601583099936658bfcf2`. Source pages present: [1]. API calls 1; tokens 21,482.

Section/source flags: independent_pdf_text_difference_requires_source_check.

Repeated-passage candidates: 0; independent-parser unmatched terms: 1; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MA Faisal.pdf

Source SHA256: `00596d57717d783e92a67f71174ff44425d8fd5f53c5e24a3799540484e0fa36`. Source pages present: [1, 2, 3]. API calls 1; tokens 61,389.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-4: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 12.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Maaz Abdullah.pdf

Source SHA256: `56d90625b515015989f2adec949c97ac4372e0508b0649529d31f0c3392a6dcf`. Source pages present: [1]. API calls 2; tokens 33,209.

Section/source flags: source_word_split_across_output_blocks; employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 2.

Employment: 16 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields Proposed groups: 2.

Education: education-1: qualification_not_established Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Madan Kumar Singh.pdf

Source SHA256: `e2db3e4c0be734d114a121d2a14023ce50bfb0f84650443bb6184d61ba29c12d`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 74,114.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields; experience-9: employer_not_established_from_supported_fields Proposed groups: 10.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MadhukaranAkshayKumar.pdf

Source SHA256: `5a802722825cc272a36da66eff0d07c7d2a11368ed3d3098ccbdbc71bea92b17`. Source pages present: [1, 2, 3]. API calls 1; tokens 41,090.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-5: employer_not_established_from_supported_fields Proposed groups: 6.

Education: education-1: qualification_not_established Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MahaleCharushilaUttam.pdf

Source SHA256: `0ed2019a297e6a8bfecfa265ecf24c1bf6781be45ca7453ca2e4e3e303b37f10`. Source pages present: [1, 2]. API calls 1; tokens 31,433.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mangesh Dhage (1).pdf

Source SHA256: `61ea9dab564c8a7c83fcdb59aff6ec0d722b4c486814f81fe42a62275772044e`. Source pages present: [1]. API calls 1; tokens 17,997.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-1: multiple_qualifications_in_one_source_span Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Manuj Mehrotra.pdf

Source SHA256: `805767d9a7d5a88beb00333ce5058ab087974211ffefaf58c04c48a8d3375972`. Source pages present: [1, 2]. API calls 1; tokens 29,999.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields Proposed groups: 2.

Education: 3 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MaritaNikitaDcruze.pdf

Source SHA256: `054387c4a9c1f1efe127e7db6b62076ffa7e64e6cb4fad84632933ff289ed8ee`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 49,814.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Md Fazeel Ahmed.pdf

Source SHA256: `0974d9d471f5c1c3c3ed535af3ef25260f4c3136b11d8047faf3669c1f6c4434`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 81,287.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group; 2 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MeghanaPalthepu.pdf

Source SHA256: `a29e34a7f1aef50cff64b91844039aeb79d4c3e5fb455a44bf935c86f93dd051`. Source pages present: [1, 2, 3]. API calls 1; tokens 36,717.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields; experience-8: employer_not_established_from_supported_fields Proposed groups: 8.

Education: education-1: qualification_not_established Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Microsoft_.Net AWS Backend Infra Developers  .pdf

Source SHA256: `9c9644d433a0b0e7312c9881c7773acb03d73fed7936a864c05a8178004115f7`. Source pages present: [1]. API calls 1; tokens 12,646.

Section/source flags: employment_relationship_concerns; out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MohitKumar.pdf

Source SHA256: `7b013f239443c10e1d9b31975380f9c286d97e183f73857db518edfe3fe16533`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 50,770.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields Proposed groups: 4.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mukkadala Ramya Pavani.pdf

Source SHA256: `634b0c3473c81fc649d8475268b79b5a5bc978258adeed99d835ef46f8565307`. Source pages present: [1, 2, 3]. API calls 1; tokens 24,621.

Section/source flags: source_word_split_across_output_blocks; employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 2.

Employment: experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NagaVishnu.pdf

Source SHA256: `b48a8a2bdc960608e092beac6d03120ea9fcddb7e46d894281578f99dadf335e`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 57,639.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 18 meaningful section blocks have no record ownership; source review required Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nageswar Reddy.pdf

Source SHA256: `af063923753f1814d2a21046e1a61c70e542d774b6356e79af8938121f29f558`. Source pages present: [1, 2, 3]. API calls 1; tokens 48,249.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 4.

Education: 2 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nikhil Kumar.pdf

Source SHA256: `73c78b61ec58b86210ae4f288a8a90ef9ff06d1af428786f49046ca29d700b42`. Source pages present: [1, 2, 3]. API calls 1; tokens 37,016.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nimisha Susan Varghese.pdf

Source SHA256: `e938b2f7006dfe367dcadf47e96f7fdc02580f4a5cf40e0249b34de2a931d966`. Source pages present: [1, 2]. API calls 2; tokens 45,006.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nisha Singh.pdf

Source SHA256: `039047878ed3e33f14ebc4d686017d1a1d972f5466e7b0c94dee4931dc2dbaff`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 74,750.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-6: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 7.

Education: 3 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NitinKumar.pdf

Source SHA256: `e5aa2942dfe1d2a75cf8f694c951d058d8a463ba230db00a50b9a419412a3551`. Source pages present: [1, 2]. API calls 1; tokens 17,373.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 18 meaningful section blocks have no record ownership; source review required; experience-2: employer_not_established_from_supported_fields Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PUPPYKUMARI.pdf

Source SHA256: `28b2147dc8895b94a1c7eacd52d2974aea75ca84408a6bed0ebc12efac55d538`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 83,250.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-7: employer_not_established_from_supported_fields Proposed groups: 7.

Education: education-1: numeric_or_grade_only_entry; education-1: date_only_entry_possible_detached_dates; education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates; education-3: numeric_or_grade_only_entry; education-3: date_only_entry_possible_detached_dates; education-4: numeric_or_grade_only_entry; education-4: date_only_entry_possible_detached_dates Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pavan Bakku.pdf

Source SHA256: `9cd414d78c4fb79f01adea54f62150e573a07892987e008d5bc167962bc3c203`. Source pages present: [1]. API calls 1; tokens 19,791.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields Proposed groups: 4.

Education: 4 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Piyush Anand 1.pdf

Source SHA256: `8092e443779e3f5874c410ef4b82ad4771477665fb13055c4fe07288587b9329`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 38,519.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields; experience-9: employer_not_established_from_supported_fields; experience-11: employer_not_established_from_supported_fields; experience-15: employer_not_established_from_supported_fields Proposed groups: 15.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Piyush.pdf

Source SHA256: `efc65516d55ae70b98f8854d45ac244d31e037a552031b21fcd8cef2fdba05f2`. Source pages present: [1]. API calls 1; tokens 16,530.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Poonam_Muley.pdf

Source SHA256: `0399f6417ff6c3b7c9bda35bef22aafc0ad7026741ce740a6592de98f0e66473`. Source pages present: [1, 2, 3]. API calls 1; tokens 28,884.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields Proposed groups: 4.

Education: 2 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pradyum Raj_1.pdf

Source SHA256: `782e34f73e083f72955546cf99a587d4f9ad20af7a4325556143c95a0ceb7ab5`. Source pages present: [1]. API calls 1; tokens 26,153.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-4: employer_not_established_from_supported_fields Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrajwalS.pdf

Source SHA256: `59e27a9b16e9cbbfcf8658adb31fe9c5619db96fccdc9c3da2d23281265556ca`. Source pages present: [1, 2]. API calls 1; tokens 26,429.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prasad PR.pdf

Source SHA256: `1a18a9aae06b32eeb868a04b5a3819c06299f9f9affc7d84cc536c99bf4e5609`. Source pages present: [1, 2]. API calls 1; tokens 22,887.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields Proposed groups: 4.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prasad_Potdar.pdf

Source SHA256: `a7e9f53513bb4c5a1304508600c7dbeda9adaa237b39c9becca2c7bb36360d7d`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 69,831.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-5: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-8: employer_not_established_from_supported_fields Proposed groups: 8.

Education: 8 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prescilla Thomas.pdf

Source SHA256: `45523bf70055191f8a1a3c1f4fd5574a6d474d83164ba380406ed16cebfd607c`. Source pages present: [1, 2, 3]. API calls 1; tokens 57,233.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 11 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rajan Dattatraya Dudhale.pdf

Source SHA256: `935e9952b655fa4620cdfb4c9fd98aa28d4794c490b5e4e4192c2c0d8b34f9a0`. Source pages present: [1, 2, 3]. API calls 1; tokens 30,002.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 13 meaningful section blocks have no record ownership; source review required; experience-2: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-5: employer_not_established_from_supported_fields Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rakesh.pdf

Source SHA256: `e6d90754647f85270932e52d022b05d4ae2deadba6f2fd17b12571b73efd453e`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 39,002.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_interview_preparation_guide.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ravi RS.pdf

Source SHA256: `b22e98c77fe9c93d2d72ec2163a7db8322ede0ad3411c76da724a87217c177ff`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 52,526.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ravi_RS.pdf

Source SHA256: `2b4ff151bcf26d9fc7f899cb4fcc46eeadca97c60c79599ee6bec1191476a86b`. Source pages present: [1, 2, 3, 4, 5]. API calls 2; tokens 136,847.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-6: employer_not_established_from_supported_fields Proposed groups: 6.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RevatiSubhashChorg.pdf

Source SHA256: `3846ac323b1f575023ce085595a1eb6220d68e8f79c8b8bd632b4bd9fb8000e6`. Source pages present: [1, 2]. API calls 1; tokens 35,600.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-8: employer_not_established_from_supported_fields Proposed groups: 9.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rutuja Herekar.pdf

Source SHA256: `d3df6990b7d635626abc2fd535b6004928936e7957fe4570836e06a5989775be`. Source pages present: [1, 2, 3]. API calls 1; tokens 36,428.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: education-1: qualification_not_established; education-2: qualification_not_established Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### S  Abhinav.pdf

Source SHA256: `c96250b351a6bddd658c9fa5d8d4cb15f125ca2f1ea8cfe58217dddd51a9de46`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 54,739.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields Proposed groups: 7.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### S gaotam.pdf

Source SHA256: `b43fe187de287b28770aa800fd36c42713a44c6c78e98013b515e6b613b026db`. Source pages present: [1]. API calls 1; tokens 32,915.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-2: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields Proposed groups: 8.

Education: 3 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAI KUMAR CHOWDRY.pdf

Source SHA256: `a6ba77fc7dae40af1c410f7c3e6d523ca104976300f5a1d4340fb97ff8b1c457`. Source pages present: [1]. API calls 1; tokens 24,527.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-3: employer_not_established_from_supported_fields Proposed groups: 3.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAIPREETHIJUNGA1_3.pdf

Source SHA256: `d3386b4ac4470acdc577cf7d16b2f13a419970b49043a1245f94c44b00461cba`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 82,736.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: employer_not_established_from_supported_fields; experience-4: employer_not_established_from_supported_fields; experience-6: employer_not_established_from_supported_fields; experience-10: employer_not_established_from_supported_fields Proposed groups: 16.

Education: 1 meaningful section blocks have no record ownership; source review required Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SANDHYABR.pdf

Source SHA256: `9d4a06d6d2d89fa85a44d5992c5f272361ce10ee8bd03aa245de96bc02feb06d`. Source pages present: [1, 2, 3]. API calls 1; tokens 22,734.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SARVAGYA.pdf

Source SHA256: `c5843cc4898b5a7e6170dc210257cce3da7639530be5394dee043b0864c7698c`. Source pages present: [1, 2]. API calls 1; tokens 28,416.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: 1 meaningful section blocks have no record ownership; source review required; experience-1: employer_not_established_from_supported_fields Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SHAIK RUSUM MOHAMMAD RASOOL.pdf

Source SHA256: `79275dc6172967e3b1591506b17f811564d4cbaaba8598b3cda7e5732fb70343`. Source pages present: [1, 2, 3]. API calls 1; tokens 36,026.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

## Failure patterns and next steps

- education_relationship_concerns: 49 documents flagged.
- employment_relationship_concerns: 86 documents flagged.
- extraction_duplicate_candidates_require_source_check: 1 documents flagged.
- independent_pdf_text_difference_requires_source_check: 2 documents flagged.
- independent_pdf_text_empty_requires_visual_or_ocr_reference: 1 documents flagged.
- out_of_scope_interview_preparation_guide: 2 documents flagged.
- out_of_scope_job_description: 2 documents flagged.
- out_of_scope_job_requirements: 2 documents flagged.
- out_of_scope_website_critique: 2 documents flagged.
- source_word_split_across_output_blocks: 2 documents flagged.

Priorities: inspect failed provider decisions without relaxing coverage rules; distinguish non-resume requirements from candidate history; fix source-supported employer/date and education/grade grouping in a separately authorized change; verify word splits and PDF text differences; independently approve a source-bound reference set. Do not force unknown text into a category to improve coverage. This report evaluates the code and artifacts bound by its manifest; code changes require separate regression evidence.

## Commands and tests

Exact stage commands and timestamps are in ../manifest.json. All stage scripts are existing batch implementations; run_pilot50_review.py only selects/freezes scope and sequences them. The checkpoint binding gate rejects changed sources, pipeline hashes or provider configuration on resume. Provider response provenance is specified in the execution mode above. This reporting command does not run the regression suite. Refer to separately recorded regression-test results; do not infer that tests ran for this batch.

## Preservation and readiness

Protected pre-existing artifacts checked: 9521; changed: 0. Original PDFs, annotations, gold and all prior reports remain untouched. Only the separate 100-document directory contains new processing artifacts.

**Do not scale further on the basis of assignment coverage.** This run exposes unresolved provider/source/grouping cases; independent semantic accuracy remains unknown. This report covers only the frozen document scope recorded in the manifest.
