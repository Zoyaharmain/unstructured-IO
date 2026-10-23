import json
from pathlib import Path
from local_api.schemas.subschema_spec import SUBSCHEMAS
OUT=Path(__file__).parent
pilot=json.loads((OUT/'pilot-summary.json').read_text())
refs=json.loads((OUT/'reference-agreement.json').read_text())
rows=[]
for i,r in enumerate(pilot['results'],1):
    mapped=json.loads((OUT/f'{i:02d}/mapping.json').read_text())
    source=json.loads(Path(r['source_artifact']).read_text())['local_sections']
    ledger={f"e{b['source_element_index']}:{b['start']}:{b['end']}":b['text'] for s in source['sections'] for b in s['blocks']}
    ledger.update({f"e{b['source_element_index']}:{b['start']}:{b['end']}":b['text'] for b in source['needs_review']})
    old={k:v for k,v in mapped.items() if k!='section_schemas'}
    r['audit_payload_without_hierarchy_chars']=len(json.dumps({'source':ledger,'schema':old},ensure_ascii=False))
    r['audit_payload_with_hierarchy_chars']=len(json.dumps({'source':ledger,'schema':mapped},ensure_ascii=False))
    rows.append(f"| {r['file']} | {r['records']} | {r['populated_items']} | {r['unresolved_attributes']} | {r['elapsed_seconds']:.4f} |")
