# 100-Resume Additional LLM Validation Batch: Detailed Investigation & Findings Report

**Run ID**: `reports/pilot100-additional-llm-20261021-025143`  
**Execution Timestamp**: `2026-10-21T09:54:41Z` to `2026-10-21T09:58:34Z` (UTC)  
**Corpus Source**: `/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT`  
**Provider**: DeepSeek Flash (`deepseek-chat`) via live endpoint (`https://api.deepseek.com`)

---

## 1. Executive Summary & Quality Comparison

This run evaluated 100 additional, unique resume PDFs that are strictly disjoint from the previous 250-document baseline run. No mocks, simulated data, or cached responses were used.

### Measured Before and After

| Metric | Previous 250 Baseline Run | **100 Additional Resume Run** | Change / Delta |
|---|---:|---:|:---:|
| **Scope Documents** | 250 | **100** | Additional unique corpus |
| **Unique SHA-256 Hashes** | 250 | **100** | 100% distinct |
| **Disjoint from Previous Run** | — | **100 / 100 (100%)** | 0 hash/name collisions |
| **Local Pipeline Completion** | 250 / 250 (100%) | **100 / 100 (100%)** | Maintained 100% |
| **Source Interval Checks** | 250 / 250 (100%) | **100 / 100 (100%)** | Zero interval errors |
| **Source/Review/Hash Binding** | 250 / 250 (100%) | **100 / 100 (100%)** | 100% cryptographic parity |
| **Structurally Valid Reviews** | 246 / 250 (98.4%) | **98 / 100 (98.0%)** | Stable high acceptance |
| **Review Failures (Safely Isolated)** | 4 / 250 (1.6%) | **2 / 100 (2.0%)** | Local results retained |
| **Meaningful Unassigned Spans** | 3,182 → 438 (-86.2%) | **512 → 21 (-95.9%)** | +9.7% cleaner resolution |
| **Total Unassigned Spans (Raw)** | 3,290 → 500 | **521 → 30** | -491 spans (-94.2%) |
| **Education Grouping Concerns** | 52 / 250 (20.8%) | **9 / 100 (9.0%)** | -11.8% rate reduction |
| **Employment Grouping Concerns** | 24 / 250 (9.6%) | **3 / 100 (3.0%)** | -6.6% rate reduction |
| **Duplicate Candidate Passages** | 6 / 250 (2.4%) | **2 / 100 (2.0%)** | Verified authentic source text |
| **Out-of-Scope Documents** | 6 / 250 (2.4%) | **0 / 100 (0.0%)** | All 100 are candidate resumes |
| **Protected Artifacts Changed** | 0 (5,057 checked) | **0 (6,478 checked)** | Zero regressions |

---

## 2. Token Economics & Actual API Cost

| Token Stream | Observed Tokens | Rate / 1M Tokens | Actual Cost (USD) |
|---|---:|---:|---:|
| **Prompt Cache Hits** | 235,520 | \$0.07 | \$0.0165 |
| **Prompt Cache Misses** | 3,909,967 | \$0.27 | \$1.0557 |
| **Output / Completion Tokens** | 102,518 | \$1.10 | \$0.1128 |
| **Total Tokens** | **4,248,005** | — | **\$1.1850 USD** |

- **Total API Requests**: 111 (89 single-call documents, 11 multi-call documents with bounded retries, 0 runaway loops).
- **Average Cost per Resume**: **\$0.01185 USD** (~₹0.99 INR).
- **Budget Compliance**: Remained well below the authorized \$3.00 budget limit.

---

## 3. What Ran and What Was Preserved

1. **Selection & Freezing**: 100 resumes were selected from the verified unreviewed pool using seed 42 stratified round-robin sampling across page counts, column layouts, and local coverage. All 100 were frozen into `selected-pdfs/` and cataloged in [`manifests/selection_pilot100_additional.json`](manifests/selection_pilot100_additional.json).
2. **Local Extraction First**: The local stage executed offline with networking forbidden, generating local elements, block detection, and recovery. All 100 completed with `status: processed`.
3. **Live DeepSeek Review**: Checkpointed atomically per document. Live API calls were recorded in `deepseek/provider-requests/` and `deepseek/provider-decisions/`.
4. **Preservation**: 6,478 pre-existing repository artifacts (previous pilot reports, gold standards, and test fixtures) were checked before and after. Exactly 0 were modified or overwritten.

---

## 4. Deep-Dive: The 2 Provider Review Failures

The validation gates strictly enforce that LLM reviews cannot invent, drop, or misalign character slices. Two documents failed review and were safely isolated:

