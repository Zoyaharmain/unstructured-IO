# Professional headline ownership

The source headline inherited sidebar skills context and could subsequently be accepted as a role-only employment record. The recovery now uses source position, heading boundaries, typography, adjacent career-summary prose and absence of employment date/employer evidence. No candidate names or exact headline strings are used in production rules.

`local_api/services/professional_headline.py::recover_professional_headline` moves a uniquely supported introductory headline into personal information and its career prose into summary. `local_completion.py` runs this before mapping. `llm_schema_mapping.py::recover_literal_contacts` restores the exact source-backed professional title if field review omits it. Source text, spans and validation remain intact; ambiguous candidates are unchanged.

The actual DOCX replay and restarted localhost API produced the full professional title, four genuine jobs, three education records and three projects. Existing profile URLs, skill union and URL-repair warnings passed checks. The local schema request took 0.544 seconds with field review disabled; this is not an external-provider latency measurement. No candidate data was sent to an external model during verification.

Regression cases cover sidebar context, misclassified introductory headlines, genuine undated employment roles, neighboring employment dates, and mocked review omission. See `tests/test_professional_headline.py`. Corrected export: `corrected-consumer.json`. Live checks: `live-check.json`.

Validation: 856 passed, 2 skipped, 15 deselected in 57.24 seconds for the unit/mock-provider/API-integration/local-model selection. Two pre-existing Node frontend checks were excluded; no frontend files changed for this fix. `git diff --check` passed.
