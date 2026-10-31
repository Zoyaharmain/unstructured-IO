# Block detection and schema mapping improvements — 30 October 2026

Implemented general changes to detection, local recovery, reviewed mapping and final
source accounting. No candidate-specific production rules or model replacements
were introduced. The prior standardization work remains intact.

## Before/after evidence

Both runs used the real cached, pinned Sentence-BERT/MiniLM model and seeded K-means
on the same saved extracted elements: **six DOCX and four PDF resumes**. The before
run used a source snapshot taken at the start of this task, including the prior
standardization changes. The after run used the updated general pipeline.

| Measurement | Before | After |
| --- | ---: | ---: |
| Meaningful source spans without a section classification | 15 | 2 |
| Populated schema attributes | 360 | 362 |
| Mapped responsibility items | 127 | 127 |
| Detected overlaps between unrelated field claims | 68 | 24 |
| Meaningful fragments still lacking a field/record association | 296 | 290 |
| Resume-provider calls in these replays | 0 | 0 |

All extracted inputs, source intervals and citations were checked unchanged/valid.
**No job identity changes occurred in any of the ten resumes.** The remaining two
section-unassigned spans are uncertain header fragments, not silently discarded
text. Remaining field association/conflict findings are exposed for grounded or
human review, not marked fully verified.

A populated-field count is not an accuracy percentage. The changes recovered six
contact/summary attributes while removing four redundant or unsupported project
field assignments, giving the net increase of two. Conflicts decreased because
project identity and other labelled fields are no longer copied indiscriminately
into whole-card descriptions.

## Root causes and changes

| Stage | Finding | General improvement |
| --- | --- | --- |
| Segmentation | Mechanical token windows split sentences; inline bullets could remain merged | Sentence-aware bounded windows and exact inline bullet boundaries; date/name hyphens remain intact |
| Heading/context detection | Some section variants were missing | Additional publication and volunteering variants reuse existing schema families |
| Contact detection | Decorative icons and modest/non-PDF name typography defeated conservative matching | Lookup-only icon handling; unique opening title/contact context; dominant name/headline element recovery |
| Preamble detection | Clear career-summary prose before a section heading remained unassigned | Explicit professional introduction plus bounded continuation recovery; hiring requirement wording excluded |
| Paragraph recovery | Leading/trailing duty fragments lacked a section despite a uniquely assigned sibling | Recover section context across one source paragraph without inventing an employer/project owner |
| Record safety | Rebuilding recovered content could produce a spurious job from words like “solutions” and “architect” | Preserve established IDs/membership and require source identity/header evidence for new employment proposals |
| Certification grouping | Explicit issuer/credential/expiry rows became separate certificate cards | Join adjacent detail rows to a same-page/lane card; a new named credential starts a new card |
| Responsibility mapping | A labelled responsibility row replaced duties before/after it | Supplement rather than overwrite the duty list; preserve prose commas/semicolons and source order |
| Contextual mapping | Supplied entries with no field hints left obvious duties unmapped | Recover source-local action clauses from established identity or an explicit role, including freelance roles with no invented employer |
| Project mapping | Whole-card descriptions duplicated names, tools and role fields | Separate literal identity, descriptions and labelled fields; preserve physical-row continuity |
| Date mapping | Full day ranges were missed and education months were dropped | Broader literal source range recognition and preserved education month precision |
| Reviewed mapping | Direct field review could bypass classification of unassigned/misclassified text | Bounded classification preflight, including all original source text, before field review when needed |
| Provider efficiency | Classification and field stages could consume independent budgets or repeat abstentions | Shared request budget; completed section review suppresses duplicate preflight; explicit per-stage call counts |
| Completion status | Empty classified input could be called a completed field review | Explicit `not_applicable / no_classified_sections`, preserving unresolved source |
| Final completeness | Broad quotes could hide values not actually mapped | Exact value-to-source intervals, remaining fragments with reasons, and unrelated-field overlap checks |
| Artifact handling | Page separators/footers could become unresolved candidate information | Preserve artifacts in provenance and exclude them from semantic human-review counts/consumer extra information |
| Inspector UI | Quote coverage could obscure unassigned content | Use authoritative server completeness intervals; safe value-based fallback; expose completeness findings in status |

