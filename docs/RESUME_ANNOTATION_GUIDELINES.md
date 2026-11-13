# Independent source annotation

A reviewer must work from the original PDF/DOCX and raw extracted text without parser sections, predicted records, provider responses or previous model-generated labels. Upstream extraction types such as Title/Header/Footer do not establish semantic truth. Do not use this development session's diagnostic examples as held-out data.

## Prepare a blind worksheet

Run raw extraction without semantic section/record parsing. Then export:

```bash
.venv/bin/python scripts/annotate_resume_sources.py export \
  --extraction /path/to/raw-extraction.json \
  --original /path/to/original.pdf --output evaluation/annotations/new-document
```

The export contains immutable source evidence, an unlabeled JSON template and a TSV worksheet. It never copies model assignments. Offsets count Python Unicode characters, not bytes or visual glyphs. A source ID `e3:10:40` identifies exactly `elements[3].text[10:40]`. Preserve the source digest, original-document SHA256, literal text and offsets.

Edit `annotation.json`; the TSV is an optional reading worksheet, not automatically approved labels. A mixed physical line can be divided into smaller exact source intervals with matching IDs and literal text. Cover every non-whitespace character once, with no overlaps. Verify extraction omissions against the original and log them separately; do not invent missing extracted words.

## Semantic decisions

1. Assign each span a canonical section from the exported category list. Section headings belong to their section. Experience responsibilities mentioning tools, awards or education remain within Experience when tied to that job. Career-wide achievements without a supported job link remain outside individual jobs.
2. Identify employer scopes separately from individual roles. A promotion or second position under one employer is a separate role. Do not create a second role merely from a client, project, technology list, date line or subsection label.
3. Give each role a `record_anchor`: the source ID of its first primary span. Every primary span of that role points to the same anchor; the anchor points to itself. A standalone company heading may be the first role's primary span and shared company context for sibling roles, but dates and duties never inherit by proximity alone.
4. Set `kind` to `responsibilities` or `achievements` for duty/impact fragments that have independently established role ownership. Set the same `unit_id` on fragments of one logical bullet across lines or pages. Other spans can use `other`, `title`, `employer`, `dates`, `heading` or `artifact`.
5. Follow continuation through page breaks and columns using the original document's reading flow. A repeated page decoration may use section `ignore`; an upstream Header/Footer classification alone is insufficient. A later-page role title or a one-word duty continuation is meaningful content.
6. Preserve missing dates as missing, and overlapping jobs as overlapping. Employer names, dates and titles cannot be inferred from the previous record. A skill or technical discipline alone does not establish a job title.
7. Record ambiguity in `notes`. Leave unresolved labels unverified until adjudication. Do not change a reference to match parser output. Partial annotations are useful for review but cannot certify whole-resume accuracy.

## Review and adjudication

Templates start with `human_verified: false` and `annotation_origin: unlabeled_template`. An LLM draft must remain identified as generated and must never be promoted merely by setting a verification flag. Independent reviewers should create blind human annotations from the source, not edit a model's answer into an alleged independent reference.

After independent manual annotation, record `annotation_origin: independent_human`, `human_verified: true`, and review metadata: `method: independent_human`, a real reviewer ID, and `saw_parser_predictions: false`. These are human attestations, not fields the parser fills automatically. Held-out labels additionally require `independence_attested: true` and a different adjudicator ID. Retain both reviewers' disagreements and their resolution in a separate append-only review log.

Validate before scoring:

```bash
.venv/bin/python scripts/annotate_resume_sources.py validate \
  --extraction /path/to/raw-extraction.json \
  --annotation evaluation/annotations/new-document/annotation.json --held-out
```

Keep original gold files unchanged. Version corrections with reviewer, date, reason, previous-file hash and new-file hash. Freeze review before viewing predictions. If a reviewer sees predictions first, mark that exposure and move the example to development/validation rather than claiming blind held-out status.

For scored evaluation, supply a JSON object mapping original source SHA256 to reviewed annotation objects, a frozen split manifest, and a selection with original source paths and hashes. `evaluate_source_ownership.py --truth ... --split-manifest ...` checks membership; held-out runs additionally require `--evaluate-held-out`. Do not run held-out resumes merely to inspect failure cases while tuning the parser.
