# Main commands used for this offline follow-up

No DeepSeek requests were made. Intermediate replay directories were preserved; final evidence is in final-offline-audit and complete-tests.

```bash
.venv/bin/python -B scripts/audit_batch50_repairs.py \
  --run reports/pilot-50-review-20261020-batch1 \
  --output reports/batch50-fix-investigation-20261020/final-offline-audit

.venv/bin/python -B scripts/batch_check_resumes.py \
  reports/batch50-fix-investigation-20261020/fresh-local-pdfs \
  --output reports/batch50-fix-investigation-20261020/fresh-local \
  --workers 1 --timeout 120

PYTHONPATH=src:. .venv/bin/python -B \
  reports/batch50-fix-investigation-20261020/reproduction/check_batch_words.py

PYTHONPATH=src:. .venv/bin/python -B \
  reports/batch50-fix-investigation-20261020/complete-tests/run_tests_offline.py
```

The fresh-local directory contains exactly four hash-bound copies. The word check is bounded to the five previously flagged PDFs and runs offline. The regression wrapper removes the provider key and blocks non-loopback sockets. Do not overwrite prior outputs to reproduce; use a new output directory for the replay. These commands do not perform a paid provider retry.
