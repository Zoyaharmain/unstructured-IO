# Reviewing and approving the 15 pilot resumes

The review editor is at **http://127.0.0.1:8022**. To start it again:

```bash
.venv/bin/python scripts/review_pilot.py --port 8022
```

It binds to loopback, reads the preserved PDFs and live-review drafts, and makes
no LLM calls. A review never silently creates a gold file. The older static pages
are displays of predictions; they do not record human approval.

## What to do in the editor

1. Select a resume and enter your reviewer name. Read every original PDF page.
   “Locate PDF page” jumps from a span to its page. The original JSON span ID,
   element index, exact offsets and proposed record are visible.
2. Check the assistant observations and the old/new LLM change list. These are
   review aids, not verified labels. “Human-review flags only” narrows the view;
   approval still requires decisions for the entire inventory.
3. Approve or correct section labels. Click “Mark this span checked” to record a
   decision. If you have actually checked every span, the explicit all-checked
   button can record those decisions together. Nothing is checked by default.
4. Use the logical block ID input to join related spans into a block. Use the
   span JSON editor to split an element at exact offsets or merge adjacent spans
   within one element. Keep text equal to the original source substring, use
   unique IDs, and update record references. A multi-element logical block uses
   shared block IDs, not rewritten text. Applying edited spans clears decisions
   so the revised inventory must be checked again.
5. Use the record ID input to move a span to a job or education record. The
   records JSON editor lets you split/merge records, remove empty records and
   enter employer/title/dates or degree/institution/year. Set `span_ids` to the
   exact members. Do not infer employer or dates from unrelated projects.
6. Add source evidence and an explicit relationship decision to each record.
   Example structure (example values, not a pilot annotation):

```json
{
  "record_id": "experience-1",
  "span_ids": ["employer-span", "title-span", "date-span", "bullet-span"],
  "employer": "Example Ltd",
  "title": "Software Engineer",
  "dates": "2020 - 2022",
  "field_evidence": {
    "employer": ["employer-span"],
    "title": ["title-span"],
    "dates": ["date-span"]
  },
  "human_relationship_decision": "approved"
}
```

For education the required fields are `degree`, `institution`, `year`, with the
same evidence structure. A field genuinely absent from the PDF must have an empty
value, `field_states: {"institution": "not_in_source"}`, and a specific explanation
in `field_notes`. Unsupported values, missing evidence, membership in another
section, overlapping record membership and incomplete fields block approval.
These structural checks cannot prove semantics: you must check the table rows
and page context yourself. Exact relationship tuple scoring is implemented in
`score_record_relationships`; it refuses legacy references without explicit
approval provenance. It can be run once approved references exist.

7. For an ignored artifact, choose the artifact action and state why. For a
   duplicate, give the original span ID and a reason; the validator requires
   matching source text. Repeated role summaries or awards in different contexts
   are not automatically duplicates. Text remains traceable in either case.
8. Record missing/unreadable PDF content in PDF issues. Open issues block approval.
   Known findings cannot be hidden by deleting them from the editor. “Resolved”
   needs an explanation. A confirmed missing extraction cannot be fixed merely
   by assigning a label or closing the issue: create a new source/extraction and
   annotation version, rebase the affected review, and validate it against the
   original PDF. Do not edit the preserved inputs or rewrite gold to get a score.
   In particular, GAURAVAGRAWAL’s missing heading/duplicate text remains a blocker.
9. If a document is outside the resume dataset, inspect all its pages and use
   “Exclude non-resume from pilot,” with a reason. This records an exclusion,
   not gold. Java Aws backend appears to be a job-requirements template and needs
   this scope decision; it must not fabricate a candidate’s earned qualifications.
10. Save working decisions at any point. The server creates a new immutable
    `revision-NNNNNN.json` under `ground_truth/human_review/<document-id>/`.
    Working annotations remain `human_verified:false`. The original predictions
    remain in the original draft file, bound by hash. On final approval, check
    every attestation, enter all reviewed pages, and click “Record explicit
    approval.” The editor validates the whole review before writing a separate
    `approved-NNNNNN.json`. It displays the exact saved path. No gold is created.

The local tool records a reviewer’s typed identity and explicit attestations; it
is not an identity verification or proof-of-expertise system. Human decisions
and corrected annotations live in the review bundle, separately from the LLM
proposal. A revision of a draft/PDF invalidates the earlier source binding. A new
working save after approval also requires fresh approval before scaling.

## Explicit export after approval

Run this only after obtaining an actual approved bundle. Set the variables to
real paths from the editor; the command fails if approval is missing or stale:

```bash
draft='ground_truth/recovery_pilot/live-review/drafts/NAME.json'
approved_review='ground_truth/human_review/DOCUMENT_ID/approved-NNNNNN.json'
.venv/bin/python scripts/verify_ground_truth.py \
  --draft "$draft" --approved-review "$approved_review" \
  --gold-dir ground_truth/approved_gold_v2 \
  --gold-jsonl ground_truth/approved_gold_v2/gold_resumes.jsonl
```

