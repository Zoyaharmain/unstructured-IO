# Independent Unseen Resume Generalization Evaluation Protocol

**Project:** `unstructured-IO`  
**Branch:** `schema-mapping-accuracy-fixes`  
**Protocol Version:** 1.0.0  
**Status:** Frozen Evaluation Standard  

---

## 1. Primary Objective & Charter

The objective of this protocol is to conduct an independent, blind evaluation of the generalized resume parsing pipeline on documents that were **strictly never exposed** to the engineering team during development, prompt tuning, heuristic rule crafting, or regression test construction.

### Integrity Mandates
1. **Blind Evaluation:** The initial evaluation baseline is frozen before any inspection or modification of production parsing logic.
2. **Zero Parser Contamination:** Ground truth annotations must be created independently of parser predictions. Unlabeled blind templates and source text inspection are used; parser outputs are never shown to annotators prior to adjudication.
3. **Semantic Exactness:** Evaluation asserts exact entity name, role title, date association, and responsibility ownership accuracy. Record-count parity is explicitly rejected as a measure of correctness.
4. **Data Isolation & Privacy:** All resumes are processed strictly within the local offline execution sandbox. Zero resume content, PII, or metadata is transmitted to external endpoints or third-party APIs.

---

## 2. Dataset Selection & Provenance Audit

### A. Source Pool
The candidate evaluation pool is derived from distinct real-world PDF and DOCX documents residing in repository storage archives. To qualify for the unseen holdout dataset, a document must satisfy the following cryptographic and lexical checks:
- **Hash Disjointness:** SHA-256 byte digest must not match any document in `tests/`, `evaluation/adversarial_fixtures/`, `resume ground truth/`, or active pilot benchmarks.
- **Name Disjointness:** Canonical filename and stem must not appear in any test script, fixture, or regression assertion.
- **Structural Diversity:** The sample must span single-column, multi-column sidebar, tabular, and academic CV layouts across varying experience depths (freshers to 20+ year veterans).

### B. Category Stratification
The holdout dataset is stratified into representative operational categories:
1. **Engineering & Technical:** Software, DevOps, Cloud Infrastructure, Data Engineering, QA.
2. **Operations & Cloud:** SRE, Systems Administration, Database Administration, Infrastructure.
3. **Leadership & Management:** Engineering Managers, Program Managers, Product Leads, Directors.
4. **Finance & Analytics:** Investment Banking, Financial Analysis, Risk & Compliance, Reporting.
5. **Healthcare & Medical:** Clinical Specialists, Physicians, Laboratory Researchers, Healthcare Administration.
6. **Academic & Research:** Postdoctoral Fellows, University Lecturers, Research Scientists, Academic CVs with publications and grant funding.
7. **Complex Layouts & Multi-Column:** Two-column sidebars, table-structured DOCX/PDF, dense formatting.

---

## 3. Independent Ground Truth Protocol

Ground truth annotations are governed by the schema defined in `ground_truth_schema.json`.

### Annotation Workflow
1. **Source Span Extraction:** Document text elements are extracted using `scripts/annotate_resume_sources.py`, generating an unlabeled worksheet (`worksheet.tsv`) preserving immutable character offsets.
2. **Blind Attribution:** Human annotators mark:
   - Canonical section boundaries (`personal_information`, `summary`, `experience`, `education`, `skills`, `certifications`, `projects`, etc.).
   - Explicit employer names (excluding departments, locations, and vendors).
   - Exact job titles (including subfunctions where appropriate).
   - Employment date ranges (`start_date`, `end_date`, `is_current`).
   - Responsibility-to-role ownership.
3. **Double-Blind Review & Adjudication:** An independent adjudicator verifies annotations, resolving discrepancies and attesting independence (`saw_parser_predictions: false`, `independence_attested: true`).

---

## 4. Evaluation Metrics & Formulas

For every evaluated resume, metric calculations use strict semantic matching:

### 1. Section Identification
$$\text{Precision} = \frac{|\text{Actual} \cap \text{Expected}|}{|\text{Actual}|}, \quad \text{Recall} = \frac{|\text{Actual} \cap \text{Expected}|}{|\text{Expected}|}, \quad \text{F1} = \frac{2 \cdot \text{P} \cdot \text{R}}{\text{P} + \text{R}}$$

### 2. Employer Extraction & Normalization
An extracted employer is marked as correct if its canonical normalized string matches the ground-truth employer name for that record.

### 3. Role Title Extraction
An extracted role is marked as correct if its canonical title matches the ground-truth title without narrative contamination.

### 4. Employer-Role Relationship Accuracy
$$\text{Relationship Accuracy} = \frac{\text{Correct (Employer, Role) Pairs}}{\text{Total Expected Pairs}}$$
A pair is correct if and only if both the employer name and role title match, and the role is correctly bound to that specific employer.

### 5. Date Association Accuracy
$$\text{Date Accuracy} = \frac{\text{Roles with Correct (Start Date, End Date)}}{\text{Total Roles with Expected Dates}}$$

### 6. Responsibility Ownership Accuracy
$$\text{Ownership Accuracy} = \frac{\text{Responsibilities Assigned to Correct Role}}{\text{Total Expected Responsibilities}}$$
Assigned responsibilities must trace to the correct employer/role boundary. Any migration across distinct employers is penalized.

### 7. Education & Certification Accuracy
$$\text{Education Accuracy} = \frac{\text{Correct (Degree, Institution) Pairs}}{\text{Total Expected Education Records}}$$

### 8. Document-Level Strict Pass Rate
A document achieves a **Strict Pass** if and only if:
1. All sections match expected categories ($\text{Recall} = 1.0$).
2. All employer names match ground truth.
3. All role titles match ground truth.
4. Employer-role relationships have 100% accuracy.
5. Zero cross-record responsibility leakage.
6. Zero unsupported/fabricated field values.
7. Zero arbitrary date borrowing.

---

## 5. Security & Robustness Protocol

1. **Adversarial Paraphrase Testing:** Tests 5 distinct prompt-injection patterns (conversational override, delimiter escape, bracketed directive, system prompt leak, tenure fabrication) to verify that untrusted resume text is never interpreted as operational instructions.
2. **Source Grounding & Evidence Resolution:** Confirms every extracted field resolves to a valid byte range (`e<idx>:<start>:<end>`).
3. **Resource & Memory Bounding:** Tracks peak resident set size (RSS) and wall-clock execution time to ensure predictable runtime across dense multi-page documents.
4. **Safe Error Handling:** Confirms corrupted DOCX and malformed PDF files fail cleanly with standard HTTP status codes without crashing worker processes.