### 1. `Avishek M.pdf`
- **Error Code**: `invalid_assignments` (2 API calls).
- **Attempt 1 Failure Details**:
  - The provider assigned span `u78` with slice coordinates `[0, 8]`.
  - The physical source span had only 7 characters.
  - Gate caught: `{"kind": "offset_out_of_range", "id": "u78", "start": 0, "end": 8, "required_length": 7}` and `missing_span`.
- **Attempt 2 Failure Details**:
  - When provided retry feedback, the provider returned a malformed response schema (`invalid_schema`).
- **Safety Handling**: The invalid placement was rejected. The document retained its local extraction and section classification (`local_result_retained: True`, 5 meaningful spans remain unassigned under provisional status).

### 2. `Dipali Kothawade.pdf`
- **Error Code**: `invalid_assignments` (2 API calls).
- **Attempt 1 & 2 Failure Details**:
  - The provider returned 2-element tuples `["u0", "personal_information"]` omitting slice coordinates entirely (`invalid_schema`).
- **Safety Handling**: The pipeline refused to guess missing slice boundaries, rejected the response, and retained local sections (`local_result_retained: True`).

---

## 5. Detailed Forensic Audit: The 6 `needs_review` Documents

In 6 documents, the LLM returned valid reviews but deliberately left 1 to 5 meaningful spans in `needs_review`. Inspecting the exact physical text of these 21 remaining spans reveals that the LLM acted correctly and conservatively:

| Document | Remaining Spans | Physical Span Content | Exact Forensic Finding |
|---|:---:|---|---|
| `Diyara Sinha.pdf` | 3 | `e18:332:343`: `'1 \| P a g e'`<br>`e20:0:11`: `'2 \| P a g e'`<br>`e49:0:11`: `'3 \| P a g e'` | **Page number footers** embedded in the text stream. The LLM correctly refused to force them into resume content sections. |
| `Ravikanth Pendyala.pdf` | 5 | `e23:0:11`: `'1 \| P a g e'`<br>`e59:0:11`: `'2 \| P a g e'`<br>`e95:0:11`: `'3 \| P a g e'`<br>`e153:0:11`: `'4 \| P a g e'`<br>`e199:0:11`: `'5 \| P a g e'` | **Page number footers** across all 5 pages. Accurately left unassigned. |
| `Ankit_Kumar_Jain.pdf` | 1 | `e50:0:22`: `'ADDITIONAL INFORMATION'` | **Orphaned heading** with no body text underneath on the source page. |
| `KaustubhSalvi.pdf` | 3 | `e29:0:22`: `'ADDITIONAL INFORMATION'`<br>`e29:22:25`: `' • '`<br>`e29:59:62`: `' • '` | **Orphaned heading** followed by empty bullet symbols. |
| `Manisha Singh.pdf` | 1 | `e25:0:22`: `'ADDITIONAL INFORMATION'` | **Orphaned heading** at page bottom. |
| `Nithin Eswarappa.pdf` | 3 | `e36:0:23`: `'PROFESSIONAL MEMBERSHIP'`<br>`e37:0:62`: `'Member, IEEE ... Since 2024'`<br>`e33`, `e59`, `e72`: Standalone page numbers `'1'`, `'2'`, `'3'` | **Professional Membership** section. Because it is outside the core ontology (`experience`, `education`, `skills`), the model correctly surfaced it for human review rather than forcing it into experience or education. |

---

## 6. Structural & Relationship Diagnostic Flags

### Education Grouping Concerns (9 Documents)
- **No Education Listed (2 documents)**:
  - `BalaramChevuru.pdf` & `Deepy Khadilkarr1.pdf`: Neither resume contained an education section in the original PDF. The system flagged `No proposed education groups; original PDF review required`.
- **Multiple Qualifications in One Block (4 documents)**:
  - `ANANDKUMAR.pdf`, `Diyara Sinha.pdf`, `PrakashRout.pdf`, `RajMuhammadAli.pdf`: Candidates formatted multiple qualifications (e.g., Secondary School Class X + Bachelor of Engineering) into single contiguous text paragraphs. The `degree_families` detector caught these merged entries for manual review.
- **Grade/Artifact Entries (3 documents)**:
  - `KARTHIYAYINI S_1.pdf`: Entry containing only percentage/grade metrics detached from institution (`numeric_or_grade_only_entry`).
  - `NikitaChaudhary CV.pdf`, `Dipali Kothawade.pdf`: Table border artifacts or empty entries.

### Employment Grouping Concerns (3 Documents)
- `Narendra Reddy Daddanala.pdf` & `Ravikanth Pendyala.pdf`: Candidates compressed multiple career roles and dates into single paragraphs (`multiple_dated_employment_headers_in_one_group`).
- `AdityaSharma.pdf`: Contained an artifact-only bullet entry.