The exporter refuses the existing `ground_truth/gold` directory, refuses to
replace an approved file, preserves decision provenance, and never sweeps all
drafts into gold. Exporting a later correction requires a new dataset version.
Keep approved exports for the full in-scope pilot in the chosen version. Explicit
out-of-scope exclusions do not get gold files.

## Compare old and new predictions without relabeling

`ground_truth/human_review/audit/section-drift.json` lists every changed source
interval, page, old/new/reference category and text. The audit reports 2,206
characters changing away from the reference and 21 toward it. The 2,185 net loss
explains the 99.92% → 97.23% difference exactly over 81,352 scored characters.
The reference labels remain untouched. Old labels agree strongly with old
predictions, so the old score is not independent proof of correctness. The prompt
and context changed, and no deterministic repeated-run experiment was done;
causation or real semantic accuracy cannot be inferred solely from this score.

Use the original PDF to resolve each issue and document the labeling policy.
Standalone Achievements headings generally differ from achievements described
inside a job; job requirements differ from actual work history; coursework and
future aspirations must not become past employment; table rows must preserve
employer/title/dates and degree/institution/year associations. These are review
policy proposals, not changes made automatically to the labels.

## Safe future candidate generation — do not run yet

Current collection: 1,082 PDFs, 453 DOCX and 6 DOC files. Candidate scaling below
labels **PDFs only**. The old saved batch is partial; it is not the complete
collection. The following commands first enforce human review, then extract into
a new source version and generate candidates in a separate directory. They have
not been run. `set -e` stops the sequence if the pilot gate fails.

```bash
(
set -e
.venv/bin/python scripts/pilot_review_gate.py \
  --review-dir ground_truth/human_review \
  --approved-gold-dir ground_truth/approved_gold_v2

resume_folder='/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT'
RESUME_AUDIT_OUTPUT_DIR="$PWD/.upstream/bulk-source-v2" \
  ./scripts/run_offline_resume_audit.sh "$resume_folder" --timeout 120

.venv/bin/python scripts/scale_ground_truth.py \
  --source-results-dir .upstream/bulk-source-v2 \
  --output-dir ground_truth/candidate_runs/after-human-pilot-v2 \
  --approved-gold-dir ground_truth/approved_gold_v2 \
  --pilot-review-dir ground_truth/human_review \
  --workers 3
)
```

The gate requires a current approved export or explicit exclusion for every pilot.
Bulk generation references approved corrections unchanged and skips them; it also
skips exclusions. PDF/extraction hash mismatch stops processing and requires an
explicit correction rebase. Automated labels go only to silver/needs_review.
Legacy auto-promoted gold files are preserved but not accepted as pilot approval.
Unchanged source-bound LLM caches avoid repeating completed requests. The source
inventory is deduplicated by filename, and output filename collisions cannot
replace another resume. This is candidate generation, not human verification of
the whole collection. Independent held-out evaluation is still needed later.

## Versioning a confirmed extraction repair

Do not replace the preserved draft or original extraction. Create a new artifact
and draft version with a new `extraction_sha256`, then explicitly rebase the human
corrections to its intervals. The review server supports an optional JSON catalog:

```json
[
  {
    "file": "NAME.pdf",
    "draft": "ground_truth/new_version/drafts/NAME.json",
    "artifact": "ground_truth/new_version/source/NAME.json",
    "pdf": "ground_truth/pilot_resumes/NAME.pdf"
  }
]
```

A real catalog must contain the complete pilot set, not this single-row example.
Preserve the default IDs for unchanged reviewed documents if reusing their saved
reviews; changed drafts should get new IDs (derived automatically if `id` is
omitted). Launch with `review_pilot.py --catalog PATH --port 8022`, check the gate
with `pilot_review_gate.py --catalog PATH ...`, and pass `--review-catalog PATH`
to candidate generation. All three must use the same catalog.

For the known missing heading, a new source version may resolve its issue with
`resolution: "reextracted"` plus a resolution note only when the extraction hash
has changed and the missing heading is actually present. The old source binding
is retained in the finding. A false alarm instead requires a specific human
explanation. A new source version must still pass full span/relationship review;
changing a hash alone is never approval. The bulk stage stops if its newly
extracted inventory no longer matches the approved correction inventory.

An excluded job template is not a successfully labeled resume. If the goal is
15 in-scope gold resumes, replace it through an explicitly versioned pilot
selection and review the replacement; do not fabricate resume labels for it.

## Run relationship evaluation after approval

```bash
.venv/bin/python scripts/evaluate_review_relationships.py \
  --predicted-dir ground_truth/recovery_pilot/live-review/drafts \
  --reference-dir ground_truth/approved_gold_v2 \
  --output ground_truth/human_review/relationship-evaluation
```

This reports exact employer/title/date and degree/institution/year tuple matches,
precision, recall, F1, and incomplete predicted records per resume. No LLM calls
are made. Missing or unapproved reference files are reported as unavailable, not
as zero accuracy. These structural/field comparisons complement, rather than
replace, checking PDF table associations and record membership against the source.
