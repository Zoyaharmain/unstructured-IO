# Exact 15-resume local pipeline + full DeepSeek verification

All 15 finish local extraction, BERT/K-means detection and local recovery before any DeepSeek review begins. DeepSeek receives all extracted spans for assigned-block review and unresolved-span placement. Model review remains a prediction, not independently verified truth.

| File | Local unassigned (raw) | Final unassigned (raw) | API calls | Review status |
|---|---:|---:|---:|---|
| A Suribhotla.pdf | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Ajay Bandagi.pdf | 7 | 0 | 1 | llm_reviewed_all_assigned |
| AkshayPatni (1).pdf | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Alvina _Fernandes.pdf | 0 | 0 | 1 | llm_reviewed_all_assigned |
| Anuradha Yadav.pdf | 14 | 0 | 1 | llm_reviewed_all_assigned |
| Charansai P.pdf | 1 | 0 | 1 | llm_reviewed_all_assigned |
| GAURAVAGRAWAL.pdf | 1 | 0 | 1 | llm_reviewed_all_assigned |
| Java Aws backend.pdf | 5 | 6 | 2 | llm_reviewed_needs_review |
| NagaVishnu.pdf | 83 | 0 | 1 | llm_reviewed_all_assigned |
| Nikhil Kumar.pdf | 1 | 0 | 1 | llm_reviewed_all_assigned |
| PUPPYKUMARI.pdf | 27 | 0 | 1 | llm_reviewed_all_assigned |
| Pavan Bakku.pdf | 0 | 0 | 1 | llm_reviewed_all_assigned |
| Prasad PR.pdf | 3 | 0 | 1 | llm_reviewed_all_assigned |
| Rutuja Herekar.pdf | 13 | 0 | 1 | llm_reviewed_all_assigned |
| S  Abhinav.pdf | 3 | 0 | 1 | llm_reviewed_all_assigned |

## Provider usage and completeness

```json
{
  "scope_documents": 15,
  "documents_completed": 15,
  "not_attempted": 0,
  "all_documents_attempted": true,
  "statuses": {
    "llm_reviewed_all_assigned": 14,
    "llm_reviewed_needs_review": 1
  },
  "provider": "DeepSeek",
  "classification_api_calls": 16,
  "usage": {
    "prompt_tokens": 395497,
    "completion_tokens": 12362,
    "total_tokens": 407859,
    "prompt_cache_hit_tokens": 383480,
    "prompt_cache_miss_tokens": 12017
  },
  "stop_reason": null,
  "llm_review_is_ground_truth": false,
  "original_word_accuracy_measured": false
}
```

## Limits

Counts above include raw needs_review blocks, potentially whitespace. Exact source invariants check preservation of extracted text, not every original PDF word. Missing PDF text, duplication, semantic section correctness and employer/title/date or degree/institution/year relationships need independent source-backed approval. No numeric semantic/word accuracy is claimed. Failed/skipped provider reviews are reported explicitly; they do not count as verified.

Local artifacts: local/documents/. Full-context reviewed artifacts: deepseek/documents/. Actual provider responses and call/token records: deepseek/provider-decisions/ and deepseek/checkpoints/. Original PDFs, previous annotations and reports were not modified.
