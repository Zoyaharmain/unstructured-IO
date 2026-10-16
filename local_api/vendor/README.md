`resume_semantic_blocks.py` is the semantic grouping module from the user-requested
https://github.com/Gopi088/knowledge-graph-resume repository, commit
48376b8d8a0f64d1ab59b405ded3d9f38fc9ae48, path
resume-kg-poc/backend/app/pipeline/semantic_blocks.py.

Copied unchanged to apply the requested employer/role/responsibility and
education/project grouping logic directly. No model, sample document, generated
output or extraction stack from that repository is required at runtime.
No standalone license file was present in that revision; no license is invented
here. Keep this provenance when updating the module.

The API adapter retains its own exact source-span ledger. This module's normalized
field strings and deduplication are not used as replacements for extracted text.
