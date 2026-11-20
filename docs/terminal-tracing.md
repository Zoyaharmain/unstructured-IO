# Terminal-first pipeline diagnostics

Run from the repository root:

```bash
RESUME_LOG_LEVEL=DEBUG \
RESUME_TRACE_DIR=/tmp/resume-pipeline-traces \
.venv312/bin/python scripts/start_resume_inspector_local.py --port 8013
```

Use an available port or stop the existing server on that port first. Logs appear
in the terminal running this command. INFO prints request/stage boundaries, review
outcomes, provider calls, durations and failures. DEBUG also prints predictions,
rule evidence, record memberships, ownership differences and field provenance.
The default model and review triggers are unchanged. `RESUME_TRACE_ENABLED=false`
disables trace emission.

The browser carries `X-Resume-Run-ID` from extraction through sections and mapping.
The backend binds the ID to the exact extraction inventory; a different inventory
starts a new run. Responses expose only this correlation header, not full traces.
The same run is used by mapping, field review and the schema audit. Private files:

```
/tmp/resume-pipeline-traces/<run-id>/state.json
/tmp/resume-pipeline-traces/<run-id>/events.jsonl
```

Sequence numbers are serialized across threads/processes. Parent decision IDs
express causality for nested stages; parallel call completion order is not source
reading order. Storage failures produce terminal warnings and do not change resume
results. Keep diagnostics private. Source text, names, contact values, prompts,
credentials and raw field values are not included in these events. Field value
fingerprints and JSON pointers allow comparison without repeating personal data.
The existing judge's private detailed files remain separately configured by
`RESUME_AUDIT_LOG_DIR`; they can contain source text.

## Interpretation

- `ml_section_prediction`: heading/content candidates and unrounded similarities
  and margins before local rules. These are not probabilities.
- `section_rule_evidence`: active context, explicit heading and record-field flags.
- `ownership`: before/after section, record, assignment rule, context and review state.
- `employment_continuation_rule`: prose/header/adjacency evidence behind merges.
- `record_group`: resulting source membership and boundary rule.
- `field_mapping`: record-local source references, status, previous/current value
  fingerprint and a pointer into the mapping response.
- `llm_call_start/end/error`: existing trigger, provider/model, linked stage,
  latency, actual provider usage when supplied, and safe errors. Call signals are
  DEBUG events. The trace also shows the model tier when section routing is enabled.
- `review_outcome`: accepted/rejected counts and execution status. Transport
  success, validation success and semantic correctness are separate facts.
- `standardization`: field path, deterministic normalization rule and warning state.

Uncalibrated model scores use `not_calibrated`; deterministic evidence uses
`evidence_only`, with probability null. LLM agreement/audit completion do not
increase a probability. Legacy fixed confidence fields are unchanged and are not
used as measured probabilities by this logger.

## Optional offline calibration

No calibration artifact is trained or enabled by default. Human-verified JSONL
rows must identify `document_group`, `task` (`section_content` or
`section_heading`), raw winning `score` (margin), `correct` (0/1), and
`label_source: "human_verified"`. Group duplicate/edited resumes together and
independently verify the frozen classifier has not trained on evaluation data.

```bash
.venv312/bin/python scripts/evaluate_confidence_calibration.py \
  --data /path/to/human-labels.jsonl --output /tmp/calibration-evaluation \
  --task section_content --method platt \
  --model-revision YOUR_MODEL_REVISION --anchor-sha256 YOUR_ANCHOR_HASH
```

This produces a grouped held-out evaluation, reliability diagram and JSON artifact.
Isotonic regression is also supported. Small datasets do not establish reliable
calibration; review counts, provenance and held-out metrics before use. Judge
findings are rejected as label provenance. `RESUME_CALIBRATION_FILE` optionally
loads one reviewed artifact, or `RESUME_CALIBRATION_DIR` loads
`section_content.json` and `section_heading.json`. Task/model/anchor mismatches
leave probability null. These probabilities describe **the ML candidate's
correctness**, never a different rule/LLM-selected category. They annotate logs
unless optional section-review model routing is configured.

## Section assignments and model tiers

Stage 2 prints a block ID followed by Input, Assigned to, Why, and Confidence.
`RESUME_LOG_VALUES=true` enables short text previews in the terminal formatter.
Those previews are excluded from the JSONL event files. Capturing the terminal
output records the previews, so keep that capture private.

Set `DEEPSEEK_CHEAP_MODEL`, `DEEPSEEK_HIGHER_MODEL`, and
`DEEPSEEK_STRONGEST_MODEL` to model IDs available on the same provider endpoint.
With matching calibration, each existing section review call uses the lowest
candidate correctness estimate across eligible model-predicted targets in that
call. At 80% or above it uses the cheap tier. From 50% up to 80% it uses the higher
tier. Below 50% it uses the strongest tier. Missing tier configuration or missing
calibration uses the configured default model and logs why. Deterministic
assignments are excluded from the confidence calculation. This changes model
selection for existing section review calls. Field mapping and the read-only
judge keep their configured model.

