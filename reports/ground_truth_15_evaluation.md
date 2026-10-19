# Ground Truth Pilot Validation: 15 Resumes Evaluation Report

> [!IMPORTANT]
> These 15 resumes constitute the **initial development and validation set**. They are used to identify baseline extraction and block-detection weaknesses, establish independent gold-standard annotations, and evaluate the impact of LLM review.

## 1. Executive Summary & Comparison

| Metric | Configuration A (Local Pipeline Only) | Configuration B (With DeepSeek Review) | Absolute Change |
|---|---:|---:|---:|
| **Overall Character Accuracy** | **58.5%** | **99.92%** | **+41.42%** |
| **Entirely Correct Resumes** | **0 / 15** (0.0%) | **9 / 15** (60.0%) | **+9 resumes** |
| **Improved Documents** | - | **15 / 15** (100%) | - |
| **Regressed Documents** | - | **0 / 15** (0.0%) | - |
| **Entirely Correct Sections** | 34 / 98 (34.7%) | 86 / 98 (87.8%) | +52 sections |

## 2. Per-Category Precision, Recall & F1 Scores

| Semantic Category | Local Precision | Local Recall | Local F1 | LLM Precision | LLM Recall | LLM F1 |
|---|---:|---:|---:|---:|---:|---:|
| `awards` | 83.6% | 18.5% | 30.3% | 100.0% | 100.0% | **100.0%** |
| `certifications` | 23.2% | 22.5% | 22.9% | 100.0% | 100.0% | **100.0%** |
| `education` | 57.7% | 84.0% | 68.4% | 100.0% | 100.0% | **100.0%** |
| `experience` | 89.2% | 56.9% | 69.5% | 100.0% | 99.9% | **100.0%** |
| `languages` | 3.9% | 100.0% | 7.5% | 100.0% | 59.6% | **74.7%** |
| `personal_information` | 97.5% | 73.1% | 83.6% | 100.0% | 100.0% | **100.0%** |
| `projects` | 42.0% | 37.1% | 39.4% | 100.0% | 99.7% | **99.9%** |
| `skills` | 31.6% | 67.3% | 43.0% | 99.4% | 100.0% | **99.7%** |
| `summary` | 68.3% | 82.1% | 74.6% | 100.0% | 100.0% | **100.0%** |

## 3. Per-Resume Accuracy & Record Grouping Breakdown

| Resume Filename | Pages | Local Cov | LLM Cov | Local Acc | LLM Acc | Work Exp Records (Gold vs Local vs LLM) | Edu Records (Gold vs Local vs LLM) |
|---|---:|---:|---:|---:|---:|:---:|:---:|
| `A Suribhotla.pdf` | 4 | 99.7% | 100.0% | 99.7% | **100.0%** | 15 / 26 / 26 | 2 / 1 / 1 |
| `Ajay Bandagi.pdf` | 1 | 92.8% | 100.0% | 88.2% | **100.0%** | 4 / 6 / 5 | 3 / 3 / 3 |
| `AkshayPatni (1).pdf` | 2 | 99.8% | 100.0% | 99.8% | **100.0%** | 7 / 11 / 11 | 1 / 1 / 1 |
| `Alvina _Fernandes.pdf` | 3 | 100.0% | 100.0% | 95.0% | **100.0%** | 2 / 6 / 4 | 2 / 3 / 3 |
| `Anuradha Yadav.pdf` | 2 | 72.0% | 100.0% | 72.0% | **100.0%** | 4 / 6 / 6 | 2 / 2 / 2 |
| `Charansai P.pdf` | 3 | 99.2% | 100.0% | 53.2% | **99.8%** | 6 / 2 / 12 | 2 / 2 / 1 |
| `GAURAVAGRAWAL.pdf` | 2 | 99.7% | 100.0% | 86.6% | **100.0%** | 3 / 5 / 5 | 3 / 4 / 4 |
| `Java Aws backend.pdf` | 2 | 91.1% | 100.0% | 32.1% | **98.8%** | 5 / 10 / 13 | 2 / 1 / 1 |
| `NagaVishnu.pdf` | 5 | 75.5% | 100.0% | 31.0% | **99.9%** | 3 / 6 / 6 | 3 / 8 / 4 |
| `Nikhil Kumar.pdf` | 3 | 99.8% | 100.0% | 99.8% | **100.0%** | 6 / 7 / 7 | 4 / 4 / 4 |
| `PUPPYKUMARI.pdf` | 6 | 92.4% | 100.0% | 3.4% | **99.9%** | 11 / 0 / 45 | 1 / 13 / 5 |
| `Pavan Bakku.pdf` | 1 | 100.0% | 100.0% | 65.8% | **99.7%** | 4 / 5 / 4 | 2 / 2 / 2 |
| `Prasad PR.pdf` | 2 | 99.2% | 100.0% | 69.3% | **100.0%** | 4 / 6 / 6 | 4 / 3 / 2 |
| `Rutuja Herekar.pdf` | 3 | 89.4% | 100.0% | 63.8% | **99.8%** | 11 / 29 / 21 | 3 / 0 / 1 |
| `S  Abhinav.pdf` | 4 | 99.2% | 100.0% | 29.1% | **100.0%** | 8 / 0 / 10 | 1 / 0 / 2 |

## 4. Key Block-Detection Weaknesses Identified in Local Pipeline

1. **Language Classification Confusion**: Local Sentence-BERT misclassified programming languages (Python, SQL, JavaScript) under spoken `languages` instead of `skills` whenever they appeared near candidate contact or profile headers.
2. **Preamble & Objective Boundaries**: First-page summary paragraphs without standard headers (e.g. `P R O F I L E S U M M A R Y` or opening role statements) were frequently dragged into `experience` or left unassigned as `needs_review`.
3. **Multi-Column Sidebar Leakage**: In two-column resumes (e.g. `Ajay Bandagi.pdf`, `Anuradha Yadav.pdf`, `NagaVishnu.pdf`), sidebar skills and contact items were merged across lanes into adjacent work experience narrative.
4. **Cross-Page Continuation**: For resumes >3 pages (`NagaVishnu.pdf`, `PUPPYKUMARI.pdf`), long engagement portfolios had project blocks erroneously labeled as education or awards when explicit section headings were absent on subsequent pages.

## 5. API Usage and Cost Projections

- **15 Pilot Resumes Actual API Usage**:
  - Total prompt tokens: ~22,500
  - Total completion tokens: ~6,000
  - Total API cost: **$0.0127 USD** (~$0.0008 per resume)
- **Scaled Full Corpus Projection (1,500 Resumes)**:
  - Projected prompt tokens: ~2,250,000
  - Projected completion tokens: ~600,000
  - **Projected Total Cost**: **$1.27 USD** (~₹107.74 INR)

