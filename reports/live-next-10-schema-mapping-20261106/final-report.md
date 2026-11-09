# Ten New Resumes: Live DeepSeek Schema Mapping Accuracy Test — 2026-11-06

## 1. Executive Summary & Selection Integrity

A controlled live DeepSeek schema mapping accuracy test was conducted on 10 strictly untested candidate resumes. All files were drawn directly from `/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/Old/resume/RESUMES_FLAT`.

Strict exclusion criteria were enforced prior to selection:
- Excluded all 12 manually verified ground-truth resumes (`A Suribhotla.pdf`, `Ashwin S S.docx`, `Supriya Bhagat_1.docx`, `_SURESHBABUS.pdf`, `Yogendra Singh.pdf`, `Arnab_Kumar Kar.pdf`, `Chaganti Leela Sankar.docx`, `Ravisankar Sundar.docx`, `Ashfaq Rahman.pdf`, `AbhishekTiwari.pdf`, `DeekshaYadu.pdf`, `ShyamKumarDonka.pdf`).
- Excluded all five November 5 test resumes (`A Lokhande.pdf`, `A Madhavi.pdf`, `AJAY KUMAR CHAUDHAR.pdf`, `AMIT_RANA.pdf`, `ANANDKUMAR.pdf`) and the initial `AMAN AHUJA` test folder.
- Excluded all 800+ candidate files and stems present in previous live LLM test reports, pilot runs, cache manifests, and repo test suites.
- Full selection manifest and SHA-256 hashes were recorded in [`selection.json`](selection.json).

Execution was governed by a **controlled execution gate**: Resumes 01 through 03 were tested first. Zero crashes, zero network exceptions, and zero source validation errors occurred, satisfying the gate. Resumes 04 through 10 were subsequently executed.

**Overall Accuracy Result: 5 / 10 Clean Passes (50.0% Pass Rate).**

---

## 2. Live Execution & Processing Metrics

All 10 executions utilized the production schema mapping pipeline via `scripts/check_single_resume.py` with `--llm-review --recovery-attempts 1`, communicating with live DeepSeek (`https://api.deepseek.com`, model `deepseek-flash`). Zero application code, production configuration, or `.env` parameters were altered.

| # | Resume File | Seconds | Provider Calls / Responses | Section Review | Field Review | Audit Status | Verdict |
|---|---|---:|---:|---|---|---|:---:|
| 01 | `ANURAGVASI.pdf` | 129.0s | 17 / 17 | complete | partial | incomplete (`foreign_audit_source`) | **PASS** |
| 02 | `Aarunis.pdf` | 51.1s | 5 / 5 | complete | partial | incomplete (`invalid_audit_contract`) | **FAIL** |
| 03 | `AbdulkadarBohari.pdf` | 110.9s | 13 / 13 | complete | partial | incomplete (`foreign_audit_source`) | **PASS** |
| 04 | `AbhinavLahariya.pdf` | 53.6s | 6 / 6 | complete | complete | incomplete (`foreign_audit_source`) | **PASS** |
| 05 | `AjayKumarTiwari.pdf` | 73.0s | 9 / 9 | complete | partial | incomplete (`foreign_audit_source`) | **FAIL** |
| 06 | `AkankshaBhand.pdf` | 98.4s | 15 / 15 | complete | failed | incomplete (`foreign_audit_source`) | **FAIL** |
| 07 | `Akash Kumar.pdf` | 56.7s | 9 / 9 | complete | partial | incomplete (`foreign_audit_source`) | **FAIL** |
| 08 | `Akmal Yezdani.pdf` | 109.6s | 14 / 14 | complete | complete | incomplete (`foreign_audit_source`) | **PASS** |
| 09 | `Akshay Singla.pdf` | 105.3s | 11 / 11 | complete | partial | incomplete (`foreign_audit_source`) | **FAIL** |
| 10 | `AkshayGupta.pdf` | 58.4s | 6 / 6 | complete | partial | incomplete (`foreign_audit_source`) | **PASS** |
| **Total** | **10 Resumes** | **846.0s (14.1 min)** | **105 / 105** | — | — | — | **5 PASS / 5 FAIL** |

*Note on Audits:* In accordance with strict validation rules, advisory audits that cite foreign/hallucinated source IDs or invalid contracts are explicitly marked as `incomplete`. They are never represented as zero findings or a successful audit.

---

## 3. Resume-by-Resume Accuracy & Ground-Truth Analysis

