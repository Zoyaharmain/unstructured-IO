# Skill citation failure and generalized repair

## Observed failure

The live development server returned source_evidence_validation,
invalid_or_cross_record_quote, technical_skills at
/section_schemas/3/records/0/attributes/0/items/1/evidence on both attempts.
The provider response body was not retained. Logs establish invalid evidence,
not whether the specific issue was quote text or source ID.

## Cause in recovery logic

The previous repair_literal_citation repaired only the first failed item and
refused stale/foreign citation IDs even if the unchanged literal value could
be established inside the declared record. Revalidating then failed on the
next incorrect citation, discarding the reviewed mapping atomically.

## Implementation

local_api/services/llm_schema_mapping.py:repair_literal_citation now repairs
all invalid citations using exact literal matches inside the item's declared
record source_ids. It cannot change values or record ownership. The original
strict validate_hierarchy is unchanged. Complete validation still runs before
commit. Repairs are recorded in field_review.evidence_repairs; original
failure diagnostics are retained. Unsupported values and values available
only in other records remain rejected. A later validation failure is reported
with its actual diagnostic, alongside the original error history.

local_api/static/schema.js labels recovered diagnostics as corrected and
revalidated, rather than claiming every correction required a provider retry.

## Offline verification

The saved LikithRaju.pdf was processed with --local-only. This may differ from
the uploaded copy. offline-citation-replay.schema.json is a CONTROLLED replay,
not a saved live provider response: 32 skill citations were deliberately
corrupted while preserving locally extracted values and declared ownership.
All 32 were rebuilt and the complete mapping passed validation in one mocked
provider attempt. No paid calls were made. See offline-citation-replay.json.

Regression tests cover multiple incorrect skills, stale citation IDs,
record-local quote repair, cross-record-only values, invented values, and a
later unsupported value after successful quote repair.

Final validation: full suite 540 passed in 113.51 seconds; strengthened mapping
regressions 20 passed afterward. JavaScript syntax and git diff --check passed.
Development server restarted at http://localhost:8012 with the updated backend.
The exact uploaded copy's next live provider response has not been verified.

## Follow-up: heading_as_record

The live server confirmed diagnostic 01b3ad5bff234161b1f074e7f810f940:
heading_as_record at /sections/2/records/0/source_ids on the second attempt.
messages() had supplied headings in the citable block list and in local owner
hints. parse_review() then correctly rejected heading ownership, but recovery
handled only citations, so both attempts could fall back for this condition.

messages() now supplies headings as text-only heading_context, excluding their
IDs from citable blocks and local ownership hints. repair_heading_owners()
removes an unused heading ID only if non-heading owners remain and no field
cites that heading. Heading-only records and heading-backed field values remain
invalid. Original source blocks and residual headings remain in the result.
The bounded recovery loop supports multiple heading repairs followed by literal
citation repair, with full validation after every modification and no changes
to the strict validators.

Verification: 73 focused mapping/diagnostic/saved-defect tests plus 4 API tests
passed. Coverage includes four parent categories, cited-heading rejection,
heading-only rejection, and combined heading/citation correction. No paid
calls were made. The updated development server runs on localhost:8012.
