# Three flagged documents: root causes, fixes and fresh live results

**Decision: do not proceed to the next 35 resumes.** The specific abstention/status problems are corrected or explicitly scoped, but source-backed work/education grouping problems remain. No new gold or semantic-accuracy claim is made.

## Measured before and after

| Document | Local raw / meaningful | Old final raw / meaningful | Fresh final raw / meaningful | API calls old → new | Fresh outcome |
|---|---:|---:|---:|---:|---|
| Java Aws backend.pdf | 5 / 5 | 11 / 11 | 11 / 11 | 2 → 1 | llm_reviewed_out_of_scope |
| NagaVishnu.pdf | 83 / 81 | 6 / 6 | 0 / 0 | 2 → 1 | llm_reviewed_all_assigned |
| Prasad PR.pdf | 3 / 3 | 1 / 1 | 0 / 0 | 2 → 1 | llm_reviewed_all_assigned |

## What ran and what was preserved

Final deterministic validation artifacts are in validated-final/: a no-API pass finalized explicit scope applicability/warnings without changing any live assignments. The raw fresh provider artifacts remain untouched in live-run/deepseek/documents/. Only these three were copied from the hash-verified original corpus. The fresh local log records discovered=3, cached=0, pending=3 and completed extraction/detection/recovery for all three before the provider stage. The DeepSeek log records cached=0 and new_attempts=3. Reviewer checkpoints say source_reextracted=false because they consume the newly generated local stage, not because old pilot JSON was replayed. No other 15/35/50/1500-document run occurred.

Actual DeepSeek requests: **3** (previous three: 6). Input tokens **70,002**, output **2,195**, total **72,197**. All three response finish reasons are stop; responses parsed with permitted categories and complete interval coverage. No API errors, skipped reviews, truncation or invalid-response retries were recorded. No chunks were used. Prices were not assumed.

All **1996** snapshotted original-run/ground-truth/source files remained unchanged; changed files: 0. The original PDFs match the selection SHA256 and fresh copies. Fresh extracted inventories match the original run for all three.

## Shared implementation

- `local_api/services/review_resolution.py`: `document_scope` recognizes requirements forms from a conjunction of content features, with no filename branches; `resolve_unassigned` handles explicitly supported declaration/sign-off and combined-heading abstentions only. It preserves all text and records source IDs, UNKNOWN classification/reason for remaining content, and explicit scope metadata. Existing section proposals in out-of-scope documents are evidence, not applicable candidate facts.
- `local_api/services/llm_section_review.py`: `make_messages` supplies document scope and clarifies declaration/combined-heading/requirements handling; `review_sections` resolves supported abstentions, revalidates coverage, updates meaningful-content status, and avoids another semantic retry for out-of-scope documents. Existing invalid/malformed/truncated-response rejection remains atomic.
- `scripts/llm_verify_resume_batch.py`: `review_document` distinguishes `llm_reviewed_out_of_scope` and uses meaningful remaining content rather than raw noise for `needs_review` reporting.
- `scripts/rerun_flagged_pilot.py`: fresh bounded rerun with source hashes, separate output and preserved prior artifacts. Only explicitly selected flagged pilot members (maximum three) are allowed.

## Per-document evidence

### Java Aws backend.pdf

**Observed cause:** All 11 old final spans are meaningful form/requirements text, not whitespace. Five local abstentions were retained and six locally assigned spans were deliberately moved to needs_review by the first valid provider response. The ledger stayed at 48 units and split_units was zero: the rise 5→11 was not splitting, truncation, parser rejection or text loss. Both old responses ended stop and had no invalid_response_attempts. They were two complete-document passes.

**Correction:** A shared requirements-form detector needs requirements headings, Mandatory Skills and at least three blank starred fields. It exposes job_requirements/out_of_scope and candidate_sections_are_applicable=false; keeps all source and provider proposals but warns they are not candidate history. Further recovery calls are suppressed for out-of-scope forms. Unresolved source spans carry UNKNOWN and an explicit out-of-scope reason.

**Outcome:** PARTIALLY FIXED: correct scope handling; explicit exclusion/human decision still needed. No forced candidate placement.

PDF pages checked: [1, 2]. Original-source page images were revisited from the prior hash-bound render directory; PDFs are unchanged. Java pages1–2 show a requirements form; Naga page5 explicitly shows declaration/sign-off and earlier pages show three employments and six named projects; Prasad page2 shows the combined heading over awards and certificate items. These are assistant source checks, not human gold approvals.

**Remaining relationship concerns:** Any Education/Experience proposals are preserved model evidence only, inapplicable to candidate records for this requirements form.

