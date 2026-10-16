# Resume Inspector

The existing FastAPI app now serves the verification UI at `/`; interactive API
docs remain at `/docs`. The current Dockerfile includes the UI, its local assets,
and the existing extraction implementation. No frontend build or Node runtime
is required in deployment.

## Review a resume

1. Open the app, select or drop one PDF/DOCX, choose a strategy, and click
   **Extract & inspect**. DOCX uses auto; PDF supports the existing four strategies.
2. Compare the original on the left with the returned blocks on the right. The
   original PDF uses the browser viewer; DOCX uses a sandboxed browser renderer.
   DOCX layout/pagination may differ from Word. **Open ↗** opens the original file
   separately if the embedded viewer is unavailable.
3. Review word, character and block counts. The pages metric only counts distinct
   page numbers on nonempty elements, and shows Unknown without page metadata.
   It does not invent a total page count.
4. Search blocks, filter their types, inspect metadata, and select a block to jump
   to its PDF page when available. Blocks retain original extraction order.
5. Use Plain text for copying, or download the actual response as JSON.
6. For word verification, copy checked text from the original resume into the
   Word comparison tab and click Compare words. Missing reference words are red;
   additional extraction words are green. Repeated words are counted, whitespace
   is normalized, punctuation is compared, and case can optionally be ignored.

Reference coverage is the percentage of pasted reference tokens matched in
reading order. Rearrangements can count as missing and added. This is not an OCR
confidence score or proof that the entire document was captured. Formatting,
coordinates, block classification and block boundaries require visual review.
Scanned resumes need a manually checked reference for reliable word comparison.

## Implementation

- `local_api/static/index.html`, `styles.css`, `app.js`: responsive, accessible
  upload, original/extraction panels, filters, tabs, comparisons and downloads.
- `local_api/static/docx-preview.html` and `docx-frame.js`: sandboxed DOCX rendering;
  document content cannot access the parent UI. Network requests are disallowed
  by the frame CSP. HTML alt-chunks are not rendered.
- `local_api/static/vendor/`: pinned JSZip 3.10.1 and docx-preview 0.3.7 assets
  with their original licenses and provenance. No CDN is needed at runtime.
- `local_api/routes/comparison.py`: deterministic ordered word comparison using
  Python difflib, independent of extraction. Limits: 100,000 characters and
  5,000 words per input. This endpoint does not run AI or alter extracted text.
- `local_api/app.py`: serves UI/static routes, retaining all extraction endpoints.
- `pyproject.toml`: includes the static assets in package data.

No upload, reference or result is persisted by the UI. Data is held in browser
memory; the existing API upload cleanup remains in force. User-triggered JSON
exports are saved locally. DOCX preview is local to the browser; extraction and
comparison use the same application server. No document contents are placed in
URLs or logs by the UI/comparison code.

## Executed verification

Python tests: **62 passed, 8 deselected in 11.54s**:

```bash
DO_NOT_TRACK=true NUMBA_CACHE_DIR=/tmp/extraction-package-numba \
MPLCONFIGDIR=/tmp/extraction-matplotlib OMP_NUM_THREADS=2 \
.venv/bin/python -m pytest tests/test_verification_ui.py \
  tests/test_text_extraction.py tests/test_local_api.py \
  -k 'not direct_extraction_parity' -q
```

Includes static routes, comparison edge cases and existing real extraction/OCR
regressions. The eight historical model-parity cases were excluded. New
comparison tests cover duplicated words, substitutions, reordered words, empty
extraction, punctuation/case controls, blank references and size limits.
Raw test results: `reports/resume-inspector-tests.txt`.

Chromium checks passed for real PDF/DOCX uploads and extraction, original preview,
block counts/search/selection, plain text equality, downloaded JSON equality,
missing-word highlighting, sandboxed DOCX rendering, mobile width and absence of
page errors. Browser tools were installed only in `/tmp`/the browser cache;
application deployment requires no browser-testing dependencies.
Evidence: `reports/resume-inspector-browser-check.json`; screenshots are in
`reports/resume-inspector-{empty,desktop,comparison,docx,mobile}.png` and use only
synthetic documents. Screenshots were visually inspected for desktop PDF/DOCX.

To start or rebuild the image, see [DEPLOYMENT.md](DEPLOYMENT.md). Restart your
running Uvicorn process or recreate your Docker container to load this update.

The refreshed Docker image `unstructured-text-api:local` (ID prefix
`9e541aa079b7`) built successfully. A temporary container with `--network none`
and `HF_HUB_OFFLINE=1` served `/`, `/docs`, the UI JS/CSS, DOCX frame and both
vendor scripts with HTTP 200. A real TXT extraction returned 200, and a comparison
against a reference with one extra word returned exactly one missing word. No
source directory or project mount was supplied. The verification container was
stopped after these checks; the image remains available for local use.
