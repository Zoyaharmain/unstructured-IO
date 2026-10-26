# Schema assignment failure diagnosis

Date: 26 October 2026. Investigation and tests used **zero paid DeepSeek calls**.
Existing project changes and the supplied schema contracts were preserved.

## Findings and limits

The company and education examples identify **Abhilash Kulkarni.pdf**. Both
problems reproduce exactly using local extraction, detection and mapping:

| Field | Reproduced before | After source-grouping fixes |
| --- | --- | --- |
| First employer | `development, template creation, setting up account in internal systems. Cut average setup time by roughly` | Morgan Stanley |
| Other employers | Department names / split job entries | Goldman Sachs, JPMorgan Chase & Co., Acuity Knowledge Partners |
| Education | Three entries; Woxsen's diploma attached to the next college | Two source-local education records |
| First qualification | Empty | Post Graduate Diploma; Management; 2015–2017; Woxsen School of Business |
| Second qualification | Split from its institution | Bachelor of Engineering; 2010–2014; Guru Nanak Dev Engineering College |

The original extraction contains the employer and both complete education
paragraphs. This was not missing source text. A citation can be literal and still
refer to the wrong semantic entity: matching a duty sentence is not proof that
it names an employer.

**The exact historical DeepSeek rejection category cannot be recovered from the
reported generic message.** The previous handler replaced every unclassified
exception with `invalid_field_mapping`, returned no cause, and logged no exception
category. No saved raw provider response for this Abhilash upload was found.
It would be incorrect to claim its rejection was definitely JSON, Pydantic or
source evidence. Each of those can generate the same old message. The offline
failure injection below is explicitly a controlled reproduction, not the
unavailable historical provider response.

## Request/response trace and red status

1. `sections.js:detectSections()` obtains `/api/v1/resume/sections`. “DeepSeek
   complete · 0 placement changes” describes section ownership only. It does not
   establish correct employer, degree, record boundary or child-field extraction.
2. `sections-ready` invokes `schema.js:mapExistingSections()` at line 14. Its fetch
   at line 23 posts extracted elements, the SectionResponse, source name and
   `review_fields: true` to `/api/v1/resume/schema`.
3. `routes/schema_mapping.py:map_existing_sections()` at line 71 calls
   `llm_schema_mapping.py:map_with_field_review()` at line 270.
4. That service creates a validated local result first, then validates settings,
   context/request budgets, provider JSON, parent coverage, child fields, typed
   attributes, record ownership, and exact source evidence. `parse_review()` is
   at line 74; `commit_review()` builds the legacy response from those same items.
5. The final catch-all at `llm_schema_mapping.py:344` is the origin of
   **“DeepSeek field mapping failed source or schema validation. Local fields
   were retained.”** The response remains schema-valid and preserves the local
   data, while `meta.field_review.status` stays `failed`.
6. Before this fix, `schema.js` explicitly called
   `workflowStage('schema', 'failed', ...)` whenever review was requested and
   `field_review.status !== 'complete'`. Thus an HTTP 200 containing usable local
   fallback was colored red. That condition is replaced by `schemaOutcome()`
   (`schema-status.js:4`) and the outcome application at `schema.js:37–39`.

HTTP source-binding failures and invalid query paths are handled by
`routes/schema_mapping.py:mapping_error()` at line 17. Invalid queries now fail
before any optional field-review/provider call.

## Failure classification

The new structured diagnostic records a correlation ID, category, exception type,
allowlisted field/path, code, safe validation message, stage and attempt number.

| Category | Condition / validation stage |
| --- | --- |
| `json_parsing` | JSONDecodeError; line/column retained without provider content |
| `response_model_validation` | Wrong JSON envelope/value/container type; Pydantic item validation |
| `parent_schema_validation` | Omitted/duplicated parent coverage; legacy parent-model validation |
| `subschema_validation` | Unknown/missing child fields, missing statuses, scalar cardinality or child value type |
| `subschema_path_validation` | Invalid `parent.child` query path |
| `source_evidence_validation` | Unsupported literal/number, absent quote, cross-record citation |
| `record_ownership_validation` | Foreign, repeated, overlapping or mismatched record source IDs |
| `source_binding_validation` | Extraction interval/source binding mismatch |
| `configuration_error`, `request_budget`, `provider_error` | Configuration, bounded resource or provider-stage errors |
| `internal_error` | Unexpected implementation exception; not mislabeled as an evidence failure |

**Missing required fields are ordinarily review findings, not the generic
exception's cause.** The compatibility model permits empty required strings.
A schema-valid response with an unstated company has `needs_review`, not a
fabricated successful mapping or a response-validation exception.

