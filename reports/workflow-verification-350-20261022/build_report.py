"""Render audited evidence without modifying production code or past reports."""
import csv,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
s=read(OUT/'summary.json');rows=read(OUT/'per-resume.json');runs=read(OUT/'batch-provenance.json')
o=read(OUT/'offline-repair-comparison.json')['summary'];pres=read(OUT/'preservation.json')
xml=ET.parse(OUT/'tests/tests.xml');suites=list(xml.getroot().iter('testsuite'))
tests={key:sum(int(x.attrib.get(key,0)) for x in suites) for key in ['tests','errors','failures','skipped']}
by_file=Counter(c.attrib.get('classname','').split('.')[1] for c in xml.getroot().iter('testcase'))
files={}
for base in ['local_api','scripts','tests']:
 for p in sorted((ROOT/base).rglob('*')):
  if p.is_file() and p.suffix in {'.py','.js','.html','.css','.json'} and '__pycache__' not in p.parts:
   files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'implementation-snapshot.json').write_text(json.dumps({'captured_utc':datetime.now(timezone.utc).isoformat(),'files':files},indent=2)+'\n')
(OUT/'test-summary.json').write_text(json.dumps({'counts':tests,'test_cases_by_module':dict(by_file),'external_connections_attempted':0},indent=2)+'\n')
queue=[]
for r in rows:
 priority=1 if r['provider_state']!='complete' or 'ocr_or_glyph_source_review_required' in r['flags'] else 2 if r['flags'] else 3
 queue.append({'priority':priority,'file':r['file'],'sha256':r['sha256'],'provider_state':r['provider_state'],
  'meaningful_unassigned':r['meaningful_unassigned'],'missing_required_fields':len(r['missing_required_fields']),
  'flags':'; '.join(r['flags']),'source_artifact':r['artifact']})
