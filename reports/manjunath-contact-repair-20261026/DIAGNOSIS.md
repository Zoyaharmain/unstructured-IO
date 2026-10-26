# Contact and field evidence recovery

The live server recorded unsupported_value(full_name), followed by
invalid_or_cross_record_quote(email) on two attempts for the displayed run.
Another concurrent request reported unsupported_value(domain_and_functional).
The live provider bodies were not saved, so these logs establish validation
failures but cannot establish the exact incorrect literal/quote returned.

Code gaps found:

- repair_literal_citation only ran for invalid_or_cross_record_quote. It did
  not recover supported values cited to valid but irrelevant source text.
- Its exact regex could not recover source whitespace differences, even
  though the existing validator explicitly accepts normalized whitespace
  through contiguous_support.
- A singleton contact record could omit its email/link source block. Citation
  repair searched only declared owners and could never recover that source,
  even though the whole personal_information parent has one contact record.

Corrections in local_api/services/llm_schema_mapping.py:

- Recover supported source literals for unsupported_value/unsupported_number
  as well as invalid quotes, including valid quotes supporting another field.
- Singletons personal_information/summary/skills can recover omitted source
  blocks from their own parent section. Repeated job/degree owners stay fixed.
- Prompt explicitly asks singleton owners to include all non-heading blocks.
- Preserve original diagnostics and audit every owner/citation correction.

local_api/services/source_fragments.py:citations has an opt-in whitespace
matching mode; quotes remain exact source substrings. Existing strict
validation is unchanged and executes again before commit. Unknown values,
foreign-record-only values and altered source bindings still fail.

Offline reproduction uses the saved Manjunath source and sections under
reports/manual-field-review-20261024-v1/manjunath-murugan. The controlled replay
intentionally omitted contact sources and corrupted name/email citations.
It recovered name/email citations and email/link/title source ownership,
then committed a complete mapping passing full hierarchy validation.
This is a controlled regression replay, not the unsaved live provider body.
See verification.json and replay.schema.json. No paid calls were made.

Final verification: 549 tests passed in 98.14 seconds. The focused suite after
prompt/import cleanup passed 51 tests; saved-source replay was repeated and
passed full hierarchy validation. Python compilation, JavaScript syntax and
git diff --check passed. Development app restarted on localhost:8012.
