# Resume schema handoff provenance

User-provided `resume-api-handoff.zip`, reviewed 22 October 2026. See
`PROVENANCE.json` for the archive SHA256 and exact source file hashes. The hashes record the original supplied contract, specification and service helpers.
The local contract in `models.py` now adds explicit work preferences, target role,
engagement type, project dates/outcomes, and certification expiry/credential fields.
The original source hashes remain in `PROVENANCE.json` for comparison. No standalone application license was supplied;
none is invented here. This bundle's Instructor MIT license applies to its
Instructor engine, which is not copied or invoked by this adapter.

The host adapter is `local_api/services/schema_mapping.py`. It consumes existing
source-bound section blocks, uses these target models and helpers, and preserves
provenance. No upstream standalone router or provider orchestration is mounted.
