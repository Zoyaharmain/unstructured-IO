# Logical resume grouping

Implemented an additive logical-context layer above immutable source fragments.
The grouping never selects one fragment to represent an entire job, paraphrases
source text, or collapses separate employment/education records together.

## Behavior

- Summary: one logical block containing every non-heading summary fragment.
- Contact and skills: one complete logical section block each.
- Experience: one logical block per established job entry, including company,
  role, dates and associated duties in their source order.
- Education/projects/certifications and other record sections: one logical
  block per established record. Multiple jobs or degrees remain separate.
- Meaningful unowned text and overlapping boundaries remain explicitly
  unresolved. Unowned bullet-only layout does not create a fake job card.
- All original blocks, headings, text, IDs, offsets and citation validators
  remain available. Logical IDs are context identifiers, not valid evidence.

## Integration

schemas/sections.py exposes computed logical_blocks, derived afresh on each
serialization so client-supplied/stale logical context cannot override current
source owners. services/logical_blocks.py builds source-preserving groups.
services/llm_schema_mapping.messages includes groups in field-review context,
while retaining the complete original source inventory and strict citations.

static/sections.js renders complete logical records first and collapses raw
fragment inspection. After field review changes owners, static/schema.js
refreshes the section view from meta.reviewed_sections so the UI reflects final
record boundaries. Grouping adds no provider requests and does not claim human
verification or semantic correctness for provisional record boundaries.

## Verification

Full suite: 578 passed in 114.42 seconds. A final focused suite after the
bullet-only residual fix passed 79 tests, including the additional regression.
Tests cover one summary, complete separate jobs, unresolved ownership,
overlapping boundaries, dynamic regrouping after record review, serialization,
original-source immutability and the saved Jayesh summary.

Headless Chrome rendered saved Abhilash section data without processing or
provider calls: 1 summary, 4 jobs, 2 education records, all 110 raw source
fragments retained, original-fragment inspection collapsed, zero JavaScript
errors. See browser-result.json, sections.json and logical-records.png.
JavaScript syntax and git diff --check passed. No paid calls were made.
