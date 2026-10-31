# Employment boundaries, responsibility ownership and month precision

## Root causes

An action-led responsibility beginning “Applied…” was accepted as a role/employer
header after splitting at an em dash. A wrapped “Completed…” bullet could also
create an independent employment anchor at the organization word in its continuation.
Some source elements contain multiple table records, so blanket rejection based
on the first words of a whole extracted element is unsafe. The final fix uses
ListItem provenance for wrapped-bullet context and preserves explicit worked-as
headers, multi-employer tables and project titles.

The PDF extraction has a literal joined boundary “Business TransformationSep 2013”.
The previous date matcher required a word boundary before the month and therefore
matched only “2013”. The month could remain attached to the mapped role, and the
duration calculator correctly refused a month-based duration from a year-only start.

## General fixes

- Recognize action-led Applied/Completed/Migrated prose and keep wrapped bullet
  fragments in their dated source employment record. Preserve complete contiguous
  source paragraphs instead of retaining only their first fragments.
- Repair previously generated source-bound entries only when clear prose continues
  an adjacent anchored record in compatible source/page/lane context. Keep source
  intervals and source evidence intact. Distinct explicit employer headers remain
  separate, including genuine company names containing action-like words.
- Recognize a capitalized calendar month joined directly to a preceding lowercase
  title character when it is followed by a full year and an explicit date range.
  Use the exact original substring; no month, date or missing space is fabricated.
- In provisional reviewed output, repair prose-only job splits only when the local
  source entry establishes the same owner. Restore richer month/year dates when a
  provider selected only the same year, and remove a month suffix from a role only
  when the exact source header supports the corrected role.
- Keep an independent/freelance role's generic practice area out of company names.
  A named employer is not invented for independent work. Both local and reviewed
  paths use the same source-backed interpretation.

Implementation: `local_api/services/employment_integrity.py`,
`record_subfields.py`, `resume_structure.py`, `local_completion.py`,
`llm_schema_mapping.py`.

## Actual-resume verification

Replayed both the existing saved sections and fresh real local-model detection on
the user's saved PDF extraction, with zero external provider calls. Both now yield
**two work records**, with all original source bindings valid:

1. Independent Consultant — Business Transformation, June 2024–Present. No named
   employer is stated by that header, so the practice area is not used as company.
   The full “Applied prior HSBC…” paragraph and the full wrapped diploma/internship
   paragraph remain responsibilities of this first record.
2. HSBC Electronic Data Processing India Pvt. Ltd., Program Manager, Business
   Transformation; **2013-09 to 2024-05**, **128 months / 10 years 8 months**.

The non-overlapping dated total is **13.0 years as of 31 October 2026**. The original
source claim, source duration and spelling/date correction metadata remain retained.

The restarted API processed the old saved section assignment locally in **0.414 s**,
returned two records and passed assertions for full duties, exact dates, duration,
total experience and the independent role's employer field. This is local schema
mapping latency; it does not measure external field-review latency.

## Evidence and limitations

Final offline regression selection: **818 passed, 2 skipped, 15 deselected**.
Includes unit, mocked-provider, API and cached local-model tests; external-provider
tests and two Node diagnostic tests were excluded. Node-dependent tests skip
when Node is unavailable. `git diff --check` passed.

- `saved-mapping.json`, `fresh-mapping.json`: source-to-schema outputs.
- `saved-sections.json`, `fresh-sections.json`: corresponding detection inputs.
- `saved-standardized.json`, `fresh-standardized.json`: normalization/audit results.
- `corrected-consumer.json`: actual default consumer JSON returned by the restarted API.
- `live-check.json`: live API assertion summary and zero-provider-call measurement.

New regressions exercise source-preserving wrapped duties, action-word company
names, joined-month boundaries, partial reviewed date/role values, reviewed prose
job splits and independent practice areas. Existing actual multi-employer table,
explicit worked-as, and project-title regressions are preserved. The source PDF
was not sent to an external provider; reviewed-output tests use mocked responses.
Other genuinely ambiguous or unstated fields remain visible for review, rather
than being invented. Passing these checks does not establish universal semantic
accuracy for every unseen resume.

App: http://localhost:8080. Regenerate schema output to apply the fixes to an
existing document; previously downloaded JSON is not overwritten.
