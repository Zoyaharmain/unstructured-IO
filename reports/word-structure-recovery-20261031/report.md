# DOCX source structure, dated records and profile links

## Root causes found in the actual document

The original DOCX contains four dated employers, three dated education entries,
three named projects, and visible LinkedIn/portfolio URLs. The information was not
missing from the document. The old local reproduction retained four date groups
but assigned narrative or joined title/company text to employer fields. The user's
reviewed output further lost record identities and returned an empty education row.

1. Role and employer share a line without a delimiter. The original field parser
   relied on pipe/dash/comma component matching and could instead choose a later
   narrative sentence containing a job-related word. A literal citation proved
   that text existed, not that it named an employer.
2. Education dates precede qualification titles, and the titles are not tagged as
   separate Title elements. Multiple qualifications were grouped into one entry;
   the cautious refiner then cleared ambiguous fields. Generic source runs were
   not available to identify an institution following an undelimited major.
3. The visible LinkedIn URL is split by spaces and a second paragraph; the portfolio
   hostname has a space inside its TLD. The stored hyperlink relationships point
   only to incomplete/root destinations, so those targets cannot supply the missing
   profile path. Visible source text contains all required URL characters.
4. The project names are short named Word list items rather than Title elements;
   grouping could treat several projects as one description.

## General implementation changes

- Extract exact Word paragraph/run and hyperlink-relationship evidence into
  metadata without rewriting visible source text. A valid HTTP(S) hyperlink target
  behind a plain label can become a separately attributed source element, rather
  than an inferred destination. Source targets and displayed text remain distinct.
- Resolve undelimited role/employer headers only in a dated record's opening source
  region, using title grammar and organization/location structure. No employer
  dictionaries or candidate-specific strings were introduced.
- Reject first-person narrative as an employer/role in field validation. Recover
  a strong dated header from that record's own source; otherwise retain uncertainty
  instead of accepting a sentence as an identity. Keep separately dated records
  when provisional review merges or empties them.
- Start education records from dates followed by a qualification, or a source-named
  program followed by an institution. Use exact title/run boundaries for qualification,
  subject and institution. Preserve completion months and do not infer start dates
  or a qualification level that the source does not state.
- Route complete literal profile URLs and supported wrap continuations from the
  opening contact region. Rebuild citations for the original raw value before
  normalizing whitespace. Remove whitespace only at URI separators or a split TLD
  before a path; no URL letters, path, domain or profile ID are supplied from memory.
  Ordinary prose spaces and bare profile labels remain invalid. Known profile
  domains require their real host/subdomain, not a lookalike suffix.
- Treat linked contact labels as contact context, not a body-section boundary.
  Keep reference/company-body URLs out of candidate-contact recovery.
- Recognize source-named short project list items and bold project titles while
  excluding action prose and project field labels.

Main code: local_api/services/word_source_structure.py, dated_record_headers.py,
dated_record_recovery.py, education_header_fields.py, profile_url_recovery.py,
text_extraction_service.py, record_subfields.py, resume_structure.py,
schema_mapping.py, contact_sections.py, employment_integrity.py,
llm_schema_mapping.py and standardization/contacts.py.

A scan of the new production modules found no candidate name, employer, school or
candidate URL from this example. Generic fixtures use fictional identities.

## Verified actual-document results

| Employer | Role | Source date range |
| --- | --- | --- |
| US Technology International Private Limited | Lead Data Scientist | February 2025–Current |
| Dark Matter Technologies | Application Programmer IV - AI/ML | September 2023–October 2024 |
| Black Knight | Application Programmer IV - AI/ML | November 2022–September 2023 |
| Thomson Reuters | Content Technical Specialist | March 2019–August 2022 |

| Qualification | Institution | Source completion date |
| --- | --- | --- |
| PG Certificate Program | Indian Institute of Technology | May 2022 |
| Bachelor of Science - BS | Annamalai University | September 2012 |
| PRINTING TECHNOLOGY | Government Institute of Printing Technology | December 1996 |

Qualification titles and subjects are kept literal. PRINTING TECHNOLOGY is not
expanded into a guessed diploma or degree level. Unknown education start dates
remain null. Normalized completion dates preserve months: 2022-05, 2012-09, 1996-12.
The three source-named projects remain separate: ZQL UI, Multi Tenancy Client,
and Q-Manager.

Normalized LinkedIn: https://www.linkedin.com/in/leela-sankar-chaganti-a4797743/

Normalized portfolio: https://www.datascienceportfol.io/leelasankar

Both values use only visible source characters, with whitespace removed and applied
url_whitespace_repaired warnings. They are not externally verified destinations.
The incomplete Word hyperlink targets remain in extraction metadata. No GitHub
profile URL is stated; github_url remains null. GitHub Actions is not a profile URL.

## Verification

**852 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider, API
and cached local-model regression selection. External-provider tests and two Node
diagnostic tests were excluded; Node-dependent tests skip when Node is unavailable.
`git diff --check` passed.

The baseline and updated visible element texts are identical. Word evidence was
added as metadata; the uploaded document is processed in memory, not edited.
Both the real cached local-model path and deliberately incomplete mocked field
review returned four supported jobs, three qualifications and the two URLs.
The mock collapsed employment/education records and omitted profile fields;
source-backed recovery restored them and normal hierarchy/source validation passed.
No actual candidate data was sent to an external provider for these checks.

The restarted API passed the actual-source assertions in **0.460 seconds** for
local schema mapping. This excludes extraction/model initialization and external
LLM latency. This verifies the stated fields for this source and the regression
fixtures, not universal semantic accuracy on every unseen document.

## Artifacts

- before-extraction.json / before-sections.json / before-mapping.json: baseline.
- after-extraction.json / after-sections.json / after-mapping.json: fresh DOCX replay.
- local-consumer.json / mock-reviewed-consumer.json: verified normalized outputs.
- local-mapping-verified.json / mock-reviewed-mapping-verified.json: source schemas.
- corrected-consumer.json / live-mapping.json / live-check.json: restarted API output.

App restarted: http://localhost:8080. Re-extract the original DOCX before generating
new JSON so the new Word run/relationship metadata is present. Previously saved
or downloaded files are not overwritten.
