# Professional highlights and DOCX preview repair

Input: _Jagat Khulbe.docx. All extraction/mapping checks were offline; provider calls: zero. Original input and prior changes are preserved.

## Causes

- `resume_structure.EXTRA_HEADINGS` treats Professional Highlights as summary. `resume_sections.detect` previously trusted that heading without checking whether its following content was explicit employment history.
- `record_subfields.DATE` did not accept apostrophe-separated short years such as Oct’21. These date-first employment headers therefore failed role/employer parsing and did not establish experience context.
- The date-first header parser also needs to distinguish a top-level `as` separating company/title from `as` inside a parenthetical former company name.
- The browser renderer cannot reliably expose floating text-box content. In this file four text boxes use Word alternate shape representations. A private preview transformation now materializes their paragraphs/tables in reading order and selects one representation. The original downloadable DOCX is unchanged. Fixed table heights no longer clip preview content.

## Changes

- `record_subfields`: accept straight/curly apostrophe year separators; parse date-first `company as role` headers using only top-level delimiters, preserving literal source values. Recognize Head as a role term. Client/unsupported prose remains excluded.
- `resume_sections`: inspect bounded following content under a summary-like heading. Explicit date-range employer/title headers establish experience instead; intervening explicit headings stop the search. Profile prose remains summary.
- `docx-frame.js`: prepare a private ZIP/XML copy for browser display, choosing one alternate representation and exposing text-box content, including nested content. No external renderer/upload required.
- `docx-preview.html`: avoid fixed cell-height clipping in the browser preview.
- `test_highlight_history.py`: seven generic tests for year forms, company parentheses, unsupported/client content, and content-dependent highlights routing.

## Verification

- Before: 56 summary blocks; most dated employment history under summary. After: 59 experience blocks grouped into nine provisional entries; zero work-history blocks at/after Professional Highlights remain in summary.
- Correctly separated examples include Tecnomic Systems / Global Delivery Head and company names with `Formerly known as` parentheticals. These checks are not a full field-accuracy certification.
- Original source interval/schema checks pass in the offline CLI final output (`final/`). Before, intermediate after, and final outputs are preserved separately.
- Headless Chrome successfully renders this actual DOCX. All 141 original leaf paragraphs are present after whitespace-only comparison; zero missing. Text-box container paragraphs are excluded from the count to avoid counting nested content twice. This establishes text presence, not pixel-perfect Microsoft Word layout.
- Affected offline tests: 84 passed in 14.13 seconds. JS syntax and diff whitespace checks pass. No paid calls.

## Remaining limits

The document's own-venture description does not name an unambiguous employer/title pair. Its provisional record remains reviewable rather than inventing a company. Some other fields and associations remain unresolved; the result is still needs_review. No blanket promise of correctness across all resume layouts is implied.
