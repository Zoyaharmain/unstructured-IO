# Enhanced hierarchical mapper: five-resume DeepSeek evaluation

## Result and recommendation

The targeted Manjunath regressions are fixed in the hierarchical output, and job
fragmentation is substantially reduced in several documents. The combined enhanced
production pipeline is NOT ready for a larger accuracy rollout: every tested resume
still has source-observed omissions or incorrect field associations. Levi's previously
correct email becomes contaminated with a phone number. Source-literal evidence and
schema validity alone do not prevent these errors.

Exactly the five user-confirmed resumes were processed. DeepSeek made 20 actual
requests: 10 section-placement requests and 10 advisory schema-audit requests. Each
resume used two bounded feedback passes. No transport failures, invalid-response
retries or finish_reason=length responses occurred. The second pair of requests per
resume is a configured feedback pass, not a network retry. No sixth resume or old350
continuation was run. Source PDFs, baselines, frozen production code, and 3,707 prior
full350 artifacts passed the post-run SHA-256 preservation check.

## Inputs, execution, and outputs

Full source paths, SHA-256 hashes, IDs and history exclusions are frozen in
[selection.json](selection.json). Inputs were `_Aashish Golhani.pdf`,
`_ManjunathMurugan.pdf`, `Aditya vashisth.pdf`, `_Levi Arbole.pdf`, and `_Rachana.pdf`.
All five were outside recorded previous LLM selections by filename and byte hash;
prior local processing was deliberately allowed. No ground-truth files were edited.

Executed command, in WSL:

```bash
cd /home/zoyaharmain/unstructured-IO
HF_HOME=/home/zoyaharmain/hf-cache HF_HUB_OFFLINE=1 DEEPSEEK_REVIEW_MAX_INPUT_CHARS=1000000 /home/zoyaharmain/venv312/bin/python scripts/run_hierarchical_five.py --manifest reports/hierarchical-deepseek-five-20261023-225341/selection.json --execute
```

The wrapper called the existing scripts/check_single_resume.py main for each PDF
using fast extraction, DeepSeek review, and one recovery attempt. It used the real
scripts/single_resume_pipeline.py run_feedback, local detection/recovery,
review_sections, map_schema/build_subschemas and the existing advisory schema audit.
The old direct ResumeSchema experimental mapper was not used. The wrapper changed
only transport telemetry and scope guards, not production mapping logic.
Model: deepseek-flash; thinking disabled; max output tokens 16,000 per request;
provider timeout 90 seconds; input-character limit explicitly raised to 1,000,000.
Root .env was loaded privately; no API key appears in saved requests or this report.

New per-document outputs are [results/01](results/01) through [results/05](results/05),
in the selection order. Each includes extraction.json, local-sections.json,
sections.json, schema.json, schema-audit.json, pipeline.json, raw provider messages,
and per-pass outputs. Full API envelopes and the shared call ledger are in results.

## Verification and denominators

- Final schema conformance: 5/5 documents.
- Exact source-interval preservation: 5/5 documents.
- Hierarchy shape and supplied record-local evidence validation: 5/5 documents.
- Literal support checks passed for 662/662 populated hierarchical items and
  857/857 quoted evidence references. These numbers verify source binding, NOT
  correct semantic parent/child choice or real-world job/education associations.
- Extracted element text matches the saved baseline exactly for 5/5 documents.
  The observed differences are not due to a new OCR/text extraction result.
- Exhaustive semantic accuracy, precision, recall, F1 and field exact-match accuracy:
  unscorable for 5/5; no reliable exhaustive human field references were established.
- 104 final LLM advisory findings are saved. They overlap, include mistakes, and
  must not be counted as 104 confirmed errors or a measured error rate.

See [evaluation.json](evaluation.json) for per-parent counts, source checks, missing
required fields, relationship warnings, usage and feedback history. Unresolved
optional fields are not automatically false negatives; the source must establish
that a value exists. No sections-only gold labels were used as field references.

