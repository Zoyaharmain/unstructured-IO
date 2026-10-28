# Detected contact blocks not reaching schema fields

## Cause established in code and regression tests

The previous unique-contact recovery searched only personal_information.
Detected contact source blocks could remain in needs_review or be classified
as skills/summary. Both local mapping and optional field review then searched
an incomplete header, so detecting text did not imply assigning it to a contact
schema. Email-ID and Contact No label variants were also missing from aliases.
No exact uploaded response/file was supplied for this turn; tests reproduce
this assignment gap explicitly rather than claiming an unsaved live capture.

## Fix

contact_sections.py adds conservative source-preserving routing for explicit
candidate contact lines on the first page from unassigned/skills/summary spans.
References, established job/education records, later pages and ordinary job
prose are not searched. Unlabelled raw contacts are eligible only before body
content. Original text, element indices and character offsets remain unchanged.
Affected record references and canonical text are updated; recovered sources
are exposed in meta.reviewed_sections so the UI and mapper agree.

The section API applies recovery after placement review; map_schema also applies
it for existing saved/direct API sections. map_with_field_review uses the same
recovered source owners before constructing provider context. Local mapping
and reviewed recovery share literal contact matching, including plus-addressed
emails and common international phone formatting. Unique values get exact
source evidence; missing/ambiguous values are not invented.

A saved Aditya PDF regression exposed phone/email text joined without a space.
The matcher now separates a ten-digit phone prefix from an email only when an
explicit country-code prefix occurs immediately before it. Plain numeric email
local parts remain intact. The full original source text is retained.

## Verification

Focused contact/saved-resume/assignment tests passed (52 tests). The API suite
passed 5 tests, including section detection -> recovery -> schema assignment
with review mocked out. A synthetic request to the running local API with
review_fields=false returned both contacts and zero provider calls, recovering
two source blocks. Tests cover request immutability, source-range validation,
reference isolation, misplaced contacts, reviewed prompt ownership, digit-leading
emails, joined phone/email, ambiguous values and dates.

The older test expecting explicit misplaced contacts to remain unmapped was
updated to assert the requested corrected behavior and recovery provenance.
The first broad run also caught the joined-phone/email case above; both failures
were resolved before the final clean full-suite run. No paid calls were made.

Final broad run: 600 passed in 110.43 seconds. An additional inline-heading
regression was then added: actual contact values incorrectly tagged as a
structural heading are retagged as contact content without duplicating spans.
A final focused run covers that case alongside the saved-resume, provider,
assignment and contact suites. Original requests remain immutable, and the
normalized sections still pass exact source-range and hierarchy validation.
Final focused result after inline-heading handling: 121 passed in 17.76 seconds.
Compilation and git diff --check passed. No paid calls were made.