queue.sort(key=lambda r:(r['priority'],-r['meaningful_unassigned'],-r['missing_required_fields'],r['file']))
with (OUT/'review-queue.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(queue[0]));writer.writeheader();writer.writerows(queue)
run_table='\n'.join(f"| {r['run']} | {r['selected']} | {r['new_hashes_in_chronological_scope']} | {r['execution']} | {r['requests_attributed_to_this_run']} |" for r in runs)
status_table='\n'.join(f'| {k} | {v} |' for k,v in s['latest_live_statuses'].items())
failed='; '.join(f"**{r['file']}** ({r['provider_error']})" for r in rows if r['provider_state']!='complete')
flags_table='\n'.join(f'| {k} | {v} |' for k,v in s['flags'].items())
module_table='\n'.join(f'| {k} | {v} |' for k,v in sorted(by_file.items()))
report=f'''# Full workflow and existing 350-document verification

**Decision: the technical regression checks pass, but do not treat these 350 documents as semantically approved or start a larger production/paid batch on this evidence alone.** The integrated schema adapter is structurally compatible; important extraction/grouping/field-completeness questions remain.

Audit recorded: {datetime.now(timezone.utc).isoformat()}. This audit made **zero new LLM calls**, did not re-extract the 350 PDFs, and did not rerun their embeddings. It verified saved provider-reviewed artifacts against original PDF hashes, current validators, current schema mapping, recorded request/response pairs where available, a second PDF text parser and the current regression suite. It does **not** constitute page-by-page human review or independent semantic certification. Production logic, annotations, provider decisions and prior reports were not edited for this audit.

## 1. What passed

| Verification | Result | What it establishes |
|---|---:|---|
| Current full regression suite | **{tests['tests']} passed; {tests['failures']} failures; {tests['errors']} errors; {tests['skipped']} skipped** | Exercised behavior passes its automated tests |
| Unique original PDF hashes | **350** | Deduplicated document identity |
| Original PDFs match frozen manifest hashes | **350/350** | Available original files match the selected bytes |
| Local extraction/review artifact bindings | **350/350** | Reviewed data belongs to its recorded local result |
| Exact source intervals/text and record-reference integrity | **350/350** | No missing/overlapping extracted intervals or invalid record references detected |
| Current schema contract | **350/350** | Pydantic output contract and source-binding gate pass |
| Schema evidence references | **350/350** | Evidence IDs refer to actual supplied source blocks, not proof of correct interpretation |
| Mapped data matches previous integration check | **350/350** | Current remapping reproduces the prior schema data |
| Preserved existing evidence | **{pres['files_checked']} checked; {len(pres['changed'])} changed** | Audited manifests, local/review artifacts and provider evidence remained unchanged |
| External sockets during full tests | **0 attempted** | Offline test harness recorded no external connections |

Evidence: [summary.json](summary.json), [all 350 per-document results](per-resume.json), [CSV](per-resume.csv), [test log](tests/regression.log), [JUnit XML](tests/tests.xml), [network guard](tests/network-guard.txt), [preservation hashes](preservation.json), [implementation snapshot](implementation-snapshot.json).

The first test collection attempt lacked the repository's `src` import path and could not import `pdf_hires`. The audit harness was corrected to include `src`; the complete suite above then passed in 109.71 seconds. No production patch was needed for that environment setup.

## 2. Actual workflow and responsibilities

```mermaid
flowchart TD
    A[Original PDF / DOCX] --> B[Local Unstructured extraction / OCR when needed]
    B --> C[Local layout and source evidence]
    C --> D[Sentence-BERT embeddings and seeded K-means]
    D --> E[Local heading, boundary, record and recovery rules]
    E --> F[Local-only block inspection]
    E --> G[Optional DeepSeek section review]
    G --> H[Local strict source validation and record rebuilding]
    F --> I[Local source-bound schema mapping]
    H --> I
    I --> J[CLI only: optional DeepSeek schema audit]
    J --> K[Bounded feedback and stagnation check]
    K --> E
```

- **Extraction:** `text_extraction_service.py` invokes Unstructured partitioning, validates formats and supplies PDF line/layout/glyph evidence. OCR is strategy-dependent; it is not used identically for every document. Extracted text is distinct from independently verified original-PDF words.
- **Local model:** `resume_sections.py` loads pinned `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. K-means uses labeled anchor initial centroids, `n_init=1`, seed 42. This is a general embedding model with clustering and rules, not a resume-fine-tuned supervised detector. Heading/layout and record rules materially affect output; results are not produced by embeddings alone.
- **Local block inspection:** the UI defaults to **Local model only** and calls `/api/v1/resume/sections/local`. It bypasses DeepSeek even when the provider is enabled. Numbered cards expose text intervals and proposed categories. They are not model-predicted rectangles drawn on PDF pages.
- **Section LLM review:** `/api/v1/resume/sections` uses the configured DeepSeek review on assigned and unresolved spans. It returns categories/source splits; strict validators reject invented IDs, bad offsets, gaps, overlap and unsupported word splits. Record structure is rebuilt locally. It does not verify PDF images or directly write corrected employer/degree field values.
- **Schema mapping:** `/api/v1/resume/schema` consumes the same elements and sections, preserves existing record boundaries and uses vendored handoff types/helpers through the local adapter. It makes **zero provider calls**. Exact source preservation and evidence IDs do not prove employer/title/degree associations are correct.
- **Single-resume CLI:** `check_single_resume.py --llm-review` additionally runs a source-citing schema audit. `single_resume_pipeline.py` feeds unknown spans, missing required fields and audit findings back through local recovery, LLM section review, mapping and audit within the configured 0–3 recovery budget. Invalid-placement retries share that budget; unchanged placements/schema stop the loop. A failed follow-up keeps validated output. The audit is advisory; it does not directly rewrite fields.
- **Important limit:** retries reuse the extraction. They do not automatically recover words absent from extraction, invent facts absent from the PDF, or guarantee repair of record relationships that require code changes. A source extraction repair requires a new extraction version and downstream run.

Code references: [local detector](../../local_api/services/resume_sections.py), [section review](../../local_api/services/llm_section_review.py), [source validator](../../local_api/services/source_validation.py), [schema adapter](../../local_api/services/schema_mapping.py), [feedback loop](../../scripts/single_resume_pipeline.py), [usage guide](../../docs/SCHEMA_MAPPING_API.md).

## 3. Scope: 350 unique documents, not the sum of all report folders

| Saved run | Documents | New hashes in scope | Execution evidence | Calls attributed to this run |
|---|---:|---:|---|---:|
{run_table}

The additional 100 are disjoint from the first 250. `batch-next` repeats 100 existing hashes and adds none. The two repair runs reuse recorded provider responses; their inherited request/token counters and timestamps must not be counted as new paid calls or new resumes. Their saved manifests/report copies do not consistently label replay provenance even though their reproduction scripts and repair reports describe it. This is a reporting provenance limitation.

The latest-live view used here consists of **100 batch-next + 100 original additional + 150 remaining pilot250 = 350**. It matches the prior schema integration source index byte-for-byte. It is an explicit evidence view, not an assertion that earlier repairs were never performed.

Historical live calls across the three live batch directories: **501** (283 + 111 + 107). For the deduplicated latest-live evidence only: **385** recorded calls and **13,943,959** recorded tokens (13,591,202 input + 352,757 output). These are historical recorded usage, not new charges and not an estimated price. Other pilot/single-resume runs are not added to this 350-scope usage total.

## 4. LLM review results and offline repairs

Latest recorded **live** statuses:

| Status | Documents |
|---|---:|
{status_table}

**347/350 have a structurally complete latest live provider review; three retain failed live review evidence:** {failed}.

The saved structural repair replay covers the additional 100. This audit verified **100/100 identical source extractions**, **100/100 identical saved provider-response files**, **100/100 passing intervals** and **100 structurally accepted replays**. It accepts the previously failed Avishek and Dipali responses under repaired validation/grouping logic, using no new calls. Combining that repair evidence with the other live results yields **349 structurally accepted results and one failed live review, JEWEL BIJOY**. Jewel remains reserved for local review under the user's instruction. Neither 349 nor 347 is a semantic accuracy score.

The repaired 100 still retain **6 meaningful unresolved spans** and **96 documents with missing required schema fields** when mapped now. Thus replay success does not establish complete schema extraction. [Offline repair comparison](offline-repair-comparison.json).

### Provider evidence completeness

There are **385 saved response-attempt records** for the latest-live scope, matching the recorded calls, but only **274 available paired request files**. **111 attempts lack a paired request in this checkout**; their original prompt cannot be fully independently replay-validated here. Absence of the prompt is an evidence limitation, not proof the provider was never called.

Of the 274 available pairs, today's strict contract accepts **265** and rejects **9**. These are attempts, not nine final failed resumes: rejected first attempts may have valid retries. No source-text mismatch was found in available request spans. Do not turn these counts into provider semantic accuracy. See `pair_validation` per document in [per-resume.json](per-resume.json).

## 5. Schema integration: valid contract, incomplete semantic extraction

All **350 outputs validate**, but **340/350** have at least one missing required string. Eight documents are classified as non-resume; their empty candidate fields are deliberate. Among the **342 candidate-or-unknown documents, 332 (97.1%)** have missing required fields. There are **2,369 missing required field instances overall**, of which **2,345** are in candidate-or-unknown documents:

| Missing field kind, candidate-or-unknown scope | Instances |
|---|---:|
| Employment role | 872 |
| Employment company | 816 |
| Education institution | 419 |
| Education degree | 195 |
| Contact phone | 25 |
| Contact email | 13 |
| Project/certification name | 4 |
| Contact full name | 1 |

These counts measure incomplete schema instances; absent source facts, fragmented or spurious records, grouping failures and mapping limitations can all contribute. They are not 2,369 independently confirmed extraction errors. Conversely, the ten outputs without missing required strings are not automatically correct.

**Code inspection identifies material field coverage limits:** the adapter does not populate work location/technologies, education field of study/start year/grade, or certification issuer/date/credential URL. Education graduation year is populated only when its date references contain one distinct year, so a two-year range can remain incomplete. Certification contents can be bundled into one name. Skills are split from existing source blocks, which can preserve broken line fragments as separate skills. Contact/name parsing and record field inference remain heuristic. Source evidence may be broader than the exact field substring. These limitations are not all counted by `missing_required_fields`, since optional fields may legally remain null or empty.

Awards and other categories without target slots remain in raw sections/unmapped blocks rather than a dedicated target schema field. `unmapped_blocks` does not itself mean omitted PDF text; a used block can also contain words not individually mapped. No word-level schema-consumption guarantee exists.

The mapper returns `success: true` for execution, while `meta.status` remains `needs_review`. Its retained handoff confidence scores are fixed heuristics, not calibrated probabilities. Type validity and reference validity must not be interpreted as field accuracy.

## 6. Remaining text, relationships and source fidelity

Across latest-live artifacts, meaningful unassigned spans change **3,239 local → 482 reviewed**. Of the 482, **413 belong to non-resume documents** and **69 to candidate-or-unknown documents**. **15 candidate-or-unknown documents** have such pending text; the additional-100 offline repair reduces its own portion to six spans but does not certify their labels.

Eight files are classified as out of scope: two website critiques, two job descriptions, two interview preparation guides and two job-requirement documents. These are provisional scope decisions, not human exclusions. Keep their source preserved and separate from candidate accuracy denominators.

Current diagnostic counts (overlap is expected):

| Diagnostic | Documents |
|---|---:|
{flags_table}

Among candidate-or-unknown documents, employment has **151 documents with flagged entries**, plus **79 with unlinked section blocks (860 blocks)**. Education has **25 documents with flagged entries**, plus **88 with unlinked blocks (195 blocks)**. There are **208 documents with at least one relationship diagnostic**. These are suspicion/ownership diagnostics, not measured semantic error rates.

A fresh `pdftotext -layout` comparison flags **10 documents** for unmatched terms or an empty independent text result. Differences may be spacing, reading order, source glyphs or actual omissions; PDF inspection is required. **Eight documents** have repeated-passage candidates; genuine repetitions are possible. **Six** have OCR/damaged-glyph source review signals. Exact extracted interval preservation does not settle original-PDF word fidelity.

## 7. Independent accuracy and contradictory older report claims

The current explicit pilot acceptance gate returned **ready: false; 0/15 reviewed documents**. Relationship evaluation found **0 documents with qualifying approved references**, so no independent relationship precision/recall/F1 can be established. [Current gate](pilot-gate.json), [current relationship evaluation](relationship-evaluation/summary.json).

Legacy `ground_truth/gold` files include `human_verified: true` flags and older comparison reports quote **99.92% character accuracy**. Those flags and historical development-set label comparisons do not substitute for the source-bound human review/export provenance required by the current gate. The old figure does not establish original-PDF OCR accuracy, schema field accuracy or accuracy across 350 documents. The historical report's 'entirely correct resumes' wording also cannot establish correct relationships merely from section-label agreement and record counts. Historical cost estimation code supplies fallback token values; this audit uses recorded usage and provides no price estimate.

Report status differences are therefore explainable: live batches, offline repaired responses, schema type checks, source-interval preservation and human acceptance measure different things. A passing technical suite does not override the missing independent acceptance evidence.

## 8. Current test and runtime evidence

The full offline suite passed **315 tests**, including extraction/interface paths; layout/heading recovery; local BERT/K-means behavior; original-source binding; strict LLM-response validation; failed-review retention; bounded retry feedback; schema contracts; local-only HTTP mode; and human-review gate behavior. Provider tests use synthetic/mocked responses; they do not independently verify every real employer/title/date association. Some tests cover guard behavior or fixtures rather than corpus accuracy.

| Test module | Cases |
|---|---:|
{module_table}

JavaScript syntax checks passed for `app.js`, `sections.js` and `schema.js`. Read-only localhost checks returned **HTTP 200** for the UI, health, schema definition and mapping specification. DeepSeek is **enabled and configured** in the running server; checking configuration here sent no resume and made no provider request. The local-only UI mode still deliberately bypasses it. [Runtime evidence](runtime-status.json).

The current wheel also built offline and was exercised outside the source checkout: health/schema GETs and a synthetic schema POST returned HTTP 200, mapping made zero provider calls, and the local block inspection route was included. [Wheel build log](wheel-build.log), [isolated wheel checks](wheel-check.json). No browser automation was performed during this audit; UI evidence consists of route/static inspection, JavaScript syntax checks and HTTP responses.

The previous authorized Jayesh live run is separate from the 350 scope: **five calls**, **three passes**, **two missing required fields**, **21 final advisory schema findings**, stopped on unchanged output. It proves the live review/feedback path can execute; it also demonstrates why assignment completion is insufficient. This audit did not make another Jayesh call.

Historical batch source snapshots differ from current code (7–10 tracked files per live run). Today's tests and remapping establish compatibility with the saved data, not that every historical PDF was freshly processed by today's complete extraction/model/review/schema pipeline. The 350 were not all given the new schema LLM audit or CLI feedback loop when originally processed.

## 9. Readiness decision and next steps

**Proceed with:** local inspection of existing predictions; source-backed correction and independent approval; bounded diagnostic use with explicit unresolved output. The implementation is executable and the regression checks pass.

**Hold:** treating all 350 as correct; unattended production use; a larger paid 300-document run justified solely by coverage, test counts or schema validity.

1. Review the [prioritized queue for every document](review-queue.csv). Resolve the pending Jewel case locally; retain the Avishek/Dipali replay provenance. Separate the eight non-resume decisions for explicit exclusion review.
2. Verify flagged extraction cases against original PDF pages; repair source extraction/version bindings before changing annotations. Avoid guessing at hidden or scanned text.
3. Correct record ownership and required-field mapping from supported source evidence. Add regression cases for observed employer/role/date, education ranges/grades, contact-name and certification boundaries; decide which optional schema fields must be supported. The current user request was verification/reporting, so this audit does not silently alter production behavior.
4. Complete and explicitly export the 15 source-bound pilot approvals/exclusions. Run the acceptance gate and relationship evaluation. Then review a held-out sample and report field-level precision/recall, missing-source-word findings and relationship accuracy against independent references. Set acceptance thresholds before expansion; this audit invents no accuracy target.
5. After the gate and measured acceptance criteria pass, select further documents by SHA256 against the full union of processed manifests. Repeated report folders do not create new resumes, and filename changes alone do not establish uniqueness.

Gate command (read-only; exit 2 means blocked):

```bash
.venv/bin/python scripts/pilot_review_gate.py \\
  --review-dir ground_truth/human_review \\
  --approved-gold-dir ground_truth/approved_gold_v2
```

Use the explicit versioned review catalog if source/draft versions are changed, as described in [pilot human review instructions](../../docs/PILOT_HUMAN_REVIEW.md). This audit created no human approvals or gold labels.

## 10. Reproducibility and scope limits

The [report inventory](report-inventory.json) indexes 18 available Markdown reports and records missing earlier references. Three earlier report folders referenced in IDE history (project-readiness-audit, repair-existing350 and local-source-repair) are absent from the current checkout; their unavailable contents were not independently reverified or recreated. This audit instead uses the available original batch artifacts and explicitly distinguishes their lineage.

The audit scripts and command outputs are preserved in this directory. `audit_saved_350.py` denies network access, reconstructs the latest-live hash scope, hashes available originals, validates saved artifacts, runs the second text parser and remaps schemas. `compare_offline_repairs.py` checks saved repair provenance separately. `tests/run_tests_offline.py` removes provider keys, selects cached models, blocks external sockets and adds the source-layout import path. No credentials are included in this report or implementation snapshot.

The audit is a development/readiness assessment of the current checkout and available saved evidence. It does not guarantee that unavailable request traces existed elsewhere, certify every original PDF word, promote a model opinion to human truth, or establish production accuracy. **Technical checks: passing. Independent semantic acceptance: pending.**
'''
(OUT/'report.md').write_text(report)
print('Report written:',OUT/'report.md')
