"""Consolidate actual JUnit observations and measurements without altering references."""
import hashlib
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET
ROOT=Path.cwd()
OUT=ROOT/'reports/source-ownership-20261112'
observed={}
for path in [*sorted((OUT/'ownership-final-suite').glob('*.xml')), OUT/'final-contracts.xml', OUT/'final-added-heading-cases.xml']:
    for case in ET.parse(path).getroot().findall('.//testcase'):
        key=(case.get('classname'),case.get('name'))
        observed[key]={'test':key[0]+'::'+key[1], 'outcome':'failed' if case.find('failure') is not None else 'error' if case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed', 'evidence':str(path.relative_to(ROOT))}
counts={outcome:sum(r['outcome']==outcome for r in observed.values()) for outcome in ('passed','failed','error','skipped')}
base=json.loads((OUT/'ownership-final-suite/summary.json').read_text())
gold=json.loads((OUT/'section-measurement/summary.json').read_text())
diagnostic=json.loads((OUT/'final-measured-diagnostics/summary.json').read_text())
audit=json.loads((ROOT/'evaluation/resume-ownership-v1/audit-summary.json').read_text())
baseline=ET.parse(OUT/'ownership-final-baseline.xml').getroot().findall('.//testcase')
baseline_counts={'replayed_failed_tests':len(baseline),'failed_on_original_core':sum(c.find('failure') is not None for c in baseline),
                 'passed_on_original_core':sum(c.find('failure') is None and c.find('error') is None for c in baseline)}
files=set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
files.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines())
code_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(files)
             if p.startswith(('local_api/','scripts/','tests/')) and (ROOT/p).is_file()}
summary={'latest_complete_repository_run':base,'latest_observations_by_unique_test_case':{'tests':len(observed),**counts},
         'supplement_policy':'Latest JUnit result per class/test identity overrides an earlier observation; added regression cases are counted once.',
         'baseline_replay':baseline_counts,'development_section_measurement':gold,
         'unlabeled_development_diagnostics':diagnostic,'dataset_audit':audit,
         'production_ready':False,'unseen_resume_accuracy':'not_established','implementation_sha256':code_hashes}