**Source integrity:** exact source intervals validated; no missing/overlapping/duplicated output intervals; returned labels limited to permitted categories; raw source text untouched. This does not certify every PDF word. Independent parser token differences are recorded in report.json; Naga differences include letter-spaced/joined headings and are not automatically declared omissions.

**Before unresolved text:**
- `e0:0:49` page 1: 'Project /Customer Name or Strategic Requirement *'; meaningful=True
- `e1:0:12` page 1: 'Job title: *'; meaningful=True
- `e2:0:21` page 1: 'Work Base Location: *'; meaningful=True
- `e3:0:38` page 1: 'Experience range: (Min to Max years) *'; meaningful=True
- `e4:0:40` page 1: 'Start Date of the Position/Requirement *'; meaningful=True
- `e5:0:19` page 1: 'No. of Positions: *'; meaningful=True
- `e18:0:17` page 1: 'Responsibilities:'; meaningful=True
- `e19:0:114` page 1: 'Development and operations of the existing system landscape as well as ensuring maintainability, reliability, and '; meaningful=True
- `e19:114:126` page 1: 'scalability.'; meaningful=True
- `e20:0:51` page 1: 'Active participation in Scrum and SAFe team events.'; meaningful=True
- `e21:0:100` page 1: 'First experience in migrating a system landscape to the Cloud are a great benefit for the candidate.'; meaningful=True

**After unresolved text:**
- `e0:0:49` page 1: 'Project /Customer Name or Strategic Requirement *'; UNKNOWN / out-of-scope requirements; text retained.
- `e1:0:12` page 1: 'Job title: *'; UNKNOWN / out-of-scope requirements; text retained.
- `e2:0:21` page 1: 'Work Base Location: *'; UNKNOWN / out-of-scope requirements; text retained.
- `e3:0:38` page 1: 'Experience range: (Min to Max years) *'; UNKNOWN / out-of-scope requirements; text retained.
- `e4:0:40` page 1: 'Start Date of the Position/Requirement *'; UNKNOWN / out-of-scope requirements; text retained.
- `e5:0:19` page 1: 'No. of Positions: *'; UNKNOWN / out-of-scope requirements; text retained.
- `e18:0:17` page 1: 'Responsibilities:'; UNKNOWN / out-of-scope requirements; text retained.
- `e19:0:114` page 1: 'Development and operations of the existing system landscape as well as ensuring maintainability, reliability, and '; UNKNOWN / out-of-scope requirements; text retained.
- `e19:114:126` page 1: 'scalability.'; UNKNOWN / out-of-scope requirements; text retained.
- `e20:0:51` page 1: 'Active participation in Scrum and SAFe team events.'; UNKNOWN / out-of-scope requirements; text retained.
- `e21:0:100` page 1: 'First experience in migrating a system landscape to the Cloud are a great benefit for the candidate.'; UNKNOWN / out-of-scope requirements; text retained.

Live deterministic resolver events: 0. The fresh prompt itself resolved Naga/Prasad; the old-response replay tests exercise deterministic fallbacks without an API call. Predictions can vary between runs, so the fresh result alone does not prove a unique causal effect or improved accuracy.

### NagaVishnu.pdf

**Observed cause:** 83 local pending units comprise 81 nonempty meaningful spans and two whitespace spans. The first valid old response assigned all 83 local pending units, but moved seven end-of-document spans from Education to needs_review (declaration, attestation, place/date and signature/name). Its second full review assigned the signer name, leaving six meaningful abstentions. Thus 83→6 is not simply 77 corrected blocks. No chunking or truncation occurred.

**Correction:** Prompt explicitly locates declarations and sign-offs in Personal Information. If the provider still abstains, exact Declaration + I hereby declare source evidence permits source-backed resolution of that declaration and adjacent same-page sign-off. It does not reclassify arbitrary body text or discard it. Remaining meaningful content retains UNKNOWN/reason. Raw whitespace stays preserved but does not drive needs_review status or retries.

**Outcome:** FLAG FIXED; overall resume PARTIALLY FIXED because work/education relationships are still wrong/unverified.

PDF pages checked: [1, 2, 3, 4, 5]. Original-source page images were revisited from the prior hash-bound render directory; PDFs are unchanged. Java pages1–2 show a requirements form; Naga page5 explicitly shows declaration/sign-off and earlier pages show three employments and six named projects; Prasad page2 shows the combined heading over awards and certificate items. These are assistant source checks, not human gold approvals.

**Remaining relationship concerns:** experience-2 merges Unlimited Innovations and Cognizant; education-2 places BE CGPA8.07 with SSC instead of the BE record. Repeated identical responsibility wording occurs in different project contexts in the source; not automatically deleted.

**Source integrity:** exact source intervals validated; no missing/overlapping/duplicated output intervals; returned labels limited to permitted categories; raw source text untouched. This does not certify every PDF word. Independent parser token differences are recorded in report.json; Naga differences include letter-spaced/joined headings and are not automatically declared omissions.

