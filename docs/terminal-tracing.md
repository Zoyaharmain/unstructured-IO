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
Existing pipeline behavior, review triggers, provider calls and exported values
are unchanged. `RESUME_TRACE_ENABLED=false` disables trace emission.

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
  DEBUG events. No confidence routing or additional calls are introduced.
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
only; no thresholds, routing, escalation or changes to pipeline decisions occur.