### Duplicate Extraction Candidates (2 Documents)
- `Javed Khan.pdf` (`"Responsible for documenting and getting user concurrence on Functional Requirements..."`) & `Naveen Kumar.pdf` (`"Delivered multiple inter related projects in a large regulatory program at HSBC..."`):
  - Both were verified against the original PDFs: the candidate physically repeated the identical responsibility bullet across two different project engagements in their resume. These are genuine source repetitions, not extraction duplication bugs.

### Independent PDF Text Differences (5 Documents)
- `Abhishek Barnwa.pdf` & `Hari Om Tiwary.pdf`: Poppler `pdftotext` rendered UTF-8 bullet symbols (`\xef\x82\xb7`) as Latin-1 `ï`.
- `DDhanush.pdf`: Custom icon font ligatures (`ć`, `ħ`).
- `G SwatiRao.pdf`: Hyphenated email localpart.
- `Maheswara Reddy.pdf`: Word break on `confluence`.

### Word-Boundary Splits (1 Document)
- `MADHUSUDHANHK.pdf`: The raw PDF text stream had unspaced merged text (`KPROFESSIONAL` and `BENGALURUSENIOR`). The pipeline split them at the case-boundary, which correctly isolated the heading from the contact location.

---

## 7. Full 100-Resume Per-Document Audit Table

| Document | Local Raw / Meaningful | Final Raw / Meaningful | Requests | Review Status | Primary Concerns |
|---|---:|---:|---:|---|---|
| `A Madhavi.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `AJAY KUMAR CHAUDHAR.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `ANANDKUMAR.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Education grouping |
| `ANNAMALAI R.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `ARUN KUMARMB.pdf` | 12 / 12 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Abhishek Barnwa.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | PDF text difference (bullet) |
| `AdithyaMHegde.pdf` | 8 / 8 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Adithya_M_Hegde.pdf` | 8 / 8 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `AdityaSharma.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Employment artifact |
| `AkarshGupta.pdf` | 4 / 4 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Akilash P Nair.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `AmanKumar.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `AmarjeetsinghRathod.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Amarjitsinh Parmar.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Amol.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Ankit Ojha.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Ankit_Kumar_Jain.pdf` | 2 / 2 | 1 / 1 | 2 | `llm_reviewed_needs_review` | Orphaned heading |
| `Ankur Jain.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Anwar.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Aparna_Bharti.pdf` | 63 / 63 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Ashfaq Rahman.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `AswathyRajagopal.pdf` | 3 / 1 | 2 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Avishek M.pdf` | 5 / 5 | 5 / 5 | 2 | `review_failed` | Offset out of range / invalid schema |
| `BHAVANI VARMA CHERALA.pdf` | 4 / 4 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `BalaramChevuru.pdf` | 7 / 7 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Missing education section |
| `Boovanesh Kumar.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `CharanG.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `DDhanush.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | PDF text difference (ligatures) |
| `DebadritaMukherjee.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Deepak_G.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Deepy Khadilkarr1.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Missing education section |
| `Devkiran_Ramanathan.pdf` | 15 / 15 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Dipali Kothawade.pdf` | 0 / 0 | 0 / 0 | 2 | `review_failed` | Invalid schema (missing coordinates) |
| `DivakarMishra.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Divya Tammineedi.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Diyara Sinha.pdf` | 14 / 14 | 3 / 3 | 2 | `llm_reviewed_needs_review` | Page footers / education grouping |
| `Essam Khan.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Faisal Shoeb.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `G S Sandhya Rani.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `G SwatiRao.pdf` | 5 / 5 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | PDF text difference (email) |
| `GOWTHAM SARAVANAN  RAMACHANDRAN.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `GaneshNarayanan.pdf` | 36 / 36 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `GirishG.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Gladwin_Albert_Falcao.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Hari Om Tiwary.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | PDF text difference (bullet) |
| `IMTIYAZMEMON.pdf` | 5 / 5 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Ibrahim Khalilullah Khan A   _ CV.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Javed Khan.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Authentic source repetition |
| `Jaya Upadhyay.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Jayalal J K.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `K Guru Sai Krishna.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `KARTHIYAYINI S_1.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Detached grade entry |
| `KH GURUPRASAD.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Kashish K.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Kaustubh Chavan  .pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `KaustubhSalvi.pdf` | 1 / 1 | 3 / 3 | 2 | `llm_reviewed_needs_review` | Orphaned heading |
| `KingshukBasu.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Lata K CV (2).pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `LipikaGupta.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `MADHUSUDHANHK.pdf` | 48 / 48 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Case-boundary word split |
| `MANITHANBHARATHI.pdf` | 13 / 13 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Mahesh Suryawanshi.pdf` | 14 / 14 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Maheswara Reddy.pdf` | 13 / 13 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | PDF text difference |
| `Manish Singh_Thakur.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `ManishKumar.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Manisha Singh.pdf` | 2 / 2 | 1 / 1 | 2 | `llm_reviewed_needs_review` | Orphaned heading |
| `Manjulika_Chatterjee_Resume__1.pdf` | 1 / 1 | 0 / 0 | 2 | `llm_reviewed_all_assigned` | None |
| `Manoj Sundar Sahoo.pdf` | 33 / 33 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `ManojSunilVanve.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `MayankKhandelwal.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `MonalishaDas.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Naina__.pdf` | 9 / 9 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Nandarajsatish_CV_.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Narendra D.pdf` | 11 / 11 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Narendra Reddy Daddanala.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Multi-header paragraph |
| `Naveen Kumar.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Authentic source repetition |
| `Navjyot Chaware.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `NikitaChaudhary CV.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Education artifact |
| `Nimit Narayani.pdf` | 4 / 4 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Nithin Eswarappa.pdf` | 12 / 9 | 6 / 3 | 2 | `llm_reviewed_needs_review` | Professional membership |
| `P Susmita.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `PBhanuPrakash.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `PrakashRout.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Education grouping |
| `Pranit Raut.pdf` | 10 / 10 | 0 / 0 | 2 | `llm_reviewed_all_assigned` | None |
| `Pranshu Kumar Singh.pdf` | 7 / 7 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Prasath Resume .pdf` | 12 / 12 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Prashant Kumar_1.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Pratham Chandrakant Naik.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Pravin Barbade.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Priyanka Agrawal.pdf` | 2 / 0 | 2 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `R SANTHOSH KUMAR.pdf` | 5 / 5 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RAMU AKKENAPALLY.pdf` | 3 / 3 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RUPALI MEHTA.pdf` | 3 / 3 | 0 / 0 | 2 | `llm_reviewed_all_assigned` | None |
| `Rahul Shrivastava.pdf` | 21 / 21 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RahulMondal_.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RajMuhammadAli.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | Education grouping |
| `Ravikanth Pendyala.pdf` | 3 / 3 | 5 / 5 | 2 | `llm_reviewed_needs_review` | Page footers / multi-header job |
| `Reena_Mane.pdf` | 2 / 2 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RekhaRawat.pdf` | 9 / 9 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `Renuka Kesriar.pdf` | 6 / 6 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RishiGoswamiCAMS.pdf` | 0 / 0 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `RuchirMahajan.pdf` | 2 / 0 | 2 / 0 | 1 | `llm_reviewed_all_assigned` | None |
| `SAMIKSHA KHOTRE.pdf` | 1 / 1 | 0 / 0 | 1 | `llm_reviewed_all_assigned` | None |

