# Baseline pipeline trace and reproduced causes (before new changes)

1. `text_extraction_service.extract_text`: content sniffing, installed Unstructured partitioner (PDF fast or OCR fallback), `pdf_section_layout.annotate_pdf_lines`, then `pdf_source_recovery.recover_pdf_source`. Source strings are not normalized for classification. Recovery retains upstream provenance.
2. `resume_sections.SectionEngine.units`: physical source lines, tokenizer cuts, explicit heading and recovery cuts, immutable source offsets. `layout_lanes` uses K-means. `_detect` uses Sentence-BERT/MiniLM plus seeded heading/content classifiers.
3. `section_recovery.recover_sections`: bounded local resegmentation/detection of unresolved merged text.
4. `resume_sections.build_sections` calls `resume_structure.entry_groups` (local lane/context fallback or reviewed employment/education geometry); `readable_resume.readable_groups` renders the same reviewed entry inventory.
5. `llm_section_review.source_ledger/make_messages`: every assigned/unassigned source span, full source context, geometry and local record hints. Provider only returns category assignments and offsets, NOT verified employer/degree record associations.
6. `llm_section_review.parse_decisions`: strict IDs/categories/relative character offsets/full contiguous coverage/word boundaries. Invalid review retries once; `review_sections` applies atomically, retains local output on failure and retains valid first review if semantic follow-up fails.
7. `review_resolution.document_scope/resolve_unassigned`: source-purpose classification and narrow supported declaration/heading recovery, no forced placement.
8. `source_accounting.account_source`, `assert_coverage`, `batch_check_resumes.validate_result`: source coverage, raw/meaningful counts, categories, canonical text/highlight/entry references. They do not establish PDF word fidelity or semantic truth.
9. `run_pilot50_review`: fixed scope/hash-preserving local-first then provider stages. `llm_verify_resume_batch.review_document`: saved actual provider responses and usage. `report_pilot50_review`: diagnostics and source comparison. Its relationship flags are heuristics; repeated degree expansions may be false positives.

## Confirmed provider causes

See baseline-failure-analysis.json and the immutable provider responses in the prior run.

- JEWEL BIJOY: first response includes u25[17:24] for 22 chars; both responses split joined PDF text without an accepted physical boundary. Raw extraction flattened Work Experiences/Developer, email/Skills/Education, degree and institution headers. Existing ordinary-word rejection cannot distinguish these source-supported joins.
- Keerthi: first response omits u19; second switches from [id,category,start,end] to [id,start,end,category]. Prior generic repair feedback lacks tuple-shape/category/boundary diagnostics. Scanned OCR has visible word errors independently of review schema.
- Pradyum Raj: both responses cut inside CERTIFICATION (offsets 13 and 19) in a combined heading. No permitted cut inventory is supplied to the provider.
- SHAIK RUSUM: first response uses absolute source-element offsets against local spans; second returns a zero-length u12 segment. The current length helper omits empty-segment errors.

Original HTTP request payloads were NOT retained. Reconstructed initial messages are saved and explicitly marked as reconstructions; exact original retries/wire payloads cannot be proven from saved response-only artifacts. Future live requests must be saved privately with credentials excluded.

## Other confirmed causes / limits

- Relationship grouping can merge jobs when visible headers are not bold; can attach education by nearest vertical distance without sufficient semantic/column evidence; fallback produces date/artifact records. Multiple qualification terms are often one expanded degree, not multiple records (e.g. Bachelor of Commerce (B.Com)). All 49/27 flagged record inventories were inspected as diagnostics, not labeled 76 errors.
- Three duplicate candidates have distinct source coordinates; Bhupendra/Raja repeat across different pages. These must not be deleted merely for equal text. Astha needs original-region inspection.
- Six text differences: Gopal includes embedded NUL glyphs (e.g. Objec-NUL-ve/exper-NUL-se), which Poppler resolves differently. Other individual missing text/header/encoding cases are listed in pdf-difference-evidence.json. Unmatched global words undercount missing occurrences.
- Mukkadala flags are joined headings ProfessionalSummary and TechnicalSkills, not proof of corrupted ordinary words. Preserve source text and distinguish the physical boundary type.
- Assignement is explicitly a website critique assignment; Devops Groovy has Hiring Manager, Open Position and mandatory requirements. Existing scope rules miss these combinations. Never use a filename or one keyword as the decision.

No baseline artifacts, PDFs, labels or gold were modified. 4,960 prior/source files were hash-snapshotted before modifications.
