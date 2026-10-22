# Individual resume check

Source: Jayesh Yadav-CV.pdf

- Extraction: fast; 55 elements.
- Sentence-BERT / K-means and local recovery: completed.
- Exact extracted-source interval validation: passed.
- LLM section review: disabled; provider calls: 0.
- Schema contract and source binding: passed.
- Separate LLM schema audit: disabled; findings: 0.
- Missing required fields: 10.

**Overall: needs review.** No human source approval or original-PDF word accuracy certification is implied.

Inspect extraction.json against the original PDF; sections.json for block placement and record ownership; schema.json for final values, field_evidence, missing_required_fields, unmapped_blocks and record_reviews; schema-audit.json for advisory LLM findings.

In LLM mode, unknown section content receives at most the configured recovery budget through the same section pipeline. Invalid responses retain validated output. Missing source words require correcting extraction (try a new run with --strategy ocr_only for scanned PDFs), then running the entire pipeline on that extraction. Missing schema fields and relationship findings require source inspection and a mapping/grouping fix; repeating identical input does not establish correctness. The schema audit never silently changes values. Preserve this run and use a new output directory after repairs.
