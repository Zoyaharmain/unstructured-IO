# Company and qualification mapping repair

Reproduced with the existing saved extraction inventory for G S Sandhya Rani.pdf,
and independently checked against PDF text. No paid requests were made.

Before: eight job records, five empty companies, one invented prose-based job,
and one education record containing both qualification source rows.

After: seven jobs: Capgemini, Accenture Solutions, Tata Consultancy Services,
and four distinct Wipro Technologies Ltd roles/periods. Clients remain separate
source context and do not replace employers. Education:

- B.Sc, Computers Science; S.S.G.S Degree College, Guntakal; 2011.
- Master of Software Engineering; BITS, Pilani; 2015.

Shared causes and changes:

1. Concatenated employer field hints included unrelated wrapped duties. The
   resulting company string failed literal evidence validation. A complete
   opening pipe-separated company/role header now overrides these polluted
   hints in `record_subfields.py`.
2. A wrapped phrase containing “role-based” was treated as a job header.
   `employment_header_fields` now rejects that capability wording.
3. Qualification segmentation depended on upstream Title typing, and the degree
   matcher omitted Master of Software Engineering. Independent qualification
   starts now establish education boundaries in `resume_structure.py`;
   `education_subfields.py` recognizes this degree and the explicit
   “from institution passing year” relationship, including acronym institutions.

Evidence checks remain enabled; no resume-name branches were introduced.
The raw extracted text inventory was not edited. Existing changes were preserved.

Validation: 61 affected structural/employment tests and 88 mapping, compact
provider, completion and cross-document regression tests passed (149 total).
Whitespace diff check passed. New tests are in
`tests/test_opening_identity_education.py`. The regenerated local output is
`local-schema.json` alongside this report. Fresh live DeepSeek output has not
been verified; these results establish the local repair and offline regressions,
not universal semantic accuracy.

## Follow-up: stated total and education subject

The first repair left two confirmed gaps: the stated-total matcher did not
recognize “11.8 years of IT experience”, and the education subject fallback
accepted “from BITS”. The shared matcher now accepts bounded experience
qualifiers; the education parser treats “from” as an institution relation and
extracts the explicit subject from the expanded degree name.

The regenerated local output has source-stated total_experience_years 11.8 and
second qualification field_of_study “Software Engineering”, institution
“BITS, Pilani”, graduation_year “2015”. 11.8 is preserved as stated decimal
years; it is not silently interpreted as eleven years eight months.
Chronologically calculated experience remains separate from this source claim.

Follow-up validation: 75 mapping/structural tests passed, followed by 19 tests
including new institution-preposition cases and cross-document education
regressions (the groups overlap). Diff whitespace check passed. No paid calls.
