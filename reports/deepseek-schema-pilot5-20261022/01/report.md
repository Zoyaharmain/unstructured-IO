# Ajay Bandagi.pdf — five-resume schema pilot

Selection: One-page finance resume; compact history, pursuing MBA, unknown second-job role and dates placed before employer.

Saved input: `reports/batch-next-20261021-064222/deepseek/documents/f3b9f2a6333cad3718ac.json` → `local_sections`. Pages: [1]. Source blocks: 80. No new extraction/block detection was run. Original PDF was not independently examined for this evaluation.

Correctly maps the primary job, finance skills, contact details and degree/major split. Godavari role is absent from blocks; empty role is appropriate. Godavari dates are internally inconsistent: start_date null but end_date/duration populated despite an ambiguous preceding range. B.Com institution is not independently established. Expected MBA completion remains explicitly qualified in metadata.

- Critical-field agreement proxy: **17/19 = 89.47%**.
- Same-block local heuristic baseline on the same critical set: **2/19**.
- Raw field citation contract: **78/78 = 100.00%**.
- Populated-value source-block assessment: {"correct_mapping": 76, "not_populated": 15, "ambiguous": 2}.
- Human-verified/PDF-verified accuracy: **not established**.

## Complete mapping output

[Mapping JSON](mapping.json) · [Unmodified provider mapping and citations](mapping-raw.json) · [Full provider envelope/usage](response-envelope.json) · [Saved source blocks](source-blocks.md) · [Every evaluated field](field-evaluation.json)

```json
{
  "contact": {
    "full_name": "Ajay Bandagi",
    "email": "ajaybandagi1998@gmail.com",
    "phone": "+91 9604657161",
    "location": "Hyderabad, Telangana, India.",
    "linkedin_url": null,
    "github_url": null,
    "portfolio_url": null
  },
  "professional_title": "Senior Accounts Executive",
  "summary": "Senior Accounts Executive with 3.5 years of experience in India Finance Operations, Accounts Payable, statutory compliances, and payroll management. Proven ability to independently manage month-end close, high-volume transactions of ₹1–2 Cr per month, and compliance-driven finance operations. Strong hands-on experience in GST, TDS, PF/PT/ESIC, payroll processing, MIS reporting, and audit coordination. Known for ownership, accuracy, statutory discipline, and timely closures in fast-paced environments.",
  "total_experience_years": 3.5,
  "skills": {
    "technical_skills": [],
    "tools_and_platforms": [
      "Tally",
      "Zoho Books",
      "Zoho Payroll",
      "Advanced Excel"
    ],
    "domain_and_functional": [
      "Accounts Payable (End-to-End)",
      "Vendor & Bank Reconciliations",
      "Cash Flow Monitoring & Management",
      "Month-End & Year-End Close Management",
      "MIS & Management Reporting",
      "GST Compliance (GSTR 1, GSTR-3B, RCM)",
      "TDS Calculation & Returns",
      "PF, PT & ESIC Compliance (Consultant Coordination)",
      "Payroll Processing (End-to-End)",
      "Audit Coordination & Audit Readiness",
      "Finance Operations",
      "Statutory Compliance Management",
      "Process Improvement (Finance)"
    ],
    "soft_skills": [],
    "all_skills": [
      "Accounts Payable (End-to-End)",
      "Vendor & Bank Reconciliations",
      "Cash Flow Monitoring & Management",
      "Month-End & Year-End Close Management",
      "MIS & Management Reporting",
      "GST Compliance (GSTR 1, GSTR-3B, RCM)",
      "TDS Calculation & Returns",
      "PF, PT & ESIC Compliance (Consultant Coordination)",
      "Payroll Processing (End-to-End)",
      "Audit Coordination & Audit Readiness",
      "Finance Operations",
      "Statutory Compliance Management",
      "Process Improvement (Finance)",
      "Tally",
      "Zoho Books",
      "Zoho Payroll",
      "Advanced Excel"
    ]
  },
  "experience": [
    {
      "company": "Vigocare Private Limited",
      "role": "Senior Accounts Executive – Finance Operations & Statutory Compliance",
      "start_date": "Dec 2023",
      "end_date": "Present",
      "duration": "Dec 2023 - Present",
      "location": "Hyderabad",
      "responsibilities": [
        "Independently managing end-to-end Accounts Payable operations, including vendor invoice verification, postings, ageing control, and payments through NEFT/RTGS.",
        "Handling monthly transaction volumes of ₹1–2 Cr, ensuring accuracy, internal controls, and timely closure.",
        "Performing vendor reconciliations and preparing Bank Reconciliation Statements (BRS) to ensure accuracy of cash and bank balances.",
        "Owning month-end and year-end close management, including journal entries, accruals, ledger scrutiny, and balance confirmations.",
        "Preparing MIS, cash flow statements, and management reports for review and decision-making.",
        "Limited knowledge-level exposure to revenue tracking and overseas billing for cash flow monitoring and MIS purposes.",
        "Owning preparation, reconciliation, and coordination with consultants for GST (GSTR-1, GSTR-3B) and PF, PT, and ESIC compliances, with final statutory filings handled through consultants.",
        "Managing end-to-end TDS compliance, including calculations, challans, and returns.",
        "Independently managing end-to-end payroll for 120 employees, including salary processing and statutory deductions.",
        "Leading audit coordination by preparing schedules, reconciliations, and statutory data for internal and external audits.",
        "Acting as SPOC for finance operations and driving process improvement initiatives."
      ],
      "technologies": []
    },
    {
      "company": "Godavari Cuts",
      "role": "",
      "start_date": null,
      "end_date": "Dec 2023",
      "duration": "Feb 2023 - Dec 2023",
      "location": "Hyderabad",
      "responsibilities": [
        "Handled Accounts Payable activities, including invoice verification, vendor payment scheduling, and reconciliation of outstanding balances.",
        "Prepared and maintained daily and monthly Bank Reconciliation Statements (BRS).",
        "Supported month-end activities through basic reconciliations and ledger checks.",
        "Assisted in GST data preparation and return filings, ensuring statutory compliance.",
        "Supported TDS calculations, documentation, and compliance requirements.",
        "Maintained accurate accounting records and supported statutory audits.",
        "Coordinated with vendors and internal departments to resolve discrepancies and ensure smooth financial"
      ],
      "technologies": []
    }
  ],
  "education": [
    {
      "institution": "Yashwantrao Chavan Maharashtra Open University",
      "degree": "Master of Business Administration (MBA)",
      "field_of_study": "Finance",
      "start_year": "July 2024",
      "graduation_year": "June 2026",
      "grade_or_gpa": null
    },
    {
      "institution": "",
      "degree": "Bachelor of Commerce (B.Com)",
      "field_of_study": "Finance & Accounts",
      "start_year": "July 2021",
      "graduation_year": "June 2024",
      "grade_or_gpa": null
    }
  ],
  "certifications": [],
  "projects": [],
  "languages": []
}
```

