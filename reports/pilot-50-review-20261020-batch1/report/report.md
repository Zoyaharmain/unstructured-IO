# 50-document pipeline and DeepSeek review report

**This is an automated development/diagnostic batch, not an accuracy certification.** No independent human-approved reference labels were used. The known pilot relationship defects remain relevant.

## Batch result

Selected **50 documents with 50 distinct SHA256 hashes** from `/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT`. Selection: original15 +35 additional PDFs, seed42, round-robin page/layout/coverage strata from the previously processed source pool. Java is deliberately retained as known out-of-scope evidence; this is not a claim that all selected documents are genuine candidate resumes. This sample is not an unbiased corpus accuracy estimate.

Local completion: **50/50**. Provider attempted: **50/50**. Structurally valid provider reviews: **49/50**. Failed documents: **1**. Skipped: **0**.

All-local-before-review sequencing: **True**. Local completion `2026-10-20T15:33:50.583262+00:00`; review start `2026-10-20T15:35:14.664246+00:00`. Times are UTC evidence. The preflight credential/model GET sends no resume and is not a review request.

### Review statuses

- llm_reviewed_all_assigned: **43**
- llm_reviewed_needs_review: **4**
- llm_reviewed_no_sections: **1**
- llm_reviewed_out_of_scope: **1**
- review_failed: **1**

Classification requests: **58**. Actual input **1,447,234** + output **45,208** = **1,492,442 tokens**. Multi-call documents: 8; recorded invalid-response attempts: 4; failed follow-ups retaining a valid first result: 0. Actual token counts are reported; no price/cost estimate is invented. Provider prompt caching does not mean a local cached response was substituted.

Raw unassigned: **918 → 218**. Meaningful unassigned: **882 → 189**. Unassigned whitespace/page noise: **36 → 29**. All source artifacts, including noise, remain preserved. Counts can change when provider decisions split spans or move assigned content back to unknown; this is not automatically a regression.

Exact extracted-source interval checks: **50/50 passed**. This-run local/review/source-hash bindings: **50/50 passed**. Missing/overlapping output source intervals: 0 in validated artifacts. These checks do not prove original-PDF word coverage or semantic correctness.

## Per-document results

Raw / meaningful counts are shown separately. “All assigned” is a coverage status only.

| Document | Local raw / meaningful | Final raw / meaningful | Requests | Review status |
|---|---:|---:|---:|---|
| A Suribhotla.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ANUTOSHTRIVEDI.pdf | 37 / 37 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ajay Bandagi.pdf | 7 / 7 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AkshayPatni (1).pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Alvina _Fernandes.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AmmeyUtpatt.pdf | 72 / 57 | 27 / 1 | 2 | llm_reviewed_needs_review |
| AmrikaBhattacharjee.pdf | 28 / 27 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ananya Guha Resume.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ankit _ agarwal (1).pdf | 0 / 0 | 1 / 1 | 2 | llm_reviewed_needs_review |
| AnupGurnani[7y_0m].pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Anuradha Yadav.pdf | 14 / 14 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Assignment.pdf | 25 / 25 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ChaitanyaSareddy.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Charansai P.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| DeepaR.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Divakar_Prep_guide.pdf | 152 / 147 | 138 / 138 | 2 | llm_reviewed_needs_review |
| Dnyaneshwar NarayanIngale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GAURAVAGRAWAL.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Girish Morab.pdf | 56 / 43 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GowthamSelvaraj.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Java Aws backend.pdf | 5 / 5 | 9 / 9 | 2 | llm_reviewed_out_of_scope |
| Java Developer & Angular_sanjeev.pdf | 8 / 8 | 40 / 39 | 2 | llm_reviewed_no_sections |
| Keerthi_SAPresume.pdf | 0 / 0 | 0 / 0 | 2 | review_failed |
| KhalidPathan.pdf | 132 / 132 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Khushal Narain Lulla.pdf | 1 / 1 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Krishnadev_S.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kulwant._Singh.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MA Faisal.pdf | 13 / 13 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Madan Kumar Singh.pdf | 16 / 16 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MadhukaranAkshayKumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mangesh Dhage (1).pdf | 14 / 14 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Md Fazeel Ahmed.pdf | 10 / 10 | 2 / 0 | 1 | llm_reviewed_all_assigned |
| Mukkadala Ramya Pavani.pdf | 36 / 36 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NagaVishnu.pdf | 83 / 81 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nikhil Kumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nimisha Susan Varghese.pdf | 9 / 9 | 1 / 1 | 2 | llm_reviewed_needs_review |
| PUPPYKUMARI.pdf | 27 / 27 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pavan Bakku.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Piyush Anand 1.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Poonam_Muley.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PrajwalS.pdf | 76 / 76 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prasad PR.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rajan Dattatraya Dudhale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ravi RS.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rutuja Herekar.pdf | 13 / 13 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| S  Abhinav.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| S gaotam.pdf | 23 / 23 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAI KUMAR CHOWDRY.pdf | 6 / 6 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAIPREETHIJUNGA1_3.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SANDHYABR.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |

