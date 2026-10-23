# Targeted hierarchical mapper defect fixes ? offline verification

The confirmed defects are covered by passing source-based regressions and a new
five-document local replay. All five outputs are ready for human review, with the
specific limitations below. They are not certified semantically accurate or approved
for a larger automatic rollout. No new DeepSeek/provider calls were made and no
additional resume batch was launched.

## Evidence and test-first workflow

Inputs are the original saved extraction and final reviewed placements from
`reports/hierarchical-deepseek-five-20261023-225341/results/01..05`. These are the
same five user-selected source hashes. The original baseline, final outputs, audit
findings and independent PDF layout text were inspected. The original report's
unsupported audit suggestions (future June 2026 on an October 2026 client date,
computed tenure, assumed credentials and nonexistent data.awards) were not used
as fix requirements or reference labels.

Before changing production logic, 11 focused tests reproduced 11 failures. Their
red result is saved in [focused-tests-before.txt](focused-tests-before.txt).
The final suite has 20 focused cases plus relevant source, section, relationship,
hierarchy, query, feedback and historical-repair regressions: **280 passed**.
See [regression-tests.txt](regression-tests.txt). The regression runner explicitly
blocks socket connections. Focused fixtures describe their provenance as regression
inputs, not human-approved field ground truth.

The current architecture remains extraction/sections -> record grouping -> local
map_schema -> hierarchical records/attributes with exact quotes. There is no new
LLM mapper, model, schema key or generated field reference. Source text is never
rewritten: corrected boundaries use actual PDF hint offsets. Record ownership is
still explicit and validated before attribute evidence is accepted.

## Before/after examples

| Resume | Before | Verified local result |
|---|---|---|
| Aashish | Two education records; missing 2008 certificate; role includes a dashboard duty | Three education records, including PG Certificate / Pune University / 2008; clean Senior Business Analyst title and retained duties |
| Manjunath | PwC used as role; company/location missing; start date only 2015 | company PwC, role Senior Business Analyst, location Chennai; October 2015; SRM and Madras institutions recovered |
| Aditya | Corrupted name/email/links; one degree; three mixed project groups | Aditya Vashisth and separate contact tokens; two degrees with institution; five source-title project cards with quoted descriptions |
| Levi | arbole60@gmail.com plus pipe/phone; bullet-only languages; role/company mixtures | arbole60@gmail.com; English and Hindi without invented proficiency; clean source-backed employment components and five project highlights |
| Rachana | Role is employer/location; headline stops at US; zero duties in first job | correct Senior Business Analyst / Scrum Master, Tieto HealthCare, Bangalore, India; full US Healthcare title and 21 source-backed duty items |

Detailed legacy examples are in [before-after-examples.json](before-after-examples.json).
Every per-parent field value-list change is in verified/01..05/differences.json.
Record counts and populated-item totals are diagnostics, NOT accuracy metrics:

| Resume | Jobs before ? after | Education before ? after | Projects before ? after | Populated hierarchical items |
|---|---:|---:|---:|---:|
| `_Aashish Golhani.pdf` | 5 ? 5 | 2 ? 3 | 0 ? 0 | 270 |
| `_ManjunathMurugan.pdf` | 4 ? 4 | 2 ? 2 | 0 ? 0 | 113 |
| `Aditya vashisth.pdf` | 3 ? 3 | 1 ? 2 | 3 ? 5 | 123 |
| `_Levi Arbole.pdf` | 5 ? 5 | 3 ? 3 | 4 ? 5 | 138 |
| `_Rachana.pdf` | 3 ? 3 | 1 ? 1 | 0 ? 0 | 177 |

Skill candidates now exclude known headings, sentence/continuation fragments,
unbalanced partial items and case duplicates. Physical list rows are not joined into
false compound skills. Legitimate Working Capital Finance, Supply Chain Finance,
Letter of Credit and source-supported payment terms were checked for retention.
The original Manjunath name/location/English/French fixes remain intact; punctuation
artifacts no longer enter the legacy language list.

