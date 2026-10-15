# Local API validation

The authoritative extraction library is installed editable from `/home/zoya_harmain/unstructured`. The source-path test unwraps the telemetry decorator and verifies that `partition()` resolves to `~/unstructured/unstructured/partition/auto.py`. The extraction checkout's tracked and untracked changes are the same as before this task; no extraction algorithms were edited.

## Method

Tests call the source library directly with a BytesIO containing each fixture, then upload identical bytes and equivalent settings to the API. They compare the complete ordered serialized element dictionaries. The direct result passes through standard JSON encoding/decoding because original coordinate tuples are JSON arrays on the wire. No field is omitted, rounded, text-cleaned or reordered.

Settings: English, YOLOX, 200 DPI, no table inference, no page-break insertion, starting page 1, fixed last-modified metadata. Full JSON parity includes original text, type, IDs, page numbers, geometry, reading order and all metadata. The top-level text, filename, requested strategy, element count and page-number set are also checked.

## Results

All 32 API tests passed in 73.62 seconds. All eight PDF/strategy comparisons matched, plus direct TXT and blank-PDF comparisons. The four retained legacy-port tests also pass. Real HTTP smoke checks passed. One Starlette test-client deprecation warning remains. See `reports/api-summary.json` for the comparison matrix.

## Evidence

- `reports/api-tests.log` and `reports/api-tests.xml`: HTTP contract tests and direct extraction comparisons.
- `reports/api-parity/`: direct element JSON and full API envelope for each PDF/strategy pair.
- `reports/api-environment.json`: source path, source hash/Git HEAD and installed dependency versions.
- `reports/http-smoke.json` and `reports/http-smoke-server.log`: temporary real Uvicorn server, successful GET /health and multipart POST /v1/partition. The server was stopped afterward.
- `reports/api-wheel-build.log`: installable wheel build; the wheel contains local_api/app.py and upstream license notices.

Test cases cover all four strategies on Jayesh's three-page resume and a generated two-page PDF, non-PDF TXT parity, valid blank PDF parity, preservation of empty elements and element order, aggregate text and page numbers, invalid strategy, missing/empty filename, empty input, uploads at/over 25 MiB, unsupported input, actual malformed/password-protected PDFs, missing dependencies (including wrapped ImportError), and unexpected processing failures without exception leaks.

## Original Jayesh behavior

The explicit hi_res comparison returns 49 elements in both paths. On page 2 the “Investigated and resolved upload-related exceptions…” paragraph is ListItem element 22 and its bullet is a separate UncategorizedText element 23 ordered afterward. This original boundary/order error remains visible. See `docs/JAYESH_FINDINGS.md` for the earlier visual inspection and geometry; current API/direct artifacts are `reports/api-parity/Jayesh Yadav-CV.hi_res.*.json`.

## Limits

Successful parity on these inputs/settings does not prove all documents, languages or optional features equivalent. All other document types use upstream dispatch, but TXT is the non-PDF type explicitly tested. Optional format dependencies and model assets must be installed. Image processing, optional table inference, alternate OCR engines, and every possible failure mode were not exhaustively tested. Original strategy fallback behavior is retained; requested_strategy reports the submitted strategy.

In this environment sandboxed TestClient calls stalled in AnyIO's thread/event-loop transport even for /health. The tests were run successfully outside that sandbox; this did not require changing API/extraction behavior. Tests exposed and resolved a JSON tuple/array comparison issue and missing PDFium exception mapping. Server responses contain structured errors and no tracebacks; logs retain diagnostic exceptions.
