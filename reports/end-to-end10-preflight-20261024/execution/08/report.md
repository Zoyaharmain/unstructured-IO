# Individual resume check

Source: Santhosh KR -  SAP EWM.pdf

- Extraction: auto; 134 elements.
- Sentence-BERT / K-means and local recovery: completed.
- Exact extracted-source interval validation: passed.
- LLM section review: complete; provider calls: 1.
- Schema contract and source binding: passed.
- Separate LLM schema audit: complete; findings: 24.
- Missing required fields: 9.
- Feedback passes: 2; stop reason: recovery_budget_exhausted.
- Total DeepSeek calls (sections and schema audits): 4.

**Overall: needs review.** No human source approval or original-PDF word accuracy certification is implied.

Inspect extraction.json against the original PDF; sections.json for block placement and record ownership; schema.json for final values, field_evidence, missing_required_fields, unmapped_blocks and record_reviews; schema-audit.json for advisory LLM findings.

In LLM mode, unresolved meaningful spans, missing schema fields and schema-audit findings re-enter local recovery, LLM section review, schema mapping and schema audit. The configured budget is shared with invalid-placement retries. See pass directories and pipeline.json. Unchanged source/mapping output stops further retries. Invalid responses retain validated output. Missing source words require correcting extraction (try a new run with --strategy ocr_only for scanned PDFs), then running the entire pipeline on that extraction. Missing schema fields and relationship findings require source inspection and a mapping/grouping fix; repeating identical input does not establish correctness. The schema audit never silently changes values. Preserve this run and use a new output directory after repairs.
