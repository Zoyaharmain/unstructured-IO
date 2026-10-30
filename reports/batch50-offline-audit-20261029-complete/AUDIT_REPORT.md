# Offline audit of the saved fifty-document run

Completed 29 October 2026. No paid/API calls. Original sources and original benchmark files were hashed before/after and are unchanged. Findings and derived exports are separate from the saved benchmark.

**The batch does not establish overall field accuracy or production readiness.** It contains 48 candidate/possible resumes and two non-resume documents (a job description and an interview preparation guide). There are confirmed record/semantic failures despite successful HTTP responses and source citations.

## Recomputed operational results

| Measurement | Result | Meaning |
|---|---:|---|
| Saved documents audited against originals | 50/50 | 35 PDF, 15 DOCX |
| Full field-review status | 41/48 applicable, 85.4% | Accepted review, not field accuracy |
| Partial field review | 5/48 | Reviewed output plus local fallback |
| Failed field review | 2/48 | Local fallback retained |
| Internal mapping success | 4/50 | Not accuracy certification |
| Mapping needs_review | 39/50 | Includes non-resume output |
| Mapping fallback_used | 7/50 | Two failed, five partial |
| Saved section review complete | 44/50 | Two failed, four lack this metadata |
| Citation inventory available | 46/50 | Current hierarchy/source-quote validation passes for those 46 |
| Checked literal field values | 3,569 | Contact, scalar record fields, all_skills, and awards items |
| Not confirmed by either PDF reading | 2 | Both long awards values in Girish Morab; needs semantic/source inspection |
| Calculable saved job durations after date repair | 164/194 | Derived coverage, not validation of employment truth |
| Insufficient saved job dates | 30/194 | No time invented |

The earlier report's 86% pure-LLM claim counts 43 non-fallback documents, which includes two not-applicable non-resumes. Full field review is 41/48 applicable resumes. Zero unresolved spans and accepted evidence do not establish correct section/entity semantics. The audit does not call fallback output accurate simply because it remains usable.

## Scope and method

Every available original was read independently using pdftotext for PDF and original Word XML for DOCX. PDF literal checks use both layout and raw reading order. The first layout-only pass flagged 17 apparent mismatches; all were confirmed by raw reading order and were not counted as model errors. The expanded final check includes achievements and flags two long award values. This distinction prevents column-reading artifacts from being mistaken for hallucinations.

Literal checks use case/punctuation/whitespace-tolerant matching. They do not test employer semantics, precision/recall, completeness of extraction, missing jobs/degrees, all responsibilities, or correct associations. They are not an accuracy percentage. Extracted-text/source quote contracts were validated where a saved inventory was available; four missing inventories are unavailable evidence, not four proved validator failures.

## Confirmed problems and repairs

1. **Split qualification expansions.** Original Ashok Kumar education lists two qualifications, PGDB and MBA. Saved output created three records. Local grouping now recognizes explicit parenthetical acronym expansions across adjacent wrapped source rows. Expanded degree names are not used as subjects. Fresh local replay has two records; field of study is not invented when still unresolved.
2. **False empty-identity job.** Jaydipsinh's saved fallback counted a record without company or role as experience. Local mapping now retains its source text/review reasons without counting an extra job. Fresh local replay has four jobs and zero identityless records. That is not a complete semantic accuracy score.
3. **Job subheadings promoted to awards.** Girish Morab's original employment sections use Key Responsibilities & Achievements. Saved awards include tools/technology lists combined with impact prose. A scoped-heading fix keeps these subheadings with their current job/project in local classification. An offline real-model regression passes. No new live provider response was tested; the saved erroneous output is preserved.
4. **Date variants.** Support comma-separated month/year, joined month-year, spaced-year extraction artifacts and explicit onwards markers. Year-spacing repairs carry warnings; year-only/ambiguous dates remain uncertain. On frozen saved fields, calculated durations rise 161 to 164 and unrecognized formats decrease nine to one. The remaining range is certification validity, which is not safely a single issue year.
5. **Latent unsafe skill expansion.** Code inspection found bare ALM converted to HP ALM without vendor evidence. This alias is now review-only and raw ALM is retained. Bare ALM was not present in this batch's all_skills arrays, so this is not presented as a measured batch error.

These changes use general source structure/date rules, not filename or candidate exceptions. All source-backed corrections still pass existing ownership/citation checks. The original report/schema outputs are not rewritten to appear improved.

## Accuracy that can actually be measured

Only A Suribhotla.pdf matches an existing human_verified=true ground-truth document and its exact extraction hash. Its saved section ownership score is 100% across 3,859 labeled non-whitespace characters and five section families. This is one document and one task, not field-value accuracy, OCR accuracy, or a representative fifty-document result. The score is saved separately.

Overall employer/role/date/education/skills/achievement precision, recall and F1 remain **unmeasured** for this batch. An expected.review-template.json is provided for independent labeling; all new rows are human_verified=false, with null expected fields. They are not LLM-generated gold. Blank expected fields do not assert absence.

## Artifacts

- summary.json and results.json: recomputed full-batch findings.
- documents/: per-document source/output hashes, structural findings and unknowns.
- standardized/: derived standardized exports of the frozen saved field values, not fresh extraction/mapping results. Existing saved errors can remain in these exports; consult findings.
- private-source-text/: local independent source readings; contains personal resume information and is inside a private output directory.
- source-inspections.json: bounded assistant-inspected findings and replay references. Not human-approved gold.
- expected.review-template.json: independent review packet for all fifty files.
- one-matched-gold-section-score.json: limited existing labeled comparison.
- repair-code-manifest.json: file hashes for the audited code changes.