## Console format

The default terminal view shows color-coded levels on a TTY, a short run ID,
and separate Input and Output lines for each event. Use
`RESUME_LOG_FORMAT=json` for one raw event per line, `RESUME_LOG_COLOR=always`
to force color in a captured terminal, or `NO_COLOR=1` for plain text.
The private JSONL files always retain the full event structure.
For model calls, the terminal shows the existing trigger and configured model.
The judge verdict reports audit coverage and findings, independently of the
local model's confidence estimate.

For a walkthrough, set `RESUME_LOG_VIEW=summary`. It keeps the seven Input,
Output and Method summaries, provider calls, model selection, judge outcomes,
and warnings and errors. The detailed view and private JSONL remain available.
Punctuation-only Stage 2 spans are omitted from the readable console. Original
source offsets and stored trace events are preserved. Rule-based assignments
say that no model probability was used.

## Verification, judge and run totals

The reference workflow's seven stages are extraction, section classification,
record grouping, source ownership recovery, schema mapping, evidence validation
and JSON export. Extraction uses the existing document parsers and OCR.
Stage 2 uses deterministic heading/context rules and Sentence-BERT/K-means
predictions. Section and structural review, field review, and the separate
schema audit use the existing DeepSeek transport. The schema audit is read-only.

Optional calibrated section consensus uses the same source inventory, retry
limits and request budget as section review. Set all three tier IDs, load a
matching human-labeled calibration artifact, and set
`DEEPSEEK_SECTION_CONSENSUS=true`. Thresholds are fractions in
`DEEPSEEK_HIGH_CONFIDENCE` and `DEEPSEEK_LOW_CONFIDENCE`.
A high-tier cheap verification that confirms the original placement makes no
second call. A cheap disagreement triggers an independent higher-tier review.
A medium-tier call gets one independent cheap opinion. The strongest model
handles low-confidence batches. Disputed decisions can use one classification
judge call per batch. `DEEPSEEK_SECTION_JUDGE_MODEL` overrides the strongest-tier
judge model. Accepted judge choices require an exact quote from the target and a
section supported by at least one recorded candidate. Invalid replies, budget
exhaustion or lack of support leave the disputed spans for human review.
The judge's verdict is evidence-checked, and it supplies no calibrated score.
If a second transport call fails, the pipeline does not send a judge request for
that batch. There is at most one independent call and one judge call per batch.

Normal logging uses `RESUME_LOG_LEVEL=INFO`, detailed logging uses `DEBUG` and
quiet mode uses `RESUME_LOG_VIEW=quiet`. `RESUME_LOG_VIEW=summary` includes model
and judge outcomes. Text previews remain opt-in. Log capture and JSONL are
separate, so optional console previews are never added to stored events.

The final summary counts stages, blocks for review, provider calls, reported
tokens and time spent in HTTP requests. The classification distribution is the
local assignment distribution before provider review. Cost is only an estimate
for calls with reported tokens and user-supplied rates, configured as
`DEEPSEEK_MODEL_PRICES_JSON={"model-id":{"input":1.0,"output":2.0}}`
with rates in USD per million tokens. These are example values, not price
recommendations. Unpriced calls and unreported tokens are excluded from the
estimate.

Summarize completed runs with:

```bash
.venv/bin/python scripts/summarize_resume_traces.py --trace-dir /tmp/resume-pipeline-traces
```

## Live terminal dashboard

The existing launcher opens a Rich dashboard by default. Run it in the terminal
you want to watch, then use the browser on the same port.

```bash
.venv/bin/python scripts/start_resume_inspector_local.py --port 8012
```

- Normal shows the live tracker, grouped block and record tables, field evidence,
  provider activity and final export destinations. Set `RESUME_LOG_VALUES=true`
  for bounded source, field and export previews in a private terminal.
- `RESUME_LOG_LEVEL=DEBUG` wraps detailed block previews and assignment reasons,
  adds safe exception frames, and enables optional
  `RESUME_LOG_PAYLOADS=true` capture. Provider bodies are redacted and saved under
  `private-payloads/` with owner-only file permissions. Enable only when needed.
- `RESUME_LOG_VIEW=quiet` shows stage and export milestones and failures.
- `RESUME_DASHBOARD_LIVE=false` disables cursor-based refresh for a scrollable
  capture. `RESUME_LOG_FORMAT=readable` keeps the older line view and
  `RESUME_LOG_FORMAT=json` prints the event stream.

Each run retains `execution.log` for human-readable milestones and `events.jsonl`
for structured source IDs and decisions. Text previews and private payloads stay
out of those ordinary files. The export table includes destinations that match
the existing schema path, including education and certification date aliases.
The dashboard does not decide whether a field, block, or record is valid.
