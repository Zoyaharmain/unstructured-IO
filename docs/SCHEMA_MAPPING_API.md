# Schema mapping API

The pipeline is:

```text
Existing text extraction → Sentence-BERT + seeded K-means sections → schema mapping
```

The schema stage consumes the **same extracted elements and section response**.
It uses the user-provided handoff's `ResumeSchema`, mapping specification and
field helpers. Record boundaries come from the existing section entries. Mapping
runs locally in the API worker thread pool and makes no model/provider calls.
The section stage continues to use its existing DeepSeek review configuration.

## Start

Use the existing project virtual environment and API dependencies. No separate
handoff server, Instructor installation or OpenAI key is required for this stage.
From the project root, start the existing application, for example:

```bash
DEEPSEEK_REVIEW_ENABLED=false .venv/bin/uvicorn local_api.app:app \
  --host 127.0.0.1 --port 8000
```

This example disables optional provider section review. Cached Sentence-BERT
weights are required for offline section detection. Mapping already-produced
blocks does not load the embedding model. Restart an existing server after the
code update, then open http://127.0.0.1:8000/docs.

## Endpoints

| Method | Path | Input / result |
|---|---|---|
| GET | `/api/v1/resume/schema/definition` | Handoff `ResumeSchema` JSON Schema |
| GET | `/api/v1/resume/schema/subschema-definition` | Section → record → attribute and evidence contract |
| GET | `/api/v1/resume/schema/mapping` | Handoff mapping specification plus integration details |
| POST | `/api/v1/resume/schema` | Existing `elements` and `sections`; mapped response |

The POST body contains `source` (optional label), `elements` (the exact element
objects from text extraction) and `sections` (the complete section API response).
A runnable synthetic request is in
`reports/schema-mapping-integration-20261022/example-request.json`.

## Python: complete API sequence

```python
import json
import requests

base = "http://127.0.0.1:8000"
with open("resume.pdf", "rb") as stream:
    response = requests.post(
        base + "/api/v1/extract/text",
        files={"file": ("resume.pdf", stream, "application/pdf")},
        data={"strategy": "fast", "include_elements": "true"},
        timeout=120,
    )
response.raise_for_status()
extraction = response.json()

response = requests.post(
    base + "/api/v1/resume/sections",
    json={"elements": extraction["elements"]},
    timeout=180,
)
response.raise_for_status()
sections = response.json()

response = requests.post(
    base + "/api/v1/resume/schema",
    json={"source": "resume.pdf", "elements": extraction["elements"], "sections": sections},
    timeout=60,
)
response.raise_for_status()
mapped = response.json()
with open("resume.schema.json", "w", encoding="utf-8") as stream:
    json.dump(mapped, stream, ensure_ascii=False, indent=2)
print(mapped["data"])
print(mapped["meta"]["missing_required_fields"])
```

If your caller already has extraction and section responses, it needs only the
last POST. In the UI, use **Resume sections → Map to schema**, then download the
schema JSON. Changing the upload or regrouping sections invalidates that result.

## Response and uncertainty

The envelope uses the handoff contract: `success`, `source`, `extraction_mode`,
`data`, `schema_mapping`, `raw_sections` and `meta`. Mode is
`existing_blocks_schema_mapping`. `data` contains contact, title, summary,
explicitly stated experience years, skills, employment, education, certifications,
projects and languages.

The additive `section_schemas` property exposes the next level of structure.
Each detected section has `records`, each record has named `attributes`, and
each attribute contains individually cited `items`. For example, personal
information exposes `full_name`, `email`, `phone`, `location`, `linkedin_url`,
`github_url`, `portfolio_url` and `professional_title`. Employment records expose
company, role, dates, location, responsibilities and technologies; education
records expose institution, degree, field of study, years and grade.

Each populated item contains a value and its own `evidence` list with a
`source_id` and exact `quote` from that block. Values without a literal,
case-insensitive source match are omitted from this nested view. No citation is
inherited from another record. An `unresolved` attribute means this mapper did
not establish the value; it does **not** prove the information is absent from
the PDF. Source-supported text alone does not prove the association is correct.
Existing relationship warnings mark populated record attributes `needs_review`.

Projects, certifications, skills, summary statements, languages, awards,
publications, volunteering and interests also have section records. Categories
outside the legacy schema use conservative explicit labels for compound
attributes. Unlabelled compound information stays in `residual_blocks` rather
than being guessed. A fragment citation does not discard the rest of its block;
partially consumed blocks remain available for review. Summary statements and
responsibility bullets intentionally remain source text within typed lists.

In the interface, **Map to schema** now displays expandable section records and
attributes with source evidence, followed by the complete downloadable JSON.
The mapping uses existing blocks locally. It does not recursively call the LLM,
re-extract the PDF, or rerun block detection. The separate DeepSeek evaluation
scripts under `reports/` are not the implementation of this API endpoint.

- `meta.field_evidence` maps populated fields to exact source IDs such as
  `e12:0:24`; offsets refer to the supplied extraction.
