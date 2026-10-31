# Split employment header association

The supplied pattern reproduced two failures: an employer/location line without a role was not recognized by single-line header grammar, and the subsequent date row began a separate record. In multi-job layouts, a date-led entry could also absorb the following role and employer before the next date row.

Changes:

- `local_api/services/dated_record_headers.py::split_employment_headers` recognizes a compact source-local role/employer header followed by a complete date range, allowing intervening explicitly labelled client rows. It supports either role/employer order and newline-containing elements. Unknown employer and location names do not require additions to the fixed city or company lists. Location recognition uses the bounded header context and a compact proper-name shape; department/practice suffixes remain conservative. This is a heuristic, not universal geographic verification.
- `recover_split_employment_headers` partitions existing entries at strongly established header starts, then joins header and date fragments. It preserves duties with their source owner and rejects cross-column/page or nonadjacent associations. Original source text is unchanged and source validation runs after recovery.
- `dated_header_candidates` makes the complete multiline identity available to both deterministic mapping and the existing source-backed LLM field repair. `record_subfields.py::refine_record` applies this complete header after provisional single-line guesses so a multiline role is not contaminated with employer words.
- `local_completion.py` runs this recovery before employment prose continuation repair. No extra model calls or external services were introduced.

The restarted local API maps the supplied header to Concentrix / Data Analyst / Visakhapatnam, April–November 2017, seven elapsed months. The example uses the complete 2017 end date already present in the reported JSON; a genuinely missing year is not fabricated. `Client: Uber International` remains in source evidence and is not substituted for the employer. The API replay adds one synthetic responsibility solely to verify ownership; it is not a full original-resume replay. See `corrected-consumer.json` and `source-mapping.json`.

Regression cases cover arbitrary employer/place names, reversed order, one multiline source element, two jobs and their duties, client-only headers, prose/department rejection, cross-column rejection, immutable extraction, repeated mapping, source validation, elapsed duration and mocked review omission.

Validation: 876 passed, 2 skipped, 15 deselected in 60.42 seconds for the unit/mock-provider/API-integration/local-model selection. Two existing Node frontend checks were excluded. `git diff --check` passed. No candidate content was sent to an external model.
