# Recovered validation shown as an active error

The user reported diagnostic f9f2263595824fda9f257d5799b972e4:
missing_source_status at /sections/0/records/1/missing, displayed beneath
“Earlier validation issue — corrected and revalidated.” The running server log
confirms the reference. This heading is rendered only for recovered=true;
map_with_field_review marks history recovered after the final candidate has
passed source/schema validation and committed successfully. The logged warning
precedes recovery and is not itself proof of a final failed result.

## UI bug and correction

schema-status.js previously selected the last history entry as diagnostic even
when recovered=true. schema.js appended that old error to the workflow card
and opened its details, making successful recovery look like an active error.

schemaOutcome now separates unresolved diagnostics from recoveredDiagnostics.
Resolved checks remain available in collapsed “Resolved validation check
(history)” details and the downloaded JSON. Active failures remain expanded.
Recovered checks no longer appear as the current failure reason. A successful
mapping with no pending findings remains success/green. If review is genuinely
needed, the card now describes its missing, unmapped, ambiguous or omitted-item
findings instead of treating historical validation as the current cause.

The backend status also counts destructive repair codes (unsupported provider
items pruned or conflicting scalar values truncated) as requires-review. A
validated result with discarded provider values cannot silently become green.
Exact quote/status repairs alone do not create this review flag. Validation
and underlying schemas are unchanged.

## Verification

96 focused tests and 4 API tests passed (100 total). Node regressions execute
schemaOutcome and the actual renderSchemaDiagnostic function with a minimal
DOM, verifying success + recovered history, pending findings + recovered
history, unresolved failures, and collapsed/expanded details. Backend tests
cover the status distinction between exact repairs and discarded values.
JavaScript syntax checks and git diff --check passed. No paid calls were made.
The development backend automatically reloaded; the browser must reload the
updated JavaScript assets to display the change.