- `meta.record_reviews` retains record source IDs and relationship warnings.
- `meta.missing_required_fields` lists unsupported required fields. The handoff
  requires string types, so unknown required strings are **empty strings**;
  optional unknown values are `null` and unknown lists are empty.
- `meta.unmapped_blocks` preserves source content not used by a target field,
  including awards/publications/other categories without a target slot.
- `meta.needs_review` retains the input's unresolved source spans.
- `meta.document_scope` identifies provisional non-resume documents; their
  candidate fields stay empty, while raw sections and unmapped text remain.
- `meta.provider_calls` is zero. Neither an ambient OpenAI key nor the handoff's
  fallback orchestration triggers a provider request through this endpoint.

The mapper does not generate default English, fictional roles, placeholder
universities, generic responsibilities or a career span from education/birth
years. It preserves skills outside the handoff's small dictionary in `all_skills`.
Ambiguous or absent record fields remain incomplete. A schema-valid result is
not a semantic accuracy certification, and `success` indicates successful mapping
execution. Output remains `meta.status: needs_review`.

The handoff's fixed confidence scores are retained for contract compatibility;
they are **not calibrated probabilities**. Its completion report covers 16
reporting groups, not every nested schema property. The JSON Schema endpoint is
the authoritative type definition.

## Errors and source binding

Malformed bodies, changed text/offsets, missing or overlapping source intervals,
changed canonical section text, duplicate record ownership and field references
outside their record return **422**. Mapping does not re-run extraction or guess
new source bindings. Supply the section response generated from the very same
extraction version.

## What was imported from the ZIP

`local_api/vendor/handoff_schema/` preserves the original `models.py`,
`schema_spec.py` and `service.py` byte-for-byte, with archive/file hashes recorded
in `PROVENANCE.json`. All 239 handoff manifest entries were verified.

The adapter calls the field helpers on existing record/section text and returns
the original target types. It does not mount the handoff's separate upload/path
APIs or invoke `parse_resume_content`, which would re-segment the document and
could silently fall back to generated placeholders. Existing extraction and
BERT/K-means algorithms supply the source boundaries.

## Check one complete resume

Run from the project root (no running HTTP server required):

```bash
.venv/bin/python scripts/check_single_resume.py \
  --file "/mnt/c/Users/Gopi Gedar/Downloads/resume.pdf" \
  --output reports/single-resume-local-001 --local-only
```

To send that chosen resume's text and mapped schema to your configured DeepSeek
endpoint for section review **and a separate schema/relationship audit**:

```bash
.venv/bin/python scripts/check_single_resume.py \
  --file "/mnt/c/Users/Gopi Gedar/Downloads/resume.pdf" \
  --output reports/single-resume-llm-001 \
  --llm-review --recovery-attempts 2
```

Replace the filename with your actual resume. `.env` supplies DeepSeek settings
only when `--llm-review` is requested. Choose a mode explicitly: `--llm-review` enables DeepSeek even if the environment has it disabled; `--local-only` makes no LLM calls. Omitting both is a usage error;
embedding weights must already be cached for offline operation. JEWEL BIJOY
remains local-only under the previously requested restriction.

Both commands run fresh extraction, Sentence-BERT/K-means, local recovery and
schema mapping. The LLM mode additionally reviews every source span, retries
invalid placements/unresolved meaningful spans with a shared bounded budget
(0–3 recovery attempts), and audits the mapped schema after each valid section pass. Unresolved meaningful spans, missing required fields or audit findings trigger another local recovery → LLM section review → schema mapping → schema audit pass, within the same recovery budget. It stops when placements/schema stop changing, the budget is exhausted, a non-retryable provider failure occurs, or no diagnostics remain. Invalid placement responses also consume the budget. Audit findings must
cite actual source intervals and never directly overwrite schema values.

Open the output `report.md`, `schema.json` and `schema-audit.json`. Compare the
original PDF with `extraction.json`; inspect missing fields, unmapped blocks and
record warnings even when the LLM finds no issues. Source validation checks the
extracted text, not unseen PDF words. Schema audit is text-only and advisory.

For scanned or missing text, run a **new output directory** with
`--strategy ocr_only`; this reruns all downstream stages on the new extraction.
For grouping/mapping problems, fix the source-supported logic before rerunning.
There is no automatic infinite full-pipeline loop: repeated identical input
cannot recover missing source evidence or certify correctness. Output stays
`needs_review` until independently checked against the PDF.

### Missing file or browser connection refused

`Downloads/resume.pdf` above is a placeholder: the file must exist. A document
already included in this checkout can be checked locally with:

```bash
.venv/bin/python scripts/check_single_resume.py \
  --file 'tests/fixtures/Jayesh Yadav-CV.pdf' \
  --strategy fast --output reports/single-jayesh-local-001 --local-only
```

The CLI runs directly and does not start a web server. To use the browser UI or
Swagger documentation, keep this command running in a separate terminal:

