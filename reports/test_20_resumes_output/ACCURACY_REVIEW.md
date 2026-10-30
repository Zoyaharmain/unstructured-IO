# Accuracy review of the saved twenty-document run

Reviewed 29 October 2026. Read-only analysis of summary_report.json and all twenty saved schema artifacts. No new extraction/provider requests and no changes to the original report or outputs.

## Conclusion

Overall field accuracy is **not measured**. The available artifacts do not justify an accuracy percentage. HTTP success, accepted citations, field counts and internal success statuses measure different properties; none establishes that all original information was extracted, classified and assigned correctly.

The batch contains nineteen candidate resumes and one interview preparation guide, rather than twenty candidate resumes. Every output is marked human_verified=false. None of the twenty filenames overlaps the existing ground_truth/gold/gold_resumes.jsonl. There is no matching expected field-value set against which to calculate precision, recall or F1 for this run.

## What is measured

| Measurement | Result | Interpretation |
|---|---:|---|
| Successful extraction requests | 20/20, 100% | Endpoint returned successfully, not source-text accuracy |
| Successful section requests | 20/20, 100% | Endpoint returned, including retained local results |
| Completed section LLM review | 18/20, 90% | Accepted review; two reviews failed |
| Successful schema requests | 20/20, 100% | Endpoint returned, including fallback |
| Complete field LLM review | 16/19 applicable resumes, 84.2% | Two partial, one failed; guide not applicable |
| Mapping status success | 3/20, 15% | Internal operational status, not measured correctness |
| Mapping status needs_review | 14/20, 70% | Includes the guide |
| Mapping status fallback_used | 3/20, 15% | Two partial reviews and one failed field review |
| Zero section needs-review units | 12/20, 60% | Placement coverage only, not classification accuracy |
| Human-verified outputs | 0/20 | Human field accuracy not established |

Among the nineteen resumes, three have internal success status (15.8%); sixteen still require review or fallback (84.2%). Neither number is field accuracy. A resume requiring review may contain many correct fields; a success status can still miss source information.

## Corrections to the original narrative

- “Section Segmentation Success 100%” describes successful requests; section LLM review completed on eighteen documents. Girish Morab and MadhukaranAkshayKumar have failed section review.
- “17 documents completed pure LLM schema mapping” conflates the sixteen complete field reviews with the guide's not_applicable status. Girish Morab and Prescilla Thomas are partial; Jaydipsinh Chudasama failed.
- Twelve, not eleven, documents have zero section needs-review units.
- Zero unresolved spans does not establish high-accuracy segmentation. Low nonzero counts also cannot be called harmless artifacts without examining the affected spans.
- Recognizing the guide is a useful individual observation, not a measured out-of-scope detection accuracy rate across a representative positive/negative test set.
- Citation/schema validation cannot establish that a cited organization is the employer, that record counts are correct, or that extraction omitted no original content.

## Required accuracy measurement

Freeze these source files and outputs. Independently label expected employer/role/date records, education, contact, skills and achievements, including absent information and extra false records. Compare predicted records with expected records and report field precision, recall and F1 by category. Score section ownership against independent source-bound labels separately from extraction text accuracy. Report both per-document averages and pooled counts, and separate the guide from candidate resumes. Evaluate fixes on unseen resumes as well as this development set.

A truthful current statement is: “Twenty documents completed API processing; nineteen were resumes. Full field review completed for 84.2% of applicable resumes. Overall extraction and semantic mapping accuracy remain unmeasured.”

Machine-readable recomputed counts: accuracy-review.json.