## Field-by-field results

`correct_mapping` is provisional AI analyst source-block agreement, not independent human truth. `citation_error` can coexist with correct value content. Analyst source references supplement the evaluation; they do not retroactively repair the raw provider response. Null/empty fields are retained for inspection; absence and ambiguity reasons are in the JSON. The CSV/JSON contain full values and exact quote text; the table abbreviates long values.

| Field | LLM value | Mapping assessment | Raw citation assessment | Analyst source IDs |
|---|---|---|---|---|
| `/contact/full_name` | Ajay Bandagi | correct_mapping | citation_supported | e0:0:13 |
| `/contact/email` | ajaybandagi1998@gmail.com | correct_mapping | citation_supported | e1:0:25 |
| `/contact/phone` | +91 9604657161 | correct_mapping | citation_supported | e2:0:14 |
| `/contact/location` | Hyderabad, Telangana, India. | correct_mapping | citation_supported | e3:0:28 |
| `/contact/linkedin_url` | None | not_populated | not_populated |  |
| `/contact/github_url` | None | not_populated | not_populated |  |
| `/contact/portfolio_url` | None | not_populated | not_populated |  |
| `/professional_title` | Senior Accounts Executive | correct_mapping | citation_supported | e0:13:125 |
| `/summary` | Senior Accounts Executive with 3.5 years of experience in India Finance Operations, Accounts Payable, statutory compliances, and payroll management. Proven ability to independently manage month-end close, high-volume transactions of ₹1–2 Cr per month… | correct_mapping | citation_supported | e0:13:125, e0:125:230, e0:230:337, e0:337:449, e0:449:518 |
| `/total_experience_years` | 3.5 | correct_mapping | citation_supported | e0:13:125 |
| `/skills/technical_skills` | [] | not_populated | not_populated |  |
| `/skills/tools_and_platforms/0` | Tally | correct_mapping | citation_supported | e13:416:500 |
| `/skills/tools_and_platforms/1` | Zoho Books | correct_mapping | citation_supported | e13:416:500 |
| `/skills/tools_and_platforms/2` | Zoho Payroll | correct_mapping | citation_supported | e13:416:500 |
| `/skills/tools_and_platforms/3` | Advanced Excel | correct_mapping | citation_supported | e13:416:500 |
| `/skills/domain_and_functional/0` | Accounts Payable (End-to-End) | correct_mapping | citation_supported | e13:0:100 |
| `/skills/domain_and_functional/1` | Vendor & Bank Reconciliations | correct_mapping | citation_supported | e13:0:100 |
| `/skills/domain_and_functional/2` | Cash Flow Monitoring & Management | correct_mapping | citation_supported | e13:0:100 |
| `/skills/domain_and_functional/3` | Month-End & Year-End Close Management | correct_mapping | citation_supported | e13:100:202 |
| `/skills/domain_and_functional/4` | MIS & Management Reporting | correct_mapping | citation_supported | e13:100:202 |
| `/skills/domain_and_functional/5` | GST Compliance (GSTR 1, GSTR-3B, RCM) | correct_mapping | citation_supported | e13:100:202, e13:202:309 |
| `/skills/domain_and_functional/6` | TDS Calculation & Returns | correct_mapping | citation_supported | e13:202:309 |
| `/skills/domain_and_functional/7` | PF, PT & ESIC Compliance (Consultant Coordination) | correct_mapping | citation_supported | e13:202:309 |
| `/skills/domain_and_functional/8` | Payroll Processing (End-to-End) | correct_mapping | citation_supported | e13:202:309, e13:309:416 |
| `/skills/domain_and_functional/9` | Audit Coordination & Audit Readiness | correct_mapping | citation_supported | e13:309:416 |
| `/skills/domain_and_functional/10` | Finance Operations | correct_mapping | citation_supported | e0:13:125 |
| `/skills/domain_and_functional/11` | Statutory Compliance Management | correct_mapping | citation_supported | e13:309:416 |
| `/skills/domain_and_functional/12` | Process Improvement (Finance) | correct_mapping | citation_supported | e13:416:500 |
| `/skills/soft_skills` | [] | not_populated | not_populated |  |
| `/skills/all_skills/0` | Accounts Payable (End-to-End) | correct_mapping | citation_supported | e13:0:100 |
| `/skills/all_skills/1` | Vendor & Bank Reconciliations | correct_mapping | citation_supported | e13:0:100 |
| `/skills/all_skills/2` | Cash Flow Monitoring & Management | correct_mapping | citation_supported | e13:0:100 |
| `/skills/all_skills/3` | Month-End & Year-End Close Management | correct_mapping | citation_supported | e13:100:202 |
| `/skills/all_skills/4` | MIS & Management Reporting | correct_mapping | citation_supported | e13:100:202 |
| `/skills/all_skills/5` | GST Compliance (GSTR 1, GSTR-3B, RCM) | correct_mapping | citation_supported | e13:100:202, e13:202:309 |
| `/skills/all_skills/6` | TDS Calculation & Returns | correct_mapping | citation_supported | e13:202:309 |
| `/skills/all_skills/7` | PF, PT & ESIC Compliance (Consultant Coordination) | correct_mapping | citation_supported | e13:202:309 |
| `/skills/all_skills/8` | Payroll Processing (End-to-End) | correct_mapping | citation_supported | e13:202:309, e13:309:416 |
| `/skills/all_skills/9` | Audit Coordination & Audit Readiness | correct_mapping | citation_supported | e13:309:416 |
| `/skills/all_skills/10` | Finance Operations | correct_mapping | citation_supported | e0:13:125 |
| `/skills/all_skills/11` | Statutory Compliance Management | correct_mapping | citation_supported | e13:309:416 |
| `/skills/all_skills/12` | Process Improvement (Finance) | correct_mapping | citation_supported | e13:416:500 |
| `/skills/all_skills/13` | Tally | correct_mapping | citation_supported | e13:416:500 |
| `/skills/all_skills/14` | Zoho Books | correct_mapping | citation_supported | e13:416:500 |
| `/skills/all_skills/15` | Zoho Payroll | correct_mapping | citation_supported | e13:416:500 |
| `/skills/all_skills/16` | Advanced Excel | correct_mapping | citation_supported | e13:416:500 |
| `/experience/0/company` | Vigocare Private Limited | correct_mapping | citation_supported | e6:0:36 |
| `/experience/0/role` | Senior Accounts Executive – Finance Operations & Statutory Compliance | correct_mapping | citation_supported | e7:0:69 |
| `/experience/0/start_date` | Dec 2023 | correct_mapping | citation_supported | e8:0:18 |
| `/experience/0/end_date` | Present | correct_mapping | citation_supported | e8:0:18 |
| `/experience/0/duration` | Dec 2023 - Present | correct_mapping | citation_supported | e8:0:18 |
| `/experience/0/location` | Hyderabad | correct_mapping | citation_supported | e3:0:28 |
| `/experience/0/responsibilities/0` | Independently managing end-to-end Accounts Payable operations, including vendor invoice verification, postings, ageing control, and payments through NEFT/RTGS. | correct_mapping | citation_supported | e9:0:101, e9:104:161 |
| `/experience/0/responsibilities/1` | Handling monthly transaction volumes of ₹1–2 Cr, ensuring accuracy, internal controls, and timely closure. | correct_mapping | citation_supported | e9:164:270 |
| `/experience/0/responsibilities/2` | Performing vendor reconciliations and preparing Bank Reconciliation Statements (BRS) to ensure accuracy of cash and bank balances. | correct_mapping | citation_supported | e9:273:376, e9:379:405 |
| `/experience/0/responsibilities/3` | Owning month-end and year-end close management, including journal entries, accruals, ledger scrutiny, and balance confirmations. | correct_mapping | citation_supported | e9:408:513, e9:516:538 |
| `/experience/0/responsibilities/4` | Preparing MIS, cash flow statements, and management reports for review and decision-making. | correct_mapping | citation_supported | e9:541:632 |
| `/experience/0/responsibilities/5` | Limited knowledge-level exposure to revenue tracking and overseas billing for cash flow monitoring and MIS purposes. | correct_mapping | citation_supported | e9:635:737, e9:740:753 |
| `/experience/0/responsibilities/6` | Owning preparation, reconciliation, and coordination with consultants for GST (GSTR-1, GSTR-3B) and PF, PT, and ESIC compliances, with final statutory filings handled through consultants. | correct_mapping | citation_supported | e9:756:859, e9:862:945 |
| `/experience/0/responsibilities/7` | Managing end-to-end TDS compliance, including calculations, challans, and returns. | correct_mapping | citation_supported | e9:948:957, e9:957:1030 |
| `/experience/0/responsibilities/8` | Independently managing end-to-end payroll for 120 employees, including salary processing and statutory deductions. | correct_mapping | citation_supported | e9:1033:1135, e9:1138:1149 |
| `/experience/0/responsibilities/9` | Leading audit coordination by preparing schedules, reconciliations, and statutory data for internal and external audits. | correct_mapping | citation_supported | e9:1152:1255, e9:1258:1274 |
| `/experience/0/responsibilities/10` | Acting as SPOC for finance operations and driving process improvement initiatives. | correct_mapping | citation_supported | e9:1277:1360 |
| `/experience/0/technologies` | [] | not_populated | not_populated |  |
| `/experience/1/company` | Godavari Cuts | correct_mapping | citation_supported | e10:0:25 |
| `/experience/1/role` |  | not_populated | not_populated |  |
| `/experience/1/start_date` | None | not_populated | not_populated |  |
| `/experience/1/end_date` | Dec 2023 | ambiguous | citation_supported | e8:0:18 |
| `/experience/1/duration` | Feb 2023 - Dec 2023 | ambiguous | citation_supported | e9:1360:1379 |
| `/experience/1/location` | Hyderabad | correct_mapping | citation_supported | e3:0:28 |
| `/experience/1/responsibilities/0` | Handled Accounts Payable activities, including invoice verification, vendor payment scheduling, and reconciliation of outstanding balances. | correct_mapping | citation_supported | e11:0:99, e11:102:141 |
| `/experience/1/responsibilities/1` | Prepared and maintained daily and monthly Bank Reconciliation Statements (BRS). | correct_mapping | citation_supported | e11:144:223 |
| `/experience/1/responsibilities/2` | Supported month-end activities through basic reconciliations and ledger checks. | correct_mapping | citation_supported | e11:226:305 |
| `/experience/1/responsibilities/3` | Assisted in GST data preparation and return filings, ensuring statutory compliance. | correct_mapping | citation_supported | e11:308:391 |
| `/experience/1/responsibilities/4` | Supported TDS calculations, documentation, and compliance requirements. | correct_mapping | citation_supported | e11:394:465 |
| `/experience/1/responsibilities/5` | Maintained accurate accounting records and supported statutory audits. | correct_mapping | citation_supported | e11:468:538 |
| `/experience/1/responsibilities/6` | Coordinated with vendors and internal departments to resolve discrepancies and ensure smooth financial | correct_mapping | citation_supported | e11:541:643 |
| `/experience/1/technologies` | [] | not_populated | not_populated |  |
| `/education/0/institution` | Yashwantrao Chavan Maharashtra Open University | correct_mapping | citation_supported | e15:0:46 |
| `/education/0/degree` | Master of Business Administration (MBA) | correct_mapping | citation_supported | e16:0:49 |
| `/education/0/field_of_study` | Finance | correct_mapping | citation_supported | e0:13:125 |
| `/education/0/start_year` | July 2024 | correct_mapping | citation_supported | e17:0:53 |
| `/education/0/graduation_year` | June 2026 | correct_mapping | citation_supported | e17:0:53 |
| `/education/0/grade_or_gpa` | None | not_populated | not_populated |  |
| `/education/1/institution` |  | not_populated | not_populated |  |
| `/education/1/degree` | Bachelor of Commerce (B.Com) | correct_mapping | citation_supported | e18:2:51 |
| `/education/1/field_of_study` | Finance & Accounts | correct_mapping | citation_supported | e18:2:51 |
| `/education/1/start_year` | July 2021 | correct_mapping | citation_supported | e19:0:21 |
| `/education/1/graduation_year` | June 2024 | correct_mapping | citation_supported | e19:0:21 |
| `/education/1/grade_or_gpa` | None | not_populated | not_populated |  |
| `/certifications` | [] | not_populated | not_populated |  |
| `/projects` | [] | not_populated | not_populated |  |
| `/languages` | [] | not_populated | not_populated |  |

