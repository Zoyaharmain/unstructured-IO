# Final readable report: selected 15 resumes

## Did this run use DeepSeek?

**Yes.** The saved run log says `cached: 0`, `new_attempts: 15`, model `deepseek-flash`, connection `ready`. The saved checkpoints record 16 classification requests with returned token usage; provider-decisions/ contains the saved response contents. The runner loads the existing key from `.env` automatically. You do not have to type a key at each run. The large provider prompt-cache-hit count is server-side input caching; it does not mean these were offline responses or free requests. Actual monetary cost was not calculated.

This report was generated only from those saved records. **No new API calls or resume processing were performed to create it.**

## Which report should you read?

This report describes `reports/pilot-full-review-20261020-072948/`. The older `reports/pilot_fallback_20261020_live_v2/report.md` is a different run with a different fallback policy. Neither report is live status for the other.

## Main result

All 15 completed local extraction/block detection and were then sent to DeepSeek for review of assigned and unresolved text. The local stages ran on the bounded set of 15 copied PDFs before the DeepSeek stage began. DeepSeek reused those local outputs rather than extracting the PDF itself. Fourteen documents ended with all extracted text assigned. Java Aws backend still has six unassigned text spans. Assignment completion does not establish that the blocks or relationships are correct.

| Resume | Unassigned meaningful spans after local processing | After DeepSeek | Requests | Outcome |
|---|---:|---:|---:|---|
| A Suribhotla.pdf | 1 | 0 | 1 | Assigned; accuracy unverified |
| Ajay Bandagi.pdf | 7 | 0 | 1 | Assigned; accuracy unverified |
| AkshayPatni (1).pdf | 1 | 0 | 1 | Assigned; accuracy unverified |
| Alvina _Fernandes.pdf | 0 | 0 | 1 | Assigned; accuracy unverified |
| Anuradha Yadav.pdf | 14 | 0 | 1 | Assigned; accuracy unverified |
| Charansai P.pdf | 1 | 0 | 1 | Assigned; accuracy unverified |
| GAURAVAGRAWAL.pdf | 1 | 0 | 1 | Assigned; accuracy unverified |
| Java Aws backend.pdf | 5 | 6 | 2 | Needs review; accuracy unverified |
| NagaVishnu.pdf | 81 | 0 | 1 | Assigned; accuracy unverified |
| Nikhil Kumar.pdf | 1 | 0 | 1 | Assigned; accuracy unverified |
| PUPPYKUMARI.pdf | 27 | 0 | 1 | Assigned; accuracy unverified |
| Pavan Bakku.pdf | 0 | 0 | 1 | Assigned; accuracy unverified |
| Prasad PR.pdf | 3 | 0 | 1 | Assigned; accuracy unverified |
| Rutuja Herekar.pdf | 13 | 0 | 1 | Assigned; accuracy unverified |
| S  Abhinav.pdf | 3 | 0 | 1 | Assigned; accuracy unverified |

## What the numbers mean

- Meaningful unassigned spans: **158 → 6**. Raw local needs_review count was 160; two NagaVishnu whitespace spans are excluded from the meaningful count.
- API requests: **16**, reviewing **15/15 documents**, including the two documents locally having zero unassigned spans. This was full review, not fallback-only.
- Actual recorded token usage: **395,497 input + 12,362 output = 407,859 tokens**.
- Extracted-source invariant checks passed for all 15 in the saved run. They show source intervals were preserved; they cannot prove every original PDF word was extracted or every block was correct.
- No independently source-bound human-approved ground truth has been established. Word accuracy, section accuracy and employer/title/date or degree/institution/year accuracy are therefore **not measured**. Do not describe 14/15 assignment completion as 93.33% accuracy.

## Issues still requiring review

**Ajay Bandagi.pdf:** Repeated extracted passages require source review: e9/e10. Repetition can also be genuine in the original PDF; do not delete it automatically.

**GAURAVAGRAWAL.pdf:** Repeated extracted passages require source review: e40/e41. Repetition can also be genuine in the original PDF; do not delete it automatically. Known source issue remains: page 2 Achievements heading is absent from this saved extraction.

**Java Aws backend.pdf:** Source is a job-requirements template, not established candidate history. Review or exclude it explicitly; blank template fields should not be invented as resume facts.

**PUPPYKUMARI.pdf:** Original PDF contains conflicting Role History/Career History dates. Human review must preserve or resolve that conflict and verify employer/title/date table rows.

**Pavan Bakku.pdf:** Check KEY ACHIEVEMENTS taxonomy and the separation of four work-history records.

**Prasad PR.pdf:** Check PGSQL block boundaries and degree/institution/date relationships. Assigning all text alone does not validate them.

**Rutuja Herekar.pdf:** Check that GenAI coursework and future QA application plans are not represented as past employment.

## Read the actual blocks

Open **index.html in this directory**. Each resume shows its detected sections as normal readable text, the local result for comparison, and any unassigned text. No API calls are made when opening it; no external scripts, fonts or analytics are included. The page contains personal resume information, so keep it private.

## Final conclusion

The recorded full-review workflow ran for all 15 and used DeepSeek. It assigned all extracted text in 14 documents and left six spans in the Java template unresolved. It has **not** established that these 14 resumes are accurate. Confirm the source-text defects, section taxonomy and employment/education record relationships against original PDFs before acceptance or scaling. No original PDF, annotation, provider response or previous report was changed while building this readable report.
