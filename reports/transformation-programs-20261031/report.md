# Transformation programs mapped as project records

## Root cause

The existing projects schema was available, but SELECTED TRANSFORMATION PROGRAMS
was not a recognized project-section heading. Its source spans remained in the
employment section and did not produce project records. Date rows also precede
some title rows in extraction order despite being aligned with the titles in the
PDF. The title selector could skip the actual title after a date-only first block.
Project date fields were not consistently populated from these literal ranges.

## General corrections

- Extend project-heading aliases for selected programs, transformation programs
  and initiatives. Recover the explicit source section through its next recognized
  heading, with bounded source/page scope. Recover program/initiative headings
  specifically without globally overriding existing work/education ownership under
  historical general project headings.
- Use separately titled, dated project/program headers as record boundaries even
  without a PDF Title element. Date-only and labelled Duration rows do not create
  new records. Existing PDF geometry associates right-aligned dates with titles
  even when the date occurs earlier in extraction order.
- Select the first meaningful project title after date/URL-only rows; separate an
  inline date range from the title; retain the complete contiguous description.
- Fill project start/end dates from the record's unique literal range, excluding
  incidental action-led narrative ranges. No employer/organization or project role
  is invented where it is not explicitly established.
- Preserve independently titled and dated source program cards if provisional
  field-review output merges, omits or truncates them. Restore their source-backed
  names, descriptions and dates and re-run normal source/schema validation.

Implementation: `local_api/services/project_section_recovery.py`,
`resume_structure.py`, `project_fields.py`, `record_subfields.py`,
`local_completion.py`, `llm_schema_mapping.py`.

## Actual source results

Both old saved sections and fresh real local-model detection now yield four
`projects` records, each with its full original description:

| Project/program | Start | End |
| --- | --- | --- |
| Canada Mortgage Operations Re-Migration Program | 2013-10 | 2014-10 |
| Canada Mortgage French Process Re-Migration Program | 2020-02 | 2020-08 |
| Mortgage & Loan Booking/Funding (Drawdowns) Automation Program | 2020-09 | 2021-02 |
| Mortgage DocPac Follow-Up Process Automation Program | 2021-11 | 2022-04 |

No project description is duplicated as an employment responsibility. Original
source bindings validate. Prior fixes remain checked: two employment records,
128-month HSBC duration, 13.0 years calculated experience, one complete PMP record,
aggregate all_skills and the complete target-role list.

The restarted API processed the saved extraction/section assignment locally in
**0.576 seconds**. This is local mapping latency, not external LLM latency. No
external provider calls were used for the actual-document replay or API smoke.
The reviewed merge/omission regression uses a mocked provider response.

## Validation and artifacts

**827 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider,
API and cached local-model selection. External-provider tests and two Node
diagnostic tests were excluded; Node-dependent tests skip when Node is unavailable.
`git diff --check` passed.

- `saved-mapping.json`, `fresh-mapping.json`: source-backed local mapping outputs.
- `saved-consumer.json`, `fresh-consumer.json`: canonical consumer exports.
- `live-mapping.json`: complete restarted API response.
- `corrected-consumer.json`: actual consumer JSON returned by the restarted API.
- `live-check.json`: assertions for all four programs and preserved prior fixes.

Passing these checks establishes the cited mappings for this saved extraction and
regression fixtures; it is not a universal semantic-accuracy guarantee. Unstated
project roles and organizations stay null rather than being inferred.

App restarted at http://localhost:8080. Regenerate the schema to apply these fixes
to the current document; previously downloaded JSON is unchanged.
