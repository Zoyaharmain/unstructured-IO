# LLM review validation

Implemented one optional full-context review inside the existing section endpoint:
local grouping first, then all assigned/unassigned spans sent together for review,
then source-linked final sections. Key-only setup selects the documented
`deepseek-flash` model and standard HTTPS endpoint. No API key was supplied and no
resume text has been sent to a real DeepSeek API during these checks.

Executed combined regression suite: **108 passed, 8 deselected in 17.24s**.
The eight historical repeated extraction model-parity cases were excluded as in
prior runs. Provider tests use mocks and verify complete assigned/unassigned
coverage, correction of wrong placements, resolving unknown spans, abstention,
exact reconstruction, invalid/duplicate/missing IDs, extra fields, limits,
missing configuration, disabled review, error sanitization, JSON-mode transport,
truncation rejection, route integration and key-only model/endpoint defaults.
Evidence: `reports/llm-review-tests.txt`.

Chromium used the actual local PDF extraction flow with the section response
intercepted locally; it did not call a real LLM. It verified completed-review
counts, visible failure retaining local blocks, explicit local-only status when
disabled, retry without duplicated section cards, 390px mobile width and no page
errors. Evidence: `reports/llm-review-browser-check.json`. The test screenshot is
in the ignored private `.upstream/resume-validation/llm-status-ui.png`.

These checks validate integration and data-conservation contracts, not DeepSeek's
resume classification accuracy. A live provider check is pending the user's API
key, then a reviewed resume is still needed to judge semantic placement quality.
The backend rejects incomplete provider decisions atomically rather than claiming
partial or failed output was validated. Original PDF extraction accuracy remains
a separate concern.

The private `.env` file is ignored by Git and excluded by the Docker build
allowlist. `scripts/start_resume_inspector.sh` builds/restarts the app while
loading that file, without printing its contents. The API status endpoint reports
only enabled/configured flags and the model, never the credential.

The launcher was executed successfully. Image `0598708e11eb` is running at
`http://localhost:8011` in `resume-inspector`. The deployed configuration endpoint
reports `deepseek-flash`, disabled/not configured while the key is blank. A real
local grouping smoke request succeeded and reported LLM review disabled. No
DeepSeek request was made. Evidence: `reports/llm-review-deployment-check.json`.
The production app remains running; the temporary browser-test server was stopped.

## Live authentication diagnosis and visible errors

The user subsequently supplied a key and restarted the app. Safe diagnostics
confirmed it was loaded from `.env`, but the actual DeepSeek `GET /models` request
returned HTTP 401. No resume/prompt was sent for this check. The configured key
was neither changed nor exposed. Live document review remains blocked by provider
authentication until the user supplies a valid key.

The fix adds a no-resume connection-check endpoint and frontend button, an
automatic startup check, and actionable sanitized status messages for rejected
keys, insufficient balance, forbidden access, rate limits and provider outages.
The local section result remains visible on review failure.

**115 passed, 8 deselected in 21.99s** including credential-status mapping,
no-prompt model checks and error sanitization. Evidence:
`reports/deepseek-connection-tests.txt`. Rebuilt image `e73be265c04b` is running at
localhost:8011; the startup script now explicitly prints the HTTP 401 diagnosis.
