# Jayesh resume reproduction

Both supplied workspace PDFs are byte-identical (SHA-256 `3cb198dccefc361de5335de139c40b595548d3beb28b6f25f0d5037dd14b9dd8`). Both were included and independently processed. They are a single unique three-page resume, not two independent layouts.

Settings: YOLOX, 200 DPI, English Tesseract, no table-structure inference, explicit last-modified metadata; see tests/settings.json. Full original and port JSON outputs are in reports/comparison. Each run produces 49 elements; entire ordered dictionaries match exactly, including coordinates and all metadata. Only the public API's additional reading_order field is removed before comparison. No metadata fields are ignored or rounded.

## Reproduced boundary problem

On PDF page 2, the second visible bullet is “Investigated and resolved upload-related exceptions and STP breaks…”. Visual inspection of the rendered source page confirms the bullet belongs to that paragraph. Both original and port instead emit:

- Element 22 (one-based): ListItem with the paragraph text but no bullet. Pixel-space box: `(191.20884704589844, 221.37733459472656)` to `(1409.25146484375, 314.25)`.
- Element 23: separate UncategorizedText containing only `•`. Box: `(183.4027777777778, 222.58333333333331)` to `(200.84722222222223, 250.3611111111111)`.

The detached marker is also ordered after the paragraph. This is a concrete original block boundary and reading-order artifact reproduced by the port. The boxes partially overlap horizontally; the original merge/cleanup and sorting behavior is preserved.

## Other observed original behavior

The page-1 CORE COMPETENCIES grid is a single Table element (element 6), with flattened text interleaving columns when table structure is disabled. Both implementations preserve that output. Generic types such as Title, NarrativeText and ListItem remain generic; no resume section or job-entry grouping is added.

Strings such as EEDUCATION and AACHIEVEMENTS & CERTIFICATIONS also match in both outputs. This report does not classify these strings as detection mistakes without independently verifying their source text. A full ordered-output match establishes reproduction on this input and configuration; it does not establish correct extraction or universal equivalence.
