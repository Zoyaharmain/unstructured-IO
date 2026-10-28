# Parent-section shape, omitted contacts and portable startup

## Confirmed live diagnostic

The running server logged reference 2e52cfa01f04479aa6b05583d8101b81:
parent_schema_validation / invalid_section at /sections/1, attempt 8.
parse_review emits this when a row does not have exactly category and records,
or records is not an array. Its previous static explanation incorrectly said
that a section was missing or duplicated. That is a different validation path.
The raw provider body was not retained, so its exact extra/missing property or
records type cannot be recovered from the log.

## Fixes

- schema_diagnostics.py gives invalid_section its own accurate explanation.
- llm_schema_mapping.repair_section_envelope normalizes an exact echoed label
  and a single complete record object returned in place of an array. These are
  unambiguous representation changes; all existing coverage, field, ownership
  and evidence validators run again before commit. Unknown keys, wrong labels,
  missing records and unsupported field values remain rejected.
- recover_literal_contacts fills omitted/unmapped email or phone only when the
  candidate's personal_information section contains one unique exact match.
  It preserves the literal formatting and source IDs, and validates the full
  result again. Plus-address emails and common international phone groupings
  are covered. Email digits and year ranges do not create phone values.
  Multiple candidates become ambiguous; reference contacts and other sections
  are never searched. A deliberately ambiguous field is not overridden.
- The local launcher no longer forces HF_HUB_OFFLINE=1 on machines without a
  cached model. Explicit user offline settings are respected. README documents
  requirements/constraints, Docker and initial model warming. Other operating
  systems were not provisioned or executed during this change.

## Controlled source replay

The saved Manjunath source was replayed with an intentionally echoed section
label and omitted email/phone fields. It completed with these repairs:
echoed_section_label_removed, unique_literal_contact_recovered(email), and
unique_literal_contact_recovered(phone), followed by full hierarchy validation.
This is a controlled regression using actual saved source, not the unsaved live
provider body. See verification.json and replay.schema.json. The replay mock
respects each requested batch's parent categories.

## Verification

Full offline suite: 592 passed in 118.86 seconds. After the final ambiguity
status adjustment, 88 focused tests passed; API diagnostics: 4 passed. A final
16-test contact/startup run additionally covers reference-contact isolation.
Python compilation and git diff --check passed. No paid calls were made.
The development app restarted at http://localhost:8012 with the updated startup
and mapping logic. Source text, original evidence and unrelated changes remain
preserved. No claim of perfect extraction or infallible LLM output is made.
