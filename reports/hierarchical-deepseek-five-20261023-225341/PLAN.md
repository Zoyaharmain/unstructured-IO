# Enhanced hierarchy: five-document run awaiting confirmation

No DeepSeek calls have been made. Only read-only investigation, preparation, and
an offline command check have been performed. Results will be created only after
the user confirms the exact selection and execution command.

## Frozen selection

All five sources are in:

`/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/`

The backslash before underscores in the pasted request was interpreted as escaping,
not part of the Linux filenames. All five actual files exist.

| # | Filename | SHA-256 |
|---|---|---|
| 1 | `_Aashish Golhani.pdf` | `c261e6afe3edb029f6231fd17ab85a9a362c5e7d9af6532ed8e8925a4eaa6b3e` |
| 2 | `_ManjunathMurugan.pdf` | `a0a6ce21e0843824a33c748fd29b4b64d6747311a721ae43b2812e007128351d` |
| 3 | `Aditya vashisth.pdf` | `fe64256cc650e0d0ab5f040d346205787f3459ca0ef38609552ef2baa830b7f2` |
| 4 | `_Levi Arbole.pdf` | `328d7e1f29325c047d72038d2b6b527fbe510b30770ef3fb2ab762f67db454d9` |
| 5 | `_Rachana.pdf` | `76852c1acdbf0839ac9ca7c00c72dc24daed771d416be436ed50c1c088068cf6` |

Full paths, file sizes, prior-history checks, baseline pointers, and code hashes are
in selection.json. All five have different source byte hashes and normalized saved
text hashes; available baseline emails also differ. No selected filename/hash matches
the previous full350 manifest, earlier pilot selections, LLM scopes, or call ledgers.
Hash comparison includes both sha256 and source_pdf_sha256 naming conventions.
All five were previously processed locally, which is allowed by this targeted rerun.
Saved selection histories are frozen by their own hashes and rechecked before execution.

## Known errors and baseline availability

The conversation explicitly documents missing name/location and unresolved English /
French language/proficiency attributes for Manjunath. Both issues are reproducible in
the selected file's saved baseline. The earlier `_ManjunathMurugan_1.pdf` variant has
the same extracted element-text hash as the selected `_ManjunathMurugan.pdf`; they
are the same regression content, and the variant will not be sent as a sixth resume.

The conversation does not identify a second distinct manual-test resume. Aashish
cannot be called the second manual test without evidence. Baseline source and mapped
outputs nevertheless exist for every requested document, so all five can have
before/after comparisons against saved local outputs. Those outputs are not human
reference labels. before-comparison.json records original contact/language statuses.

## Implementation inspected

- Name/location: improved merged header handling, adjacent contact-context grouping,
  source-bound location extraction, and rejection of contact-only candidate names.
- Languages: language/proficiency decomposition with Unicode text and per-item evidence.
- Hierarchy: SectionSchema(category) -> SubschemaRecord(record_id, source_ids) ->
  Attribute(name, status) -> AttributeValue(value, evidence, status) -> SourceQuote.
- Broader enhancements: known and letter-spaced headings survive PDF word cuts;
  paragraph section ownership survives lane changes; job boundaries use source
  geometry; explicit label aliases, record-local dates and conflicting labels are
  handled consistently in legacy and hierarchical values.

Authoritative code is local_api/services/schema_mapping.py, section_subschemas.py,
record_subfields.py, resume_sections.py, resume_structure.py, and
local_api/schemas/subschemas.py and subschema_spec.py. The legacy ResumeSchema data
remains part of the production response alongside section_schemas.

## Exact proposed execution command

Run in WSL:

```bash
cd /home/zoyaharmain/unstructured-IO
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 DEEPSEEK_REVIEW_MAX_INPUT_CHARS=1000000 /home/zoyaharmain/venv312/bin/python scripts/run_hierarchical_five.py --manifest reports/hierarchical-deepseek-five-20261023-225341/selection.json --execute
```

Without --execute, the wrapper only validates the selection/configuration and cannot
make provider requests. That offline command completed with verified_no_calls.
Seven offline tests passed for source changes, baseline changes, wrong document
count, duplicate selection, prior-history overlap and default no-call behavior.

## Actual production stages to be invoked

scripts/run_hierarchical_five.py only adds selection guards and provider telemetry.
For each selected source it invokes scripts/check_single_resume.py main with
--strategy fast --llm-review --recovery-attempts 1. That calls the existing extraction,
local BERT/K-means/recovery, and scripts/single_resume_pipeline.py run_feedback.
The latter performs DeepSeek source-span placement review, production map_schema
(including section_schemas), and the production advisory LLM schema audit. Feedback
re-enters these same services when needed. No old direct ResumeSchema mapping runner
is imported, no alternative mapper is implemented, and no existing reports are reused
as new predictions.

The transport wrapper saves full API envelopes and usage while preserving the existing
production request shape and finish-reason checks. The existing source-span and audit
validators still govern response application. Raw requests/responses, final sections,
schema, audit and each feedback pass remain in each document's output directory.

## Approved scope to be confirmed

- Provider/model: DeepSeek / deepseek-flash; thinking disabled, configured key present.
- One explicit runtime override: review input limit 1,000,000 characters, because
  Aashish's old schema alone is 211,576 characters. Default is 200,000. .env is unchanged.
- Two feedback passes at most per document, including one recovery attempt.
- At most four placement/audit requests per document; at most twenty across all five.
  No automatic transport retries and no calls for any other resume.
- Fatal authentication/balance/model-access failures stop further requests.
- Output: `reports/hierarchical-deepseek-five-20261023-225341/results`.
  Existing results make the runner refuse; it never auto-resumes a paid run.
- Previous full350 files, frozen production implementation, source PDFs and baselines
  are verified by SHA-256 before execution and checked again at completion.

## Evaluation after confirmation

Inspect exact parent/attribute assignment, employment/education/project associations,
source quotes, omissions, conflicting and duplicated values, date associations and
advisory LLM findings per resume. Compare Manjunath name, location, English proficiency
and French proficiency against the user-supplied excerpts, explicitly marking this
as a limited regression check rather than exhaustive field ground truth.
Compare all five new outputs with their saved baselines. Check any extracted-text
changes separately so differences caused by extraction are not called mapper gains.

No exhaustive human-verified field references were established for this selection.
Precision, recall, F1, exact field accuracy, and overall semantic mapping accuracy
therefore remain unscorable. Schema conformance, exact quote validity, advisory LLM
findings and observed source-based defects will be reported separately, with explicit
denominators. The earlier 15 section labels will not be used as field ground truth.

Provider-request counts, stage attempts/retries, actual response usage, per-call and
per-document latency will be saved. Cost will be reported only if available or based
on a verified contemporaneous rate; no historical price or fabricated cost is assumed.

No paid execution will start until the user confirms the selection and command above.