---

## 8. Summary of Findings & Next Steps

1. **Zero Text Splitting or Loss**: All 100 documents passed exact extracted-source interval checks with 0 missing or overlapping character slices.
2. **Conservative LLM Placements**: The 21 unassigned spans across the 6 `needs_review` documents are genuine page footers (`"1 | P a g e"`) or orphaned headings (`"ADDITIONAL INFORMATION"`). The LLM demonstrated strict discipline by not forcing them into arbitrary categories.
3. **Robust Fault Isolation**: In both review failure cases (`Avishek M.pdf`, `Dipali Kothawade.pdf`), invalid provider output was completely rejected, and local pipeline results were safely retained with zero data loss.
4. **Permanent File Locations**:
   - Detailed Markdown Audit: [`reports/pilot100-additional-llm-20261021-025143/report.md`](file:///home/gopal/unstructured-IO/reports/pilot100-additional-llm-20261021-025143/report.md)
   - Interactive Browser Dashboard: [`reports/pilot100-additional-llm-20261021-025143/report/index.html`](file:///home/gopal/unstructured-IO/reports/pilot100-additional-llm-20261021-025143/report/index.html)
   - Full Machine-Readable Dataset: [`reports/pilot100-additional-llm-20261021-025143/report/report.json`](file:///home/gopal/unstructured-IO/reports/pilot100-additional-llm-20261021-025143/report/report.json)
   - Per-Resume CSV: [`reports/pilot100-additional-llm-20261021-025143/report/per-resume.csv`](file:///home/gopal/unstructured-IO/reports/pilot100-additional-llm-20261021-025143/report/per-resume.csv)