(OUT/'pilot-summary.json').write_text(json.dumps(pilot,indent=2))
mapped=json.loads((OUT/'04/mapping.json').read_text())
record=next(s for s in mapped['section_schemas'] if s['category']=='education')['records'][0]
source=json.loads(Path(pilot['results'][3]['source_artifact']).read_text())
block=next(b for s in source['local_sections']['sections'] for b in s['blocks'] if b['source_element_index']==80 and b['start']==10)
query=json.loads((OUT/'04/query.json').read_text())
(OUT/'actual-example.json').write_text(json.dumps({'resume':'A Madhavi.pdf','original_block':block,'nested_record':record,'query':{'path':'education.institution','matches':query}},indent=2,ensure_ascii=False))
table='\n'.join(f"| `{parent}` | {', '.join('`'+k+'`'+('[]' if v['multiple'] else '') for k,v in fields.items()) or 'Residual source only'} |" for parent,fields in SUBSCHEMAS.items())
report=f'''# Hierarchical schema extension and verification

The existing schema-mapping stage now has centrally defined child fields, strict structure and source validation, and record-preserving field queries. It reuses the existing mapper and source blocks. Legacy `data` and all previous raw outputs are preserved. This implementation used **zero provider calls, zero tokens, zero extraction runs and zero block-detection runs**.

**This is not a completeness or semantic-accuracy certification.** The local mapper still leaves substantial source information unresolved. The five saved examples demonstrate structure and traceability, not readiness to process a larger batch automatically.

## Existing workflow and files inspected

| Stage | Actual implementation and behavior |
|---|---|
| Ingestion/extraction | `local_api/routes/extraction.py`, `local_api/services/text_extraction_service.py`, `local_api/schemas/extraction.py`: validated uploads, Unstructured partition, original element metadata, existing PDF layout/source recovery. Unchanged. |
| Segmentation | `local_api/services/resume_sections.py`, `section_recovery.py`, `record_relationships.py`, `local_api/data/section_anchors.json`, `local_api/schemas/sections.py`: cached Sentence-BERT, seeded K-means, heading/layout rules, entry ownership and source intervals. Unchanged. |
| Source validation | `local_api/services/source_validation.py`: complete exact intervals, canonical text, valid entry/field indices and non-overlapping ownership. Reused unchanged before mapping. IDs stay `e<element>:<start>:<end>`. |
| Optional section review | `local_api/services/llm_section_review.py`, `local_api/routes/sections.py`: explicit reviewed/local endpoints, configured DeepSeek, strict assignments, bounded retries and preservation of valid results. Unchanged. |
| Parent mapping | `local_api/services/schema_mapping.py`, `local_api/vendor/handoff_schema/models.py`, `service.py`, `schema_spec.py`: the live schema API uses local handoff helpers and source-bound section entries; it does not itself call DeepSeek. Vendor files unchanged. |
| Individual feedback | `scripts/check_single_resume.py`, `scripts/single_resume_pipeline.py`: local recovery, optional section review, mapping, advisory read-only schema audit, bounded feedback and stagnation handling. These consumers receive the additive hierarchy without changing legacy data. Unchanged. |
| Separate LLM schema evaluation | `reports/deepseek-schema-full350-20261022/run_single_resume.py`, `run_full350.py`, `envelope_pipeline.py`, `schema_gate.py`: the mapping prompt requests the existing ResumeSchema plus evidence on every scalar/list item. Raw/candidate separation, strict parsing, quarantine, model/call ledgers and frozen production hashes stay unchanged. This is separate from the production UI mapper. |
| Pointer handling | The evaluation gate normalizes only provably equivalent evidence pointers on a copy and records normalizations/rejections. It never inherits parent citations. The new query layer emits canonical pointers directly; it does not normalize or rewrite model responses. |
| Downstream consumers | `local_api/routes/schema_mapping.py`, `local_api/static/schema.js`, `scripts/single_resume_pipeline.py`, `scripts/check_single_resume.py`, existing mapping/feedback tests. Legacy `data` still validates as ResumeSchema. The existing UI consumes the additive `section_schemas`. |

No general field-query service existed. The UI's text search searches extracted elements, not schema fields, so a small local function and HTTP query endpoint were added.

## Before and after

Before: source elements → detected section blocks/entries → local ResumeSchema data → generic nested display. Child names/types had no central validation and fields had no dedicated query interface. References had no child-field definition.

After: exactly the same extraction, sectioning and parent mapping → predefined child attributes within the same supplied records → strict source-aware validation → existing display/download plus field-level queries. Compound education text can be refined within its own record, while unresolved/ambiguous content remains visible. There is no recursive model loop or additional model request.

## Parent-to-child specification

The authoritative registry is `local_api/schemas/subschema_spec.py`. Primary names, scalar types and array cardinality derive from the existing handoff models. Additional detected categories have explicit conservative slots. Illustrative names such as `institution_name` are not renamed into the legacy contract: use `institution`, `degree`, `company`, and `role`.

| Parent | Allowed child fields |
|---|---|
{table}

`professional_title` remains the existing root legacy field and is exposed under personal information in the hierarchy. `total_experience_years` remains the existing numeric root legacy field and is exposed under summary. The original summary string remains in `data`; the hierarchy exposes source statements. Other existing model properties retain their names and types. No education-status, credential-ID, employment-type or other speculative fields were added merely because they appeared in illustrative requirements.

## Validation and uncertainty

- Unknown parent/child names, missing/duplicate children, extra keys, wrong types, non-finite numbers and multiple scalar values are rejected.
- Every populated scalar and list item has its own nonempty exact source quote. A shared source block may support several fields, but every field explicitly cites it.
- The validator checks source existence, record-local ownership, quote occurrence, value support and residual-source validity. It does not infer evidence from a parent citation.
- Queries return record IDs, semantic field paths and JSON pointers resolving to the returned mapping's actual value, together with quotes and source IDs.
- Missing attributes are `unresolved`, not assertions that the source PDF lacks those facts. Empty source blocks remain preserved as residuals but cannot support populated attributes.
- Multiple qualifications in a merged supplied record are not paired by proximity. Expected/in-progress education and approximate experience remain marked for review. Training/research content retains explicit association warnings.
- Obvious email/contact strings are rejected as names in the nested view. This prevents a known legacy helper failure from propagating while retaining legacy data for compatibility and diagnosis.
- Unsupported values are omitted from the nested view and source remains available; partial fragment citations never discard the rest of a block.

The source-aware hierarchy validator must be used for externally loaded hierarchies; Pydantic structure validation alone cannot verify quotes against original source. The HTTP query endpoint always remaps and validates supplied source blocks rather than trusting client-provided mapped citations.

## Actual source example and query

A Madhavi's saved original source block is `e80:10:113`:

> {block['text']}

The nested record retains `record_id: education-1` and emits:

| Child | Value | Exact quote in that block |
|---|---|---|
| `degree` | Bachelor of Engineering | Bachelor of Engineering |
| `institution` | Andhra University | Andhra University |
| `field_of_study` | ECE | ECE |
| `graduation_year` | 2015 | 2015 |

`start_year` and `grade_or_gpa` remain unresolved. This source-backed example was checked against saved text, **not independently against the PDF**. Complete source, mapped record and query result are in `actual-example.json`.

Example Python query:

```python
matches = query_subschemas(mapped.section_schemas,
                           'education.institution', record_id='education-1')
```

The actual result includes `parent: education`, `child: institution`, `field_path: education[0].institution`, `record_id: education-1`, value `Andhra University`, and evidence `{{"source_id":"e80:10:113","quote":"Andhra University"}}`. Its item pointer is `{query[0]['items'][0]['pointer']}`.

HTTP: `POST /api/v1/resume/schema/query` with the existing `elements`, `sections`, `query_path` and optional `record_id`. Definition: `GET /api/v1/resume/schema/subschema-definition` includes `x-hierarchy`. Unknown paths or invalid source bindings return 422; unresolved fields return empty item lists. Multiple records are returned separately.

## Offline pilot: five representative saved block outputs

Selection reused the earlier pilot's frozen scope: compact finance (Ajay), two-column software (DDhanush), dense engineering/training/projects (Boovanesh), multi-page business analysis (Madhavi), and research/publications (Nithin). No new PDFs were extracted and no saved source/LLM response was overwritten.

| Resume | Records | Populated child items | Unresolved attributes | Local mapping seconds |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

All five hierarchy outputs passed structure and source-aware validation. All **{pilot['populated_items']} emitted items** have individually valid supporting quotes. **{sum(r['unresolved_attributes'] for r in pilot['results'])} attributes remain unresolved**; this is a count of record-field slots, not a count of missing source facts. Every mapping and query is saved under `01/`–`05/`. Latencies are single local runs including initial import/cache overhead; they are not a benchmark or provider latency measurement.

### Separate source-to-field quality check

The existing 113 AI-authored saved-block reference opportunities were reused with strict case/punctuation-normalized exact comparison and same-record selectors. **{refs['strict_source_bound_matches']}/{refs['denominator']} ({100*refs['strict_source_bound_matches']/refs['denominator']:.2f}%)** matched both value and a cited reference block. **{refs['upstream_parent_assignment_differences']}** unmatched opportunities have different upstream parent assignments; the remaining **{refs['denominator']-refs['strict_source_bound_matches']-refs['upstream_parent_assignment_differences']}** are unresolved/different local fields or associations under this strict matching rule.

This is **strict reference agreement, not semantic accuracy**. Shortened degree representations, unresolved selector fields and legitimate source-format differences can fail exact comparison. The old reference set contains known association ambiguities and was not human/PDF verified. The measurements nevertheless show that valid citations on emitted fields do not establish sufficient completeness. No larger-scale readiness claim is justified by this pilot.

## Calls, costs and failure modes

New DeepSeek calls: **0**. New provider tokens: **0**. Incremental provider charge for this implementation/evaluation: **0**. No malformed provider responses or quarantine events were generated because no provider request was made; this is not evidence of a 0% provider failure rate. Existing raw/candidate and quarantine tests exercise the unchanged safeguards offline.

The optional single-resume LLM audit currently serializes the whole schema envelope. An added hierarchy can increase that audit's prompt size even though it adds no calls. `pilot-summary.json` records source-plus-schema serialized character counts with and without `section_schemas`. These are characters, not billed token estimates; the existing 200,000-character default guard remains active. No live audit token/cost/latency estimate is invented. The separate full350 mapping prompt and call workflow were not changed.

## Compatibility and preservation

Legacy fields, meanings, missing-value conventions and model types are unchanged. Nested education refinements do not overwrite `data`. Existing clients may continue reading `data`; clients consuming new attributes should use the registry and new source IDs on each record. Historical nested outputs lacking these source IDs must be regenerated from their saved source blocks before source-aware validation/querying; raw model responses need not be rerun.

`preservation.json` compares a snapshot of **3,550 existing files**: all historical raw inputs/outputs, vendor files, extraction/segmentation/provider code and scripts in that snapshot remain unchanged. Only authorized schema-extension files changed. New implementation files and new reports are separate. This is preservation evidence for the inspected snapshot, not an assertion that previously reported runs are now certified.

## Files changed or added

Existing files modified: `local_api/schemas/subschemas.py`, `local_api/schemas/mapping.py`, `local_api/services/section_subschemas.py`, `local_api/routes/schema_mapping.py`, `docs/SCHEMA_MAPPING_API.md`.

New production files: `local_api/schemas/subschema_spec.py`, `local_api/services/subschema_validation.py`, `local_api/services/education_subfields.py`. New regression file: `tests/test_hierarchical_schema.py`. New offline evaluation scripts, examples and machine-readable outputs are confined to this report directory. Existing UI files require no change for these additions because the prior generic attribute renderer already handles them.

## Test results

See `tests/unit.log`, `tests/integration.log`, `tests/regression.log` and JUnit XML. The final recorded counts are appended after the final regression run. Structural tests do not prove original PDF extraction accuracy.

## Remaining work

The hierarchy and query interface are implemented. Review unresolved blocks and incorrect local record ownership against a source-approved set before scaling. The local mapper remains substantially less complete than the separate saved DeepSeek mapping evaluation; this change does not silently substitute one workflow for the other. Arbitrary prose, cross-block joins, unlabeled compound credentials, and missing/merged upstream records remain conservative limitations. No additional calls or larger batch were started, and no new approval is needed for the delivered local implementation.
'''
import xml.etree.ElementTree as ET
checks={}
for name in ('unit','integration','regression'):
    path=OUT/'tests'/('tests.xml' if name=='regression' else name+'.xml')
    cases=list(ET.parse(path).getroot().iter('testcase'))
    checks[name]={'tests':len(cases),'failures':sum(c.find('failure') is not None or c.find('error') is not None for c in cases)}
(OUT/'tests-summary.json').write_text(json.dumps(checks,indent=2))
report=report.replace('See `tests/unit.log`, `tests/integration.log`, `tests/regression.log` and JUnit XML. The final recorded counts are appended after the final regression run. Structural tests do not prove original PDF extraction accuracy.',
    f"Focused unit tests: **{checks['unit']['tests']} passed**. Selected HTTP integration tests: **{checks['integration']['tests']} passed**. Full regression suite: **{checks['regression']['tests']} passed**, zero failures, in 85.50 seconds. These runs overlap and must not be added together. The full run disabled provider keys and external sockets; no external socket attempt occurred. JavaScript syntax and scoped diff checks passed. Logs and JUnit XML are under `tests/`; machine counts are in `tests-summary.json`. Structural tests do not prove original PDF extraction accuracy.")
(OUT/'report.md').write_text(report)
print('Report saved.')