## Failures and provider uncertainty

**AmmeyUtpatt.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Ankit _ agarwal (1).pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Divakar_Prep_guide.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: ['invalid_assignments']. 138 meaningful spans remain. Local-result retained: False.

**Java Aws backend.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: ['invalid_assignments']. 9 meaningful spans remain. Local-result retained: False.

**Java Developer & Angular_sanjeev.pdf — llm_reviewed_no_sections**. Provider state: complete; error: none; invalid attempts: []. 39 meaningful spans remain. Local-result retained: False.

**Keerthi_SAPresume.pdf — review_failed**. Provider state: failed; error: invalid_assignments; invalid attempts: ['invalid_assignments', 'invalid_assignments']. 0 meaningful spans remain. Local-result retained: True.

**Nimisha Susan Varghese.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

## Source, section and relationship concerns

The following are explicit diagnostics, not automatic ground truth. Exact repeated passages may be genuine repetitions. Independent text-parser differences may be reading order, spacing, broken words or missing source text; check the PDF before declaring an omission. Word-boundary splits are concrete source-boundary observations; canonical joined text may still be intact. Relationship flags identify suspicious grouping, not an exhaustive association score.

### A Suribhotla.pdf

Source SHA256: `620ab3d24d19d580d53bb5973d7d5d029b1cc9aed359d427215990aedd818a55`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 25,922.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ANUTOSHTRIVEDI.pdf

Source SHA256: `e32145dc06b21fc56903196401fa57a773655f7706fa74031116d0d37d3aea7b`. Source pages present: [1, 2]. API calls 1; tokens 23,508.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ajay Bandagi.pdf

Source SHA256: `6462281d67c91a043cf95f218aac2539d2479e9b78268a425d0746ebd2ae1cea`. Source pages present: [1]. API calls 1; tokens 20,641.

Section/source flags: extraction_duplicate_candidates_require_source_check; employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 1; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AkshayPatni (1).pdf

Source SHA256: `7f950f0e57892ba655f6601c90bced1679e30bd110c87444a82e937a36594cf4`. Source pages present: [1, 2]. API calls 1; tokens 18,706.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group; experience-3: artifact_only_entry Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Alvina _Fernandes.pdf

Source SHA256: `655dd07fd73e7a35e8663fbee6b2b8204bef1890fbbca42e63afdfbc8c19c386`. Source pages present: [1, 2, 3]. API calls 1; tokens 20,425.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: numeric_or_grade_only_entry; experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmmeyUtpatt.pdf

Source SHA256: `07821a296523d0d353dbe7de3a82fe2713deb7c67025a7cf0508e83dc743dd38`. Source pages present: [1, 2]. API calls 2; tokens 74,826.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmrikaBhattacharjee.pdf

Source SHA256: `e042840e69bb458a11e4d782de7309db979eceef01fe84ec1b7ae9012cead558`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 45,415.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group; experience-2: multiple_dated_employment_headers_in_one_group Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ananya Guha Resume.pdf

Source SHA256: `808f9ed3c7c79527b24e30863a1691d023ca3fb051eece68a11c69ce7b40f8ea`. Source pages present: [1, 2]. API calls 1; tokens 16,903.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ankit _ agarwal (1).pdf

Source SHA256: `f83463b281e1f7597c751a24fbb4d1379b36a6e0acbcca8fa293e1bc78ed9f50`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 56,465.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-5: artifact_only_entry Proposed groups: 7.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AnupGurnani[7y_0m].pdf

Source SHA256: `122acdd99f6a0ee553537bc746d2e5d8d32531c41e52a0598237e4e020902917`. Source pages present: [1, 2]. API calls 1; tokens 20,621.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates; education-3: multiple_qualification_mentions_in_one_group_requires_review; education-4: numeric_or_grade_only_entry; education-4: date_only_entry_possible_detached_dates Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Anuradha Yadav.pdf

