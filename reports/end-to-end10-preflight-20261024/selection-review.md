# Frozen proposed sample

| # | Resume | Saved pages | Selection rationale |
|---|---|---:|---|
| 1 | Aditya vashisth.pdf | 2 | Explicitly requested reviewed development control; intentional prior LLM reuse, not generalization evidence |
| 2 | _ManjunathMurugan.pdf | 2 | Explicitly requested reviewed development control; intentional prior LLM reuse, not generalization evidence |
| 3 | Chandan Kumar BV.pdf | 1 | short resume; provisional saved-output feature, not an accuracy label |
| 4 | Siva Mari.pdf | 10 | long employment history; provisional saved-output feature, not an accuracy label |
| 5 | Divya Balyan.pdf | 3 | multiple education records; provisional saved-output feature, not an accuracy label |
| 6 | Vikrant Roy.pdf | 9 | project-rich resume; provisional saved-output feature, not an accuracy label |
| 7 | Sundar.pdf | 3 | certification-rich resume; provisional saved-output feature, not an accuracy label |
| 8 | Santhosh KR -  SAP EWM.pdf | 3 | unresolved/fragmented diagnostic case; provisional saved-output feature, not an accuracy label |
| 9 | Sumit.pdf | 8 | long document; provisional saved-output feature, not an accuracy label |
| 10 | HarmeetSingh cv.pdf | 2 | compact multi-section resume; provisional saved-output feature, not an accuracy label |

Full original paths, SHA-256 hashes, saved source/mapping hashes, prior-history flags and code fingerprints are in selection-manifest.json. Eight generalization documents have no match by hash or filename in the inspected prior selections, including the previous 350 manifest. Aditya and Manjunath intentionally reuse earlier paid tests as development controls. All ten have distinct original hashes and distinct normalized saved-text hashes. Similar rewritten versions cannot be ruled out by hashing alone. Layout descriptors are saved metadata, not manual layout approvals. Candidates are provisionally resume-like according to saved diagnostics, not independent scope labels.

Planned provider: deepseek-flash at https://api.deepseek.com. Key present; validity untested. Two provider stages: all-span section review and advisory schema audit. Local extraction, recovery and both schema mappers make no paid calls. Expected first-pass volume: 20 requests; with one bounded recovery pass, cap 40 total and 4 per document, including invalid responses. Limits can stop documents before all expected calls. No additional retries, documents or larger batch. Costs unavailable until verified price/usage evidence exists.

Proposed command, not yet executed with --execute:

```bash
.venv/bin/python reports/end-to-end10-preflight-20261024/run_ten.py --manifest reports/end-to-end10-preflight-20261024/selection-manifest.json --execute
```

Wait for user confirmation of this exact scope and budget before provider execution.
