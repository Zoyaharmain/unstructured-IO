# Inline certification record boundaries

The source-local certification recovery previously recognized separate source blocks and a narrow pipe-before-Workshop/Certificate/Diploma pattern. An entire middle-dot-separated inventory stayed in one source block and one entry; `credential_values` then selected that entire row as one name.

`local_api/services/certification_integrity.py::inline_credential_cuts` now recognizes top-level middle dots, bullets, semicolons and pipes in certification content. It uses the existing certification label registry and detail recognition to retain metadata with its title. Parentheses/brackets protect internal punctuation. Commas, slashes, ampersands, dashes and plain line wrapping do not create boundaries. Bare alphabetic fragments and narrative cues remain conservative. Issuer-like fragments are not extra certificates. No candidate names or certificate-name catalog was added.

`recover_certification_cards` creates exact non-overlapping source spans for each inline title. `resume_structure.py::entry_groups` makes these distinct entries even when the same source element also contains labelled metadata. `credential_values` extracts each title without the trailing list separator. `repair_review_certifications` restores the affected source-supported cards if field review merges or omits them, without replacing unrelated certification records.

The supplied example exports six certifications through the restarted local API with no provider calls. Names and their source evidence are preserved; issuer, dates, IDs and URLs remain null when unstated. See `corrected-consumer.json`. Tests cover alternate separators, repeated mapping, unchanged source text, exact source validation, metadata ownership, name punctuation, line wrapping, issuer pipes and a mocked model merge. This is a structural improvement, not a claim that arbitrary ambiguous prose can always be classified automatically.

Validation: 867 passed, 2 skipped, 15 deselected in 74.48 seconds for the unit/mock-provider/API-integration/local-model selection. Two existing Node frontend checks were excluded; no frontend changes were needed for this fix. `git diff --check` passed.
