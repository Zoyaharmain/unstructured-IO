# Five-resume LLM test: repository investigation and preflight

No LLM or model-list API requests have been made. No old outputs, source PDFs,
production code, ground truth, or approval metadata were modified by this investigation.
This directory contains investigation artifacts, not completed five-resume test results.

## Numbered schema terminology

No explicit definition or alias for "Schema 2", "Schema 1", or "Sub-schema 1" was
found in repository code, docs, report text, the prior full350 schema and mapping
outputs, or the original handoff implementation. Searching numbered terminology
returned no matches. JSON property order is not a schema identity, so neither the
second root property nor the first attribute can be assigned those names.
No precise named parent/child mapping can therefore be established from those aliases.

## What the previous approximately 350-resume run actually tested

`reports/deepseek-schema-full350-20261022/target-schema.json` is titled
`ResumeSchema`. Its root fields are contact, professional_title, summary,
total_experience_years, skills, experience, education, certifications, projects,
and languages. Definitions include ContactInfo, CategorizedSkills, WorkExperience,
Education, Project, and Certification. There is no named Schema 2/Sub-schema 1.

`run_single_resume.py:31` defines the direct mapping prompt; lines 145-157 send
`ResumeSchema.model_json_schema()` and saved source blocks to DeepSeek. The core
response is `{data, evidence}`. `envelope_pipeline.py` validates that core and adds
missing_information, uncertainties, upstream_observations without changing data.
`schema_gate.py` validates populated leaf JSON pointers and their exact source quotes.
`resumes/001/candidate-mapping.json` demonstrates that five-key envelope. It has no
section_schemas, SubschemaRecord, or Attribute structure.

The manifest reserves 350 resumes. The call ledger records 309 attempts; summary.json
reports 300 schema-valid results, 9 quarantines, and 41 manifest entries unattempted.
Its saved schema-validity and citation-compliance rates are diagnostics, not global
field accuracy. `score.py:26` scores selected reference facts using record selectors
and token containment (year extraction for year fields), not exhaustive exact-match
precision/recall/F1. The 141 gate facts cover the old gate documents. The reference
file does not itself include human-verification metadata, which must not be invented.

## Current production hierarchy and mapping stages

```text
Original extracted elements
  -> SectionResponse.sections[] + needs_review (local detection/recovery)
  -> optional DeepSeek source-span placement review
  -> map_schema(existing elements, reviewed sections)
       -> data: ResumeSchema (legacy typed records)
       -> section_schemas[]: SectionSchema
            category: named parent section
            records[]: SubschemaRecord (record_id, source_ids)
              attributes[]: Attribute (name, status)
                items[]: AttributeValue (value, status)
                  evidence[]: SourceQuote (source_id, exact quote)
  -> optional advisory LLM audit; bounded feedback can repeat the existing pipeline
```

This is evidenced by `docs/SCHEMA_MAPPING_API.md`,
`local_api/services/schema_mapping.py:36,211`,
`local_api/services/section_subschemas.py:20`,
`local_api/schemas/subschemas.py:16,28,40,47`, and
`scripts/single_resume_pipeline.py:24,58,68`.
The mapping endpoint itself calls no provider. The production feedback runner uses
LLM placement review and an advisory schema audit; it does not use the old isolated
LLM direct mapper. Substituting that mapper would change the evaluated implementation.

The exact current named parent/child registry is:

| Parent category | Child attributes |
|---|---|
| `personal_information` | `full_name`, `email`, `phone`, `location`, `linkedin_url`, `github_url`, `portfolio_url`, `professional_title` |
| `summary` | `statements`, `total_experience_years` |
| `experience` | `company`, `role`, `start_date`, `end_date`, `duration`, `location`, `responsibilities`, `technologies` |
| `education` | `institution`, `degree`, `field_of_study`, `start_year`, `graduation_year`, `grade_or_gpa` |
| `projects` | `name`, `description`, `role`, `technologies`, `url` |
| `certifications` | `name`, `issuer`, `issue_year` |
| `skills` | `technical_skills`, `tools_and_platforms`, `domain_and_functional`, `soft_skills`, `all_skills` |
| `awards` | `name`, `issuer`, `date` |
| `publications` | `title`, `publisher`, `date`, `url` |
| `volunteering` | `organization`, `role`, `dates`, `activities` |
| `languages` | `language`, `proficiency` |
| `interests` | `interest` |
| `references` | `name`, `relationship`, `organization`, `email`, `phone`, `availability` |

