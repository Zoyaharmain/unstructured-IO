# Nested section schema implementation

Implemented an additive section → record → attribute representation in the existing schema API and inspection interface. Existing ResumeSchema `data` and upstream extraction/block detection remain compatible. No provider calls were made for this implementation.

## Workflow reviewed

1. The text extraction endpoint produces immutable source elements with page metadata.
2. Local Sentence-BERT embeddings, seeded K-means and heading/layout rules detect section blocks. Local recovery may reconsider unresolved source spans; it does not create source text.
3. The reviewed section endpoint optionally uses DeepSeek for section assignment. The local endpoint avoids provider calls.
4. The schema endpoint consumes those exact source elements and section responses, validates interval and record bindings, then applies the existing local handoff mapping helpers.
5. The new nested stage reuses those record boundaries and typed values. Each section exposes records, each record exposes named attributes, and each scalar/list item has its own exact source citation. It makes no new model requests.
6. The single-resume feedback runner uses this same schema endpoint service internally; its saved schema JSON therefore includes the new nested representation. Its existing bounded recovery and optional read-only schema audit remain separate from this structural change.

The saved DeepSeek mapping scripts under the full350 report directory are a separate evaluation workflow. They are not the mapper behind the UI's Map to schema button. Adding nested fields locally does not integrate that evaluation runner into production.

## Delivered structure

`POST /api/v1/resume/schema` now returns `section_schemas` alongside the legacy envelope. `GET /api/v1/resume/schema/subschema-definition` exposes the nested contract.

- Personal information: full name, email, phone, location, LinkedIn, GitHub, portfolio and professional title.
- Experience: separate job records containing employer, role, dates, location, responsibility items and technologies.
- Education: institution, degree, specialization, years and grade. Explicit specialization/major/GPA labels can refine unresolved fields within their own record.
- Projects, certifications and categorized skills retain their existing typed attributes.
- Summary: individual source statements. Narrative content is intentionally retained as statements rather than converted into invented facts.
- Languages, awards, publications, volunteering and interests have conservative attribute slots. Compound facts require explicit labels; unlabelled source remains available for review.

Every emitted item cites a source block ID and a literal quote occurring in that block. Missing values remain unresolved, rather than being declared absent from the original PDF. Existing relationship warnings mark mapped attributes as needing review. Unmapped or partially consumed blocks remain in `residual_blocks`, including source from categories without safe attribute assignments. Unknown/non-resume content is preserved without candidate attributes.

The UI displays expandable section and record cards, field values, source quotations and unresolved text. It continues to offer the full downloadable JSON. Rendering uses textContent for source strings.

## Verification

The offline saved-source check reused Jayesh's existing extraction and pass-01 sections: **5 sections, 11 records, 82 populated attribute items**. All emitted source quotes occurred in their referenced blocks. Extraction runs: **0**; block detection runs: **0**; provider calls: **0**. See `saved-check.json` and `saved-jayesh-nested.json`.

Regression coverage includes individual citations, missing fields, invented values, record-local support, partial-block preservation, ambiguous associations, non-resume handling, HTTP serialization and the discoverable nested definition. **321 tests passed in 108.29 seconds** with external sockets disabled. The focused mapping, single-resume and local-inspection run passed **28 tests**. `node --check local_api/static/schema.js` and scoped `git diff --check` passed. Logs and JUnit results are recorded under `tests/`.

## Limits and next steps

This implements a traceable hierarchy; it does not certify that all resumes have correct segmentation, employer/date ownership or complete attributes. Conservative local rules leave unlabelled compound facts unresolved. A literal citation proves textual support, not semantic association. Existing training/research and expected-date uncertainties require source review; no automatic completion is claimed.

The existing full350 report records a halt at document 309, 300 schema-valid responses and nine quarantined JSON responses. Those are historical report claims, not a new audit of every PDF in this implementation. The report's acceptance/compliance percentages are not independent human accuracy measurements. Historical outputs were not rewritten.

Restart the API using your existing launcher, refresh the browser, group an individual resume, and select **Map to schema**. Inspect each section's attributes and source evidence, especially residual blocks. Review a varied small set against the original PDFs before using these nested records for downstream decisions or starting a larger mapping run.
