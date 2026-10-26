# Abhijit integration diagnosis and repair

Review date: 26 October 2026 (Asia/Kolkata).

The supplied output exposed a missing integration stage. DeepSeek reviewed
section ownership, while schema mapping still called only regex/local handoff
helpers. The handoff's original `parse_resume_content()` orchestrator includes an
LLM structured-extraction branch, but the host adapter had imported only its
models, specifications, and heuristic helpers. Enabling DeepSeek section review
therefore did not repair missing or incorrect field values.

The extraction adapter is working for this DOCX: its ordered word-token sequence
matches the DOCX paragraphs, with no missing or added word tokens. BERT and seeded
K-means remain the local detection stage. They have not been replaced.

## Corrected architecture

1. Existing local Unstructured API extracts the document text and provenance.
2. Existing Sentence-BERT/K-means and structural recovery propose sections.
3. DeepSeek reviews section ownership using the whole-document source context.
4. New DeepSeek field mapping applies the imported ResumeSchema definitions and
   field descriptions, repairs record ownership, and emits source-backed items.
5. Pydantic and exact-source validators reject unknown fields, invented values,
   foreign citations, overlapping records, unexplained omissions, or invalid shapes.
6. Legacy fields, hierarchical subschemas, field indexes, evidence and source
   statuses are built from the same validated items. Invalid field responses
   receive bounded correction attempts; failures retain local results visibly.

The frontend explicitly requests this field stage. The individual CLI includes
it when `--llm-review` is selected. Schema/query APIs retain their local default
and support `review_fields: true` for explicitly requested provider mapping.

## Abhijit results

| Item | Supplied output | Repaired result |
| --- | --- | --- |
| Employment records | 6; one earlier job omitted | 7, including Engagement Media |
| Employer/role associations | Missing roles and misassigned employers | All seven employer/role pairs checked against source |
| Degrees | MBA; B.Com degree blank | MBA and B.Com with institutions and specializations |
| Certifications | 5, including spurious `S` | Four actual certificate/course names |
| Flat skills | 4 | 49 literal competencies/tools |
| Professional headline | Empty | Full source headline |
| Career summary/highlights | Incomplete/misclassified | 15 source statements retained |
| Required fields missing | 4 | 0 |
| Reviewed candidate fields unmapped/ambiguous | Several gaps | 0 / 0 in this run |

The fixes also prevent matching CERTIFICATION inside CERTIFICATIONS, preserve
slash-separated competencies, recognize B.Com, keep numeric year evidence, and
avoid treating training responsibilities or client-count qualifiers as evidence
that an entire employment/summary record is uncertain. Career-wide highlights
and business impact belong to summary rather than skills or an arbitrary job.

## What legitimately remains empty

The source does not provide LinkedIn/GitHub/portfolio URLs, education grades, or
certificate issuers/issue dates. It contains a bare LinkedIn label and no external
DOCX hyperlink relationship. These fields now say **Not stated**, rather than
claiming the mapper cannot resolve them. A job containing only `2017` does not
establish a separate end date.

Two final screening/editorial notes remain outside candidate fields. They tell
an editor what to add only after screening; they are not evidence that the
candidate owns the qualifications mentioned there. They remain visible for
inspection instead of being converted into candidate skills or credentials.

## Verification and limits

- Source interval conservation and record-local citation validation passed.
- Legacy and nested repeated-record fields agree, including their dates.
- All seven employer/role pairs, both degrees and four certificate names were
  checked against the source document.
- DeepSeek was exercised on the real document. The final accepted saved live
  response was replayed after tightening deterministic validation and heading
  normalization, without further paid calls. This distinction is retained in
  `meta.verification_run`.
- Browser verification replays the saved live artifacts: DeepSeek mode requests
  `review_fields=true`, displays populated schema fields, differentiates missing
  source facts, and enables download without JavaScript exceptions. This browser
  check makes no additional provider calls.
- Test results are recorded in `test-verification.json`.

These are results for this specific source, not a claim of perfect accuracy on
all resumes. Schema and quote validity cannot independently prove every semantic
association. Unsupported data must remain absent or flagged, rather than invented.

## Files and reproduction

- [Corrected schema](final/after.schema.json)
- [Corrected record ownership](final/reviewed-sections.json)
- [Source and field checks](verification.json)
- [Original supplied output](before.schema.json)
- [Final extraction](final/extraction.json)
- [Saved live field response](final/provider-response-3.json)
- [Browser result](browser-result.json)
- [Browser screenshot](frontend.png)

The updated local app runs at http://localhost:8012. Refresh the page before
uploading again. Start it again with:

```bash
.venv/bin/python scripts/start_resume_inspector_local.py --port 8012
```

For a new CLI run, use `--llm-review` and a new output directory:

```bash
.venv/bin/python scripts/check_single_resume.py \
  --file "/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT/Abhijit_Dey.docx" \
  --strategy auto --llm-review \
  --output "reports/abhijit-check-$(date +%Y%m%d-%H%M%S)"
```

Historical downloaded outputs were preserved; they do not update automatically.
