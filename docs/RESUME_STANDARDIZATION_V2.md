# Resume standardization version 2

Version 2 introduces a consumer JSON contract without replacing the source-bound
mapping contract used by the inspector and its evidence validation.

## Outputs and migration

- The inspector's JSON download uses `consumer_export` from the mapping response.
- `POST /api/v1/resume/schema/standardize` accepts a resume object or `{ "data": ... }`
  and returns the version 2 consumer envelope.
- Add `?include_audit=true` to that endpoint to include original data, processing
  warnings, calculation details and source evidence.
- The inspector's **Include source evidence and audit details in download** option
  preserves the full source-bound response evidence in the download. Its on-screen
  inspection view also retains evidence.
- `GET /api/v1/resume/schema/standardized-definition` returns the consumer data
  JSON Schema. The existing `/definition` remains the legacy mapping definition.

Consumer envelope:

```json
{
  "export_type": "standardized_resume",
  "schema_version": "2.0.0",
  "source": "resume.pdf",
  "data": {},
  "validation_status": {
    "is_valid": true,
    "usable": false,
    "requires_human_review": true,
    "issues_count": 1
  }
}
```

`data` always contains contact, professional title, summary, source-stated total
experience, categorized skills, experience, education, certifications, projects,
languages, awards, achievements, publications, volunteering, interests, references
and additional sections. Missing scalar text is null; absent collections are [].
The discoverable schema specifies the complete structure, rather than the abbreviated
empty `data` above. Validation flags do not certify factual correctness.

Breaking changes for consumer clients:

| Previous consumer fields | Version 2 |
| --- | --- |
| `education.start_year`, `graduation_year`, duplicate ISO fields | `start_date`, `end_date` |
| `certifications.issue_year`, `issue_year_iso` | `issue_date` |
| Contact phone and duplicate `phone_e164` | `phone`, separate `phone_extension` |
| Categorized skills and duplicate flat union | Categorized skills; union retained internally |
| Calculated total experience/overlap/completeness in candidate data | Optional audit calculation metadata |
| Required large source/metadata envelope | Optional `audit` |
| Source duration overwritten in the main projection | `stated_duration` alongside calculated duration |

The legacy internal models retain original and parsed date fields to support
source validation and the inspector. Consumers should use `consumer_export`, not
mistake the mapping response's original `data` for standardized consumer data.

## Responsibility by stage

| Concern | Responsible stage and implementation |
| --- | --- |
| Extracted characters, OCR, PDF/DOCX reading order | Existing extraction and layout recovery; not rewritten by this change |
| Section/job boundaries and literal associations | Existing section engine, `schema_mapping.py`, `record_subfields.py`, optional grounded field review |
| Preference vs residence and target role vs current title | Explicit label/context refinement plus guarded title mapping; ambiguous content remains residual |
| Certificate expiry, credential ID, verification link; project dates/outcomes; engagement type | Additive source-bound model/registry fields and explicit label extraction |
| Malformed shapes and unknown fields | `standardization/input.py`; rejects non-object/nonfinite roots and retains unsupported values for review |
| Contact formatting | `standardization/contacts.py`; extension separated before digit formatting; HTTP(S) URL parser shared by contacts/projects/certifications |
| Safe skill aliases and spelling | `skills.py` and `suggestions.py`; no semantic product expansion for ambiguous aliases; no proper-name spell suggestions |
| Dates and elapsed time | `dates.py`; no century inference, no inclusive extra month |
| Additional structured sections and unmapped content | `mapping.py`, `additional.py`; validated hierarchy projection and residual value accounting |
| Consumer representation and metadata separation | `consumer.py`, `export.py`; browser forwards the server-produced consumer projection |
| Warning counts, discrepancies and downstream usability | `cross_field.py`, `validation.py`, mapping findings, and UI status |

No candidate-specific correction rules were added.

## Dates and duration policy

Normalized dates are ISO `YYYY`, `YYYY-MM` or `YYYY-MM-DD`, at the precision actually
established by the source. Invalid/ambiguous/unrecognized dates are null in consumer
data and retained in audit source values with review findings. A two-digit year is
not assigned an invented century. Current employment is an explicit `is_current`
flag with a null end date. No missing end date alone establishes current employment.

Month-only elapsed duration is `(end_year-start_year)*12 + end_month-start_month`.
September 2020 to February 2021 is five months. Same-month endpoints are zero known
elapsed months, not an assertion that no days were worked. Year-only ranges are
insufficient for a month duration. Exact day ranges use completed calendar months
and remaining days. Source-stated durations and source-stated total career years
remain separate from calculated values; discrepancies beyond rounding tolerance
require review.

Aggregate experience merges intervals before calculating elapsed time. Month-only
or mixed-precision intervals use first-of-month calculation boundaries and remain
approximate; those assumed calculation boundaries are never emitted as source dates.
Exact-day intervals retain day boundaries. Touching intervals are merged without
being called overlapping. Residual days are converted using 365.2425/12 days per
month for a total rounded to one decimal year. Partial totals are marked incomplete;
missing/invalid spans do not become fabricated employment time.