Source SHA256: `60484622d8466a2e242f2cc097d78747f051cb7174484ae06bfe6bb0375aca5a`. Source pages present: [1, 2]. API calls 1; tokens 14,549.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: artifact_only_entry Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Assignment.pdf

Source SHA256: `010745684c449b883e813e1f81362c77825882c541977ba91a88e990f4cc2e79`. Source pages present: [1]. API calls 1; tokens 5,800.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ChaitanyaSareddy.pdf

Source SHA256: `8238d23e03b0beabf2356a8bd53ee9b98a50ca1a6c702b4e65439ca3df64cdd0`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 35,947.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: artifact_only_entry Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Charansai P.pdf

Source SHA256: `cc435e0166b283e4e32650b799ee526b1a3bc0dcb1c0819ebecda40ae90437e3`. Source pages present: [1, 2, 3]. API calls 1; tokens 31,383.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### DeepaR.pdf

Source SHA256: `5bce56951525b124f6021414b32dd206bc299f819e72ce2ab3a0fe2753a62f36`. Source pages present: [1, 2]. API calls 1; tokens 18,722.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-4: artifact_only_entry Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Divakar_Prep_guide.pdf

Source SHA256: `28f6fb290df57439f44528c7958ec85e721d944b42a1ff66a6418765bdf9d265`. Source pages present: [1, 2, 3, 4, 5]. API calls 2; tokens 64,864.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dnyaneshwar NarayanIngale.pdf

Source SHA256: `850ec405810adb1222c4dd3766940847fb75497d187f177df4dd0b740db40526`. Source pages present: [1, 2]. API calls 1; tokens 15,509.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GAURAVAGRAWAL.pdf

Source SHA256: `9bbcb0781eecdd553e6ce120b8a33e889436fd65c5c445854112345b84b08ac6`. Source pages present: [1, 2]. API calls 1; tokens 16,737.

Section/source flags: extraction_duplicate_candidates_require_source_check; independent_pdf_text_difference_requires_source_check; employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 1; independent-parser unmatched terms: 1; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Girish Morab.pdf

Source SHA256: `b9e510607779fa6d259accdfd7c3c99b2f54598bc870d9e1cb564f55d0d7fab0`. Source pages present: [1, 2, 3]. API calls 1; tokens 44,647.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GowthamSelvaraj.pdf

Source SHA256: `2e96285ea903ae02b62cc1fcbbd3b74bcf172ca5d1fcf0c5873f7790b455847e`. Source pages present: [1]. API calls 1; tokens 16,473.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Java Aws backend.pdf

Source SHA256: `a829c05aa18916dce49096991a37e28a470d28c3effd5a7132f7e6b15af6f218`. Source pages present: [1, 2]. API calls 2; tokens 20,996.

Section/source flags: out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Java Developer & Angular_sanjeev.pdf

Source SHA256: `0001fd97e8314265a495d8d70aa83ec1196240c3be2518eba5dd90758e82066e`. Source pages present: [1]. API calls 2; tokens 17,409.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Keerthi_SAPresume.pdf

Source SHA256: `ad5e648e21102bce534924ab7c5a0e196ed0b56663189d05fce6e9f83c823750`. Source pages present: [1]. API calls 2; tokens 11,784.

Section/source flags: independent_pdf_text_empty_requires_visual_or_ocr_reference; provider_review_failed_local_result_retained.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### KhalidPathan.pdf

Source SHA256: `a12eb0d5cf74a50c893cae0707a7d5826f2628aa7e6606c4a337d4df11faa3b1`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 40,701.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Khushal Narain Lulla.pdf

Source SHA256: `6ebae0c3da8a6bddb82ceecd7dd00bf7a8515dfda685f70f4fc7297a8af16ce1`. Source pages present: [1]. API calls 2; tokens 21,799.

Section/source flags: source_word_split_across_output_blocks; employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 1.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Krishnadev_S.pdf

Source SHA256: `46511b668f2663bce892111ee9c68bb15f1e429435a6e24dbd90f456a1cf82e5`. Source pages present: [1, 2, 3]. API calls 1; tokens 29,496.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group; experience-3: artifact_only_entry Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kulwant._Singh.pdf

Source SHA256: `7c04045cda7528b50c3a136468d772ea89cc8cc8bf0af599d8eb80df1506f09f`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 36,644.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MA Faisal.pdf

Source SHA256: `00596d57717d783e92a67f71174ff44425d8fd5f53c5e24a3799540484e0fa36`. Source pages present: [1, 2, 3]. API calls 1; tokens 45,827.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Madan Kumar Singh.pdf

