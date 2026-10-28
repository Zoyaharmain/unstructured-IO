# Subtitle and paragraph continuation repair

Offline reproduction used Anita Das.pdf, strategy fast. No provider calls were made.

The extracted source was intact. A single summary paragraph had been split into units with different layout lanes; only the first units received summary placement. Twelve source fragments remained in needs_review, including the expertise subtitle. The contact helper also chose two words from the professional headline as the candidate name, causing the headline to be truncated.

Changes:
- Recover contiguous unassigned tails only within a uniquely assigned source paragraph. Summary continuations remain summary. Pipe-separated opening expertise continuations become skills. Mixed ownership, gaps, headings, and repeated-record sections remain excluded.
- Prefer a unique standalone opening identity fragment over a name guessed from a professional headline.
- Preserve literal unlabelled achievement statements in the existing awards name field when the section is already routed to awards. Issuer and date are not invented. This does not indiscriminately move employment-specific accomplishments.
- Clarify that residual source excerpts include headings and text not fully covered by field citations. They are not a count of wholly unmapped blocks; evidence is retained.

Before: 12 unassigned fragments; incorrect candidate name; truncated headline.
After: 0 unassigned fragments; opening identity and full headline retained. Exact source interval validation passes. Original source IDs, text, and offsets are preserved. Before and after artifacts are alongside this report.

Four portable anonymized regression tests cover source preservation, mixed-owner rejection, identity/headline separation, and achievement statements without invented issuer/date. Additional validation results are reported in the final response.

This fixes the reproduced failures, not a universal accuracy guarantee. Ambiguous source ownership still requires review. No new paid LLM evaluation has been performed.

Verification: the broad offline run completed 649 passing tests, with 8 slow direct PDF/OCR parity cases excluded. Its one failure was an existing expectation that an unlabelled explicit award name must stay empty; that expectation was updated to assert the literal name and exact citation while keeping issuer/date empty. The affected subschema and new regression tests were rerun together with the benchmark repair tests. JavaScript syntax and diff whitespace checks pass. The excluded OCR parity cases are not claimed as verified in this repair.
Affected-test rerun: 36 passed in 6.45 seconds. No remaining failure in that rerun.
