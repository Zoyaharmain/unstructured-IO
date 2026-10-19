# DeepSeek review in the existing section pipeline

The same `POST /api/v1/resume/sections` request now supports an optional second
stage: local BERT/K-means/structure grouping → bounded local boundary recovery → DeepSeek review → final blocks.
There is no separate user action or independent unassigned-text workflow. The
initial LLM request contains every assigned and unassigned source span together,
in source order, with its current category, page, lane and offsets. This gives the
reviewer the full resume context instead of reviewing isolated unknown snippets.

The reviewer can confirm placements, move incorrect ones, and assign previously
unassigned text. Unsupported or uncertain text can still remain in Needs review;
the system does not force an incorrect category to make that list empty.

## Configuration

No key means no external review. The user only needs to supply a key; the
backend defaults to `deepseek-flash` and `https://api.deepseek.com`. Setting the key
enables review automatically, unless explicitly disabled. Put this one value in
a local ignored `.env` for Docker, or set it in the server process environment:

```dotenv
DEEPSEEK_API_KEY=your-private-key
```

Adding the key and enabling the server environment sends the uploaded resume's full extracted text, including
personal/contact details, to the configured endpoint. The key stays on the
backend and is never included in the prompt, browser response, or logs. Only use
an endpoint you intend to receive the resume. The default model supports Chat Completions JSON output. Its current availability
is listed in the official [model reference](https://api-docs.deepseek.com/quick_start/pricing/).
Non-thinking mode is selected explicitly for a bounded structured classification
pass; this is not a claim that it gives the best accuracy on resumes. Optional
overrides are `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`,
`DEEPSEEK_THINKING_MODE=enabled`, and `DEEPSEEK_REVIEW_ENABLED=false`. `DEEPSEEK_BASE_URL` can include `/v1`; the adapter appends
`/chat/completions`. HTTPS is required and redirects are rejected. DeepSeek's
[JSON output guide](https://api-docs.deepseek.com/guides/json_mode/) and
[Chat Completions reference](https://api-docs.deepseek.com/api/create-chat-completion/)
describe the provider request format. No additional SDK dependency is needed.

A blank ignored `.env` has been prepared. Put your key after `DEEPSEEK_API_KEY=`
and run the launcher to build/restart the app with that file:

```bash
./scripts/start_resume_inspector.sh
```

It keeps the UI at `http://localhost:8011`. No model or URL setup is required.

For local Uvicorn, load `.env` into the process environment before launch. The
application does not automatically read `.env`. For a rebuilt Docker image, pass
`--env-file .env` when creating the container; editing the host file does not
change an already running container's environment. Do not place a real key in
`.env.example`, frontend JavaScript, a Dockerfile, or a tracked file.

`GET /api/v1/resume/review-status` returns enabled/configured flags and the model
name, never the key. Without an API key, the existing local grouping
continues and the UI explicitly identifies it as local-only.

## Strict source-preserving application

Each input span has a stable request-local ID. The model returns JSON assignment
pairs only, for example `{"assignments":[["u0","experience"],["u1","education"]]}`.
Mixed spans can instead use four-item decisions, such as `["u0","skills",0,10]`,
with Unicode character offsets relative to that span. Every character must be covered
exactly once, with no gaps or overlaps. No returned resume prose is accepted.
The backend requires a complete decision for every ID and only the existing
canonical categories or `needs_review`.
Unknown/duplicate/missing IDs, unsupported categories, truncated output and
extra response fields reject the whole review. Splits slice the original source only.

Decisions are applied atomically using the original text and offsets. The API
then rebuilds one block per category and checks exact reconstruction of every
source element. Source words are neither rewritten nor deduplicated. All reviewed
spans, including any still unassigned, have `reviewed_by_llm:true` and their
`local_section`, `local_assignment`, and `llm_action` for inspection.

`metadata.llm_review` reports `disabled`, `not_configured`, `complete`, or `failed`,
plus reviewed/changed/resolved counts and whether the local result was retained.
Complete means all spans received structurally valid LLM decisions, not that
those decisions are proven correct. The overall section status stays provisional
or needs_review. Extraction verification remains a separate caller review flag.

Timeout, provider rejection, malformed output or document-limit failure retains
all local assigned and unassigned spans unchanged, with a visible failure status.
There is no automatic network retry or partial application within a pass. If meaningful
unassigned spans remain after a valid review, one further full-context review is
allowed (at most two provider calls). A failed follow-up retains the complete first
review and reports the recovery failure. Limits reject the entire
review rather than silently truncating input or sending only part of the resume.
The default is 600 spans and 200,000 prompt characters; operators can adjust
within explicit bounds for their model and budget. The timeout is at most 300s.
Resume text is treated as untrusted data, including any embedded instructions.

## Validation and deployment state

Provider-independent tests exercise complete review/reassignment, unresolved
abstention, invalid/partial IDs, source reconstruction, disabled/missing config,
limits, error sanitization, transport JSON mode and HTTP integration. They use a
mocked provider and never send a resume to a real LLM.

Live validation for the Aditya PDF is recorded in `reports/aditya-browser-check.json`.
Mocked-provider tests establish source preservation and error behavior, rather
than DeepSeek classification accuracy.

## Run and check

1. Put a valid DeepSeek API key in `.env` as `DEEPSEEK_API_KEY=...`.
2. Run `./scripts/start_resume_inspector.sh`. It builds/restarts the app, then
   performs a credential/model check using `GET /models` without sending a resume.
3. Look for `DeepSeek check READY`. If it says FAILED, read the specific error.
4. Open `http://localhost:8011` and refresh with Ctrl+Shift+R. Open Resume sections
   and use **Check DeepSeek connection** before uploading if desired.
5. Upload the resume and click **Extract & inspect**. Wait for the review result.
   A successful credential check is separate from a completed document review.

The connection check is also available with:

```bash
curl -s -X POST http://localhost:8011/api/v1/resume/review-connection
```

`review-status` only reports whether settings exist; it does not authenticate the
key. `review-connection` actually checks the provider without any resume/prompt.

The UI distinguishes authentication, balance, rate-limit, network and invalid-output
failures. A failed initial review keeps all local grouping intact.

## PDF boundaries and visible emphasis

PDF layout analysis includes text inside Form XObjects. Strictly contained line
matches are discarded so a short word cannot split a longer source line. An
additional local pass can recover strong concatenated section labels in unresolved
text. None of these steps rewrites extracted words.

Canonical section text highlights company headers, project titles and education
lines using source offsets. The browser builds text nodes and strong elements,
including correct Unicode offset handling; model-generated HTML is never rendered.

## Recovery accounting and pilot reconciliation

The current prompt includes every original source element, all assigned/unassigned
spans, coordinates, evidence scores and existing entry hints. Returned categories
remain strict source-offset decisions; output resume prose is never accepted.
`metadata.source_accounting` reports each exact source interval's outcome:
assigned, explicit non-content artifact, or human review. Only whitespace and
explicit page separators/page-number footers are identified automatically as
artifacts. Repeated text is preserved; it is not silently deduplicated.

`DEEPSEEK_RECOVERY_ATTEMPTS` allows 0–3 recovery attempts (default 1) beyond the first
request. Invalid/incomplete decisions may be retried with validation feedback;
unresolved meaningful content may receive another full-context review. Every
attempt is validated atomically. Provider errors are not retried automatically,
and a failed follow-up retains the preceding valid review. Completion means valid
provider decisions, while `all_meaningful_text_assigned` is reported separately.
Neither means independently verified semantic correctness.

Draft annotations now project the union of local and reviewed source boundaries,
so LLM split decisions are preserved. Disagreements remain human-review flags;
unassigned text remains needs_review instead of being fabricated as Experience.
Source-bound caches are used for new drafts; legacy caches require exact source
coverage and are marked as lacking full configuration provenance. Record fields
without source evidence remain blank, and field relationships are still proposed.
No automatic promotion to gold occurs in recovery or evaluation.

The live 15-resume results and limitations are in
[the recovery report](../reports/pilot-recovery-report.md). Replaying saved results
with `python scripts/check_pilot_recovery.py` makes no API calls. The bulk workflow
uses final candidate assignment coverage, retaining local flags separately.