`schema_diagnostics.py:record_failure()` at line 106 logs sanitized JSON.
`client_diagnostic()` at line 113 exposes full sanitized detail only for
`RESUME_APP_ENV=development`; production exposes category and reference ID.
Neither client nor server diagnostics serialize raw exception inputs, `str(exc)`,
provider bodies, API keys, full resumes, or Pydantic validation inputs/context.
Unknown path components are replaced with `unknown_field`.

In development, `schema.js:renderSchemaDiagnostic()` at line 50 displays these
fields using textContent. Production retains the safe summary/reference and
correlated sanitized server-side details.

## Outcome semantics

The additive `meta.mapping_result` preserves legacy schema fields and the original
`meta.field_review` status/diagnostic:

| Status | UI | Meaning |
| --- | --- | --- |
| `success` | Green | Execution completed without current completeness findings; not certification of accuracy |
| `needs_review` | Amber | Valid output has missing/ambiguous/unmapped or unresolved source items |
| `fallback_used` | Amber | Field review failed/was unavailable; source-bound local output is usable for inspection and requires review |
| `failed` | Red | No validated mapping result is available, e.g. invalid source binding or failed HTTP request |

A recovered retry retains its validation history with `recovered: true`. An
unrecovered failure always retains `field_review.status: failed` and its diagnostic,
even when local fallback is usable. Source/shape validation was not weakened.

## Company and education root causes

- `record_relationships.py:field_kinds()` (line 39) treated `systems`/`services`
  vocabulary as employer evidence even inside wrapped responsibility prose.
  `record_subfields.py:responsibility_fragment()` (line 63) now identifies those
  clauses before employer heuristics.
- `resume_structure.py:reviewed_employment_groups()` (line 241) previously needed a
  role/business keyword in each anchor. Dictionary-free company names above role
  rows were omitted or attached to preceding entries. Lines 275–288 now recognize
  a bold employer row paired with the contiguous role row in the same source
  element. `record_relationships.py:annotate_relationships()` (line 67) keeps that
  header as employer evidence.
- `record_subfields.py:refine_record()` at line 149 previously overwrote an
  established company with a department inferred from `Role — Department`.
  An established organization header is now retained; role-like mistaken company
  values still allow correction. A saved-resume regression exposed this distinction
  during testing, and it was corrected before completion.
- `resume_structure.py:entry_groups()` at line 143 previously used geometry-aware
  education grouping only after LLM review. The local fallback instead started
  new records at qualification/date rows, leaving an institution orphaned and
  appending the next institution to the previous degree. Existing
  `reviewed_education_groups()` (line 327) now also applies when PDF row evidence
  exists, keeping each original institution/qualification card together.
- `education_subfields.py:refine_education()` (line 8) now recognizes Post Graduate
  Diploma/PGDM and treats its parenthetical abbreviation as the same qualification,
  rather than two competing qualifications. No missing grade or unstated major is
  inferred for the engineering degree.

## Evidence and verification

- [Local reproduction before fixes](before/schema.json)
- [Corrected local result](after-local.schema.json)
- [Corrected source ownership](after-local.sections.json)
- [Controlled diagnostic](controlled-failure-diagnostic.json)
- [Controlled fallback response](controlled-failure.schema.json)
- [Browser check](browser-result.json) and [screenshot](frontend.png)
- [Test results](verification.json)

The browser check injects a deliberately unsupported employer into a source-bound
candidate and uses saved local results; its “section review complete” state is
simulated to reproduce the reported UI sequence. It makes no provider calls.
It verifies amber fallback, visible company/path/reason/reference details, retained
local fields, an enabled download, and no JavaScript exceptions.

Run development diagnostics with:

```bash
.venv/bin/python scripts/start_resume_inspector_local.py --port 8012 --development
```

Review the original document against the corrected local JSON. Historical download
files are preserved and do not update automatically. Reproducing the precise old
provider rejection requires its original response or a future newly logged failure;
no paid request was used to guess that missing evidence.

## Follow-up: company citation failure

The running development server recorded `source_evidence_validation`, code
`invalid_or_cross_record_quote`, field `company`, at
`/section_schemas/1/records/1/attributes/0/items/0/evidence` on both provider
attempts. This establishes an invalid quote/source-record binding; it does not
establish whether the literal company name itself was incorrect. The provider
body was not retained and no paid replay was made.

`llm_schema_mapping.repair_literal_citation` now replaces an invalid quote only
when its existing citation IDs belong to the declared record and the unchanged
literal value can be cited from that record's source blocks. The full candidate
then passes the existing validator. Foreign citations and unsupported values
remain rejected. The original failure diagnostic is retained as recovered on
success. The bounded provider retry now receives the sanitized category, code,
field, path and validation message rather than generic feedback alone.

Verification: 65 mapping/diagnostic/saved-defect tests and 4 API tests passed,
using offline or mocked provider responses. No paid DeepSeek calls were made.
Development server restarted at http://localhost:8012. A fresh user upload is
still needed to verify the live provider response for this specific document.
