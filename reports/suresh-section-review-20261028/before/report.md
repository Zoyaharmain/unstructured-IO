# Individual resume check

Source: _SURESHBABUS.pdf

- Extraction: fast; 44 elements.
- Sentence-BERT / K-means and local recovery: completed.
- Exact extracted-source interval validation: passed.
- LLM section review: disabled; provider calls: 0.
- Schema contract and source binding: passed.
- Separate LLM schema audit: disabled; findings: 0.
- Missing required fields: 4.
- Feedback passes: 1; stop reason: local_only.
- Total DeepSeek calls (sections and schema audits): 0.

**Overall: needs review.** No human source approval or original-PDF word accuracy certification is implied.

Inspect extraction.json against the original PDF; sections.json for block placement and record ownership; schema.json for final values, field_evidence, missing_required_fields, unmapped_blocks and record_reviews; schema-audit.json for advisory LLM findings.

In LLM mode, unresolved meaningful spans, missing schema fields and schema-audit findings re-enter local recovery, LLM section review, schema mapping and schema audit. The configured budget is shared with invalid-placement retries. See pass directories and pipeline.json. Unchanged source/mapping output stops further retries. Invalid responses retain validated output. Missing source words require correcting extraction (try a new run with --strategy ocr_only for scanned PDFs), then running the entire pipeline on that extraction. Missing schema fields and relationship findings require source inspection and a mapping/grouping fix; repeating identical input does not establish correctness. The schema audit never silently changes values. Preserve this run and use a new output directory after repairs.
