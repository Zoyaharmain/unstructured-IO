# Competencies, profile links, and repeated-employer records

All changes use source structure and field semantics, without candidate/file-specific rules. No paid provider calls were made.

## Verified behavior

- Different roles and periods at one employer stay separate experience records. A one-line entry is legitimate; it need not have a responsibility list. Responsibilities from the more detailed entry are not copied. An anonymized regression asserts exact ownership for a detailed role followed by a one-line role at the same employer.
- The preserved Jagat output has two Blackbox roles: Mar’10–Dec’18 / Service Delivery Manager – Key Accounts, and Jan’19–Sept’20 / Manager –Technical Consulting. No company-name deduplication merges them.
- Jitendra Sagar DOCX: all source elements 7–12 (core competencies, business analysis competencies, technical skills, and their tables) route to skills. Final output contains 122 literal all_skills items. This count is not an overall accuracy metric.
- The heading matcher now recognizes short competency headings independent of their domain modifier. It treats Business Analysis Competencies as a heading rather than a skill value.
- The skill parser previously discarded literal competency phrases over eight words. The bounded limit is now thirty words, with existing source and responsibility checks retained. The arrow bullet is handled as list formatting. Separate physical rows are not concatenated into new skills.
- The vendor contact helper truncates GitHub handles containing section words such as skills/projects/education. A local source-bound profile parser now preserves the complete literal handle, rejects repository paths as candidate profiles, and does not choose among conflicting profile links. Header profile fragments can be recovered from summary/skills or unassigned blocks before employment/reference content.

## Source check for the requested resume

No XML or relationship part in Jitendra Sagar.docx contains GitHub. The final GitHub field remains empty; no address is invented. This document therefore verifies competency handling but cannot reproduce a missing existing GitHub target. Hidden-link-only targets in other documents were not established by this example and are not claimed as verified.

## Verification

139 affected offline tests passed in 16.59 seconds, including ten new generic regressions. The local CLI final source/schema checks pass. Python compilation and diff whitespace checks pass. Original files and previous fixes are preserved.

Before/final artifact directories contain private source-derived data. The before directory was generated after the initial generic length/profile repairs and before the competency-heading change; it is not an untouched historical baseline. The decrease from 123 to 122 skill items removes the heading from the values list.

This does not certify every field across every layout. Unknown fields and uncertain associations remain reviewable instead of being guessed.
