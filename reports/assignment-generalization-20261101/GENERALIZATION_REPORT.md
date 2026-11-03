# Shared format and ownership corrections

The requested Yogendra Singh.pdf was used to reproduce general format failures. No code branches use a candidate or filename. Prior Arnab changes were preserved. Original source files and prior reports were not modified. New paid/provider network calls: zero.

## Shared causes

- Employment recognition depended on familiar role vocabulary and narrow worked-as/at grammar. Explicit `working in ... post of ...` and `experience in ... postof ...` relations were not recognized, especially when the role itself was misspelled. The shared parser now uses these explicit relation labels, independent of employer names and without autocorrecting the role text. Generic skill-experience prose remains excluded.
- Full day-month-year ranges, wrapped numeric dates and repeated connectors such as `to till till now` were not consistently recognized. Source date matching now preserves the full literal date span. Only fragments belonging to the same established labelled employment record are joined for field refinement.
- A corporate suffix/date continuation could become a separate record. Adjacent same-page source continuation after an explicit post label now stays with its record. Payroll organizations are used only when the source explicitly says payroll was/is/with; an unlabelled client/employer split is not invented.
- Geometry/font heuristics overrode explicit numbered projects. Numbered project markers now establish record boundaries before layout heuristics, including descending numbers and an academic-project prefix. Description, role and environment rows stay inside their owning project. Pure project identifiers and punctuation are not descriptive names.
- A singular Educational Qualification heading was missed. It now establishes education context through the shared heading registry.
- Parenthetical institution-like abbreviations were being asserted as subjects. Those ambiguous associations are now flagged rather than mislabeled. A literal GGPA value or an unambiguous record-local percentage is retained as grade_or_gpa without inventing a grading scale.

## Exact-source verification

The independent original PDF reading shows six employment/internship statements, six numbered projects and two qualifications. Before the shared fixes, the current local output had one malformed experience record, no education records, and project names such as Description/Responsibilities. After the fixes, both the offline mapper and the running local API retain six employment/internship records, six named projects and two degree records.

The project names recovered from literal source spans are Healthcare AI, Comerica Bank TMS, HIS, Referal, Hospital Management System, and Literacy Management. Original spelling is preserved. A source-stated six-month internship is not assigned invented start/end dates.

School abbreviations remain unresolved as institution fields where the local mapper cannot establish the institution association; they are source-visible and no longer wrongly asserted as subjects. Numeric dates can still require day/month interpretation review during standardization. These remain genuine uncertainties, not a promise of complete factual accuracy.

Before and after extracted element-text inventories are identical. Final source interval and record-local quote/hierarchy validation passes. The exact original source hash and comparison are in comparison.json.

## Integration and regression checks

- Running localhost:8012 local endpoints: `/sections/local` then `/schema` with review_fields=false returns 6 jobs, 6 projects and 2 education records, provider_calls=0. Artifacts: yogendra-after/live-local-sections.json, live-local-schema.json, runtime-check.json.
- Injected offline field-review round trip retains six jobs and six projects with complete schema validation: yogendra-after/mock-reviewed-schema.json. This is not a new live DeepSeek evaluation.
- 250 affected offline tests passed in 54.35 seconds across model section detection, record parsing, project grouping, payroll/context boundaries, existing saved layouts and source validation.
- New generic tests use unrelated names, alternate grammatical prefixes, wrapped date formats, descending project numbers, separate header/title rows, and negative capability/prose examples. They verify that foreign content is not guessed into records and that ambiguous education context stays reviewable.
- Changed modules compile and diff whitespace checks pass.

## Limits

These changes improve shared format families; they do not prove correctness for every layout or every LLM response. A fresh paid section/field review was not run. Existing source inventories and field-review ownership constraints remain enforced. Before declaring general production accuracy, independent record/field ground truth and a held-out semantic evaluation are still required.