Source SHA256: `e2db3e4c0be734d114a121d2a14023ce50bfb0f84650443bb6184d61ba29c12d`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 54,291.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MadhukaranAkshayKumar.pdf

Source SHA256: `5a802722825cc272a36da66eff0d07c7d2a11368ed3d3098ccbdbc71bea92b17`. Source pages present: [1, 2, 3]. API calls 1; tokens 31,570.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mangesh Dhage (1).pdf

Source SHA256: `61ea9dab564c8a7c83fcdb59aff6ec0d722b4c486814f81fe42a62275772044e`. Source pages present: [1]. API calls 1; tokens 12,287.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Md Fazeel Ahmed.pdf

Source SHA256: `0974d9d471f5c1c3c3ed535af3ef25260f4c3136b11d8047faf3669c1f6c4434`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 30,169.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mukkadala Ramya Pavani.pdf

Source SHA256: `634b0c3473c81fc649d8475268b79b5a5bc978258adeed99d835ef46f8565307`. Source pages present: [1, 2, 3]. API calls 1; tokens 18,993.

Section/source flags: source_word_split_across_output_blocks.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 2.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NagaVishnu.pdf

Source SHA256: `b48a8a2bdc960608e092beac6d03120ea9fcddb7e46d894281578f99dadf335e`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 45,123.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nikhil Kumar.pdf

Source SHA256: `73c78b61ec58b86210ae4f288a8a90ef9ff06d1af428786f49046ca29d700b42`. Source pages present: [1, 2, 3]. API calls 1; tokens 28,183.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nimisha Susan Varghese.pdf

Source SHA256: `e938b2f7006dfe367dcadf47e96f7fdc02580f4a5cf40e0249b34de2a931d966`. Source pages present: [1, 2]. API calls 2; tokens 34,951.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PUPPYKUMARI.pdf

Source SHA256: `28b2147dc8895b94a1c7eacd52d2974aea75ca84408a6bed0ebc12efac55d538`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 64,041.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: education-3: numeric_or_grade_only_entry Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pavan Bakku.pdf

Source SHA256: `9cd414d78c4fb79f01adea54f62150e573a07892987e008d5bc167962bc3c203`. Source pages present: [1]. API calls 1; tokens 15,266.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 1.

Education: education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Piyush Anand 1.pdf

Source SHA256: `8092e443779e3f5874c410ef4b82ad4771477665fb13055c4fe07288587b9329`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 27,949.

Section/source flags: independent_pdf_text_difference_requires_source_check; employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 12; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Poonam_Muley.pdf

Source SHA256: `0399f6417ff6c3b7c9bda35bef22aafc0ad7026741ce740a6592de98f0e66473`. Source pages present: [1, 2, 3]. API calls 1; tokens 22,322.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrajwalS.pdf

Source SHA256: `59e27a9b16e9cbbfcf8658adb31fe9c5619db96fccdc9c3da2d23281265556ca`. Source pages present: [1, 2]. API calls 1; tokens 19,561.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates; experience-4: numeric_or_grade_only_entry; experience-4: date_only_entry_possible_detached_dates; experience-5: numeric_or_grade_only_entry; experience-5: date_only_entry_possible_detached_dates Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prasad PR.pdf

Source SHA256: `1a18a9aae06b32eeb868a04b5a3819c06299f9f9affc7d84cc536c99bf4e5609`. Source pages present: [1, 2]. API calls 1; tokens 16,687.

Section/source flags: source_word_split_across_output_blocks; employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 2.

Employment: experience-3: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rajan Dattatraya Dudhale.pdf

Source SHA256: `935e9952b655fa4620cdfb4c9fd98aa28d4794c490b5e4e4192c2c0d8b34f9a0`. Source pages present: [1, 2, 3]. API calls 1; tokens 23,023.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: artifact_only_entry Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ravi RS.pdf

Source SHA256: `b22e98c77fe9c93d2d72ec2163a7db8322ede0ad3411c76da724a87217c177ff`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 38,252.

Section/source flags: source_word_split_across_output_blocks; employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 1.

Employment: experience-1: multiple_dated_employment_headers_in_one_group; experience-3: artifact_only_entry Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rutuja Herekar.pdf

Source SHA256: `d3df6990b7d635626abc2fd535b6004928936e7957fe4570836e06a5989775be`. Source pages present: [1, 2, 3]. API calls 1; tokens 28,235.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### S  Abhinav.pdf

