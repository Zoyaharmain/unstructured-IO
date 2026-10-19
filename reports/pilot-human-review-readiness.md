# Human review readiness: 15-resume pilot

## Current decision

**Do not scale yet.** The live LLM assigned all extracted spans, but this does not establish PDF word coverage, correct sections, or correct work/education relationships. No human approvals or new gold exports were created in this task. The local review editor is running at http://127.0.0.1:8022.

## What the audit established

- Exact reconstructed extraction is not a transcription check. GAURAVAGRAWAL page 2 visibly contains an Achievements heading absent from the saved extraction and one awards paragraph that appears twice in extraction but once in the page image. Both problems survived zero-unassigned accounting. They are now approval blockers.
- The independent pdftotext comparison flagged four documents: Ajay Bandagi, GAURAVAGRAWAL, Rutuja Herekar and NagaVishnu. Most reported differences in Ajay/Rutuja/Naga are compatible with joined/spaced headings; they still require source review and are not automatically called omissions.
- Java Aws backend is visibly an unfilled job-requirements template. It needs an explicit scope/exclusion decision, not invented work-history or degree labels.
- Work/education evidence checks block approval for all 15 current drafts. This means their relationship fields/evidence are incomplete or unverified, not that every proposed grouping has been proven wrong.
- Automated audit covered all 15; visual spot checks in this task covered PUPPYKUMARI page 1, Rutuja page 3, Java Aws backend page 1 and GAURAVAGRAWAL page 2. This is not a claim that every PDF page has already been independently reviewed.

## Why the reference agreement changed

Both outputs were rechecked on the same extracted inventory and unchanged reference spans. Of 81,352 non-whitespace scored characters, the old output matched 81,284 and the new one matched 79,099. Exactly **2,206 characters moved away from the reference and 21 moved toward it**, a net loss of 2,185 matches: 99.9164% → 97.2306% (**−2.6859 percentage points**). Entire-resume matches changed from 9 to 7.

The drift audit identifies each changed interval, text, source element, PDF page, old/new label and reference label. Changes concentrate in Pavan’s Achievements bullets, Rutuja’s foundational GenAI/coursework section, and the Java job-template requirements. The new prompt supplies more source context and record hints, but a single non-deterministic run does not establish a unique causal explanation. The existing references were auto-promotable and often close to the old predictions; therefore neither score is independently established semantic accuracy. No reference labels were changed.

| Document | Old reference agreement | New reference agreement | Relationship/evidence findings | PDF-parser difference |
|---|---:|---:|---:|---|
| Pavan Bakku.pdf | 99.68% | 83.08% | 11 | False |
| Ajay Bandagi.pdf | 100.00% | 100.00% | 20 | True |
| AkshayPatni (1).pdf | 100.00% | 100.00% | 14 | False |
| Prasad PR.pdf | 100.00% | 100.00% | 17 | False |
| Anuradha Yadav.pdf | 100.00% | 100.00% | 14 | False |
| Java Aws backend.pdf | 98.77% | 63.62% | 6 | False |
| GAURAVAGRAWAL.pdf | 100.00% | 100.00% | 23 | True |
| Charansai P.pdf | 99.82% | 99.12% | 11 | False |
| Alvina _Fernandes.pdf | 100.00% | 98.15% | 20 | False |
| Nikhil Kumar.pdf | 100.00% | 100.00% | 17 | False |
| Rutuja Herekar.pdf | 99.83% | 83.62% | 14 | True |
| S  Abhinav.pdf | 100.00% | 99.10% | 15 | False |
| A Suribhotla.pdf | 100.00% | 100.00% | 14 | False |
| NagaVishnu.pdf | 99.90% | 99.90% | 16 | True |
| PUPPYKUMARI.pdf | 99.92% | 99.92% | 35 | False |

## Review and approval workflow

The old static dashboard did not record human decisions. The new editor shows original PDFs, immutable model proposals, assistant observations and old/new drift separately. Section decisions, split/merge edits, logical block IDs, record membership and record-field evidence are stored in append-only working revisions, not in the source drafts. Typed reviewer identity is self-attested. Each final approval requires decisions for every span, all PDF pages checked, explicit content/relationship attestations and no unresolved source findings.

Approval writes a source-bound approved review bundle, **not gold**. Only a separate explicit export can create a new approved dataset version. The exporter refuses missing approval, stale PDF/draft hashes, unsupported relationships, and overwriting an existing approved file or the existing ground_truth/gold directory. Gold provenance includes the exact approval bundle hash. A later working edit invalidates the prior readiness gate until reapproval/export.

Employer/title/date and degree/institution/year values must be supported by evidence span IDs inside the same record. Wrong-section members, shared membership, unsupported values and absent unverified fields block approval. Strict tuple precision/recall/F1 scoring is implemented for later approved references: equal entry counts do not constitute a relationship match. It refuses legacy human_verified flags without explicit approval provenance. No relationship accuracy is claimed yet.

## Review priorities

1. GAURAVAGRAWAL page 2: confirm the missing heading and duplicate paragraph; create/review a new extraction version without editing the originals.
2. Java Aws backend: check both pages and explicitly exclude if confirmed as a job template. Replace it in a new pilot version if 15 in-scope resumes are required.
3. PUPPYKUMARI page 1: check the four employer/title/date table rows and four education rows. Role History dates disagree with Career History dates; preserve and resolve that discrepancy explicitly. Check project/client links on pages 2–6.
4. Rutuja page 3: coursework/Topics Studied/QA Applications I’m Building Toward should not silently become past employment. The education list names degrees/years without institutions; do not invent them.
5. Pavan page 1: compare KEY ACHIEVEMENTS against the new Summary assignments.
6. Review the remaining documents using the per-document drift and relationship queue. These observations are assistance, not human approvals.

## Files and commands

- Full instructions and future guarded bulk command: `docs/PILOT_HUMAN_REVIEW.md`.
- Interactive editor: `http://127.0.0.1:8022` (`.venv/bin/python scripts/review_pilot.py --port 8022`).
- Per-document review queue: `ground_truth/human_review/audit/index.html`.
- Exact old/new changes: `ground_truth/human_review/audit/section-drift.json`.
- Relationship findings: `ground_truth/human_review/audit/relationship-issues.json`.
- Source comparison and source-page previews: `ground_truth/human_review/audit/`.
- A gate-only check was run; it correctly reported 0/15 reviewed and exited with status 2. No bulk generation started, no new LLM calls were made, and no annotations were promoted.
- The future bulk command is enclosed in set -e and starts with a blocking pilot gate. It extracts to a new source version and generates only silver/needs_review candidates in a new output directory. Approved corrections are skipped/referenced and hash-checked; mismatches require explicit rebase.
- Current collection contains 1,082 PDFs, 453 DOCX and 6 DOC files. The candidate scaling command labels PDFs only; the earlier saved batch is partial.

## Preservation and validation

All 93 protected files (original PDFs, current drafts, review pages and existing gold) matched their initial SHA256 hashes after the work. No real human decisions were written by tests. Local browser/API checks loaded all 15 and rejected an unreviewed approval without writing a revision. The full local regression suite passed 173 tests, with 8 upstream parity cases deselected.
