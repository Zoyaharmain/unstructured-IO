# Subschema fallback and stale server diagnosis

The user supplied production diagnostic reference
78a8f647534247b38464114d1957cf67, category subschema_validation. Its code/path
were deliberately removed by client_diagnostic in production. No matching
persisted server record was found. The exact request body/provider output is
not available; the following reproduction is a confirmed mapper bug, not a
claim to have reconstructed that live response.

## Reproduced mapper bug

repair_literal_citation removed redundant missing statuses for populated fields
but did not append a repair entry. map_with_field_review only revalidates when
a repair is reported. A candidate with a fully source-backed company AND
missing.company=not_stated therefore failed missing_source_status, was cleaned
internally, and still fell back without validating the corrected result.

Before patch, the new test
`test_redundant_missing_status_for_source_backed_field_is_revalidated` failed:
field_review.status was failed instead of complete. After patch it passes,
using a mocked provider and recovery_attempts=0 (one mocked response, no paid
call). The fix reports redundant_missing_status_removed and executes full
validation before commit. Cleanup is limited to known populated fields with
not_stated; unknown missing keys and unsupported employers still fail.

## Other fixes

- Production diagnostics now include fixed error code, registry field and safe
  static validation message. Raw provider text, resume text, paths, exception
  inputs and evidence analysis remain omitted in production.
- missing_source_status message now accurately describes mismatched empty-field
  declarations, including both missing and redundant declarations.
- Retry context/budget checks set stage=request_budget before checking limits,
  preventing a budget failure from being mislabeled internal_error.
- Development launcher watches local_api Python files, keeping schema edits
  from silently leaving an older schema loaded. Verified reload in server logs.

Historical logs showed scalar_multiple_values(language), while the current
registry already supports multiple languages. The separately started server
on port 8012 was checked directly and DID already serve that corrected registry;
the historical error is not asserted to explain the user's current reference.
That server had been launched without --development, explaining the opaque
reference-only UI diagnostic. It was restarted with development diagnostics
and automatic reload. No other application ports were restarted.

## Tests

Added regressions cover multiple literal languages against the current registry,
launcher reload options, retry budget categorization, redundant missing status
revalidation, unknown missing-key rejection and unsupported-company rejection.
Updated production diagnostic assertions test safe actionable reasons without
private exception/provider content.

Focused final suite: 92 passed. API suite: 4 passed. No paid calls.
JavaScript syntax and git diff --check passed.

Live smoke verification with a synthetic request (review_fields=false):
- GET subschema-definition returns languages.language multiple=true.
- Invalid query returns 422 with category, code and path in development.
- No provider calls were made.

The first broad run overlapped an edit to the production diagnostic test and
collected the old reference-only assertion: 561 passed, 1 obsolete assertion
failed. Updated targeted tests pass; a clean final full run was started after
all code/assertion edits to verify one consistent version.

Clean final verification: 565 tests passed in 107.77 seconds. The current app
is running at http://localhost:8012 with reload and detailed diagnostics enabled.
No paid provider calls were made during this work.