```bash
.venv/bin/python -m uvicorn local_api.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ for upload controls or
http://127.0.0.1:8000/docs for API documentation. Stopping that terminal's server
causes the browser to report connection refused.

### Feedback evidence

Each run saves `pipeline.json` with the actual stop reason, plus `pass-01/`,
`pass-02/`, etc. Each pass preserves sections, schema, audit and feedback.
`provider-calls.json` counts attempted calls, including failed ones; credential-free
request/response artifacts permit inspection of the feedback sent. These files
contain resume data and are kept inside the private run directory.

Unmapped blocks can include awards/publications with no target schema field;
they are preserved, not automatically treated as lost words. Missing required
fields can represent facts absent from the PDF. Retries never fabricate them.

For the HTTP UI, a bare uvicorn command does not load `.env`. Restart the
server with the provided settings loader and explicit review mode when you want
DeepSeek enabled for uploaded documents:

```bash
.venv/bin/python scripts/serve_resume_api.py --llm-review --port 8000
```

Stop the old server with Ctrl+C first. This launcher loads only DeepSeek settings from `.env` without requiring python-dotenv, and does not print the key. The web section endpoint uses its existing
section retry path; the complete schema feedback loop documented here is the
`check_single_resume.py` command. An old report remains a record of its original
local-only execution; it does not change when review is enabled for a new run.

## Inspect the local model's detected blocks

Open the Resume Inspector UI, upload a resume, then choose **Resume sections →
Detection mode → Local model only · no DeepSeek** (the default inspection mode).
The internal local endpoint runs Sentence-BERT/K-means and local boundary recovery;
it never calls DeepSeek, regardless of the server's provider setting. Choose
**Local model + DeepSeek review** explicitly to inspect reviewed output instead.

**Detected block boundaries and labels** shows every assigned and unresolved
interval as a numbered outlined card, in extracted source order. Each card shows
its full exact text, predicted section, PDF page, source element, character range,
assignment method and available similarity/cluster evidence. Filter by section;
use **Locate source block** to inspect the extracted element and navigate its PDF
page. Check that the outlined interval contains the right passage and has the
right section label. Similarity scores are not calibrated correctness scores.

These cards show text intervals, not spatial bounding-box predictions. Compare
with the PDF to judge reading order, missing passages, inappropriate splits and
wrong section ownership. A local result remains provisional until that comparison.
Changing modes invalidates the preceding schema result and regenerates sections.
The UI does not automatically perform a DeepSeek connection check in local mode.

## Predefined child registry and queries

`local_api/schemas/subschema_spec.py` derives the primary child names and list
cardinality from the existing handoff models and defines the remaining detected
categories explicitly, including references. Existing names are preserved:
`education.institution`, `education.degree`, `experience.company` and
`experience.role` are the actual paths, rather than renamed aliases from examples.
The `/subschema-definition` response includes this registry under `x-hierarchy`.
Unknown parents, children, extra keys, wrong value types and duplicate/missing
child definitions are rejected. Source-aware validation additionally checks
record ownership, real source IDs, exact quotes and per-item value support.

The query interface is a Python function and a source-bound HTTP endpoint:

```python
from local_api.services.subschema_validation import query_subschemas
matches = query_subschemas(mapped.section_schemas, 'education.institution',
                           record_id='education-1')
```

```text
POST /api/v1/resume/schema/query
{
  "elements": [...same source elements...],
  "sections": {...same section response...},
  "query_path": "education.institution",
  "record_id": "education-1"
}
```

`record_id` is optional. Results preserve records and include `parent`, `child`,
`field_path`, `record_id`, `status`, `review_reasons`, and individually cited
`items`. The `pointer` on each item resolves to its value in the corresponding
mapping response's `section_schemas` array. The HTTP endpoint remaps the supplied
source-bound blocks locally; it does not accept unverified mapped citations or
call DeepSeek. An unresolved field returns an empty item list; an absent parent
or unmatched record returns no matches. Unknown field paths return HTTP 422.

The nested education view can refine a single combined qualification into its
literal degree, institution, field of study, explicit year range and GPA.
It never merges entries or pairs multiple qualifications by proximity. Expected
completion and merged qualification ambiguities remain review warnings. Explicit
labels refine unresolved attributes only within that record. Source content that
cannot be decomposed safely remains in residual blocks. These refinements affect
`section_schemas` only, preserving the original `data` contract and its values.

No LLM response is rewritten or normalized by this endpoint. The separate
DeepSeek evaluation gate retains its raw/candidate separation, auditable pointer
normalization and malformed-response quarantine. Previously frozen production
hashes in old evaluation runs describe those runs; they must not be bypassed to
resume them with modified production code.

To retrieve related fields, retain the returned record ID. For example, query
`experience.company`, then query `experience.role` with the selected result's
`record_id`. Do not zip values from independent field lists: unresolved values
and differing record counts make positional joins unsafe. The item pointer is a
JSON Pointer into the complete mapping response, not into the query response.