## Predeclared critical opportunities

Degree plus field_of_study may satisfy one reference degree opportunity. Original month-year strings are accepted when the expected year matches; this does not remove date-association ambiguity. Country codes, punctuation/whitespace, labels such as CGPA and enclosing lab/organization context are normalized as documented in the main report.

| Reference | Target | Expected source fact | Actual value | Result |
|---|---|---|---|---|
| f001 | root.contact.full_name | Ajay Bandagi | Ajay Bandagi | correct_mapping |
| f002 | root.contact.email | ajaybandagi1998@gmail.com | ajaybandagi1998@gmail.com | correct_mapping |
| f003 | root.contact.phone | +91 9604657161 | +91 9604657161 | correct_mapping |
| f004 | root.professional_title | Senior Accounts Executive | Senior Accounts Executive | correct_mapping |
| f005 | root.total_experience_years | 3.5 | 3.5 | correct_mapping |
| f006 | experience.company | Vigocare Private Limited | Vigocare Private Limited | correct_mapping |
| f007 | experience.role | Senior Accounts Executive – Finance Operations & Statutory Compliance | Senior Accounts Executive – Finance Operations & Statutory Compliance | correct_mapping |
| f008 | experience.start_date | Dec 2023 | Dec 2023 | correct_mapping |
| f009 | experience.end_date | Present | Present | correct_mapping |
| f010 | experience.company | Godavari Cuts | Godavari Cuts | correct_mapping |
| f011 | experience.start_date | Feb 2023 | None | ambiguous |
| f012 | experience.end_date | Dec 2023 | Dec 2023 | ambiguous |
| f013 | education.degree | Master of Business Administration (MBA) – Finance | Master of Business Administration (MBA) | correct_mapping |
| f014 | education.institution | Yashwantrao Chavan Maharashtra Open University | Yashwantrao Chavan Maharashtra Open University | correct_mapping |
| f015 | education.start_year | 2024 | July 2024 | correct_mapping |
| f016 | education.graduation_year | 2026 | June 2026 | correct_mapping |
| f017 | education.degree | Bachelor of Commerce (B.Com) – Finance & Accounts | Bachelor of Commerce (B.Com) | correct_mapping |
| f018 | education.start_year | 2021 | July 2021 | correct_mapping |
| f019 | education.graduation_year | 2024 | June 2024 | correct_mapping |

