# Arnab PDF schema-assignment investigation

Source: the requested Downloads/Arnab_KumarKar.pdf. The exact input hash and before/after counts are in comparison.json. All processing and verification were local or used injected mocked provider responses. No paid DeepSeek calls.

## Reproduced failures and causes

- `record_subfields.employment_header_fields` split role/organization headings at both pipes and dashes. A heading such as `Business Analyst | Employer — Client` became three components, and the two organization components were rejected. The first job disappeared after identity pruning; another job had no company. The fix preserves the complete organization compound as one literal component. It does not invent an employer/client split.
- `education_subfields.refine_education` treated an acronym plus its full expansion, separated by an en dash, as two qualifications. Both degree fields were discarded. Matching expansions now recognize parentheses or dash syntax and dotted degree abbreviations. A genuinely different second degree still remains ambiguous.
- Institution matching expected a narrow name ending, rejecting an institute with a parenthesized acronym and campus/city suffix. Record-local literal institution names with these shapes are now retained; names are not synthesized.
- Letter-spaced multiword headings were collapsed without spaces but not matched to their ordinary aliases. Additional Information therefore became a third education record. Compact alias lookup and the explicit additional-information heading now establish a context boundary.
- `certification_integrity.detail_row` did not recognize status-only Active rows. These became certificate names. Status words are now detail content. Repeated identical statuses also lacked unique pdf_source_lines hints; original element bounding boxes now provide row alignment when the short source element has its own geometry, with same-page and right-side alignment constraints.
- A certified-in-collaboration issuer phrase after a pipe became another certification. It now stays with the title. A separate literal year on the source row is also retained. Issuer phrases are preserved literally rather than shortened to a guessed issuing organization.

## Measured behavior

| Local output | Before | Running API after |
|---|---:|---:|
| Experience records | 3 | 4 |
| Jobs with empty company | 1 | 0 |
| Education records | 3 | 2 |
| Certificate-card records | 11 | 6 |
| Certificate names equal Active or empty | 4 | 0 |

The original independently inspected work history has four entries. The two education rows map to MBA / IIM Kozhikode / 2022 and B.Tech / Gandhi Engineering College / 2015. Expanded degree names are not invented as subjects; unknown subjects remain empty. The master’s-program card retains 2025.

These are record/field recovery measurements, not a complete semantic accuracy score. An unlabelled organization compound remains literal and explicitly requires employer/client association review. A nested course-module list and a shared/combined certificate listing remain source-visible; six cards must not be read as six independently verified earned credentials. Certificate status text remains attached to the source card; no unsupported status schema field was introduced.

## Verification

- Before and after extraction element-text inventories are identical.
- Final source-interval and hierarchy/quote validation passes.
- Actual localhost:8012 API exercised with `/sections/local` and `/schema` using `review_fields:false`: four jobs, two education records, six provisional credential cards, zero Active/empty certificate names, zero provider calls. Artifacts: live-local-sections.json, live-local-schema.json, runtime-check.json.
- Mocked field-review round trip preserves four jobs and passes full schema validation: after/mock-reviewed-schema.json. This does not establish what a fresh live provider response will return.
- 208 affected offline regressions passed in 47.85 seconds. Eight new generic cases cover role/organization compounds, acronym expansions, institution syntax, status metadata, repeated-status geometry, source year retention, and letter-spaced headings. Existing foreign/cross-record evidence and boundary checks remain enforced.
- Changed modules compile and diff whitespace checks pass. No candidate or filename-specific branches, no original-text rewriting, no weakened citation validation.

The original fifty-resume run is unchanged. This investigation uses a fresh local baseline for the exact Downloads PDF, rather than presenting old benchmark results as new model output.
