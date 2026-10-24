import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
protected=load(OUT/'protected-before.json');changed=[p for p,h in protected.items() if not Path(p).is_file() or sha(Path(p))!=h]
code=load(OUT/'code-before.json');existing=[p for p,h in code.items() if sha(ROOT/p)!=h]
allowed=['local_api/services/llm_section_review.py','scripts/check_single_resume.py','scripts/single_resume_pipeline.py','tests/test_llm_section_review.py','tests/test_flagged_review_resolution.py']
assert not changed and set(existing)==set(allowed)
for name in ['local_api/services/record_relationships.py','local_api/services/education_subfields.py','local_api/services/record_subfields.py','local_api/services/schema_mapping.py','tests/test_phase1_repairs.py']:
 assert sha(ROOT/name)==code[name]
result={'protected_files_checked':len(protected),'protected_files_changed':changed,'existing_code_files_modified_in_phase2':existing,'new_code_files':['local_api/services/review_chunking.py','tests/test_review_chunking.py'],'phase1_classifier_preserved':True,'phase1_fingerprint_regressions_pass':True,'education_and_mapping_rules_unchanged':True,'live_api_calls':0,'ten_input_replay_extraction_detection_embeddings':0,'previous350_rerun':False,'notes':'Guarded regression suite exercises its own existing fixtures and cached local models; the frozen ten-input replay forbids extraction, detection, model loading and sockets. Runtime __pycache__ excluded from immutable artifacts.'}
(OUT/'preservation-check.json').write_text(json.dumps(result,indent=2)+'\n')
commands=[
 ('Focused chunk and integration tests', 'AUDIT_TEST_LABEL=focused-final- PYTHONUNBUFFERED=1 .venv/bin/python reports/ten-resume-phase2-20261024/run_tests_offline.py tests/test_review_chunking.py tests/test_phase1_repairs.py tests/test_single_resume_check.py tests/test_llm_section_review.py tests/test_section_subschemas.py tests/test_structural_grouping.py', 'focused-final-tests.txt'),
 ('Historical response compatibility plus chunk contracts','AUDIT_TEST_LABEL=compatibility- PYTHONUNBUFFERED=1 .venv/bin/python reports/ten-resume-phase2-20261024/run_tests_offline.py tests/test_flagged_review_resolution.py tests/test_review_chunking.py tests/test_phase1_repairs.py','compatibility-tests.txt'),
 ('Final 24 chunk tests including source crosswalk','.venv/bin/python -m pytest -q tests/test_review_chunking.py','chunk-final-tests.txt'),
 ('Final complete offline suite, no exclusions','AUDIT_TEST_LABEL=verified- PYTHONUNBUFFERED=1 .venv/bin/python reports/ten-resume-phase2-20261024/run_tests_offline.py','verified-tests.txt')]
