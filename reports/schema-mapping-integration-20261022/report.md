# Schema mapping integration review — 22 October 2026

**Implemented a schema-mapping stage after the existing text extraction and Sentence-BERT/seeded K-means section stage.** It consumes the exact element inventory and complete section response, and returns the handoff's ResumeSchema contract with provenance and unresolved-field warnings. No external provider requests were made during integration or validation.

## ZIP review

Reviewed the user-provided Windows handoff ZIP and installation guidance. Verified **239/239 manifest checksums**. The unchanged target models, specification and service helpers are retained under `local_api/vendor/handoff_schema`, with archive/file hashes in `PROVENANCE.json`.

The standalone handoff is a complete parser, not just a field mapper. Its orchestrator re-segments raw text and may invoke OpenAI depending on environment settings; its fallback supplies placeholder contact/education/role values, a default language, document-year experience estimates and truncated responsibility lists. Directly running that parser on the current source inventory would lose important section/record boundaries and uncertainty. The host adapter instead uses its contract and helper functions on the existing source sections and record proposals. The full upstream provider orchestrator and standalone upload/path routers are not called or mounted. Instructor is not needed for this local schema-mapping path; no replacement Instructor was downloaded.

## Added API and UI

| Method | Route | Behavior |
|---|---|---|
| POST | `/api/v1/resume/schema` | Map existing `elements` plus `sections` into the handoff response contract |
| GET | `/api/v1/resume/schema/definition` | Target ResumeSchema JSON Schema |
| GET | `/api/v1/resume/schema/mapping` | Mapping specification and integration semantics |

The frontend now offers **Map to schema**, an inspectable JSON preview and **Download schema JSON** after section grouping. Upload/regroup resets abort stale mapping requests and invalidate previous results. Source text is displayed through text nodes. JavaScript syntax checks passed; this pass did not run browser automation.

The adapter validates exact extracted-source coverage, canonical section text, record ownership and field references before mapping. The same validator now lives in `local_api/services/source_validation.py` and is imported by the existing batch audit, so the installed API has no dependency on an unpackaged `scripts` directory. Validation behavior was preserved.

Existing input sections and records are not regrouped or reclassified. Each mapped value has source evidence; record warnings and unknown text remain available. Missing required strings are empty strings for handoff compatibility and are listed in `meta.missing_required_fields`. Optional missing fields are null or empty lists. No fabricated universities/roles/responsibilities, default English or career span derived from unrelated dates is added. Skills not covered by the handoff dictionary remain in `all_skills`; C#/C++ punctuation is handled. Employer-first and role-first pipe headers, and dated organization headers without company suffixes, have dedicated regression coverage.

The handoff's confidence scores remain fixed heuristic values, explicitly labelled as uncalibrated. Its completion percentage covers 16 reporting groups and is not a probability or whole-schema accuracy score. Non-resume documents retain their source text while candidate fields remain empty.

## Validation

- **304 tests passed in 87.80 seconds** after the final mapper changes: [full regression log](final-tests/regression.log), [JUnit results](final-tests/tests.xml).
- All **350 distinct saved live-document artifacts** passed schema-response validation, source input immutability and candidate record-boundary count checks: [summary](saved-document-summary-final.json), [per-document results](saved-document-results-final.json), [source index](validation-source-index.json).
- The previously consolidated local-repair index is absent in this checkout. The compatibility check therefore reconstructs the latest available **live** artifact per PDF hash from saved manifests; offline replay folders are excluded. It does not claim to have tested removed local-proposal artifacts. Existing deleted files were not restored.
- **340/350 documents have at least one missing required field**, including out-of-scope documents. These are explicit incomplete mappings, not schema-validation failures, and their missing values were not invented. Record/section semantic correctness remains unmeasured.
- Real in-process HTTP sequence **text extraction → cached Sentence-BERT/K-means section API → schema mapping** returned **200 → 200 → 200** on the existing PDF fixture, with 55 source elements and four proposed sections. Provider section review was disabled and zero external socket attempts occurred: [HTTP smoke result](http-pipeline-smoke.json).
- Built the project wheel offline, verified inclusion of the new routes, shared validator, handoff contract/provenance and frontend assets, then exercised its real mapping/definition HTTP endpoints outside the source checkout: [wheel build](wheel-build-final.log), [installed-wheel check](installed-wheel-check.log).
- Vendored source hashes still match the original handoff. JavaScript syntax checks and `git diff --check` passed. No paid API calls were made.

Schema-valid output means the API contract is compatible. It does not certify the previously identified source/relationship problems in the 350-document corpus. Every mapped result remains provisional and exposes its evidence/missing fields for review.

## Use it

Restart the existing API process to load the added routes. No separate handoff server or API key is needed for mapping. See [the complete integration guide](../../docs/SCHEMA_MAPPING_API.md) for the startup command and Python sequence using all three existing/new endpoints. [Example request](example-request.json) and [example response](example-response.json) are generated from a synthetic source-bound fixture.

```bash
DEEPSEEK_REVIEW_ENABLED=false .venv/bin/uvicorn local_api.app:app \
  --host 127.0.0.1 --port 8000
```

This example disables optional provider review for the section stage. Mapping itself makes zero provider calls regardless of ambient provider keys. Open `/docs` for the added API contracts or use **Resume sections → Map to schema** in the UI.