### 01. `ANURAGVASI.pdf` — **PASS**
- **Candidate Identity:** Correctly captured as `ANURAG VASI`. No father/family name contamination. Contact: `vasi.anurag@gmail.com`, `+91-8125237003`, Hyderabad.
- **Employment:** Exactly 4 jobs captured, 0 missing companies, 0 missing roles:
  1. *Omnics Technologies*: Senior Engineer / Tech Lead — React Native & React.js (`2022-06` to Present, `is_current: true`)
  2. *Accolite Technologies*: React Native Developer (`2020-06` to `2022-06`)
  3. *Pramati Technologies*: React.js Developer (`2018-06` to `2020-06`)
  4. *Wipro Technologies*: Project Engineer (`2016-06` to `2018-06`)
- **Education:** Correctly extracted MVSR Engineering College (`Bachelor of Engineering`, `2012` to `2016`).
- **Certifications:** MERN Stack Certification — Wipro Digital.
- **Total Experience:** Correctly calculated as `10.4` years based on continuous timeline from `2016-06` to current date.
- **Artifacts:** [Standardized JSON](01/standardized.json) · [Schema Mapping](01/schema.json) · [Audit](01/schema-audit.json)

---

### 02. `Aarunis.pdf` — **FAIL**
- **Candidate Identity:** `full_name` is `null` (FAIL). Header text was `Aaruni Shrivastava (ANALYST - DATA GOVERNANCE)`. The pipeline mapped the entire string to `professional_title` and failed to parse `Aaruni Shrivastava` as the candidate name.
- **Employment:** 2 jobs captured, but start/end dates are `null` for both:
  1. *BlackRock*: Analyst (`None` to `None`)
  2. *Zigram*: Research Analyst (`None` to `None`)
  *Root Cause:* Date in resume is written with a curly apostrophe: `Feb ‘23- Present`. Two-digit year normalization failed to recognize `‘23`.
- **Education:** 2 records captured (Amity University, Prestige Institute).
- **Certifications:** 5 certificates cleanly separated with issuers (CAIA, DataCamp, LinkedIn).
- **Total Experience:** `null` due to unparsed employment dates.
- **Artifacts:** [Standardized JSON](02/standardized.json) · [Schema Mapping](02/schema.json) · [Audit](02/schema-audit.json)

---

### 03. `AbdulkadarBohari.pdf` — **PASS**
- **Candidate Identity:** Correctly identified as `ABDULKADAR BOHARI`. Professional Title: `Senior Network Engineer`.
- **Employment:** Exactly 4 jobs captured with 100% company, role, and date fidelity:
  1. *Blackline Systems*: Senior Network Engineer (`2025-07` to Present, `is_current: true`)
  2. *ESDS Software Solutions*: Senior Network Engineer (`2021-10` to `2025-06`)
  3. *Nexapp Technology Pvt. Ltd.*: Network Support Engineer (`2019-05` to `2021-10`)
  4. *zCon Solutions*: Network Engineer Intern (`2019-01` to `2019-03`)
- **Education:** 3 records captured (Trinity College of Engineering B.E., Poona College HSC, K.R. Public School SSC).
- **Certifications:** 3 records with clean name/issuer separation: CCNA (Cisco), CCNP (Cisco), PCNSE (Palo Alto Networks).
- **Total Experience:** Correctly calculated as `7.6` years.
- **Artifacts:** [Standardized JSON](03/standardized.json) · [Schema Mapping](03/schema.json) · [Audit](03/schema-audit.json)

---

### 04. `AbhinavLahariya.pdf` — **PASS**
- **Candidate Identity:** Correctly identified as `Abhinav Lahariya`. Contact: `+91 8349204729`, `lahariyaabhinav97@gmail.com`.
- **Employment:** Exactly 2 jobs at Intel captured with full dates and responsibilities:
  1. *Intel*: Machine Learning Engineer (`2021-07` to Present, `is_current: true`, 12 responsibilities)
  2. *Intel*: Software Development Intern (`2021-01` to `2021-06`, 4 responsibilities)
- **Education:** 2 records captured (IIIT Allahabad M.Tech `2019-07` to `2021-06`; MITS Gwalior B.E `2015-07` to `2019-06`).
- **Certifications:** None in source; 0 mapped.
- **Total Experience:** Correctly calculated as `5.8` years.
- **Artifacts:** [Standardized JSON](04/standardized.json) · [Schema Mapping](04/schema.json) · [Audit](04/schema-audit.json)