`needs_review` retains unassigned source blocks and has no attribute schema.
The registry has version 1; that version does not name a "Sub-schema 1".
`personal_information` maps to legacy `data.contact`; `professional_title` is a
root field in legacy data but an attribute of personal_information in the hierarchy.
Other mappings are snapshotted in hierarchy.json. The schema endpoints are
GET /api/v1/resume/schema/definition and GET /api/v1/resume/schema/subschema-definition.

## Dataset and the meaning of previously untested

The accessible dataset is `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT`.
It has 1541 files, including 1082 PDFs.
Every current dataset filename is already present in the saved local1541 mapping
inventory. Consequently this dataset cannot supply five filenames never seen by
any previous local test. Prior local processing is not proof of a prior paid LLM test.

After excluding all prior explicit selection manifests, pilot selection files,
LLM scope files, and all 350 reserved entries, 731 PDF filenames remain
outside those saved selections. Names are compared case-insensitively and known
SHA-256 identities are excluded. This is an LLM-selection candidate pool, not proof
that every file is entirely new to all historical processing or that all candidate
semantic identities are distinct. Exactly five sample candidates were byte-hashed
below; they are NOT a final test selection. No extraction or LLM execution occurred.
All five have previously saved local mapping records; hashes indicate whether the
actual PDF bytes match that local inventory.

- `_Aashish Golhani.pdf` ? `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/_Aashish Golhani.pdf` ? SHA-256 `c261e6afe3edb029f6231fd17ab85a9a362c5e7d9af6532ed8e8925a4eaa6b3e`; already present in local inventory: True (same bytes: True).
- `_Levi Arbole.pdf` ? `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/_Levi Arbole.pdf` ? SHA-256 `328d7e1f29325c047d72038d2b6b527fbe510b30770ef3fb2ab762f67db454d9`; already present in local inventory: True (same bytes: True).
- `_ManjunathMurugan.pdf` ? `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/_ManjunathMurugan.pdf` ? SHA-256 `a0a6ce21e0843824a33c748fd29b4b64d6747311a721ae43b2812e007128351d`; already present in local inventory: True (same bytes: True).
- `_Rachana.pdf` ? `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/_Rachana.pdf` ? SHA-256 `76852c1acdbf0839ac9ca7c00c72dc24daed771d416be436ed50c1c088068cf6`; already present in local inventory: True (same bytes: True).
- `_ShaikSuhana.pdf` ? `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/resume/RESUMES_FLAT/_ShaikSuhana.pdf` ? SHA-256 `19e01c74b08dcaaaa49625b73c629125c3c7dc7e732f5cde4aa46433124c28b1`; already present in local inventory: True (same bytes: True).

## Configuration and evaluation limits

The production runner loads the root .env, not scripts/.env. Sanitized settings:
DeepSeek / `deepseek-flash`, review enabled, API key present, thinking `disabled`.
The key was not displayed or saved. No network availability was assumed or checked.
Each tested document may require placement and audit calls and bounded retries;
"five resumes" is not necessarily "five API requests". A future runner must cap
scope to the five frozen document hashes, record actual response envelopes, usage,
latency, failures and retries, and avoid retrying additional documents.

The 15 gold annotations label source-character section ownership; they are not
field-level references. Reliable human-verified field references have not been
established for any final five-document selection. Semantic scores must remain
null/unscorable until that provenance exists. Structural validity, literal evidence
presence, advisory LLM findings, and field completion must be reported separately.
No comparable field-accuracy difference from full350 can currently be calculated.
No API cost was incurred by this preflight, and no current price was assumed.

## Required resolution before the paid test

1. Establish whether the intended target is the CURRENT production hierarchical
   mapping of every named parent/attribute, or the OLD direct ResumeSchema mapping
   experiment. These are distinct workflows; neither defines the numbered aliases.
2. Establish whether "untested" means not in prior LLM mapping/review selections
   (candidate pool exists) or never in any saved local mapping (no new filenames).
3. Freeze and hash exactly five eligible inputs only after those definitions are
   established. Preserve full350 outputs; do not execute its continuation scripts.

Prior full350 file hashes are preserved in prior350-preservation.json.
