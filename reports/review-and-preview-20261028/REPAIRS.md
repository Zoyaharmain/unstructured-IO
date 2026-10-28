# Review failure visibility and narrow DOCX preview

## Confirmed fixes

- The original preview rendered a Word page wider than the left-hand panel. Width constraints on the iframe did not constrain Word's page. Preview now preserves page dimensions, scales each page to available panel width, and recalculates on resize. Fit width and 100% controls are available; 100% supports horizontal scrolling. Text-box preparation and original-file download behavior are preserved.
- Chunk section review rejected an otherwise supported response envelope containing `type: json_object`; whole-document `inspect_assignments` accepts that same envelope. Both paths now use the same allowance. Unknown properties, unknown/context IDs, missing coverage, invalid offsets and unsupported word cuts remain rejected. Two regressions cover the compatible envelope and continued rejection of foreign/missing targets.
- Failed section review now exposes its error code, chunk check and bounded validation issue types/span IDs in the UI. Server logs contain bounded structural diagnostics rather than resume text or provider prose.
- Invalid company citations now include sanitized value/quote lengths, evidence IDs, and whether the unchanged value occurs in the record. Exact quote and ownership validation is unchanged. This helps distinguish record-local literal values with bad references from unsupported values.

## Evidence and limits

The screenshot shows Step 2 `invalid_assignments`. The diagnostic pasted afterward is a distinct Step 3 error: `invalid_or_cross_record_quote`, company, `/section_schemas/0/records/2/attributes/0/items/0/evidence`, reference df44d48366134bc8b5a77b3b092db0b9. That diagnostic does not identify the provider's actual quote or source ID. No captured provider response for this live run was available, and no paid calls were made. The envelope inconsistency is a reproduced implementation bug; it is not established as the exact cause of this live failure. An unsupported company citation must continue to fail validation or use explicitly reviewed fallback.

Headless Chrome verification with Jitendra Sagar.docx: viewport 600px, page left 16px, right 569px, 18,048 rendered characters; 100% view horizontally scrollable. Browser testing used an isolated loopback harness, now stopped. This checks width/readability, not pixel-perfect Microsoft Word fidelity.

Initial affected test run: 81 passed. Final expanded diagnostic/section/schema/UI run results are recorded in the final response. No paid calls, no source validation disabled, no original files altered.

Final expanded run: 117 passed in 10.63 seconds. JavaScript syntax and diff whitespace checks passed.