## Per-resume summary

| Resume | API requests | Wall seconds | Tokens | Final audit advisories | Observed outcome |
|---|---:|---:|---:|---:|---|
| `_Aashish Golhani.pdf` | 4 | 50.377 | 359,306 | 20 | Contact retained; jobs consolidate 18 to 5, but titles/responsibility fragments still mix and a PG certificate is absent from education. |
| `_ManjunathMurugan.pdf` | 4 | 18.539 | 122,370 | 16 | Name/location and both proficiency pairs fixed; four job groups remain, but PwC/title assignments and a split date are wrong. |
| `Aditya vashisth.pdf` | 4 | 28.008 | 163,705 | 25 | Three work groups recovered; legacy name/email/links are corrupted, hierarchical name/email unresolved, and the M.Tech record is missing. |
| `_Levi Arbole.pdf` | 4 | 32.931 | 252,392 | 24 | Jobs consolidate 19 to 5 and location is recovered; email regresses by absorbing the phone, roles remain conflated, and languages are omitted. |
| `_Rachana.pdf` | 4 | 22.109 | 185,429 | 19 | Name/location and English proficiency improve; first role is employer/location, first job has no responsibilities, and the title is truncated. |

Record-count changes are diagnostic, not a standalone grouping accuracy metric.
All groupings remain subject to field/record source review. Aditya's first page was
visually inspected via source-review/03-page1.png, and independent pdftotext -layout
outputs for all five PDFs are saved under source-review/.

## Known manual errors: before and after

Only one distinct manually tested candidate can be established from the conversation:
Manjunath. The name/location and language examples are both from that resume.
The previously examined _ManjunathMurugan_1.pdf variant has the same extracted element
text as the selected file; it was not submitted as an additional document. A second
distinct manual-test candidate cannot be identified from available provenance.

The saved Manjunath baseline had a contact row misused as full_name, no location,
15 experience fragments, one merged education group, and unresolved language fields.
The new hierarchy has the correct name and full location, four employment groups,
two education groups, and separate English/French proficiency pairs.

| User-reported regression check | New hierarchical result |
|---|---|
| personal_information.full_name | Pass |
| personal_information.location | Pass |
| English + proficiency | Pass |
| Français + proficiency | Pass |

The returned values are Manjunath MURUGAN; Noisy-le-Grand, France;
English / Full Professional Proficiency (C1); and Français / Débutant (cours intensif en cours).
These are four checks against user-supplied examples, not an exhaustive gold score.
The legacy data.languages list still contains a bullet artifact; the hierarchy's
language pairs are clean. Fixing the nested output did not clean every legacy value.

All five saved local baselines were compared, even though only Manjunath has
identified manual-test provenance. [before-after.json](before-after.json) contains
field value-list differences and [before-comparison.json](before-comparison.json)
retains the original contact/language statuses. Aashish's 18 job fragments become 5;
Levi's 19 become 5; Rachana's 23 become 3. Rachana's wrong Healthcare candidate name
becomes RACHANA and its full location and English proficiency are recovered.

## Confirmed source-observed defects and likely causes

[observed-defects.json](observed-defects.json) gives concrete values, source excerpts
where available, classifications and root-cause inferences. It is an observation log,
not newly fabricated human-approved ground truth.

1. Employment headers: Manjunath role is PwC with company unresolved; the final job
   uses its title as company. Rachana role is Tieto HealthCare plus location. The
   vendor fallback assumes a company-first header and the shared header recognizer
   only handles exactly three pipe parts (record_subfields.py:59-71). Four-part
   role/company/location/date headers and dash-based headers remain weak.
2. New email regression: Levi's baseline arbole60@gmail.com becomes
   arbole60@gmail.com | 9823506339. labelled_fields (record_subfields.py:74-87)
   consumes text until the next known label rather than the end of the email token,
   then overrides the correct token extractor. Literal source presence and a plain
   string schema accept the resulting wrong field.