**Before unresolved text:**
- `e113:0:11` page 5: 'Declaration'; meaningful=True
- `e114:0:110` page 5: 'I do hereby declare that above particulars of information and facts stated are true, correct, and complete to '; meaningful=True
- `e114:110:146` page 5: 'the best of my knowledge and belief.'; meaningful=True
- `e115:0:17` page 5: 'Place: Hyderabad '; meaningful=True
- `e115:17:34` page 5: 'Date: 9 June 2026'; meaningful=True
- `e116:0:10` page 5: 'Signature '; meaningful=True

**After unresolved text:**
None. This means assignment coverage only, not overall semantic correctness.

Live deterministic resolver events: 0. The fresh prompt itself resolved Naga/Prasad; the old-response replay tests exercise deterministic fallbacks without an API call. Predictions can vary between runs, so the fresh result alone does not prove a unique causal effect or improved accuracy.

### Prasad PR.pdf

**Observed cause:** The remaining old unit is page2 e26[0:24], AWARDS & CERTIFICATIONS with trailing space. It is meaningful heading text. The provider assigned the other two locally pending units and abstained on this mixed heading in both valid complete responses. Two calls were first review + semantic follow-up, not chunking, truncation or invalid-response retries.

**Correction:** Prompt allows source-word-boundary handling for combined headings. Fallback splits only an exact Awards & Certifications heading (or reversed order), only when both named section families already contain assigned source content. The &/spaces remain attached to a source interval; coverage is still exact. In the fresh live run the provider assigned the heading in one call; deterministic splitting was needed in the old-response replay test, not applied to this live response.

**Outcome:** FLAG FIXED; overall resume PARTIALLY FIXED because record relationships and the PGSQL internal block boundary remain concerns.

PDF pages checked: [1, 2]. Original-source page images were revisited from the prior hash-bound render directory; PDFs are unchanged. Java pages1–2 show a requirements form; Naga page5 explicitly shows declaration/sign-off and earlier pages show three employments and six named projects; Prasad page2 shows the combined heading over awards and certificate items. These are assistant source checks, not human gold approvals.

**Remaining relationship concerns:** education-1 combines Liverpool, IIIT-B and JSS while education-2 holds MSc degree alone; experience-3 holds Oct25–Present detached from PWC. PGSQL remains intact in extraction but split into source blocks; not changed by this narrowly scoped fix.

**Source integrity:** exact source intervals validated; no missing/overlapping/duplicated output intervals; returned labels limited to permitted categories; raw source text untouched. This does not certify every PDF word. Independent parser token differences are recorded in report.json; Naga differences include letter-spaced/joined headings and are not automatically declared omissions.

**Before unresolved text:**
- `e26:0:24` page 2: 'AWARDS & CERTIFICATIONS '; meaningful=True

**After unresolved text:**
None. This means assignment coverage only, not overall semantic correctness.

Live deterministic resolver events: 0. The fresh prompt itself resolved Naga/Prasad; the old-response replay tests exercise deterministic fallbacks without an API call. Predictions can vary between runs, so the fresh result alone does not prove a unique causal effect or improved accuracy.

## Tests and limits

Full regression: **199 passed**, no deselections, in 95.64s (regression-tests.log, tests.xml). Added source-backed suite: **14 passed** in 0.29s (source-replay-tests.log). Existing malformed/incomplete/truncated-response, retry, coverage, invalid category/offset and local-retention tests remain included. An initial local source-replay test exposed a signer-name fragment separated from Signature; recovery was corrected to consult the original source element label, then all 14 passed. An earlier sandbox combined test invocation stalled; only the completed outside-sandbox regression and completed 14-case replay run are counted.

New tests cover literal combined-heading offsets with supporting content, unsupported combined headings remaining unknown, explicit declaration vs a bare word, scope detection vs normal prose, whitespace/page breaks/footer retention with no unnecessary retry, meaningful C# not suppressed, and replay of all three actual first provider responses. Replay checks assert no input mutation and that deterministic recovery leaves provider Experience/Education source ownership unchanged. This preserves those proposals; it does not prove their record associations are correct.

All source IDs and complete record memberships are in report.json and live-run/deepseek/documents/. Provider response contents and per-document call/token records are in live-run/deepseek/provider-decisions/ and checkpoints/. UNKNOWN is an explicit unresolved classification in metadata, not a new canonical section that hides uncertainty. No whitelist of these filenames was added to production logic.

**Readiness: NO for the next 35.** Decide Java exclusion and independently correct/approve the employment/education groupings. Naga/Prasad abstention flags are fixed; their overall resume correctness remains partially fixed/unverified.