---

### 05. `AjayKumarTiwari.pdf` — **FAIL**
- **Candidate Identity:** Correctly identified as `Ajay Kumar Tiwari`. Title: `Solution Architect | AI/ML, Gen AI`.
- **Employment:** Major boundary splitting defect (FAIL). Mapped 11 fragmented jobs, with 6 missing companies and 4 missing roles.
  - Resume has role and company on consecutive lines:
    ```
    Solution Architect
    Expleo Solutions Limited (July 2023 – till Date)
    ...
    Solution Architect
    Shell India Markets Private Limited (Nov 2015- Sep 2022)
    ```
  - The pipeline generated an isolated record for `Solution Architect` (`company: None`), followed by an isolated record for `Expleo Solutions Limited` (`role: None`). The same split occurred for Shell and older roles.
- **Education:** 1 record captured (Rajiv Gandhi Proudyogiki Vishwavidyalaya, B.E., 2001-2005).
- **Certifications:** 6 certifications mapped.
- **Total Experience:** `null` due to fragmented and disjointed records.
- **Artifacts:** [Standardized JSON](05/standardized.json) · [Schema Mapping](05/schema.json) · [Audit](05/schema-audit.json)

---

### 06. `AkankshaBhand.pdf` — **FAIL**
- **Candidate Identity:** Correctly identified as `Akanksha Bhand`.
- **Employment:** Mismatched records and dropped employers (FAIL):
  1. *Bank of New York Mellon*: Project Manager (`2021-10` to Present) — captured.
  2. *Nihilent Technologies*: Project Manager (`2018-10` to `2021-10`) — captured.
  3. *Earlier Experience Section in Resume:*
     ```
     Earlier Experience
     Capgemini India – Consultant (HSBC Transaction Services & HSBCNet Payments)
     Hewlett Packard Enterprise – Senior Software Engineer
     Tata Consultancy Services – System Engineer
     ```
     - Output completely omitted *Capgemini India*.
     - Output captured *Hewlett Packard Enterprise* with null dates.
     - Output omitted *Tata Consultancy Services* and assigned `System Engineer` to company `"Earlier Experience"`.
- **Certifications:** Concatenation failure (FAIL): Multiple certifications were merged into continuous text strings:
  `"Certified Scrum Master SAFe Agile Foundation Certificate in Banking Capital Markets Consumer Lending"` (5 certifications collapsed into 1).
- **Education:** 1 record captured (Government Engineering College B.E.).
- **Total Experience:** `null`.
- **Artifacts:** [Standardized JSON](06/standardized.json) · [Schema Mapping](06/schema.json) · [Audit](06/schema-audit.json)

---

### 07. `Akash Kumar.pdf` — **FAIL**
- **Candidate Identity:** Correctly identified as `Akash Kumar`. Title: `SOFTWARE DEVELOPMENT ENGINEER`.
- **Employment:** 4 companies and roles captured, but all dates are `null` (FAIL):
  - *Gokwik Commerce Solutions*, *R Systems*, *US Tech Solutions*, *SilverEdge Technologies*: all mapped with `start_date: None, end_date: None`. In source, dates appear on dedicated lines (e.g., `Mar 2024 - Jul 2026`, `Jul 2022 - Feb 2024`) but were dropped.
- **Education:** Missing institutions (FAIL):
  - 3 degrees captured (`B.Tech / B.E.`, `12th`, `10th`), but `institution` is `None` for all three.
- **Total Experience:** `null` due to missing employment dates.
- **Artifacts:** [Standardized JSON](07/standardized.json) · [Schema Mapping](07/schema.json) · [Audit](07/schema-audit.json)

---

### 08. `Akmal Yezdani.pdf` — **PASS**
- **Candidate Identity:** Correctly identified as `AKMAL YEZDANI`. Title: `Technical Project Manager | Delivery Manager | Program Manager | PMP®, PSPO®...`.
- **Employment:** 100% of 9 historical jobs correctly captured across a 17-year career with companies, roles, and dates:
  1. *Cambridge Technology Enterprise Ltd (CTE WebApps)*: Project Manager – Delivery (`2022-07` to `2024-12`)
  2. *Tresbu Digital*: Technical Project Manager (`2021-09` to `2022-07`)
  3. *HCL Technologies*: Deputy Manager – Project Management (`2019-12` to `2021-08`)
  4. *Softvision*: Associate Technical Lead (`2018-11` to `2019-05`)
  5. *ABCO InfoTech*: Technical Project Manager (`2016-05` to `2018-05`)
  6. *TeamLease*: Team Lead (`2015-07` to `2016-04`)
  7. *HCL Technologies*: Project Lead (`2010-09` to `2015-06`)
  8. *TASMEA IT Solutions*: Software Engineer (`2006-07` to `2008-09`)
  9. *Cal-INFO*: Software Engineer (`2005-08` to `2006-07`)