## Provider missing-information statements

These are provider claims, not independent truth. Compare with field-evaluation.json for analyst disagreements and actual mapping omissions.

```json
[
  {
    "path": "/experience/1/role",
    "reason": "not_in_source",
    "detail": "No job title appears between the Godavari Cuts organization line and its responsibilities bullets; the role is separated and not captured.",
    "source_ids": [
      "e10:0:25",
      "e11:0:99"
    ]
  },
  {
    "path": "/experience/1/start_date",
    "reason": "ambiguous_source",
    "detail": "The date range 'Feb 2023 - Dec 2023' appears at the end of the Vigocare responsibilities block rather than adjacent to the Godavari Cuts entry; association to Godavari Cuts is inferred from document order/segmentation, not explicit placement.",
    "source_ids": [
      "e9:1360:1379",
      "e10:0:25"
    ]
  },
  {
    "path": "/education/1/institution",
    "reason": "not_in_source",
    "detail": "No institution name appears in the education blocks for the B.Com entry; only degree and dates are present.",
    "source_ids": [
      "e18:2:51",
      "e19:0:21"
    ]
  },
  {
    "path": "/education/0/start_year and /education/0/graduation_year",
    "reason": "ambiguous_source",
    "detail": "Raw values 'July 2024' and 'June 2026' with 'Pursuing | Expected Completion' are placed in year fields as extracted date text, not normalized years; degree is in progress.",
    "source_ids": [
      "e17:0:53"
    ]
  },
  {
    "path": "/contact/linkedin_url",
    "reason": "not_in_source",
    "detail": "Only the bare handle 'ajaybandagi' appears with no URL or platform label; no LinkedIn URL is stated in source.",
    "source_ids": [
      "e4:0:11"
    ]
  },
  {
    "path": "/languages",
    "reason": "not_in_source",
    "detail": "No spoken languages are listed in the source.",
    "source_ids": []
  },
  {
    "path": "/certifications",
    "reason": "not_in_source",
    "detail": "No certifications, licenses, or courses are listed in the source.",
    "source_ids": []
  },
  {
    "path": "/projects",
    "reason": "not_in_source",
    "detail": "No dedicated projects section or project entries are present.",
    "source_ids": []
  },
  {
    "path": "/skills/technical_skills",
    "reason": "not_in_source",
    "detail": "No programming languages, algorithms, or core engineering skills are listed; skills are finance-domain and tooling.",
    "source_ids": []
  },
  {
    "path": "/skills/soft_skills",
    "reason": "not_in_source",
    "detail": "No explicit soft-skill list is provided; soft attributes in summary were not treated as enumerated skills.",
    "source_ids": []
  }
]
```

## Provider upstream observations

```json
[
  "Block e9 intermixes Vigocare responsibilities, bullet separators, and the date range 'Feb 2023 - Dec 2023'; the Godavari Cuts role title and its date line appear detached or missing, and the date range is attached to the previous employer's block.",
  "The Godavari Cuts entry lacks an explicit role/designation, leaving /experience/1/role unknown rather than invented.",
  "The B.Com education record has dates (July 2021 - June 2024) but no institution name; institution left empty for that record.",
  "The summary block uses local category 'experience' and other blocks are 'needs_review', but textual role is used for professional_title; local categories are not treated as authoritative.",
  "The LinkedIn-style handle 'ajaybandagi' is stored with no URL or platform label; it is not mapped to linkedin_url because no URL was stated.",
  "No awards, memberships, or publications were found in the provided source blocks.",
  "All populated fields were extracted only from the provided source blocks; no original PDF layout or external verification was performed."
]
```
