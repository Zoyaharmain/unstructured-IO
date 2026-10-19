# Fresh 15-resume local-first fallback run

No human-verified accuracy percentage is available. Zero unassigned measures coverage of extracted text only. Known extraction and record-grouping defects require source review; this runner does not silently fix or hide them.

```json
{
  "scope": 15,
  "completed": 15,
  "new_api_calls": 0,
  "llm_documents": 0,
  "local_only_documents": 2,
  "initial_meaningful_unassigned": 275,
  "after_local_meaningful_unassigned": 158,
  "after_final_meaningful_unassigned": 158,
  "errors": 0,
  "provider_stop_reason": null,
  "semantic_accuracy": null,
  "word_accuracy": null,
  "human_ground_truth_independently_verified": false,
  "llm_policy": "only documents with meaningful unassigned spans after local recovery; all spans supplied as context/review",
  "usage": {}
}
```

| Document | Initial unassigned | After local | Final | DeepSeek calls | Status |
|---|---:|---:|---:|---:|---|
| Pavan Bakku.pdf | 0 | 0 | 0 | 0 | local_all_assigned |
| Ajay Bandagi.pdf | 7 | 7 | 7 | 0 | needs_review_llm_disabled |
| AkshayPatni (1).pdf | 1 | 1 | 1 | 0 | needs_review_llm_disabled |
| Prasad PR.pdf | 3 | 3 | 3 | 0 | needs_review_llm_disabled |
| Anuradha Yadav.pdf | 14 | 14 | 14 | 0 | needs_review_llm_disabled |
| Java Aws backend.pdf | 31 | 5 | 5 | 0 | needs_review_llm_disabled |
| GAURAVAGRAWAL.pdf | 1 | 1 | 1 | 0 | needs_review_llm_disabled |
| Charansai P.pdf | 1 | 1 | 1 | 0 | needs_review_llm_disabled |
| Alvina _Fernandes.pdf | 0 | 0 | 0 | 0 | local_all_assigned |
| Nikhil Kumar.pdf | 1 | 1 | 1 | 0 | needs_review_llm_disabled |
| Rutuja Herekar.pdf | 104 | 13 | 13 | 0 | needs_review_llm_disabled |
| S  Abhinav.pdf | 3 | 3 | 3 | 0 | needs_review_llm_disabled |
| A Suribhotla.pdf | 1 | 1 | 1 | 0 | needs_review_llm_disabled |
| NagaVishnu.pdf | 81 | 81 | 81 | 0 | needs_review_llm_disabled |
| PUPPYKUMARI.pdf | 27 | 27 | 27 | 0 | needs_review_llm_disabled |

DeepSeek is skipped when the local stage assigns all meaningful text, even if it assigned something incorrectly. For failed local documents, full resume text is transmitted for relational context and all assignments may be reviewed. Extraction diagnostics do not by themselves trigger an API request. OCR retry occurs only for empty fast extraction; repeated identical local recovery stops immediately. This is bounded recovery, not an endless rerun or a guarantee of correctness.

See results.json for per-document extraction diagnostics, local passes, exact span accounting, provider usage and error status. Original PDFs, annotations, caches and prior reports remain untouched.
