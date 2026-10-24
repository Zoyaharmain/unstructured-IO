# Ten-resume evaluation preparation

Completed offline audit and Group 02 import; awaiting user confirmation before paid execution.

- Group 02 reviewer: `manjunath-muruga`; five accepted employment field decisions, one uncertain location, zero rejected. v5 has 17 partial expected fields and retains old provenance.
- Ten originals frozen and hash-verified: two intentional development controls and eight documents excluded from inspected prior LLM selections by filename/hash.
- All ten saved baselines pass structural evidence checks. New end-to-end results and semantic metrics are pending.
- 410 full tests, 168 overlapping focused tests, four new checks passed; no failures/skips in completed runs. Sandbox TestClient hangs were diagnosed and reruns completed outside the sandbox with provider keys removed and external connections blocked.
- Preserved 15,775 existing files; production mapping unchanged; API requests: zero.

Read architecture-audit.md, group02-validation.md, selection-review.md, regression-tests.txt, limitations-and-defects.md and final-readiness-assessment.md. Proposed provider: deepseek-flash; section review plus advisory schema audit; expected 20 first-pass requests, maximum 40 with one recovery pass. No cross-candidate search implementation found; field mapping is local.

NO-GO for production scaling. Await confirmation for only the frozen ten-document diagnostic command in execution-command.txt.