text='Phase 2 exact offline commands/results\n\n'
for title,command,file in commands:text+=title+'\n'+command+'\n'+(OUT/file).read_text()+'\n'
text+='Completed full run: 458 passed, zero failures/errors/skips. Focused counts overlap and are not additive. Runs using TestClient completed outside the sandbox under the documented offline guard because the sandbox was previously shown to hang TestClient.\n\nInitial implementation logs are preserved: chunk-tests-initial.txt (three test-fixture issues), pure-tests.txt (a fixture lacked populated evidence), full-tests.txt (1 failed, 456 passed: historical NagaVishnu whole-response fixture routed into the new chunk protocol). The compatibility test now explicitly matches its historical large character budget with large test-only token-policy budgets, without changing its source-ownership assertions. full-final-tests.txt then passed 457 tests; the final crosswalk test raised the final suite to 458. No genuine production failure was skipped or marked xfail.\n\nNetwork guard logs:\n'
for p in sorted(OUT.glob('*network-guard.txt')):text+=p.name+': '+p.read_text()
text+='\nOffline snapshot/replay/analysis:\n.venv/bin/python reports/ten-resume-phase2-20261024/snapshot.py\nPHASE2_REPLAY_NAME=replay-verified .venv/bin/python reports/ten-resume-phase2-20261024/replay.py\n.venv/bin/python reports/ten-resume-phase2-20261024/analyze_replay.py\n\nReplay result: 10/10 stages planned and validated using mocked transport only; 56 mock attempts under shared caps (global128/document32/pass16); zero live calls. 17/17 partial reference tuples unchanged, separated by provenance. No section detection, PDF extraction or embeddings. Guards replace those functions and provider transport with prohibitions. Earlier replay/ and replay-final/ are preserved.\n'
(OUT/'test-results.txt').write_text(text)
rows=load(OUT/'before-after-comparison-verified.json')['documents']
table='\n'.join(f"| {r['file']} | {r['section_calls']} | {r['audit_calls']} | {r['section_review']} / {r['schema_audit']} |" for r in rows)
summary='''# Phase 2 offline implementation and replay

**Completed offline. No live DeepSeek/API calls. NO-GO for production scaling or semantic certification.**

The actual section-review stage now supports deterministic source-owned chunks and strict global merge validation. The CLI schema-audit stage uses compact record-bound units and exhaustive acknowledgement coverage. Both share per-pass, per-document and run request budgets. Source IDs, offsets, layout and established anchors remain traceable; failed/unreviewable chunks cannot claim complete coverage. Phase 1 and education/mapping policy are preserved.

## Verified frozen-input replay

The baseline is the Phase 1 after/ output built from the original ten frozen extraction/section inventories. These are already processed development/stress inputs, not ten fresh human labels. Mock placement confirms frozen categories; mock audits acknowledge all units with no findings. Thus the following are structural orchestration results, not DeepSeek performance or accuracy measurements.

| Resume | Mock section requests | Mock audit requests | Aggregate stage statuses |
|---|---:|---:|---|
'''+table+'''

All ten complete both mocked stages, using **56 synthetic requests** total. Siva Mari and Vikrant Roy now fit multi-chunk section/audit plans; Divya, Sundar and Sumit fit the compact audit plans. Maximum measured chunk request: **99,862 serialized characters/bytes**, under the 200,000-character and 100,000-input-policy bounds, with 16,000 output tokens reserved against the configured 128,000 local context guard. Largest owned-target count: 406 (limit 600). These numbers use mock-only configuration; a real provider plan must be regenerated with its approved current configuration and verified context/token behavior.

No legacy data, nested values/quotes, field index, parent assignment, source interval, established entry membership or residual coverage changes in any of the ten outputs. Two meaningful unknown spans remain. Source-accounting reason strings and unresolved-block confirmation/provenance annotations change because the production review path records the synthetic review; full recursive differences are in output-differences-verified.json. Record crosswalks are saved in each review state and are source-overlap diagnostics, not automatic reference-label alignment.

Reference comparison remains **Group01 6/6, Group02 5/5, older Manjunath expectations separately 6/6**. Only those 17 partial tuples are scored. Pending rows and uncertain A069 stay excluded; precision/recall/F1 and whole-resume semantic accuracy remain unavailable. Empty mock audit findings do not resolve the original 101 provider concerns.

## Tests, preservation and limits

- Final full offline suite: **458 passed**, no failures/skips; **24 chunk-contract tests** passed. The larger focused/compatibility runs also passed; overlapping counts are explained in test-results.txt.
- Test transports were mocked; offline guard logs record zero external socket attempts. Initial failures and their fixes remain visible; no failing source invariant was removed.
- Preservation: '''+f"**{len(protected):,} prior files checked, zero changed**"+'''. Original PDFs, frozen runs, ground truth and prior 350 artifacts remain untouched. Only the approved chunking/integration/test files changed relative to the Phase 1 snapshot.
- No extraction/detection/embeddings for the ten-input replay; the full regression suite independently exercises its normal fixtures and cached model tests. No server or larger batch started.
- Remaining limitations: byte-based token-policy calibration, indivisible oversized fields/context, provisional upstream record ownership, adjacent-only association audit scope, D2 paragraph reconstruction and incomplete human semantic labels. See limitations.md.

## Review files and stop boundary

- design.md — contracts, budgeting and integration.
- changes.md — exact production/test changes.
- test-results.txt — commands, actual outcomes and retained failure history.
- source-coverage-ledger-verified.json — owned/checked units, identities and shared budget events; detailed plans/messages in replay-verified/.
- before-after-comparison-verified.json / output-differences-verified.json — source/mapping/record comparisons.
- reference-comparison-verified.json — provenance-separated partial tuples.
- request-measurements-verified.json — serialized chunk envelope guards.
- preservation-check.json — immutable-artifact checks.
- readiness-assessment.md / limitations.md — NO-GO for scaling; conditions for a separately approved small provider pilot.

**Stopped here.** Any paid evaluation needs explicit new document scope, current settings and a new request cap. The old 40-call approval is not reused, and these 56 mocks are not a paid authorization.
'''
(OUT/'report.md').write_text(summary)
(OUT/'files-changed.json').write_text(json.dumps({'phase2_existing':existing,'phase2_new':result['new_code_files'],'after_sha256':{p:sha(ROOT/p) for p in existing+result['new_code_files']}},indent=2)+'\n')
files=[p for p in OUT.rglob('*') if p.is_file()]
(OUT/'created-files.json').write_text(json.dumps({'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(files)],'self_hash_excluded':True},indent=2)+'\n')
print(json.dumps(result,indent=2))
