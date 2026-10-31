# Certification identity versus credential metadata

## Root cause

The card grouper recognized colon-labelled metadata but did not recognize
`Certification #…`, `Issued July …`, `Valid through …` or `Verify:` consistently.
A new extracted source element could therefore create another certificate whose
name was its credential-ID/date row. The verification row also crosses a PDF
layout lane. In this extraction the date row and verification row are joined into
one source element, so consuming an entire trailing string as an expiry date
would incorrectly include the verification URL and search instructions.

## General correction

`local_api/services/certification_integrity.py` identifies detail rows by their
explicit ID/date/issuer/verification labels. The card grouper in
`resume_structure.py` attaches adjacent same-page details to their preceding named
credential, allowing a wide continuation row without borrowing a separate column.
New named credentials still start new cards. Original source spans are preserved,
including zero-length elements from saved extractions.

The source-backed refiner extracts literal IDs, bounded calendar date phrases,
issuer and URL tokens. It does not put registry search instructions into a URL or
create a certificate identity from an orphan detail row. Names and issuers are
separated only with supported source-header structure. Conflicting metadata is
retained for review rather than guessed. No name, credential number or candidate-
specific matching rule was added.

A named workshop following a pipe is separated from the preceding diploma's
wrapped explanatory text, preserving exact source offsets. Provisional LLM output
that splits a named credential's metadata into another record is repaired only
when both records belong to the same established local source card, followed by
normal source/hierarchy validation. Scalar conflicts retain the existing rejection/
repair diagnostics. Code is integrated through local_completion.py,
record_subfields.py and llm_schema_mapping.py; external review instructions also
explicitly distinguish certificate names from credential metadata.

## Verified result for the supplied PDF extraction

The PMP is **one record**:

- Name: Project Management Professional (PMP)®
- Issuer: Project Management Institute (PMI)
- Credential ID: 4459787
- Issue date: 2026-07
- Expiry date: 2029-07
- Verification URL: https://pmi.org/certifications/certification-resources/registry

The PG Diploma — Data Science & Machine Learning with AI and the AI Tools Workshop
remain separate credentials. The workshop retains its source provider Be10x and
source year 2026. The three resulting identities replace the prior incorrect
three-card interpretation (PMP title, PMP metadata, merged diploma/workshop).
No issuer/year is invented for the diploma where the source does not state one.

Both saved-section replay and fresh real local-model detection passed the same
assertions, with no source-binding errors or external provider calls. The prior
two-employment-record result, September 2013 start, 128-month HSBC duration and
13.0-year total remain intact. These checks inspect the actual saved extraction;
they are not a claim of universal semantic accuracy on unseen documents.

## Validation and artifacts

**822 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider, API
and cached local-model regression selection. External-provider tests and two Node
diagnostic tests were excluded; Node-dependent tests skip where Node is unavailable.
`git diff --check` passed.

The restarted local API returned the correct consumer JSON in **0.372 seconds**
without external provider calls. This is local schema mapping, not LLM latency.

- `checks.json`: saved/fresh local-model results and exact fields.
- `saved-mapping.json`, `fresh-mapping.json`: source-to-schema records/citations.
- `saved-consumer.json`, `fresh-consumer.json`: default normalized exports.
- `corrected-consumer.json`: actual response from the restarted API.
- `live-check.json`: API assertions, timings and preserved employment checks.

App: http://localhost:8080. Regenerate schema output to apply the changes; existing
JSON downloads are not overwritten.
