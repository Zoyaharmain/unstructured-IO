# Structural record assignment review

Reproduced from the reported PDF with `scripts/check_single_resume.py --strategy fast --local-only`. No external review or paid provider calls. Original artifacts and prior workspace edits are preserved.

## Causes and changes

- `resume_structure.project_source_groups`: chose bold rows or bullet rows as mutually exclusive boundary strategies. A portfolio/employer overview was interpreted as a project identity; numbered projects were swallowed into it. Record boundaries now combine explicit numbering, visible titles and uniquely aligned date/title rows. Overview rows stop the prior record without creating an identity. Action bullets cannot independently create project records. Source intervals are unchanged.
- `resume_structure.EXTRA_HEADINGS`: Technical Profile had no skills heading recognition, so its content inherited Summary. Added the generic heading alias.
- `contact_sections.recover_contact_sections`: contact routing only recognized contact literals. A large name in another layout column remained unassigned, allowing the vendor name heuristic to choose a country. Recovery now accepts a unique first-page name-shaped span only when its font is at least 1.5 times the first-page median, near the top of the page, excluding recognized headings and professional titles. Missing or ambiguous typography does not establish a name. Both section endpoints and direct schema mapping receive extraction geometry.
- `record_subfields.employment_header_fields`: grammatical `worked/working as … at/with …` headers were not decomposed. Literal role/employer phrases are now parsed without changing their text or inferring a location suffix. Trailing `from` before a wrapped date is excluded consistently.
- `resume_structure.reviewed_employment_groups`: a shared responsibilities section following several history-only jobs generated another job from bold task text. It cannot introduce new employers without an explicit employment header. Shared duties remain source content for LLM ownership review; no unsupported attribution to the last job.
- `llm_schema_mapping.SYSTEM`: requires independent boundary verification, distinction between portfolio context, projects and task bullets, and location/name checks. Local groups remain proposals and original source IDs remain mandatory evidence. No new API stage or provider call was added.

## Verified behavior

`before/` is the initial reproduction. `verified/sections.json` is a fresh extraction/detection after the structural changes. `verified/final-schema.json` includes the final wrapped-header refinement.

- Candidate name recovered from its original span rather than the location column.
- Four employment records; literal roles and employer phrases separated. Employer phrases retain city suffixes when no explicit boundary establishes the location separately.
- Technical Profile assigned to Skills.
- Ten numbered projects retain separate records and descriptions. Two additional titles with missing bold metadata recover through same-row dates. Portfolio overview rows no longer masquerade as projects.
- Eight new offline regression tests cover the real extraction and independent synthetic variants, action bullets, numbered identities, grammatical employment headers and source/hierarchy checks.
- Exact source coverage and hierarchy validation pass; input requests remain unchanged.

This is not a guarantee of perfect extraction from every layout. Missing qualifications, ambiguous shared duties and unsupported associations remain unresolved rather than invented. Live DeepSeek output was not invoked or verified in this review.

## Validation run

- Full offline suite: **619 passed in 113.01 seconds**.
- Final focused structural/field/earlier-resume regressions after the shared-duty guard adjustment: **29 passed**. New structural cases individually: **8 passed** (the eighth case was added after full-suite collection).
- `git diff --check` and changed Python module compilation: passed.
- Running application at port 8012: POST `/api/v1/resume/schema` with saved extraction/sections and `review_fields:false` returned HTTP 200, correct candidate name, four jobs and zero provider calls. See `verified/runtime-verification.json`. No live LLM review was requested.
