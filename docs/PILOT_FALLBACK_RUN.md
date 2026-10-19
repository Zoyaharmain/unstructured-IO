# Run exactly the selected 15 resumes with local-first recovery

Run from `/home/gopal/unstructured-IO` in WSL. The runner uses `ground_truth/selected_15_resumes.json`; it does not select the first 15 directory entries or scan the remaining collection. All 15 source hashes must match before processing starts. Original sources, annotations and previous results are not edited. Use a fresh output directory each time.

Local only, no DeepSeek:

```bash
cd /home/gopal/unstructured-IO
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/check_pilot_fallback.py \
  --folder '/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT' \
  --output "reports/pilot-local-$(date +%Y%m%d-%H%M%S)"
```

Live document-level fallback, only after authorizing transmission of full extracted text (including contact details) to DeepSeek:

```bash
cd /home/gopal/unstructured-IO
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/check_pilot_fallback.py \
  --folder '/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT' \
  --output "reports/pilot-fallback-live-$(date +%Y%m%d-%H%M%S)" \
  --use-deepseek
```

Put DEEPSEEK_API_KEY in the ignored local .env or environment; the script never prints it. Existing provider model/base settings are honored. It does not make a separate credential-check request.

## Actual stages

1. Fresh fast PDF extraction. Empty extraction alone triggers one local OCR retry.
2. BERT/K-means block detection.
3. Up to two local recovery calls while meaningful spans remain unassigned. Stop immediately when unchanged; repeatedly running deterministic logic on identical input cannot guarantee improvement.
4. If meaningful spans remain and --use-deepseek is enabled, call the existing DeepSeek reviewer for that document. Full extracted source provides context; the existing reviewer can review/reassign all its spans. Locally complete documents never trigger a provider call under this policy.
5. Exact source-interval accounting and separate extraction diagnostics. Repeated text and independent-parser differences require PDF review, not blind deletion or forced assignment. Authentication/balance failures stop further provider use.

## Results

Open the new output directory's report.md, per-resume.csv and summary.json. results.json includes each retry, fallback trigger, remaining spans, source diagnostics and actual API/token usage. documents/ holds local extraction and local/final blocks; provider-decisions/ holds private provider responses for files actually sent. Preserve this directory privately because it contains resume personal information.

Coverage is not accuracy. A locally complete but wrongly assigned document is skipped by this fallback policy. Missing PDF text is not repairable by an LLM that never received it. Work/education relationship accuracy requires independent source-backed human decisions. semantic_accuracy and word_accuracy therefore remain null until genuine approved references exist. There is no automatic gold promotion or full-collection run.