3. Merged contact fields: Aditya's PDF independently shows Aditya Vashisth, a
   standalone email, and separate GitHub/LinkedIn links. Concatenated extraction
   makes the legacy full_name Engineering LeadAditya VashisthTechnical and absorbs
   phone digits into email and neighboring labels into URL paths. Hierarchical
   name/email/GitHub are unresolved; LinkedIn remains a source-literal corrupted URL.
4. Education: Aditya loses the separate Master's record; Aashish's 2008 PG certificate
   is absent from education; Manjunath and Rachana institution values remain missing
   despite the universities appearing in source. Column/qualification grouping and
   combined-line institution refinement need work.
5. Duties/titles: Aashish's legacy role includes a dashboard responsibility; the
   hierarchical role is suppressed. Rachana's first job has zero responsibilities
   despite explicit source bullets. Title/action heuristics do not recover enough
   continuation spans, while legacy canonical joins can absorb unrelated content.
6. Split source fields: Manjunath loses October from October 2015; Rachana loses
   Healthcare from its headline. Date/title helpers operate on isolated fragments
   rather than assembling a supported field across adjacent source spans.
7. Mixed parent labels: Levi's Languages: English, Hindi inside Personal Details
   produces no hierarchical language records; the legacy language list is a bullet.
   Labeled list routing and the schema/legacy language paths remain inconsistent.
8. Residual quality: all_skills can contain case variants, heading text and sentence
   fragments. One duplicate skill candidate is detected for Aashish. Unknown and
   residual blocks remain exposed; they are not silently discarded.

## Audit findings that were not accepted as confirmed defects

The DeepSeek auditor says June 2026 is a future date in Aashish; on the client date
2026-10-23 it is not. It also suggests a missing computed tenure when Levi's source
has no numeric total, a missing certification based only on Rachana's role/awareness,
and data.awards even though legacy ResumeSchema has no such field. Those statements
must not trigger invented dates, tenure, credentials or schema keys.
[Audit claim review](audit-claim-review.json) records these cautions. Findings about
Aditya's GitHub also need explicit legacy-versus-hierarchical paths: one is corrupted
and populated, while the other is unresolved. Audit validation currently checks
source-ID existence and envelope shape, not factual correctness of every finding.

## Usage, latency, cost, and failures

Actual recorded prompt tokens: 1,058,157. Completion tokens: 25,045.
Total: 1,083,202. Prompt-cache hits: 60,160; misses: 997,997.
Total wall time including extraction, pipeline work and checks: 152.149 seconds.
Summed provider-request latency: 125.734 seconds (sequential calls).
All 20 responses have finish_reason=stop. Provider failures: 0/20.
All five have two feedback passes; Aashish, Aditya and Levi exhaust the configured
budget; Manjunath and Rachana stop for no source/mapping progress.

Cost is unavailable: the provider envelopes return usage but no billed-cost field.
No current rate was verified, so no historical pricing or unsupported dollar amount
was applied. Full envelopes preserve the actual model response IDs and token details.

## Interpretation and next step

The evidence supports a partial improvement, not a reliable accuracy claim. Targeted
Manjunath fields and some gross record fragmentation improve, but serious association
and token-boundary defects remain. This is an enhanced-plus-LLM run compared with
saved local outputs; it does not isolate the causal contribution of code changes from
LLM review. It is not comparable to full350's direct-mapper citation or gate-fact scores.

Fix contact field boundaries, combined-header decomposition, multi-span fields,
responsibility continuation and education grouping before expanding. Add the observed
regressions as source-bound tests, enforce semantic field-shape checks in both legacy
and nested outputs, and then rerun only a separately confirmed bounded evaluation.
Obtain independently human-verified field/record references before reporting accuracy.
No production mapper changes or extra paid retries were made during this evaluation.
