# General resume standardization verification — 30 October 2026

Implemented consumer schema version 2, preserving the original source-bound mapping
contract for the inspector. No candidate-specific production corrections were added.

## Changes and the stage responsible

| Issue | Stage | Result |
| --- | --- | --- |
| Redundant ISO/year fields and inconsistent missing values | Consumer projection | One date field per meaning; YYYY / YYYY-MM / YYYY-MM-DD or null; stable empty arrays |
| Unsupported source fields disappearing | Input preparation | Original path/value retained in additional sections; malformed types flagged rather than split/coerced into invented records |
| Awards/publications/other categories absent from consumer data | Mapping-to-standardization adapter | Existing validated structured sections promoted into fixed supplemental records |
| Partial evidence quote treated as complete content coverage | Both local and reviewed hierarchy builders, projection | Only the actual mapped value consumes content; unassigned text remains visible |
| Preferences treated as residential location | Contact field refinement and normalization | Explicit work preferences separate from residence; conflicting/ambiguous associations reviewed |
| Target role treated as current title | Field registry, title mapping and provider instructions | Target role retained separately; target-role wording excluded from current-title guessing |
| Missing certificate expiry/credential/verification fields | Source contract and explicit labels | Added fields and date/URL normalization, without inferring absent values |
| Project dates, organization, outcomes or engagement types lacking slots | Source contract and explicit labels | Added source-bound slots; unknown details retained |
| Phone extension incorporated into international number | Contact normalization | Extension separated before digit formatting; country code never guessed |
| Malformed URL creation | Shared URL normalization | Parse HTTP(S) destination, reject invalid/unsupported links, preserve original evidence |
| Ambiguous skill expansion and version loss | Skill standardization | Preserve ALM / teams / apache / python3; no technology alias rules in domain or soft-skill lists |
| Proper-name spelling suggestions and repeated warnings after correction | Suggestion stage | Dedicated proper-name fields excluded; scan standardized prose only |
| Date inference and inconsistent experience calculations | Date stage | No invented century; elapsed months; exact-day intervals; overlap union; source-stated duration separate |
| Discrepancies leaving downstream usability true | Validation finalization | Consistent review/usable flags, discrepancy findings and exact returned issue counts |
| Incomplete normalization audit | Change accounting | Before/after collection logs; applied log counts separate from unapplied suggestions |
| Source audit borrowing another unmapped record's text | Audit planning | Preserve provisional source ownership boundaries without inventing employment records |
| Provider fallback status overwritten by route | Mapping API | Retain fallback status and its diagnostic |
| Large mandatory consumer metadata and browser/server projection drift | Export/API/browser | Small default consumer envelope; optional audit; browser forwards server projection |
| Re-standardizing consumer JSON changes current status/details | Input and supplemental normalization | Canonical date aliases, explicit current flag, stated duration and detail round trips preserved |
| Arbitrary original `raw_*` detail keys stripped | Consumer projection | Remove only internal record fields; preserve original custom detail keys |

Full contract and migration details: [RESUME_STANDARDIZATION_V2.md](../../docs/RESUME_STANDARDIZATION_V2.md).

## Automated verification

- **719 passed, 2 skipped, 44 deselected** in the offline unit, mocked-provider and
  API integration selection. The two diagnostic tests requiring Node were excluded
  from pytest because Node is unavailable, and their actual JavaScript assertion
  scripts were separately executed successfully using V8. The consumer projection
  forwarding function was also checked in V8.
- The selection excludes live provider calls, local model and heavy extraction
  tiers; it is not a claim that every installed OCR/model path was exercised.
- Health, discoverable consumer schema, direct standardization and full mapping
  endpoints passed smoke checks on the restarted local server.
- Final consumer projections were rechecked against all ten consolidated audit
  outputs after the last production changes.
- `git diff --check` passed.

## Ten-resume replay and before/after comparison

Inputs: `reports/resume-batch-repairs-20261027/final-local`, comprising **six DOCX
and four PDF saved extraction/section artifacts**. Provider/network calls: **zero**.
All source bindings were validated, and saved inputs were hash-checked unchanged.

| Check | Result |
| --- | --- |
| Source-bound replays | 10/10 passed |
| New identity/responsibility changes against a replay of the prior code | 0 documents |
| Differences against older historical saved mappings | 6 documents; all also occur on the prior-code replay |
| Structured award entries in candidate JSON | Previously 0; now 2 |
| Visible additional content fragments | 466 retained in candidate data, with source IDs where available |
| Independent original-document checks | 3 matching-hash original PDFs available |
| Literal values checked against those originals | 205 |
| Literal values not confirmed by independent text comparison | 4; retained as unresolved findings, not silently changed |
| Resumes requiring review | 10/10 |

The four independently unconfirmed values are project descriptions 13/14 and
certification names 0/1 in Abdul Shukoor's saved mapping. Literal comparison does
not establish whether these are OCR, reading-order or association errors; independent
source review is still required. See `results.json` for paths, and the corresponding
numbered audit output for evidence.

## Remaining limitations

Seven original documents were not available with matching hashes in the repository;
those checks use saved extraction and source bindings. This run did not perform
fresh PDF/DOCX extraction, OCR or visual layout review. It does not certify complete
semantic recall against all original pages.

The general pipeline now retains unresolved material instead of silently hiding it.
It does not force every fragment into an employment/project/certificate field.
Complex employment vs project associations, unlabelled credential details,
mis-segmented responsibilities and extraction damage remain reviewable source
issues. All ten replayed resumes correctly remain marked for human review rather
than being described as fully verified.

## Artifacts

- `summary.json`: aggregate replay results.
- `results.json`: per-document before/after and independent source checks.
- `01.audit.json` through `10.audit.json`: consumer output plus optional full audit.
- `final-checks.json`: final test/runtime verification and projection rechecks.
- `scripts/audit_standardization_v2.py`: reusable offline replay tool.

Open the restarted application at http://localhost:8080 and regenerate JSON to use
version 2. Existing downloads remain unchanged. The audit-download checkbox controls
whether the downloaded file includes processing evidence.
