# Shared provider recovery review

## Confirmed root cause

The live diagnostic `327efd9125bd485ba72f36a19367157a` reported a generic
response-model KeyError after an evidence validation failure. Compact response
expansion can reject a value before the legacy `sections` payload exists.
The recovery loop then attempted legacy citation repair on an empty dictionary.
This hid the useful source-evidence diagnostic and could discard validated
results from earlier batches.

## Changes

- `local_api/services/llm_schema_mapping.py`: only run legacy repair on a legacy
  sections envelope. Failed compact batches retain the original diagnostic;
  successful batches remain available. Compact literal matching permits layout
  whitespace differences, returns original source quotes, and retains ownership
  and full hierarchy validation.
- `local_api/services/review_chunking.py` and `llm_section_review.py`: retain
  sanitized invalid-JSON, invalid-envelope and unknown-target diagnostics from
  chunked section review. Failed section reviews remain atomic.
- `tests/test_compact_field_review.py` and `tests/test_review_chunking.py`:
  regression coverage for the crash, whitespace matching, successful batch
  retention, unsupported evidence rejection and structured section failures.

No filename-specific conditions or evidence-validation bypasses were added.
Existing workspace changes and fixtures were preserved.

## General handoff inspected

Field review already performs section preflight for unresolved meaningful source
when prior section review has not completed. It supplies full section blocks,
record hints, uncited-content targets and overlap targets to field mapping.
This is enabled only when provider review is configured/enabled and remains
subject to the shared request budget. An LLM can still abstain or return an
invalid answer; such content must remain visibly unresolved.

## Offline validation

270 tests passed in two groups:

1. 117 passed: compact field review, review chunking, section envelope, section
   review, batch failure repairs, multiline headers/date alignment, stated
   duration regression and existing document repair regressions.
2. 153 passed: LLM schema mapping, block completion/provider preflight,
   standardization v2/layer, standardized durations/export, year precision and
   assignment-format generalization.

Tests used mocked providers and existing offline artifacts. No new paid calls
were made. The original live provider response was unavailable, so this does not
prove that its semantic assignments are corrected or that every resume maps
accurately. The fix prevents the reproduced recovery crash and preserves useful
evidence failures instead of turning failures green.
