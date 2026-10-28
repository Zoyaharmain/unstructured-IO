# Offline resume batch check

Documents: 10 · Checks passed: 10 · Human-answer comparisons: 0 · Provider calls: 0

Checks passing establishes source/schema consistency, not semantic accuracy. Unreviewed results have no accuracy verdict. Comparisons cover only declared expected fields; PDF/OCR accuracy still requires source review.

| Resume | Checks | Accuracy | Review needed | Details |
|---|---|---|---|---|
| A A Ashwini.docx | pass | not_reviewed | True | documents/5013f84de9b27b45d558.report.md |
| A Fairoz.docx | pass | not_reviewed | True | documents/3e18198fb9a59e744fa4.report.md |
| A Lokhande.pdf | pass | not_reviewed | True | documents/ac5d6e270873f4463129.report.md |
| A Sateesh Kumar 2.docx | pass | not_reviewed | True | documents/a55629e7fd65ad776c0b.report.md |
| A Sateesh Kumar.docx | pass | not_reviewed | True | documents/2e7969595c4f155884cf.report.md |
| A Suribhotla.pdf | pass | not_reviewed | True | documents/455f5323879db82963ef.report.md |
| A.Bhargava.docx | pass | not_reviewed | True | documents/d714f19e0af02c92c26d.report.md |
| AananthyManoharan.docx | pass | not_reviewed | True | documents/f7c7bc2157347fed1878.report.md |
| Abdul Shukoor.pdf | pass | not_reviewed | True | documents/5bcf520a368f60d3971e.report.md |
| Abhishek Hanashi.pdf | pass | not_reviewed | True | documents/dcd959e6a5031f3d2627.report.md |

Copy expected.template.json outside the run directory. For each reviewed source, fill expected_data with selected fields from schema.json data and set human_reviewed to true. Preserve sha256. Run again with --expected pointing to that file. Lists require exact record counts and compare without ordering. Missing optional fields can be omitted from expected objects. Existing artifacts are never overwritten.