## Main implementation points

- `local_api/services/local_completion.py`: bounded label/paragraph/record-context recovery.
- `local_api/services/preamble_recovery.py`: source-backed opening summary recovery.
- `local_api/services/contact_sections.py`: contact/name context and icon handling.
- `local_api/services/resume_sections.py`, `resume_structure.py`: segmentation, heading variants and credential card boundaries.
- `local_api/services/record_subfields.py`, `project_fields.py`, `education_subfields.py`: actual field recovery and precision.
- `local_api/services/llm_schema_mapping.py`: classification preflight, completeness targets, grounded record review and shared budget.
- `local_api/services/mapping_completeness.py`: final exact source-to-field ledger.
- `local_api/services/schema_mapping.py`, `schema_diagnostics.py`: local integration and review status.
- `local_api/services/standardization/mapping.py`: preserve real residual information while excluding accounted artifacts.
- `local_api/static/schema.js`, `schema-status.js`: honest source coverage/status display.

`meta.completeness_check` includes mapped intervals/field paths, unmapped intervals,
original snippets, local evidence/review reasons, artifacts and field conflicts.
A known section with an unresolved employer/project association is retained as such;
it is not forced into a new employment record.

## Verification

- **774 passed, 2 skipped, 15 deselected** in the offline unit, mocked-provider,
  API integration and real local-model selection.
- The skipped Node-dependent coverage/export tests were supplemented with direct
  V8 checks. Two additional diagnostic test scripts requiring Node were excluded
  from pytest and their actual assertions were run in V8. Full UI syntax, server-led
  source coverage, broad-quote handling, consumer forwarding and completeness
  status checks passed.
- Focused regressions cover first/last duties, comma preservation, cross-column
  ownership, fragmented names, full dates, credential detail grouping, project
  descriptions, non-invented freelance employers, classification preflight, request
  budgets and reviewed abstention handling.
- A **live DeepSeek synthetic-only check** completed section classification and
  grounded award mapping with **two calls total**, matching the strict budget.
  No candidate resume data was sent for this check. See `live-synthetic-check.json`.
- The restarted local API passed synthetic local detection/mapping smoke checks:
  intact duties, grouped credential fields, separated project description/tools,
  source completeness and zero provider calls in local mode.
- Source/schema model contracts and the pinned model/anchor files are unchanged;
  see `code-fingerprints.json`. Existing source validation remains in force.
- `git diff --check` passed.

## Limitations and unresolved findings

The ten-document test replays saved extraction, not fresh OCR or a visual review of
all original pages. It does not establish a semantic accuracy percentage. Twenty-four
field overlaps and 290 field/record-association fragments remain explicit review
findings in this local-only evaluation. More section assignments do not establish
which employer owns an ambiguous responsibility. Configured grounded review can
re-examine them using full source context; unsupported associations remain visible
instead of being invented.

## Artifacts and reproduction

- `before/`, `after/`: per-document real-model replay outputs and summaries.
- `comparison.json`: common evaluator results for source/field conservation and quality signals.
- `code-fingerprints.json`: source fingerprints and unchanged-contract/model checks.
- `live-synthetic-check.json`: live provider status/call-budget verification.
- `final-checks.json`: final automated/runtime verification summary.
- `scripts/replay_detection_accuracy.py`: generic offline local-model replay tool.
- `scripts/compare_detection_replays.py`: generic comparison/source-validation tool.

Full pipeline documentation: [BLOCK_DETECTION_COMPLETENESS.md](../../docs/BLOCK_DETECTION_COMPLETENESS.md).

Open http://localhost:8080 and regenerate the sections/schema output to use the new
pipeline. Previously downloaded JSON files are unchanged.
