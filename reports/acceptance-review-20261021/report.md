# Acceptance review prepared — 21 October 2026

**Decision: do not start a larger paid batch or accept the 350 documents for production yet.** Proceed with source review of the existing pilot. This preparation made no provider calls and recorded no human approvals.

## Work completed

- Prepared a [review page](index.html) and [prioritized queue for all 350 distinct documents](all-350-review-queue.csv), deduplicated by PDF hash using the latest recorded live artifact per document. Full source text, scope, grouping and source-fidelity evidence are in [queue JSON](all-350-review-queue.json).
- Prioritized 19 documents with historical provider failures, scope questions, OCR or damaged-glyph concerns. Another 244 have unresolved text or employment/education association warnings. The remaining 87 have no such automated priority flags; their semantics still require independent sampling. Priorities are triage signals, not confirmed error rates. Historical live failures remain visible even where a later offline replay accepted a saved response.
- Checked all 15 pilot PDF/draft/extraction inputs. All are available; [45 input files remained unchanged](pilot-preservation.json). Draft validation identifies 247 structural/field-evidence issues across the pilot; see [per-document preflight](pilot-preflight.json). These include unverified fields and record membership, not 247 independently confirmed semantic mistakes.
- Ran the [actual pilot acceptance gate](pilot-gate.json): **0 of 15 documents currently qualify through explicit human approval/export or exclusion**.
- Ran [relationship evaluation](relationship-evaluation/summary.json): **0 documents evaluated**, because no qualifying approved references exist. Accuracy is unavailable, not zero and not 100%.
- Located the running [human review editor](http://127.0.0.1:8022). Verified all 15 document endpoints and original PDF hashes through read-only requests. See [editor verification](editor-check.json). No save, approve, exclude or export requests were sent.
- Checked the six remaining meaningful spans from the additional-100 offline replay against an independent PDF text parser: **6/6 appear on the stated PDF pages**. Saved [page context and source IDs](remaining-span-source-checks.json). This confirms text presence; it does not settle category policy or prove semantic accuracy. Three are Additional Information headings; the others are the Professional Membership heading, IEEE membership and Since 2024. They remain preserved for a policy/section decision, rather than becoming a false certification or job.
- Ran focused readiness/report checks: **20 tests passed**, recorded in [validation.log](validation.log). The preceding complete project regression remains **274 passed**; no production code changed during this preparation.

## Your next action

Open **http://127.0.0.1:8022**. Begin with **GAURAVAGRAWAL.pdf** (known missing-heading/duplicate-extraction concerns) and **Java Aws backend.pdf** (possible job template requiring exclusion). Then review the remaining pilot documents, checking every PDF page, section label, employer/title/date and degree/institution/year relationship. The editor records your decisions; viewing predictions does not approve them. Known extraction defects need a new source version and annotation rebase before approval, as described in the [review instructions](../../docs/PILOT_HUMAN_REVIEW.md).

A proposed treatment of the six additional-100 spans is to preserve Additional Information as a source heading attached only to demonstrably supported content, and preserve IEEE membership as professional membership. This is a proposed labeling policy, not an automatic reassignment. The current taxonomy has no professional-membership category. Decide/version that policy before expanding categories or changing annotations.

After source issues are resolved and explicit pilot reviews are exported, rerun:

```bash
.venv/bin/python scripts/pilot_review_gate.py \
  --review-dir ground_truth/human_review \
  --approved-gold-dir ground_truth/approved_gold_v2
```

Use the same explicit catalog for the editor and gate if any pilot extraction/draft is versioned. Run relationship and section evaluation against the approved references, followed by an independent held-out sample. Set acceptance thresholds from those measurements before another bounded live batch. The [detailed workflow](../../docs/PILOT_HUMAN_REVIEW.md) includes export and evaluation commands.

**Can you process more resumes now?** Additional diagnostic processing is technically possible, but I do not recommend spending on more resumes yet. First establish whether the existing predictions are correct. The missing requirement is independent source-backed approval and evaluation; further automated coverage alone cannot supply it.