## Preservation and review

Only exact mapped values consume source content. An evidence quote containing an
entire paragraph does not imply that the whole paragraph was mapped. Remaining
meaningful text is promoted into `additional_sections` with its source IDs and an
unresolved status. Additional fields that the legacy schema does not understand
are retained with their original path/value. Supplemental sections use a consistent
record shape with `details` for attributes that cannot be safely projected.

The spelling whitelist is advisory only in prose summary, responsibilities and
project descriptions. Names, employers, institutions, certification titles and
project names are not dictionary spell-checked. Location consensus can still
produce an explicitly unverified suggestion; it never changes the location.
Suggestions inspect the standardized representation, so already-corrected skills
are not flagged again. Ambiguous skill aliases (`ALM`, `teams`, `apache`, `python3`)
are preserved; domain and soft-skill categories do not receive technology aliases.

`issues_count` counts all returned warning/log entries. `total_normalizations` counts
applied log entries, not distinct fields; collection transformations have their own
before/after log. `corrections_by_type` counts applied entries only. Unresolved
warning/review findings set `requires_human_review=true` and `usable=false`.
Invalid input, missing candidate identity or invalid dates also set `is_valid=false`.
Syntactically valid JSON never establishes independent verification.

## Verification and limitations

`tests/test_standardization_v2.py` covers input shapes, contact handling, aliases,
source preservation, supplemental sections, date ambiguity, discrepancies, API
contracts, normalization accounting and overlapping exact-day spans. Existing
standardization, mapping, citation validation and API regression suites remain in
use. The audit planner also retains provisional source boundaries for unmapped
records, preventing a source-omission finding from borrowing another record's text.

Replay saved PDF/DOCX artifacts without provider calls:

```bash
/home/zoyaharmain/venv312/bin/python scripts/audit_standardization_v2.py \
  --run reports/resume-batch-repairs-20261027/final-local \
  --output /tmp/new-standardization-replay
```

The output directory must be new. Inputs are hash-checked for immutability. An
optional `--baseline-mappings` file allows identity/responsibility comparisons
against a replay of the prior code. Available original PDFs/DOCX are compared only
when their hashes match the saved source inventory. Literal presence is not a
semantic or layout accuracy score.

This work does not guarantee perfect extraction or association for every future
resume. It preserves and flags unresolved content instead of hiding it, and adds
structured fields where there is explicit evidence. Fully resolving complex
employment/project relationships, unlabelled certificate information, OCR damage
and missing source text still requires source review or further extraction work.

## Correction metadata and calculated totals (31 October 2026)

Default exports now include `warnings` and `standardization_metadata`, without
requiring `include_audit=true`. Metadata `corrections` contains applied system
changes, including field path, original/normalized values, reason and rule basis.
Advisory spelling suggestions have `applied=false` and are not listed as corrections.
Source evidence remains available in the optional audit bundle.

`data.total_experience_years` is now the date-derived non-overlapping total when
all supplied employment records have calculable dates; otherwise it is null and
an incomplete-total warning is emitted. `data.stated_total_experience_years`
preserves the original numeric claim; original summary text retains qualifiers
such as “14+”. Partial calculated totals remain in metadata with completeness=false.
Explicit current roles use the request's current date, recorded in `as_of_date`;
closed roles never extend to today. Gaps are excluded and overlaps count once.
The numeric total is decimal years rounded to one decimal, rather than an integer
or a years.months encoding. Duration discrepancies are explicitly logged as applied
corrections and preserve source-stated durations, including common yrs/mos forms.

## Aggregate skills export

`data.skills.all_skills` is included in default and audited consumer JSON and in
the published ConsumerSkills definition. It contains the case-insensitively
deduplicated union of normalized categorized skills and any additional source-listed
aggregate skills, in source/category order. All four categorized lists remain
available. Empty resumes emit an empty all_skills array. Regression coverage is in
`tests/test_all_skills_export.py`.

## Year-only duration policy

Valid year-only employment ranges now return explicitly labelled annual-resolution
estimates rather than null. For example, 2020–2023 gives “Approximately 3 years”;
2023–Present uses the reference date's year. A same-year range gives “Less than
1 year (year precision)”. Mixed year/month ranges with an unknown endpoint month
also use annual resolution. Source start/end dates retain their original precision.

`duration_months` is estimated years times 12 for these records; it is not a known
elapsed month count. Default metadata experience_calculations records
`duration_status=estimated_year_precision`, `duration_is_approximate=true` and
current-role as-of dates. Applied estimate warnings are included in default JSON.
Invalid, future or missing endpoints still cannot produce a duration.

Year-level intervals participate in the non-overlapping total using common
computational year-label boundaries, without inventing employment months. The
metadata flags calculated_experience_is_approximate and warns that exact gaps and
overlaps cannot be established at year precision. calculated_experience_complete
means every record was included at its supplied precision, not that exact months
are known. Existing month/day calculations retain their previous behavior.
