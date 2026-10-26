# Frontend and DeepSeek verification

Date: 26 October 2026 (Asia/Kolkata).

The previous saved CLI run explicitly used local-only mode. The existing private
`.env` already contained a key and enabled DeepSeek, but the frontend defaulted
to local detection. The new local launcher loads provider settings from `.env`
without executing configuration or displaying credentials.

The updated app is served at **http://localhost:8012**. The existing service on
8011 was left running. To launch the updated app again:

```bash
.venv/bin/python scripts/start_resume_inspector_local.py --port 8012
```

Dropping or choosing a PDF/DOCX now runs extraction, configured DeepSeek section
review, and source-bound schema mapping automatically. Three progress cards
show the actual stage state. Schema output includes evidence and missing,
unmapped, or ambiguous field counts. Failed review keeps local results and shows
an explicit incomplete-review message. Local-only mode remains available.

## Checks performed

- Live credential/model connection check returned `ready` for `deepseek-flash`.
- Real Chrome drag-and-drop test used the existing Jayesh PDF fixture.
- Extraction returned 55 source elements.
- One live DeepSeek request completed; 119 source spans were reviewed, with 10
  placement changes and one split span.
- Automatic schema mapping completed, displayed 63 attributes, and enabled the
  schema download. Two required fields remained missing and were shown.
- No browser JavaScript exceptions occurred.
- Switching to local mode made no provider calls and displayed local-only state.
- A simulated provider outage displayed failed review while still mapping the
  retained local sections. This test made no additional provider calls.
- Mobile layout at 390 px had no horizontal overflow.
- Focused API/review/UI tests: 78 passed. Provider environment tests: 3 passed.
- JavaScript syntax checks and `git diff --check` passed.

The completed review does not certify extraction or field accuracy. Compare
values and evidence with the original PDF. Historical CLI reports were retained.

Evidence: [live browser results](browser-result.json),
[local/failure/mobile checks](browser-modes.json),
[desktop screenshot](frontend.png),
[mobile simulated failure screenshot](mobile-simulated-failure.png).
