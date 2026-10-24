# Group 02 explicit-decision validation

Decision file: `/mnt/c/Users/Gopi Gedar/Downloads/group-02-employment-v4-reviewed-2026-10-24T11-42-09.774Z.json`.

Reviewer on all six rows: **manjunath-muruga** (self-declared). Recorded review timestamp: `2026-10-24T11:42:09.774Z`. This is the reviewer name, not a change in the reviewed document: all six decisions concern **Aditya Vashisth**, parent `experience`, current record `experience-1` (Persistent Systems).

| Row | Field | Submitted decision | Explicit expected value | Validation |
|---|---|---|---|---|
| A064 | company | correct | Persistent Systems | Accepted |
| A065 | role | correct | Engineering Lead | Accepted |
| A066 | start_date | correct | Apr 2022 | Accepted |
| A067 | end_date | correct | Present | Accepted as source wording |
| A068 | duration | correct | Apr 2022 - Present | Accepted |
| A069 | location | ambiguous | null | Preserved as uncertainty; excluded from verified fields |

For each accepted row, the submitted expected value is also its exact quote in source block `e12:647:706`: `Engineering Lead | Persistent Systems | Apr 2022 - Present `. Every quoted substring occurs exactly in that block; block intervals match the immutable extraction; the field is predefined under experience; record experience-1 owns the cited block; submitted values, parent, record and evidence match the displayed tuple. Nothing was copied into ground truth merely because it was predicted.

A069 reviewer note is preserved verbatim: **“such as Unable to verify location”**. Expected values, parent and association remain null in the submitted ambiguous decision. It is not a negative label or approval of absence, and no location was inferred.

Five accepted, zero rejected, one uncertain. v5 appends only the five accepted decisions and preserves uncertainty separately at `ground_truth/field_level/v5/uncertainty/group02.json`. Earlier 12 reference fields remain unchanged, including the six Manjunath prior expectations with their original, narrower provenance. There are now 17 partial expected fields (Aditya 8; Manjunath 9), not whole-resume approvals. Eleven are explicit Group01/02 decisions, six are prior expectations. Of the 230 worksheet rows, 11 have correct decisions, one is ambiguous and 218 remain pending.

The exact source file, SHA-256, reviewer metadata, validation reasons and frozen source/prediction bindings are saved in group02-validation.json. This importer did not visually re-review the PDFs or authenticate reviewer identity. The selected original PDF bytes for both controls were found under the current corpus folder and match their reference SHA-256 hashes; source relocation does not create additional human labels.