## Remaining limitations

There has been no new paid fifty-document run or unseen-resume semantic benchmark. The scoped-heading changes may not prevent an LLM from proposing a bad reassignment; the new live output remains unverified. Thirty job date sets remain insufficient. Some subjects/institutions and other source associations remain unresolved. These gaps are preserved for review, not silently filled. Source-word presence alone cannot detect a missed record or a plausible wrong category.

## Per-document audit

| Document | Mapping | Field review | Source literal checks | Unconfirmed values | Saved citation inventory |
|---|---|---|---:|---:|---|
| A Suribhotla.pdf | success | complete | 47 | 0 | available |
| AbhishekTiwari.pdf | needs_review | complete | 57 | 0 | available |
| Anita Das.pdf | needs_review | complete | 106 | 0 | available |
| Arnab_KumarKar.pdf | needs_review | complete | 86 | 0 | available |
| Ashfaq Rahman.pdf | needs_review | complete | 61 | 0 | available |
| Ashok Kumar.pdf | needs_review | complete | 65 | 0 | available |
| Ashwin S S.docx | needs_review | complete | 44 | 0 | available |
| BenjaminRosanSunil (1).pdf | needs_review | complete | 86 | 0 | available |
| Chaganti Leela Sankar.docx | needs_review | complete | 88 | 0 | available |
| Chandan_Das.pdf | needs_review | complete | 70 | 0 | available |
| CharugundlaShalini.pdf | needs_review | complete | 96 | 0 | available |
| DeekshaYadu.pdf | needs_review | complete | 51 | 0 | available |
| Devops Groovy.pdf | needs_review | not_applicable | 0 | 0 | unavailable |
| Dipti_Jadhav.docx | fallback_used | failed | 100 | 0 | unavailable |
| G S Sandhya Rani.pdf | fallback_used | partial | 91 | 0 | available |
| GAURAVAGRAWAL_1.pdf | success | complete | 70 | 0 | available |
| Girish Morab.pdf | needs_review | complete | 83 | 2 | available |
| Gopal.docx | needs_review | complete | 49 | 0 | available |
| HarshVardhanDewangan.pdf | needs_review | complete | 64 | 0 | available |
| Jaydipsinh Chudasama.pdf | fallback_used | failed | 53 | 0 | unavailable |
| Jitendra Sagar.docx | needs_review | complete | 206 | 0 | available |
| Joseph Julliet BA.docx | needs_review | complete | 95 | 0 | available |
| MadhukaranAkshayKumar.pdf | needs_review | complete | 84 | 0 | available |
| MeenalDixit[5y_9m].docx | needs_review | complete | 51 | 0 | available |
| NaynaTonge- CV.pdf | needs_review | complete | 86 | 0 | available |
| Nitya Ravindran.pdf | needs_review | complete | 67 | 0 | available |
| PURNACHANDRASETHI (1)_1.pdf | success | complete | 87 | 0 | available |
| Pankaj_Satish_Sharma.pdf | needs_review | complete | 51 | 0 | available |
| PradeepKempanna.pdf | needs_review | complete | 70 | 0 | available |
| Pranchal kushwah.docx | needs_review | complete | 60 | 0 | available |
| Prasad_Potdar.pdf | needs_review | complete | 97 | 0 | available |
| Prashant Bangilwar.docx | needs_review | complete | 35 | 0 | available |
| Prescilla Thomas.pdf | fallback_used | partial | 11 | 0 | available |
| RUSHI M.pdf | success | complete | 34 | 0 | available |
| Rakesh.pdf | needs_review | not_applicable | 0 | 0 | unavailable |
| Ravisankar Sundar.docx | needs_review | complete | 74 | 0 | available |
| SAURABH KUMAR SINGH.docx | needs_review | complete | 135 | 0 | available |
| Sachin Karney.docx | needs_review | complete | 74 | 0 | available |
| SanketBabasahebLavate.pdf | needs_review | complete | 54 | 0 | available |
| SapnadipBaidya.pdf | needs_review | complete | 78 | 0 | available |
| Sayantan Paul.pdf | needs_review | complete | 62 | 0 | available |
| Shanmuga Priya.pdf | needs_review | complete | 93 | 0 | available |
| Shradhajain (1).pdf | needs_review | complete | 57 | 0 | available |
| Shruti Jha.pdf | fallback_used | partial | 74 | 0 | available |
| ShubhamSureshMane.pdf | needs_review | complete | 105 | 0 | available |
| ShyamKumarDonka.pdf | fallback_used | partial | 65 | 0 | available |
| Supriya Bhagat.docx | needs_review | complete | 78 | 0 | available |
| Supriya Bhagat_2.docx | needs_review | complete | 78 | 0 | available |
| UzerKhan_1.pdf | needs_review | complete | 52 | 0 | available |
| Vivek Prabhakar Karekar.docx | fallback_used | partial | 89 | 0 | available |

## Final code verification

191 affected offline tests passed in 25.05 seconds. This includes fourteen audit-specific regressions covering column-reading false positives, missing inventory handling, recurring date forms, unsafe skill aliases, source-preserving fallback job pruning, degree acronym expansions versus genuine multiple qualifications, and scoped job subheadings. Changed Python modules compile; changed-file whitespace checks pass. No paid calls were made.
