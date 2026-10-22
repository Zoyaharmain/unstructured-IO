import csv,hashlib,html,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.parents[1]
read=lambda p:json.loads(p.read_text())
s=read(OUT/'summary.json');inherited=read(OUT/'inherited-citation-summary.json');overall=s['overall'];selection=read(OUT/'selection.json');calls=read(OUT/'call-ledger.json')
for result in s['per_resume']:
 result.update(inherited[result['document']-1])
overall['direct_or_parent_citation_supported']=sum(r['direct_or_parent_citation_supported'] for r in inherited)
overall['direct_or_parent_citation_support_percent']=round(100*overall['direct_or_parent_citation_supported']/overall['populated_scalar_fields'],2)
overall['incorrect_populated_values_identified']=0
overall['unsupported_populated_values_identified']=0
overall['additional_source_supported_mapping_omissions']=3
overall['model_requested']=calls[0]['model_requested']
overall['models_returned']=sorted({c['model_returned'] for c in calls})
overall['estimated_cost']=None
overall['estimated_cost_reason']='Provider envelopes report token usage, not monetary amounts; no verified applicable tariff supplied.'
overall['original_pdf_independent_review_performed']=False
(OUT/'summary.json').write_text(json.dumps(s,indent=2)+'\n')
refs=read(OUT/'reference-facts.json')
production=read(OUT/'production-hashes-before.json')
changed=[p for p,h in production.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
sourcechanged=[row['file'] for row in selection if hashlib.sha256((ROOT/row['source_artifact']).read_bytes()).hexdigest()!=row['source_artifact_sha256']]
(OUT/'preservation.json').write_text(json.dumps({'production_files_checked':len(production),'changed':changed,'source_artifacts_changed':sourcechanged,'pdf_extraction_calls':0,'block_detection_calls':0,'paid_mapping_calls':len(calls),'paid_retries':0},indent=2)+'\n')
assert not changed and not sourcechanged and len(calls)==5

def text(v):return json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else str(v)
def cell(v,limit=250):
 v=text(v).replace('|','\\|').replace('\n',' ')
 return v if len(v)<=limit else v[:limit]+'…'

def example(number,path,detail):
 fields=read(OUT/f'{number:02d}/field-evaluation.json');r=next(r for r in fields if r['path']==path)
 return {'document':number,'field':path,'source':r['analyst_evidence'],'mapped_value':r['value'],
  'mapping_status':r['mapping_status'],'raw_citation_status':r['support_status'],'raw_provider_evidence':r['evidence'],'evaluation':detail}
examples=[
 example(1,'/experience/0/company','Correct employer, independently separable from location in the block. Raw field citation is exact.'),
 example(1,'/experience/1/start_date','The date range precedes Godavari Cuts but is attached to the prior responsibilities element. Null is a defensible abstention; not counted as a confirmed mapping omission. The separate end_date/duration are populated from that same uncertain association, which is inconsistent.'),
 example(1,'/education/0/graduation_year','Source explicitly says Pursuing / Expected Completion. The output carries June 2026 and its missing_information explains the in-progress qualification. This is not proof the degree was already earned; year formatting needs normalization policy.'),
 example(2,'/skills/technical_skills/7','Spring Security is present in the freelance source, but its raw citation points to an unrelated skills line. Value support and citation correctness are separate.'),
 example(2,'/education/0/grade_or_gpa','Correctly preserves CGPA from its academic source despite local language/project category mistakes elsewhere.'),
 example(2,'/projects/0/name','Correct project recovered even though the local block category is experience. Existing local category errors were not treated as authoritative.'),
 example(3,'/skills/technical_skills/0','Go (Golang) is in source. The provider cites its parent technical_skills array, not the required per-item pointer; strict raw per-field evidence fails. Analyst-derived evidence is separate.'),
 example(3,'/education/0/graduation_year','Detached 2022/2018/2016 are not safely associated from block labels alone. Leaving graduation year null is appropriate uncertainty, not a confirmed schema-mapping miss.'),
 example(3,'/experience/1/role','Front-End Development Trainee is literal source text. Whether a training program belongs under employment requires a policy; no fabricated job title is established.'),
 example(4,'/experience/0/company','Employer is Tech Mahindra; the client Mastercard is not fabricated as a separate employer. The schema has no client field.'),
 example(4,'/experience/3/responsibilities/0','NPCI responsibility recovered from locally labeled projects blocks and attached to the source-supported employer. This corrects a local label problem during mapping without rerunning block detection.'),
 example(4,'/experience/3/responsibilities/-','The source work item Worked on Tag Mapping to Element level mapping for IMPS is absent from both mapped responsibilities and projects. This is a source-supported target omission, not absent PDF text.'),
 example(4,'/skills/all_skills/0','ISO8583 is source-supported, but no raw citation is supplied for this duplicate flat-list item. Schema validity alone does not enforce provenance.'),
 example(5,'/education/0/field_of_study','Intelligent Systems is explicit in the degree text but this available schema field is null. Classified as a mapping omission; the degree itself remains populated.'),
 example(5,'/experience/1/responsibilities/0','Value can be reconstructed from e34 plus e35 after excluding interleaved dates. The provider quotes autonomous as if it were in e35; it is actually in e34. This is a concrete incorrect quotation, not evidence of an invented thesis.'),
 example(5,'/education/0/graduation_year','December 2015 is literal but detached from both degree rows. The association is ambiguous without PDF/layout review; literal support alone does not make it correct.'),
]
# Enrich empty-field examples with the separately supplied ambiguity evidence.
for e in examples:
 if e['source']:continue
 raw=read(OUT/f"{e['document']:02d}/mapping-raw.json");blocks={b['source_id']:b['text'] for b in read(OUT/f"{e['document']:02d}/source-blocks.json")}
 sourceids=[]
 for m in raw.get('missing_information',[]):
  if e['field'] in m['path']:sourceids+=m.get('source_ids',[])
 e['source']=[{'source_id':sid,'quote':blocks[sid]} for sid in dict.fromkeys(sourceids) if sid in blocks]
(OUT/'examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n')
notes={
1:'Correctly maps the primary job, finance skills, contact details and degree/major split. Godavari role is absent from blocks; empty role is appropriate. Godavari dates are internally inconsistent: start_date null but end_date/duration populated despite an ambiguous preceding range. B.Com institution is not independently established. Expected MBA completion remains explicitly qualified in metadata.',
2:'Correctly maps two work records, three projects, academic grades and three course providers from blocks with faulty local labels. Spoken languages remain empty. Professional headline Software Engineer is taken from a job role rather than an explicit headline, so its headline interpretation is ambiguous. The chief failures are missing/incorrect field citations, especially all_skills duplicates and misaligned technical-skill indices.',
3:'Correctly maps the main employer, three project names, three degrees and course providers. Detached education years are left null rather than guessed. The trainee entry is explicitly qualified as training but represented in experience; employment policy remains ambiguous. Most list citations are on parent arrays instead of each item, so only 32 populated fields meet the strict raw contract.',
4:'Correctly distinguishes four employers and their roles/date ranges, keeps the Tech Mahindra client separate, restores NPCI responsibilities mislabeled as projects, and maps certification issuers/years where stated. Candidate residence is correctly not inferred from workplace Hyderabad. Flat all_skills items lack field citations. The source Tag Mapping/IMPS work item is omitted from the target responsibilities and projects. No definite incorrect populated value was identified against the saved blocks in this sample.',
5:'Recovers research and employment records from locally misclassified publications, keeps awards/membership out of certifications and identifies repeated footer contacts. Education and Siemens date associations remain ambiguous; graduate-student history represented as employment is policy-ambiguous. Two explicit specializations are left null. One quote points to the wrong block for autonomous; one technology citation omits its continuation block. Original source contains interleaved text, not a mapping-created PDF omission.'}
for doc,row in zip(selection,s['per_resume']):
 n=doc['number'];d=OUT/f'{n:02d}';fields=read(d/'field-evaluation.json');facts=read(d/'critical-fact-evaluation.json');mapping=read(d/'mapping.json');raw=read(d/'mapping-raw.json')
 tables='\n'.join(f"| `{r['path']}` | {cell(r['value'])} | {r['mapping_status']} | {r['support_status']} | {cell(', '.join(x['source_id'] for x in r['analyst_evidence']))} |" for r in fields)
 facttable='\n'.join(f"| {f['id']} | {cell(f['collection']+'.'+f['field'])} | {cell(f['expected'])} | {cell(f['actual'])} | {f['status']} |" for f in facts)
 out=f'''# {doc['file']} — five-resume schema pilot

Selection: {doc['reason']}

Saved input: `{doc['source_artifact']}` → `{doc['section_key']}`. Pages: {doc['pages']}. Source blocks: {doc['blocks']}. No new extraction/block detection was run. Original PDF was not independently examined for this evaluation.

{notes[n]}

- Critical-field agreement proxy: **{row['critical_facts_correct']}/{row['critical_fact_denominator']} = {row['critical_agreement_percent']}%**.
- Same-block local heuristic baseline on the same critical set: **{row['baseline_critical_correct']}/{row['critical_fact_denominator']}**.
- Raw field citation contract: **{row['raw_citation_supported']}/{row['populated_scalar_fields']} = {100*row['raw_citation_supported']/row['populated_scalar_fields']:.2f}%**.
- Populated-value source-block assessment: {json.dumps(row['analyst_mapping_status_counts'])}.
- Human-verified/PDF-verified accuracy: **not established**.

## Complete mapping output

[Mapping JSON](mapping.json) · [Unmodified provider mapping and citations](mapping-raw.json) · [Full provider envelope/usage](response-envelope.json) · [Saved source blocks](source-blocks.md) · [Every evaluated field](field-evaluation.json)

```json
{json.dumps(mapping,ensure_ascii=False,indent=2)}
```

## Field-by-field results

`correct_mapping` is provisional AI analyst source-block agreement, not independent human truth. `citation_error` can coexist with correct value content. Analyst source references supplement the evaluation; they do not retroactively repair the raw provider response. Null/empty fields are retained for inspection; absence and ambiguity reasons are in the JSON. The CSV/JSON contain full values and exact quote text; the table abbreviates long values.

| Field | LLM value | Mapping assessment | Raw citation assessment | Analyst source IDs |
|---|---|---|---|---|
{tables}

## Predeclared critical opportunities

Degree plus field_of_study may satisfy one reference degree opportunity. Original month-year strings are accepted when the expected year matches; this does not remove date-association ambiguity. Country codes, punctuation/whitespace, labels such as CGPA and enclosing lab/organization context are normalized as documented in the main report.

| Reference | Target | Expected source fact | Actual value | Result |
|---|---|---|---|---|
{facttable}

## Provider missing-information statements

These are provider claims, not independent truth. Compare with field-evaluation.json for analyst disagreements and actual mapping omissions.

```json
{json.dumps(raw.get('missing_information',[]),ensure_ascii=False,indent=2)}
```

## Provider upstream observations

```json
{json.dumps(raw.get('upstream_observations',[]),ensure_ascii=False,indent=2)}
```
'''
 (d/'report.md').write_text(out)
selectiontable='\n'.join(f"| [{x['file']}]({x['number']:02d}/report.md) | {len(x['pages'])} | {x['blocks']} | {x['reason']} |" for x in selection)
metrictable='\n'.join(f"| [{r['file']}]({r['document']:02d}/report.md) | {r['critical_facts_correct']}/{r['critical_fact_denominator']} ({r['critical_agreement_percent']:.2f}%) | {r['baseline_critical_correct']}/{r['critical_fact_denominator']} | {r['raw_citation_supported']}/{r['populated_scalar_fields']} ({100*r['raw_citation_supported']/r['populated_scalar_fields']:.2f}%) |" for r in s['per_resume'])
usagetable='\n'.join(f"| {c['file']} | {c['model_returned']} | 1 | {c['usage']['prompt_tokens']:,} | {c['usage']['completion_tokens']:,} | {c['usage']['total_tokens']:,} | {c['status']} |" for c in calls)
exampletable='\n'.join(f"| {e['document']} `{e['field']}` | {cell(' / '.join(x['source_id']+': '+x['quote'] for x in e['source']),350)} | {cell(e['mapped_value'],250)} | {cell(e['evaluation'],450)} |" for e in examples)
main=f'''# DeepSeek schema mapping evaluation — exactly five resumes

**Result: promising source-block mapping, but not ready for unattended integration under the requested provenance contract.** All five responses satisfy the existing schema types. Most checked core facts agree with the saved blocks, but field-level citations are incomplete or misaligned, several associations remain ambiguous, and three source-supported target assignments are missing (two specializations and one work item). No production code was modified.

Evaluation saved: {datetime.now(timezone.utc).isoformat()}. **Exactly five mapping POSTs; zero retries or larger batches.** A separate preflight `GET /models` checked the key/model and sent no resume text. The API key was loaded privately from `.env` and is not present in saved requests/reports. No original PDF was independently checked; all accuracy-like numbers below are **provisional source-block agreement**, not human-verified resume accuracy.

## 1. Inspection and selected scope

Before calls, this evaluation inspected the existing `ResumeSchema` models, source-binding validator, local schema adapter, DeepSeek transport, local/review block formats and current acceptance/evaluation workflow. The production mapper is heuristic and makes no LLM calls; this pilot is an isolated direct LLM mapper using the same target schema. It does not change the application routes or production mapping behavior.

| Resume | Pages | Saved local blocks | Why selected |
|---|---:|---:|---|
{selectiontable}

All five come from the existing 350-document scope and have distinct frozen PDF hashes. The exact artifact hashes and local-block inventories are in [selection.json](selection.json). Inputs use **local_sections**, before prior DeepSeek section changes, to isolate direct schema mapping on local detections. Every assigned and unknown span was included. Source order, IDs, offsets, page and local category were provided; local labels were advisory. Existing source/PDF snapshots were not re-extracted. These five are purposive examples, not a random accuracy sample, and contain no scanned-image OCR case.

## 2. Method and calculation denominators

The provider returned `data` matching the existing target plus `evidence`, `missing_information` and `upstream_observations`. Required unknown strings stay empty, nullable fields null and lists empty. Instructions required extractive, source-supported values; no tenure arithmetic, fictional records, inferred spoken English or external facts. Every populated scalar/list item was requested to have a JSON-pointer citation with source ID and exact quote. Requests never contained the reference answers.

**Three different measurements are reported, with different meanings:**

1. **Critical-field agreement proxy (requested per-resume accuracy measure):** before mapping calls, an AI analyst froze **113 source-block field opportunities** covering contact, employers/roles/dates, degrees/institutions/grades, projects and certificate providers/years. Numerator = selected opportunities agreeing with source-supported output after documented normalization. Denominator = all 113; ambiguous opportunities remain in the denominator and are not counted correct. Result: **111/113 = 98.23%**. Ajay's two Godavari dates are conservatively ambiguous; they are not declared extraction/mapping errors. This is a targeted source-block agreement score, not whole-resume accuracy or full-schema recall. The two missing Nithin specialization fields and the missing A Madhavi Tag Mapping work item were found outside this predeclared set and are separately reported, not hidden or added post hoc to improve the benchmark. [Frozen reference facts](reference-facts.json), [all critical results](critical-fact-evaluation.json).
2. **Populated-field source-block assessment:** **668 populated scalar leaves** across the five mapped objects. Each list item counts separately, including repeated facts in categorized skills, all_skills and job technologies. AI analyst assessment: **646 provisionally correct/source-supported; 22 ambiguous; 0 definite invented values or definite incorrect populated value mappings identified from the available blocks**. Conservative supported-and-unambiguous proportion = **646/668 = {100*646/668:.2f}%**. This is not independent semantic precision. It includes local quote lookup and targeted source association review, and is vulnerable to missed errors; duplicates can inflate the apparent weight of skills. Three missing assignments and 129 other null/empty slots are outside the populated-field denominator. No exhaustive source-fact recall denominator was established.
3. **Strict raw per-field citation compliance:** **432/668 = 64.67%**. A pass requires the provider's own exact per-leaf pointer, existing source IDs, exact quotes and value support from those quotes. **236 populated fields fail this strict raw criterion**. This failure does not imply 236 hallucinated values. Boovanesh often supplies valid parent-array citations rather than per-item citations; DDhanush and A Madhavi omit citations for duplicated all_skills entries. Some DDhanush citations point to the wrong item. One Nithin quote combines words from the wrong source block. Evaluator-derived references are stored separately and are not counted as raw compliance.

Normalization permits case/Unicode/whitespace/punctuation differences, degree/major splitting, numeric equivalents, a source month-year containing the expected year, grade label prefixes and enclosing organization/lab names. These allowances are explicit and can yield agreement even when output formatting needs cleanup. Eight unambiguous education-year fields contain original month-year strings rather than canonical four-digit years; two additional Nithin month-year fields also have uncertain degree associations. JSON Schema permits strings, so this is a field-normalization/policy warning rather than a type-validation failure.

The reference set and adjudication were produced by this AI assistant from saved blocks. They are **not independent human labels**, and there was no second paid LLM judge or PDF inspection. Scores must not be generalized to all 350 resumes. Old malformed extraction text remains an upstream limitation.

**Parent-array evidence sensitivity check:** allowing deterministic inheritance from a provider-cited parent list raises supported coverage to **572/668 = 85.63%**. All 140 additional fields are in Boovanesh; its parent-array references do support those items. Thus those 140 failures are a granularity/contract issue, not completely absent source evidence. The remaining **96/668** still fail even with parent inheritance. [Inheritance calculation](inherited-citation-summary.json). The strict 64.67% result remains unchanged, and investigator-derived global lookup is never counted as provider evidence.

## 3. Per-resume and overall results

| Resume | Critical-field agreement proxy | Same-input local mapper baseline | Strict raw citations |
|---|---:|---:|---:|
{metrictable}
| **Overall** | **111/113 (98.23%)** | **36/113 (31.86%)** | **432/668 (64.67%)** |

The local baseline was rerun only as a local mapping function over the **same saved local blocks**, without embeddings, extraction or provider calls. It preserves detected entry boundaries and consequently leaves many fields blank. The comparison suggests that whole-block LLM mapping can recover source relationships missed by the existing mapper; it is not an independently validated model accuracy comparison or a production acceptance result.

Every output and every scalar/empty field is available in the linked per-resume reports, `mapping.json`, unmodified `mapping-raw.json`, and `field-evaluation.json`. The consolidated [field-evaluation.csv](field-evaluation.csv) contains all **800 evaluation rows**: 799 emitted scalar/empty-slot rows plus one observed missing-array-item opportunity. Empty arrays count as one empty slot for inspection only, not as a recall opportunity. [Machine-readable summary](summary.json).

## 4. Concrete field-level examples

Long examples are abbreviated in this table; [examples.json](examples.json) and the per-resume field JSON preserve full values, source quotes and IDs.

| Resume / field | Source text and block | LLM value | Evaluation |
|---|---|---|---|
{exampletable}

The Nithin quote error is exact: source `e34:58:163` ends with **autonomous**, while `e35:0:76` begins **mobile robot navigation**. The provider quotes **autonomous mobile robot navigation** against e35, which is not an exact substring. The thesis content is reconstructable from three real fragments, so this is an incorrect citation, not an invented thesis value. The evaluation records those corrected supporting fragments separately without altering raw output.

## 5. Missing information versus mapping errors

- **Appropriately absent:** Ajay's Godavari role and B.Com institution are not explicitly established; Boovanesh job dates and project roles are absent; A Madhavi's home residence is not stated; spoken languages are not listed. Empty fields here are not automatically mapping failures.
- **Ambiguous upstream associations:** Ajay's second-job range is attached to the preceding employer element; Boovanesh's 2022/2018/2016 values are detached from education rows and locally classified as certification text; Nithin's education and Siemens dates are detached/interleaved. Mapping must retain uncertainty rather than invent reliable associations.
- **Confirmed mapping omissions against saved blocks:** Nithin `education[0].field_of_study` should carry **Intelligent Systems** from `e8:38:82`; `education[1].field_of_study` should carry **Electronics and Communication** from `e8:120:176`. Both remain null. A Madhavi’s `e61:0:56` states **Worked on Tag Mapping to Element level mapping for IMPS.**, but this item is absent from her mapped NPCI responsibilities and projects. Its evaluation path ends in `/-` to denote a missing array item, not an emitted model property. The text is present and the target fields exist, so these are mapping omissions even though degree strings retain the words. They are not PDF extraction failures.
- **Unsupported values:** no definite fabricated scalar fact was identified by the source-block checks and AI analyst review. This is not a proof of zero hallucination. One provider quote is concretely unsupported as attributed, and 236 fields fail the raw citation contract; model-declared missing-information reasons also remain claims to review.
- **Schema/policy gaps:** the target lacks dedicated awards, publications, membership and mentoring slots. Those cannot be silently forced into certifications. Notes preserve their existence, but do not constitute a complete structured mapping of every original fact. Training/graduate-student entries in work history need a typed policy. Expected completion and 7+/around-3 experience qualifiers cannot be fully represented by a plain year/float without metadata.

All 668 populated leaves have separate analyst source references in field-evaluation.json, including ambiguous values; reference validity does not resolve semantic ambiguity. Raw outputs were not repaired or reissued. This distinction prevents evaluator citation supplementation from disguising provider provenance failures.

## 6. Upstream defects kept separate

The source binding validator passed for all five local block inventories: all extracted characters are preserved and offsets are exact. This does not establish original-PDF word accuracy.

- Ajay: name/phone/location are unknown blocks; the summary is split across experience/unknown categories; finance dates are attached to a preceding responsibility element; a Godavari bullet ends mid-sentence in source. Those are pre-existing input/segmentation concerns.
- DDhanush: programming skills are locally classified as spoken languages; project blocks are locally classified as experience; contact text contains `(cid:...)` glyph placeholders. The LLM corrects some category interpretation but cannot certify the PDF glyphs.
- Boovanesh: detached years, standalone bullets, empty elements and wrapped skill fragments are inherited input structure. Parent-array evidence is a new response-contract issue, not an extraction issue.
- A Madhavi: NPCI responsibilities are locally under projects, and one named project continues across blocks. Correct reassociation is possible from explicit company markers/source order, without rerunning extraction.
- Nithin: research jobs occur under publications; dates are interleaved in thesis and job text; name/email/page footers recur; `BOct 2023 - Nowengaluru, India` is garbled in the saved source. These are upstream defects. The wrong quote attribution, unfilled specialization fields and omitted Tag Mapping work item are mapping/evidence defects introduced or left by this pilot.

## 7. Model, usage, cost and failures

| Resume | Model returned | Mapping calls | Input tokens | Output tokens | Total tokens | Result |
|---|---|---:|---:|---:|---:|---|
{usagetable}
| **Total** | **deepseek-flash** | **5** | **41,546** | **32,429** | **73,975** | **5 schema-valid outputs** |

Prompt-cache hit tokens: **9,728**; miss tokens: **31,818**. These are subsets of prompt tokens, not additional tokens. Provider prompt caching does not mean responses were reused locally. All five were fresh mapping requests. The configured and returned model is `deepseek-flash`; thinking follows the configured mode, captured in each request. All responses ended with `finish_reason: stop`; no transport, authentication, truncation or target-schema failures occurred. Citation-contract failures are reported above rather than hidden by schema success.

**Cost estimate: unavailable.** The envelopes provide token usage, not billed monetary amounts; no verified applicable tariff is supplied by these artifacts. No fallback price or total cost is invented. Inspect your provider billing for the actual charge. [Credential-free call ledger](call-ledger.json) and per-resume response envelopes provide the actual usage.

## 8. Tests and preservation

Existing relevant tests: **73 passed; 0 failed** — schema mapping, single-resume feedback, report source binding, LLM response validation and local-only block inspection. The test harness removed provider keys, blocked external connections and recorded **zero external connection attempts**. [Test log](tests/regression.log), [JUnit XML](tests/tests.xml), [network guard](tests/network-guard.txt).

Production files checked: **{len(production)}; changed: 0**. Selected source artifacts changed: **0**. No production application, mapper, detector, schema model, API route or `.env` file was edited. Evaluation scripts/results are confined to this new private directory. [Preservation evidence](preservation.json). No extractor, detector or embedding model was invoked by the pilot; the local baseline calls only the existing mapper.

## 9. Recommended next steps — no additional calls launched

1. Keep this as an **evaluation prototype**. The source-block agreement is encouraging; five purposive examples do not justify changing production or scaling to 300 resumes.
2. For a proposed future implementation, validate `data` **and evidence** as one atomic contract. Require per-leaf pointers, exact quote spans and record-specific source ownership; reject or explicitly flag missing/misaligned citations. Handle repeated all_skills facts with deterministic citation reuse, preserving the original model evidence. Do not hide failures with a second unreported paid call.
3. Preserve typed uncertainty for ambiguous employer/date associations, expected completion and approximate experience. Set policy for trainees/research students. Normalize years only with source-backed transformations and evidence; do not infer employers or spoken languages.
4. Fix the demonstrated specialization and work-item omissions and evaluate source-supported complete-record recall, per-role responsibilities/technologies and record associations on an independently reviewed reference set. Our 113 selected facts do not enumerate every possible field opportunity.
5. Review source PDF pages for the upstream layout/date/glyph cases, then complete independent approval. Schema-only prompting cannot repair facts missing from extraction or fill unsupported target slots.
6. Show this report and obtain user approval **before any additional paid calls, prompt retry, larger batch or production integration change**. This run ended after the five authorized mapping POSTs and made no paid evaluation/judging calls.

## 10. Reproducibility and audit trail

[selection.json](selection.json) freezes resume names, rationale, artifact hashes, local-source key and block hashes. [target-schema.json](target-schema.json) is the existing target definition. `reference-facts.json` was written before mapping calls and not sent to the provider. `run_pilot.py` creates an attempt ledger before sending a request and refuses an existing ledger, preventing accidental repeat calls. `evaluate.py` performs literal/citation checks; `adjudicate.py` adds documented AI source-block assessments and a same-input local baseline comparison; it is not a second LLM judge. Run `evaluate.py`, `adjudicate.py`, `inherit_citations.py`, then `build_report.py` to rebuild the offline evaluations without paid calls. `run_pilot.py` refuses to run again because the call ledger exists. Every evaluation-derived citation is explicitly identified separately from the raw provider citations.

Full per-resume JSON and source excerpts contain personal data and remain in this directory; they are not published. **Human-verified accuracy, original-PDF accuracy and unbiased corpus accuracy remain unmeasured.**
'''
(OUT/'report.md').write_text(main)
# Small static navigation page; detailed Markdown/JSON remain authoritative.
rows=''.join(f'<tr><td><a href="{x["number"]:02d}/report.md">{html.escape(x["file"])}</a></td><td>{s["per_resume"][i]["critical_agreement_percent"]}%</td><td><a href="{x["number"]:02d}/mapping.json">Mapping JSON</a></td><td><a href="{x["number"]:02d}/field-evaluation.json">Every field</a></td></tr>' for i,x in enumerate(selection))
(OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Five-resume DeepSeek schema pilot</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:20px}td,th{padding:12px;border:1px solid #ccc}table{border-collapse:collapse}p{line-height:1.6}</style><h1>Five-resume DeepSeek schema mapping pilot</h1><p>Exactly five mapping calls; 73,975 tokens. All five outputs schema-valid. Critical-field source-block agreement: 111/113 (98.23%). Strict raw citations: 432/668 (64.67%). These are AI-assisted source-block assessments, not human/PDF-verified accuracy.</p><p><a href="report.md">Detailed report</a> · <a href="summary.json">Machine-readable summary</a> · <a href="field-evaluation.csv">All field results CSV</a></p><table><tr><th>Resume</th><th>Critical agreement proxy</th><th>Output</th><th>Evaluation</th></tr>'+rows+'</table><p>No production change or larger batch was launched. Approval is required before further paid calls.</p>')
print('Saved main report, five full per-resume reports, examples and navigation page.')
