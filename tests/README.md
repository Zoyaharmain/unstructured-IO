# Test tiers

Pytest imports both the repository-root `local_api` package and the legacy
`src/pdf_hires` package through `pyproject.toml`. Provider tests are excluded
by default. Ordinary test runs also remove provider keys and disable review.

```bash
# Fast deterministic CI (unit/schema plus mocked-provider behavior)
python -m pytest -m "unit or mock_provider"

# In-process local HTTP contracts; no external services
python -m pytest -m api_integration

# Mocked/replayed provider and recovery behavior; no provider calls
python -m pytest -m mock_provider

# Real PDF/OCR/hi_res extraction; requires local system/model dependencies
HF_HUB_OFFLINE=1 python -m pytest -m extraction_slow

# Real cached Sentence-BERT/K-means section detection
HF_HUB_OFFLINE=1 python -m pytest -m local_model

# Live provider stage: empty unless explicitly added and separately authorized
python -m pytest -m provider
```

Every collected test receives exactly one primary tier in `tests/conftest.py`.
Tests that use a provider name but inject or replay the response belong to
`mock_provider`, not `provider`. A live-provider test must carry the `provider`
marker explicitly and is never part of the default `pytest` command.