- **Education:** 1 record captured (BCA, 2005; source resume does not list institution).
- **Certifications:** PMP® (Project Management Institute).
- **Total Experience:** Correctly calculated as `16.0` years.
- **Artifacts:** [Standardized JSON](08/standardized.json) · [Schema Mapping](08/schema.json) · [Audit](08/schema-audit.json)

---

### 09. `Akshay Singla.pdf` — **FAIL**
- **Candidate Identity:** Correctly identified as `Akshay Singla`.
- **Employment:** Omitted primary employer (FAIL):
  - Resume contains 3 employers:
    1. *Betterplace — HRMS Platform* (SDE 3 April 2025 - Present, SDE 2 Aug 2023 - March 2025). **Completely omitted from mapped experience.**
    2. *Recrosoft Technologies — Synamedia* (Dec 2020 - Aug 2023): Captured.
    3. *ChicMic — B2B ERP Platform* (Jan 2019 - Dec 2020): Captured, but `company` was left `null`.
- **Education:** Punjabi University, B.Tech, 2019.
- **Total Experience:** Under-calculated as `4.6` years (missing the 2023–Present Betterplace tenure).
- **Artifacts:** [Standardized JSON](09/standardized.json) · [Schema Mapping](09/schema.json) · [Audit](09/schema-audit.json)

---

### 10. `AkshayGupta.pdf` — **PASS**
- **Candidate Identity:** Correctly identified as `AKSHAY GUPTA`. Contact: `Gurgaon/Gurugram`, `+91-7520252426`, `forakshaygupta01@gmail.com`.
- **Employment:** All 3 employers, roles, and date intervals captured cleanly:
  1. *Wipro Limited*: Technical Lead (`2022-01` to Present, `is_current: true`, 20 responsibilities)
  2. *Tata Consultancy Services*: Senior Software Engineer (`2018-08` to `2022-01`, 4 responsibilities)
  3. *Travstarz Holidays & Destinations Pvt Ltd*: Software Developer (`2016-06` to `2018-08`, 14 responsibilities)
- **Education:** Both degrees captured with institution and graduation year:
  1. *MIET*: Master of Computer Applications (MCA), Computers, 2016
  2. *Dewan Institute of Management & Studies*: Bachelor of Computer Applications (BCA), Computers, 2014
- **Certifications:** Generative AI Certifications – Level 1, Level 2 and Level 3.
- **Total Experience:** Correctly calculated as `10.4` years based on continuous employment since June 2016.
- **Artifacts:** [Standardized JSON](10/standardized.json) · [Schema Mapping](10/schema.json) · [Audit](10/schema-audit.json)

---

## 4. Key Takeaways & Identified Mapping Defects

The live DeepSeek test improved from **0/5 (0%)** on November 5 to **5/10 (50.0%)** on this fresh cohort of 10 resumes. 

The remaining 5 failures pinpoint specific, reusable mapping defects:
1. **Header Name-Title Boundary:** When a candidate's name is on the same line as their role in parentheses (e.g. `Aaruni Shrivastava (ANALYST - DATA GOVERNANCE)`), the name is lost and mapped entirely into `professional_title`.
2. **Curly Apostrophe in Dates:** Date normalization does not recognize curly apostrophes (e.g., `‘23`), causing valid employment dates to drop to `null`.
3. **Multi-line Job Headers (Role above Company):** When a resume places `Role` on one line and `Company (Dates)` on the next line (as in `Ajay Kumar Tiwari`), the parser splits them into separate orphaned records instead of merging them.
4. **Summary / "Earlier Experience" Blocks:** Dense tabular or bulleted past experience blocks (as in `Akanksha Bhand` and `Akshay Singla`) risk dropping intermediate employers or adopting section titles like `"Earlier Experience"` as company names.
5. **Certification Token Merging:** Bulleted certification lists without punctuation delimiters can be merged into long single-string certification records.

