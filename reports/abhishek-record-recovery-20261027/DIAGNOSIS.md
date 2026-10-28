# Abhishek Kumar Singh: actual-resume diagnosis and fixes

Source: the exact PDF path supplied by the user. Offline Unstructured extraction
and section detection were run against that file with --local-only. The
original root extraction.json, sections.json and schema.json preserve the before
state. No paid calls were made.

## Actual defects

1. Employment headers used `Employer, Role`. employment_header_fields split
   pipes and dashes but did not support the comma form. Its role vocabulary also
   omitted Team Leader. All three companies could therefore remain empty.
2. reviewed_employment_groups did not reliably accept non-bold comma headers
   as boundaries, while bold technical category labels could create false
   boundaries. The local result had four job records, including one starting
   with Operating Systems / Servers / Cloud Services instead of an employer.
3. The right-aligned 08/2014–07/2018 education date was extracted into an earlier
   source element than the EDUCATION heading, so source-order context put it in
   experience. This polluted the third job's dates. The original PDF line
   coordinates place it on exactly the same row as the degree, to its right.
4. Education refinement could misread the month in a month/year range as an
   abbreviated graduation year.
5. The header phone source began with a layout pipe. The raw-contact routing
   checked the whole span as a phone, so it left that detected number unassigned.
6. Separately, valid LLM responses could declare company/role not_stated despite
   record-local source evidence. Previously those empty declarations were
   accepted without checking explicit source headers or validated local fields.

## Changes

- record_subfields.employment_header_fields: supports a short comma-separated
  role suffix, preserves employer commas/punctuation, recognizes Team Leader.
  Duty clauses and ambiguous combined headers remain excluded.
- resume_structure.reviewed_employment_groups: accepts explicit employer-role
  headers as anchors; technical category labels do not create job anchors.
- education_date_recovery.recover_education_dates: moves a date only when PDF
  coordinates align it to exactly one degree row on the same page, to its right.
  Text, element indices and offsets remain unchanged. It is applied in local
  recovery, after section review, and when mapping saved/direct sections.
- education_subfields: recognizes MM/YYYY ranges and does not confuse them
  with abbreviated years.
- contact_sections: ignores layout pipes only for header-contact recognition;
  the original source text remains unmodified and is cited literally.
- llm_schema_mapping.recover_record_fields: reconciles empty not_stated/unmapped
  record fields against explicit record-local labels/headers and supported local
  identities. It does not overwrite populated/ambiguous values, search other
  jobs, infer absent companies, or bypass full hierarchy validation. Supported
  existing local company/role values take precedence over a broader header
  alternative. Education dates with uncertainty findings are not promoted.

## Verified results

Three jobs, not four:

| Employer | Role | Dates |
|---|---|---|
| SLK Software | Team Leader | 01/2025 – Present |
| Impetus Technologies | SRE/Devops Engineer | 06/2021 – 12/2024 |
| Cavisson Systems | Software Engineer | 10/2018 – 05/2021 |

Education: Bachelor of Technology, 2014–2018. Email and phone are populated.
The final schema is final-local.schema.json. verified-reviewed.schema.json is a
CONTROLLED mock LLM omission replay against the actual extraction, not a live
provider response: all six company/role fields were deliberately omitted and
then recovered with record-local evidence. verify_recovery.py reproduces it.

Both revised source coverage and hierarchy evidence validators passed. Original
source text, source IDs, offsets and record relationships remain inspectable.
Remaining unassigned content/uncertain fields have not been fabricated or hidden;
this verifies the reported identity/date/contact problems, not perfect accuracy
for every field or every possible resume format.

## Tests

Full offline suite: 611 passed in 115.35 seconds. The final pipe-prefix fix adds
one further contact regression and is included in the final focused run. Tests
cover the actual extracted fixture, comma-company punctuation, separate jobs,
missing versus ambiguous identity, cross-job isolation, missing PDF geometry,
contact prefixes, and source immutability. No paid calls were made.

Final runtime verification: the actual saved extraction posted to the running
local schema API with review_fields=false returned three populated job
identities, both contacts, correct education graduation year, and zero provider
calls. Final API/actual-resume/contact/omission regressions: 19 passed.
See runtime-verification.json. git diff --check and compilation passed.