## Validation and consistency

- Exactly 5 saved sources replayed; 0 provider calls, 0 model invocations and zero
  incremental provider cost. Both socket connect and provider entry points are blocked.
- 5/5 outputs pass schema and exact source-interval/record ownership validation.
- 821 populated hierarchical items carry 954 valid exact source quotes.
- 0 shared legacy/hierarchical field mismatches across contact, headline, skills,
  employment, education, projects and certifications. Summary/list and language
  representations retain their different schemas; source-backed language/proficiency
  pairs are checked rather than requiring identical container structures.
- 3,872 protected files (original five-resume run plus prior350 artifact snapshot)
  have matching SHA-256 hashes. Originals were not overwritten. No ground-truth
  files were edited; no approval or human-verification metadata was fabricated.

See [verification.json](verification.json) for evidence totals, source hashes,
protected-file results, per-resume counts and the exact change set.
A source quote can prove literal support but cannot independently establish semantic
correctness; these totals must not be presented as field accuracy or recall.

## Multi-span evidence safeguards

Each quote is still an exact substring of its own source interval and belongs to
the supplied record. A scalar split within an element must use contiguous original
positions. Paragraphs spanning elements must cover the intervening factual content
in source order; only whitespace/empty bullet layout markers may be skipped.
The complete source ledger is used to check gaps. A paragraph join may add a newline
separator to a value, never to a fabricated source quote. Foreign-record references,
reordered content, partial element gaps and unsupported values remain rejected.

Regression tests include ambiguous multi-employer headers that must abstain, foreign
source/gap rejection and unstated language proficiency. The original unsupported-
legacy-value test remains intact: nested mapping does not invent a replacement for
a mutated unsupported employer. The previous combined-education test was updated
because the user now requires legacy and nested shared values to agree; it still
asserts that the input/source has not changed.

## Regressions discovered and corrected during this phase

Broader tests/replay found collateral issues before the verified outputs were saved:

- Grade rows were initially excluded by the new education direction rule; they now
  retain nearest preceding qualification ownership, with table alignment safeguards.
- Non-resume source interval identity initially changed; physical refinement now
  leaves explicitly non-resume inventories intact.
- Strict shared-value filtering initially erased multi-element project descriptions.
  Visible project titles/bullets now establish the proper cards, and exact ordered
  per-span evidence preserves all ten current project descriptions. Domain/client
  lists are retained as source residuals rather than fabricated project cards.
- Several certificate names initially became empty when cross-card legacy text was
  rejected. Source-local certificate cards retain supported names in both outputs.
- Engineered duties and valid row-based skills initially risked omission; regression
  tests now retain them. A false compound made by joining two physical skill rows
  was removed rather than accepted merely because its characters occurred in source.

No regression is detected by the final 280-test suite or the covered field comparisons.
This is bounded regression evidence, not a guarantee for unseen resumes. Intermediate
pass directories and the earlier final/ directory are development artifacts; only
[verified/summary.json](verified/summary.json) and verified/01..05 are authoritative.

## Remaining items for human review

1. Aditya's source uses 2018?21 and 2013?17. Start years are retained; completion
   years remain null with a review reason instead of expanding an unstated century
   or incorrectly using the start year as graduation. His TechTree role still reads
   Engineer where the PDF title includes Software Engineer; the missing prefix is
   routed into another source card by the frozen placement decisions.
2. Aashish's long professional headline is still in the saved summary placement,
   so professional_title remains null. Some wrapped employer names are still partial.
3. Certification cards can contain bundled credentials; Aditya retains an upstream
   duplicated/concatenated certificate blob alongside separately extracted titles.
   The source is preserved and legacy/nested values agree, but one-credential-per-
   record deduplication is not certified. Card counts are not credential counts.
4. Levi's SSC completion year is still unresolved, and the Nelito job still has no
   captured duties. A reviewer should check the original table and project/duty
   ownership rather than infer missing values. Bare language lists do not establish
   proficiency and remain explicitly incomplete at that child attribute.
