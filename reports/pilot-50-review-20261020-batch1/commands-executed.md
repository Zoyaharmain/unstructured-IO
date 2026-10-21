# Commands executed for this run

The provider preflight used the existing `check_connection()` function with the private key loaded from .env and review enabled. It made GET /models only, returning ready for deepseek-flash. The provider batch itself also performs its existing GET /models check. These two credential/model requests do not transmit resume text and are separate from the 58 classification requests reported.

Local stage only (no resume-review requests):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/run_pilot50_review.py \
  --output reports/pilot-50-review-20261020-batch1 --local-only
```

After all 50 local records were processed successfully, provider stage:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/run_pilot50_review.py \
  --output reports/pilot-50-review-20261020-batch1 --resume
```

Exact underlying CLI argv and start/finish timestamps are in manifest.json. The wrapper invokes existing batch_check_resumes.py with two workers and a 120-second per-document deadline; then llm_verify_resume_batch.py with two workers. The input directory contains only 50 hash-verified PDF copies. No whole-collection folder is passed to either processing stage.

Offline regression suite (API key removed, external sockets blocked):

```bash
PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 timeout -k 5 240 \
  .venv/bin/python -B reports/pilot-50-review-20261020-batch1/tests/run_tests_offline.py
```

Result: 199 passed in 83.96 seconds; zero deselections, zero failures, zero external network attempts in tests. Tests use fixtures and mocked provider responses, not additional corpus/provider requests.

Read-only report generation:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/report_pilot50_review.py \
  --run reports/pilot-50-review-20261020-batch1
```

The reporter was rerun after adding CSV token columns and an empty-independent-PDF-text diagnostic; it reads saved artifacts, runs independent Poppler text diagnostics on these same 50 PDFs and never calls the API or production models.

To resume an interrupted run, use the same --resume command only while source hashes, pipeline code/configuration hashes and model/base configuration match. Valid checkpoints are reused. It does not automatically retry failed paid reviews. A completed run skips the provider stage. Do not delete checkpoints to force completion.
