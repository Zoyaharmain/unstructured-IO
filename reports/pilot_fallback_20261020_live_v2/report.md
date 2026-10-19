# Fresh 15-resume local-first fallback run

No human-verified accuracy percentage is available. Zero unassigned measures coverage of extracted text only. Known extraction and record-grouping defects require source review; this runner does not silently fix or hide them.

```json
{
  "scope": 15,
  "completed": 15,
  "new_api_calls": 15,
  "llm_documents": 13,
  "local_only_documents": 2,
  "initial_meaningful_unassigned": 275,
  "after_local_meaningful_unassigned": 158,
  "after_final_meaningful_unassigned": 6,
  "errors": 0,
  "provider_stop_reason": null,
  "semantic_accuracy": null,
  "word_accuracy": null,
  "human_ground_truth_independently_verified": false,
  "llm_policy": "only documents with meaningful unassigned spans after local recovery; all spans supplied as context/review",
  "usage": {
    "prompt_tokens": 378079,
    "completion_tokens": 11535,
    "total_tokens": 389614,
    "prompt_cache_hit_tokens": 349432,
    "prompt_cache_miss_tokens": 28647
  }
}
```

| Document | Initial unassigned | After local | Final | DeepSeek calls | Status |
|---|---:|---:|---:|---:|---|
| Pavan Bakku.pdf | 0 | 0 | 0 | 0 | local_all_assigned |
| Ajay Bandagi.pdf | 7 | 7 | 0 | 1 | llm_reviewed_all_assigned |
| AkshayPatni (1).pdf | 1 | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Prasad PR.pdf | 3 | 3 | 1 | 2 | llm_reviewed_needs_review |
| Anuradha Yadav.pdf | 14 | 14 | 0 | 1 | llm_reviewed_all_assigned |
| Java Aws backend.pdf | 31 | 5 | 5 | 2 | llm_reviewed_needs_review |
| GAURAVAGRAWAL.pdf | 1 | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Charansai P.pdf | 1 | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Alvina _Fernandes.pdf | 0 | 0 | 0 | 0 | local_all_assigned |
| Nikhil Kumar.pdf | 1 | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Rutuja Herekar.pdf | 104 | 13 | 0 | 1 | llm_reviewed_all_assigned |
| S  Abhinav.pdf | 3 | 3 | 0 | 1 | llm_reviewed_all_assigned |
| A Suribhotla.pdf | 1 | 1 | 0 | 1 | llm_reviewed_all_assigned |
| NagaVishnu.pdf | 81 | 81 | 0 | 1 | llm_reviewed_all_assigned |
| PUPPYKUMARI.pdf | 27 | 27 | 0 | 1 | llm_reviewed_all_assigned |

DeepSeek is skipped when the local stage assigns all meaningful text, even if it assigned something incorrectly. For failed local documents, full resume text is transmitted for relational context and all assignments may be reviewed. Extraction diagnostics do not by themselves trigger an API request. OCR retry occurs only for empty fast extraction; repeated identical local recovery stops immediately. This is bounded recovery, not an endless rerun or a guarantee of correctness.

See results.json for per-document extraction diagnostics, local passes, exact span accounting, provider usage and error status. Original PDFs, annotations, caches and prior reports remain untouched.

## Additional measured coverage

81,199/81,364 meaningful extracted non-whitespace characters assigned: **99.80% coverage**, not word or section accuracy. 13/15 documents have all meaningful extracted text assigned. See llm-assignment-changes.csv for 364 changed intervals (a change is not automatically correct), and remaining-unassigned.csv for 6 remaining nonempty spans. Provider input cache hits are provider billing metadata; all 15 classification requests were live, not reuse of a saved local LLM response.

Eight offline checks passed for bounded scope, meaningful fallback gating and private configuration loading. The first live startup stopped before any API calls due to missing python-dotenv; the runner now reads simple DEEPSEEK_ configuration without that dependency or shell execution. No application endpoint behavior was changed; this policy is implemented by scripts/check_pilot_fallback.py.