5. Skill/domain taxonomy and residual prose still require review. Case de-duplication
   is not synonym normalization or semantic skill validation. Reviewed placement
   labels are historical inputs, not gold parent-category assignments.

These limitations are visible in the new outputs; none is hidden behind an accuracy
claim or a fabricated review approval. The source remains available for every item
or unresolved fragment. Human review can now check the repaired fields and remaining
ambiguities together. Do not launch another paid batch based on these tests alone.

## Exact files changed

This list is relative to the frozen implementation used in the original paid run,
so unrelated pre-existing workspace edits are excluded. [files-changed.json](files-changed.json)
contains the complete machine-readable list, including five fixture files.

| File | Change |
|---|---|
| `local_api/services/record_subfields.py` | Bound labelled emails, decompose unambiguous varied employment headers, match split date runs. |
| `local_api/services/source_rows.py` | New: respect exact PDF hint offsets and route explicit spoken-language rows; leave non-resume placement identity intact. |
| `local_api/services/source_fragments.py` | New: build exact per-span quotes and validate ordered paragraph evidence without foreign records or skipped factual content. |
| `local_api/services/list_fields.py` | New: case-insensitive skill de-duplication, physical-row/parenthesis-aware candidates, spoken-language list parsing. |
| `local_api/services/education_subfields.py` | Recognize PG certificates and physical degree rows, refine institutions and majors, flag abbreviated completion years. |
| `local_api/services/record_relationships.py` | Separate title/action shapes and retain responsibility continuations within existing job ownership. |
| `local_api/services/resume_structure.py` | Use qualification rows, institution direction, table alignment, project titles/bullets and source-local certificate cards. |
| `local_api/services/resume_sections.py` | Apply source-row refinement before constructing section entries. |
| `local_api/services/schema_mapping.py` | Share refined values between legacy/nested output and keep only source-supported fields; retain multi-span duties and titles. |
| `local_api/services/section_subschemas.py` | Use strict shared citations and map language records; do not silently repair mutated unsupported legacy values. |
| `local_api/services/subschema_validation.py` | Validate joined scalar evidence against the complete source inventory and supplied record ownership. |
| `local_api/vendor/handoff_schema/service.py` | Do not treat Engineering Lead as a candidate name. |
| `scripts/replay_hierarchical_defects.py` | New: validate and replay only the five saved inventories with sockets/provider entry points prohibited. |
| `tests/test_saved_hierarchical_defects.py` | New: 20 focused regression and negative cases from saved source observations. |
| `tests/test_hierarchical_schema.py` | Update the old legacy-unchanged expectation to requested shared-field consistency; original request/source immutability assertion remains. |

New source fixtures: tests/fixtures/hierarchical_defects/01.json, 02.json, 03.json,
04.json and 05.json. Report/test-runner artifacts are confined to this new directory.
No changes were made to NOTICE, ground_truth, the provider integration, or original
paid-run/350-run outputs during this defect-fixing phase.

## Commands and deterministic replay limitation

From `/home/zoyaharmain/unstructured-IO`:

```bash
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 /home/zoyaharmain/venv312/bin/python reports/hierarchical-defect-replay-20261023-231542/run-regressions.py
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 /home/zoyaharmain/venv312/bin/python scripts/replay_hierarchical_defects.py --source-run reports/hierarchical-deepseek-five-20261023-225341 --output reports/hierarchical-defect-replay-20261023-231542/verified
```

The second command was executed once for verified/; choose a NEW output directory
for any later replay because the tool refuses to overwrite existing output.
This replay rebuilds section rows/entries and runs the current production mapper
using frozen saved extraction and placement decisions. It does not rerun extraction,
Sentence-BERT detection or DeepSeek, and therefore cannot predict a fresh model's
choices. It isolates local grouping/mapping changes under fixed source/placement
inputs. Exhaustive field-level precision, recall, F1 and semantic accuracy remain
unscorable without independent human-verified references.
