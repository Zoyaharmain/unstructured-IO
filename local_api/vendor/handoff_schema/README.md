# Resume schema handoff provenance

User-provided `resume-api-handoff.zip`, reviewed 22 October 2026. See
`PROVENANCE.json` for the archive SHA256 and exact source file hashes. The three
Python files are unchanged copies of the supplied resume application's contract,
specification and service helpers. No standalone application license was supplied;
none is invented here. This bundle's Instructor MIT license applies to its
Instructor engine, which is not copied or invoked by this adapter.

The host adapter is `local_api/services/schema_mapping.py`. It consumes existing
source-bound section blocks, uses these target models and helpers, and preserves
provenance. No upstream standalone router or provider orchestration is mounted.