Source SHA256: `c96250b351a6bddd658c9fa5d8d4cb15f125ca2f1ea8cfe58217dddd51a9de46`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 41,865.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### S gaotam.pdf

Source SHA256: `b43fe187de287b28770aa800fd36c42713a44c6c78e98013b515e6b613b026db`. Source pages present: [1]. API calls 1; tokens 28,205.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAI KUMAR CHOWDRY.pdf

Source SHA256: `a6ba77fc7dae40af1c410f7c3e6d523ca104976300f5a1d4340fb97ff8b1c457`. Source pages present: [1]. API calls 1; tokens 17,911.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: numeric_or_grade_only_entry; experience-1: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAIPREETHIJUNGA1_3.pdf

Source SHA256: `d3386b4ac4470acdc577cf7d16b2f13a419970b49043a1245f94c44b00461cba`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 63,095.

Section/source flags: independent_pdf_text_difference_requires_source_check; source_word_split_across_output_blocks; employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 2; word-boundary splits: 1.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SANDHYABR.pdf

Source SHA256: `9d4a06d6d2d89fa85a44d5992c5f272361ce10ee8bd03aa245de96bc02feb06d`. Source pages present: [1, 2, 3]. API calls 1; tokens 17,744.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

## Failure patterns and next steps

- education_relationship_concerns: 26 documents flagged.
- employment_relationship_concerns: 26 documents flagged.
- extraction_duplicate_candidates_require_source_check: 2 documents flagged.
- independent_pdf_text_difference_requires_source_check: 3 documents flagged.
- independent_pdf_text_empty_requires_visual_or_ocr_reference: 1 documents flagged.
- out_of_scope_job_requirements: 1 documents flagged.
- provider_review_failed_local_result_retained: 1 documents flagged.
- source_word_split_across_output_blocks: 5 documents flagged.

Priorities: inspect failed provider decisions without relaxing coverage rules; distinguish non-resume requirements from candidate history; fix source-supported employer/date and education/grade grouping in a separately authorized change; verify word splits and PDF text differences; independently approve a source-bound reference set. Do not force unknown text into a category to improve coverage. No production logic was changed for this batch.

## Commands and tests

Exact stage commands and timestamps are in ../manifest.json. All stage scripts are existing batch implementations; run_pilot50_review.py only selects/freezes scope and sequences them. The checkpoint binding gate rejects changed sources, pipeline hashes or provider configuration on resume. No prior-run provider output was imported. The isolated offline regression suite results are in ../tests/regression.log and ../tests/tests.xml; external networking was blocked and the provider key removed in the test process.

## Preservation and readiness

Protected pre-existing artifacts checked: 2589; changed: 0. Original PDFs, annotations, gold and all prior reports remain untouched. Only the separate 50-document directory contains new processing artifacts.

**Do not scale further on the basis of assignment coverage.** This run exposes unresolved provider/source/grouping cases; independent semantic accuracy remains unknown. No 150-document or 1,500-document run was started.

## Additional source and provider findings

local completed: 20 Oct 2026 21:03:50 IST; review started: 20 Oct 2026 21:05:14 IST; review completed: 20 Oct 2026 21:07:31 IST.

The pipeline auto-detected **one** out-of-scope form. Independent source-text inspection additionally identifies **Divakar_Prep_guide.pdf** as an interview preparation guide (heading: OMS Interview Preparation Guide) and **Java Developer & Angular_sanjeev.pdf** as a job description (opening: I need two senior Angular resources as per the below defined JD). Thus this is 50 collection documents, not 50 independently confirmed candidate resumes. These observations did not change production classifications or replace any selected file.

**Keerthi_SAPresume.pdf:** local extraction used OCR. The independent text-only parser returns empty text, so an independent visual/OCR reference is needed. DeepSeek response1 omitted u19 from 20 required IDs; response2 included u15[20:36] for a source span of length20. Both returned finish_reason=stop but failed interval validation. The original local result was retained. No additional paid retry was made after the bounded attempts.

**Tests:** 199 passed, zero failed/deselected, in 83.96s; test process made zero external connection attempts. Call/token totals and all 50 row/hash bindings were cross-checked. Pipeline source/configuration hashes remained unchanged throughout.

Exact executed commands and safe resume behavior: [commands-executed.md](../commands-executed.md). The new files are orchestration/reporting only; extraction, BERT/K-means, local recovery and review algorithms were not changed for this run.
