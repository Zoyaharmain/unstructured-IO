# Shared education/certification headings and false credential identities

## Why the three records appeared

The combined heading was split into source fragments. Its `& Certification`
fragment was treated as a credential title, and the separate source date range
`2026–2029` was treated as another title. The certificate grouper did not recognize
an unlabelled date range as metadata, and strict lane matching did not join a
right-aligned date to its left-hand title.

Fresh extraction exposed an additional layout problem: the PDF parser labelled
bottom-of-page text as Footer and merged the degree plus AWS certificate into one
element, while merging both date ranges into another. Recovering only the old
JSON fragments would not fix this new-extraction path. The B.E. qualification
anchor also failed because dotted-abbreviation cleanup removed whitespace before
Computer, joining two words in the lookup representation.

## General corrections

- Combined Education/Certification headings and connector-prefixed heading
  fragments are structural context, never credential identities.
- Within an explicit shared heading, use original PDF source-line offsets to
  separate merged physical rows without rewriting source text. Classify literal
  degree rows as education and credential rows as certifications.
- Attach date ranges only using unique source-row alignment. Preserve ambiguous
  associations for review. No degree/certificate names or missing dates are invented.
- Treat date-only rows as metadata, never new named certificates. Orphan date rows
  remain retained without creating invented credential identities. A uniquely
  associated certificate range supplies its source issue/expiry years.
- Recognize right-aligned credential details by original row geometry rather than
  requiring matching column labels. Keep distinct named certificates separate.
- Preserve whitespace when normalizing dotted degree abbreviations for lookup.
  Source text is unchanged. This allows B.E. and its aligned dates to stay together.
- Provisional reviewed heading-only records are excluded from credential identities;
  date-only records are restored to their established named source card. Normal
  source, field and hierarchy validation remains in place.

Implementation: local_api/services/combined_credentials.py,
certification_integrity.py, resume_structure.py, record_relationships.py and
local_completion.py. No candidate-specific production rules.

## Actual PDF and API result

Freshly extracted the supplied Ashfaq Rahman PDF, ran the real cached local model
and mapped the source with no external provider calls. The result is:

- One education record: B.E., Computer Science and Engineering, Rao Bahadur College
  of Engineering; source dates 2012–2016.
- One certification record: AWS Certified Solutions Architect – Associate; source
  year range 2026–2029 maps to issue_date=2026 and expiry_date=2029.
- No credential named `& Certification` or `2026–2029`.

The actual PDF contains the 2026–2029 range aligned with the AWS row. The issuer,
credential ID and verification URL stay null where not explicitly stated. No
external validity check or issuer expansion was performed. Exact source bindings
were validated, and no source characters were dropped or duplicated.

The restarted API passed the same assertions in 0.421 seconds for local mapping.
This is not a live external-review latency or semantic-accuracy guarantee.

## Validation and artifacts

**841 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider,
API and cached local-model regression selection. External-provider tests and
two Node diagnostic tests were excluded; Node-dependent tests skip when Node
is unavailable. `git diff --check` passed.

- extraction.json: fresh locally extracted elements with original PDF row geometry.
- fresh-mapping.json: source-to-schema output, including evidence and recovered sections.
- corrected-consumer.json: canonical export from the direct local replay.
- live-consumer.json: actual canonical export returned by the restarted API.
- checks.json and live-check.json: fresh-source and API verification assertions.

Regressions cover shared-heading fragments, degree/date ownership, metadata-only
records, footer-merged rows, source immutability, reverse heading order, existing
PMP detail cards, and mocked model responses that split one certificate into three.
Unseen ambiguous layouts remain reviewable rather than being forced into a record.

App restarted: http://localhost:8080. Regenerate JSON to use the changes; old saved
and downloaded files remain unchanged.