(OUT/'verification-summary.json').write_text(json.dumps(summary,indent=2))
(OUT/'latest-test-observations.json').write_text(json.dumps(sorted(observed.values(),key=lambda x:x['test']),indent=2))
focused_pass=sum(c.find('failure') is None and c.find('error') is None for c in ET.parse(OUT/'final-contracts.xml').getroot().findall('.//testcase'))
failures='\n'.join('- `'+r['test']+'`' for r in sorted(observed.values(),key=lambda x:x['test']) if r['outcome'] in {'failed','error'})
f1=gold['section_macro_f1']
text=f'''# Resume ownership implementation and evaluation

The ownership architecture and evaluation tooling are implemented. This is **not production-ready**: semantic regressions remain, and independent unseen-resume accuracy is **not established**. Raw extraction code and existing ground-truth files were not changed. No branch was merged or pushed.

## Reproduced root causes

| File / function | Original failure mechanism | Change |
| --- | --- | --- |
| `local_api/services/resume_sections.py`, `SectionEngine._detect` | Upstream Title/Header could stop strong semantic context; Footer/PageBreak could suppress meaningful headings or numeric content; ListItem could suppress exact section aliases. | Require semantic/source evidence; exact heading semantics override weak upstream types. Source-supported page artifacts are distinguished from body text. |
| `local_api/services/resume_structure.py`, `entry_groups` / `reviewed_employment_groups` | Role boundaries depended on style/context, nearby anchors could merge, and vertical tolerance could pull a preceding duty into a later role. | Separate role evidence, preserve reading-lane order, abstain on ambiguous merged columns. |
| `local_api/services/schema_mapping.py`, `map_schema` | A preceding iteration's `refs` closure widened the next record's evidence; implicit previous-employer/client inheritance copied complete source headers. | Explicit primary ownership; company-only context with field-specific evidence. Parent titles, dates and duties are excluded from child refinement. |
| `local_api/services/schema_mapping.py`, `map_schema` | When only one job had no duties, arbitrary Projects text was copied into it. | Remove the cross-section fallback. Repair must explicitly reassign existing source IDs. |
| `local_api/services/llm_section_review.py`, `make_messages` | Existing provider contract accepted section assignments only, despite supplying record hints. | Add a separate bounded structural stage with source-only create/split/merge/assign/review/employer-link operations. |
| `local_api/services/source_accounting.py`, `account_source` | Complete text coverage and section assignment did not establish primary role ownership or semantic accuracy. | A frozen source ledger and explicit ownership graph complement coverage accounting. |
| `local_api/services/record_relationships.py`, `annotate_relationships` | Re-annotation could erase external uncertainty and replace accepted structural fields. | Preserve review reasons and validated ownership. Mapping cannot silently heal away accepted abstentions. |
| `local_api/services/record_subfields.py`, `employment_header_fields` | Redundant action-word filtering dropped organization literals; parenthesized role specializations became clients; a rewritten component could crash a position lookup. | Preserve source-supported organization/role literals; only explicitly labeled client parentheses become client evidence; guard source-position lookup. |

Exact architecture entry points: `source_ownership.snapshot`, `role_boundary_operations`, `apply_operations`, `materialize`, `validated_ownership_state`, `finalize_ownership`; `employer_context.valid_employer_context` and `valid_record_context`. See [architecture and lifecycle](../../docs/RESUME_OWNERSHIP.md).

## Architecture and integrity

The existing extractor, section detector, recovery stack and mapper are retained. The new frozen ledger stores source IDs, exact Unicode intervals, raw text, original types, page, coordinates, normalized bounding boxes where available, extraction order and lane. A digest binds source text and metadata. Each source interval has one primary owner at most. Shared company evidence is explicitly field-specific and does not widen other fields' evidence.

Provider operations cannot invent source text, source IDs or arbitrary record IDs. Validation is atomic and checks source coverage, owner membership, section compatibility, entity kinds and employer context. Local unsupported employer links become Needs Review; invalid provider links reject the entire transaction. Accepted ownership is checked against its persisted ledger before mapping and cannot be replaced by heuristic recovery. Missing dates and ambiguous associations remain unresolved.

## Dataset audit and independent evaluation preparation

The local inventory contains {audit['unique_source_documents']} unique source-byte hashes. {audit['previously_exposed_documents']} have tracked historical references. Frozen manifests contain {audit['split_counts']['development']} development documents, {audit['split_counts']['validation']} reserved validation candidates and {audit['split_counts']['held_out_test']} reserved held-out candidates. Unmatched candidates are not certified unseen: independence attestation, duplicate/version review and independent annotation remain required. Per-resume external/pretraining use is not documented and is not claimed absent.

Audit evidence identifies prior selections, processing, tests, annotations and development reports. Used resumes stay in development; renamed byte-identical sources cannot cross splits. Existing gold and regression fixtures are not unseen data. The held-out evaluator requires explicit invocation, independent human review plus distinct adjudication, original-document hash binding and a fresh exposure check.

The blind export was exercised on a development extraction: 94 unlabeled source spans, exact source hash retained, no predicted sections or record ownership. Its unverified template was rejected by the validation CLI. See [annotation guidelines](../../docs/RESUME_ANNOTATION_GUIDELINES.md) and [audit summary](../../evaluation/resume-ownership-v1/audit-summary.json). LLM drafts are never automatically promoted to independently verified ground truth.

## Actual verification

The latest complete repository-wide run attempted all {base['modules_attempted']} modules and completed {base['complete_modules']}; {base['passed']} passed, {base['failures']} failed, {base['errors']} errors, {base['timed_out_modules']} timed-out modules. Ordinary provider exclusions/credential fixtures remained active. Earlier in-sandbox API timeouts were environmental; the isolated health test passed outside the sandbox, and subsequent complete runs were performed there.

After the final contract/type regressions, latest JUnit observations cover **{len(observed)} distinct test cases: {counts['passed']} passed, {counts['failed']} failed, {counts['error']} errors, {counts['skipped']} skipped**. This combines the complete run with the later focused JUnit results by test identity, not by summing overlapping runs. The focused ownership/evaluation/schema contract run passed {focused_pass} cases; four additional upstream-heading-type cases passed separately. Complete logs, JUnit and [per-case latest results](latest-test-observations.json) are retained.

Replaying the {baseline_counts['replayed_failed_tests']} failing full-suite cases against HEAD core implementations in memory reproduced {baseline_counts['failed_on_original_core']} failures; {baseline_counts['passed_on_original_core']} passed on the original core. This is a scoped baseline replay, not a claim that all remaining failures predate the change. Compatibility gaps remain and require review. In particular, retaining incomplete roles changes some record counts, suppressing unsupported date inheritance can leave total experience unknown, and the old Projects-to-only-job copying expectation intentionally remains unsatisfied. Existing expectations were not edited to make these changes pass.

The configured DeepSeek transport was tested with generated fiction: seven accepted create/assign operations, two experience records, zero source-validation errors, and remaining uncertainty retained. This checks protocol/integrity, not real-resume accuracy. Earlier real development responses with invalid entity assignments were atomically rejected. Automatic approval review blocked an additional real-resume transmission because document-specific approval was missing; the final provider protocol check used generated fiction instead.

## Measured results and limits

| Metric | Development evidence | Independent unseen test |
| --- | --- | --- |
| Section macro F1 | {f1:.4%} on {gold['evaluated_documents']} previously used section-labeled documents | Not established |
| Non-whitespace section character accuracy | {gold['accuracy']:.4%}; {gold['scored_characters']:,} scored characters | Not established |
| Record-boundary F1 | Not measured: complete independent role references unavailable | Not established |
| Responsibility ownership accuracy | Not measured: independent responsibility-to-role references unavailable | Not established |
| Cross-record leakage | Not measured; source-integrity checks are not semantic leakage accuracy | Not established |
| Unresolved-span rate | {diagnostic['unresolved_span_rate']:.4%} on nine unlabeled development documents | Not established |

The nine-document diagnostic batch contains six PDFs and three DOCX files, including table and column layouts; all nine processed and preserved source coverage. Although disjoint from historical batch selections, these examples are development diagnostics, not claimed unseen test evidence. Existing section labels retain their recorded legacy `human_verified` provenance; they were not independently re-certified here. Pipeline failures in section evaluation are scored as abstentions instead of being omitted from the denominator. That run reports {gold.get('pipeline_failures',0)} pipeline failures and {gold.get('source_unavailable_documents',0)} unavailable sources.

Reference evaluation is independent of parser segmentation: humans may choose different exact source intervals. Responsibility `unit_id` joins cross-line/page fragments for ownership scoring. Only human reference `ignore` spans are excluded from section accuracy. Abstentions lower ownership accuracy, while cross-record leakage counts actual wrong-role assignments. Null metrics remain null until appropriate reference labels exist.

## Remaining failing observations

{failures}

The implementation is ready for code review and further development/validation work. It is not a production acceptance result. Independent held-out annotation, resolution of semantic compatibility failures and validation on genuinely independent resumes remain necessary.
'''
(OUT/'IMPLEMENTATION_REPORT.md').write_text(text)
print(json.dumps({'latest_test_observations':summary['latest_observations_by_unique_test_case'], 'baseline_replay':baseline_counts,
                  'development_section_macro_f1':f1,'unresolved_span_rate':diagnostic['unresolved_span_rate'],'unseen_resume_accuracy':'not_established'},indent=2))
