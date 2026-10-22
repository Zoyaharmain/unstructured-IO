# A Madhavi.pdf — five-resume schema pilot

Selection: Three-page business-analysis resume; four employers, explicit client/project distinctions, dates, certificates and page-spanning responsibilities.

Saved input: `reports/pilot100-additional-llm-20261021-025143/deepseek/documents/759f6eb8c9035adbbfcc.json` → `local_sections`. Pages: [1, 2, 3]. Source blocks: 112. No new extraction/block detection was run. Original PDF was not independently examined for this evaluation.

Correctly distinguishes four employers and their roles/date ranges, keeps the Tech Mahindra client separate, restores NPCI responsibilities mislabeled as projects, and maps certification issuers/years where stated. Candidate residence is correctly not inferred from workplace Hyderabad. Flat all_skills items lack field citations. The source Tag Mapping/IMPS work item is omitted from the target responsibilities and projects. No definite incorrect populated value was identified against the saved blocks in this sample.

- Critical-field agreement proxy: **30/30 = 100.0%**.
- Same-block local heuristic baseline on the same critical set: **16/30**.
- Raw field citation contract: **123/158 = 77.85%**.
- Populated-value source-block assessment: {"correct_mapping": 158, "not_populated": 52, "missing_assignment": 1}.
- Human-verified/PDF-verified accuracy: **not established**.

## Complete mapping output

[Mapping JSON](mapping.json) · [Unmodified provider mapping and citations](mapping-raw.json) · [Full provider envelope/usage](response-envelope.json) · [Saved source blocks](source-blocks.md) · [Every evaluated field](field-evaluation.json)

```json
{
  "contact": {
    "full_name": "A MADHAVI",
    "email": "madhavi.aradhyula03@gmail.com",
    "phone": "+91-9494916311",
    "location": null,
    "linkedin_url": "linkedin.com/in/madhavi-av-a3ba34b0",
    "github_url": null,
    "portfolio_url": null
  },
  "professional_title": "Business Analyst",
  "summary": "Results-driven professional with 8 years of experience in business analysis, product ownership, and quality assurance within the digital payments industry. Hands-on exposure to requirement gathering, writing user stories, acceptance criteria, and functional documentation (BRD/FSD). Experienced in collaborating with stakeholders and technical teams to support gap analysis, process flows, and payment system implementations. Currently enhancing BA expertise while leveraging strong payments domain knowledge and Agile/Scrum experience to bridge business and technology needs effectively. Experienced in digital payments systems, including cards (ATM & POS),Tokenization, IMPS, UPI, AEPS, NEFT, RTGS, SWIFT, and cross-border payment solutions, with hands-on knowledge of transaction flows, clearing and Settlement.",
  "total_experience_years": 8.0,
  "skills": {
    "technical_skills": [
      "ISO8583",
      "ISO20022 XML",
      "BPMN"
    ],
    "tools_and_platforms": [
      "Linux",
      "Windows",
      "FINSIM",
      "BOSS",
      "MSGSIM",
      "T3",
      "Postman",
      "Oracle",
      "Postgres",
      "Redis",
      "Cassandra",
      "Kafka",
      "IST Switch",
      "Bharat Switch",
      "Nexus",
      "JIRA",
      "ALM",
      "Excel",
      "Apache Tomcat9",
      "Nginx",
      "Confluence",
      "Teams",
      "Draw.io",
      "MS Visio"
    ],
    "domain_and_functional": [
      "Business Analysis & Requirement Gathering",
      "BRD/FSD Documentation and Writing User Stories",
      "Stakeholder & Vendor Management",
      "Process Modelling (AS-IS / TO-BE)",
      "Agile & Scrum (CSPO Certified)",
      "Payment Switch Migration",
      "Regulatory & Compliance Requirements",
      "Product Ownership & Backlog Management"
    ],
    "soft_skills": [],
    "all_skills": [
      "ISO8583",
      "ISO20022 XML",
      "BPMN",
      "Linux",
      "Windows",
      "FINSIM",
      "BOSS",
      "MSGSIM",
      "T3",
      "Postman",
      "Oracle",
      "Postgres",
      "Redis",
      "Cassandra",
      "Kafka",
      "IST Switch",
      "Bharat Switch",
      "Nexus",
      "JIRA",
      "ALM",
      "Excel",
      "Apache Tomcat9",
      "Nginx",
      "Confluence",
      "Teams",
      "Draw.io",
      "MS Visio",
      "Business Analysis & Requirement Gathering",
      "BRD/FSD Documentation and Writing User Stories",
      "Stakeholder & Vendor Management",
      "Process Modelling (AS-IS / TO-BE)",
      "Agile & Scrum (CSPO Certified)",
      "Payment Switch Migration",
      "Regulatory & Compliance Requirements",
      "Product Ownership & Backlog Management"
    ]
  },
  "experience": [
    {
      "company": "Tech Mahindra",
      "role": "Business Analyst cum UAT Tester",
      "start_date": "Aug 2022",
      "end_date": "Present",
      "duration": "Aug 2022 – Present",
      "location": "Hyderabad",
      "responsibilities": [
        "Gathered, analyzed, and documented business requirements.",
        "Converted requirements into user stories, Prepared functional workflows.",
        "Executed test plans and validated transaction processing across payment systems for Authorization flows which includes ATM,POS,MDES transactions.",
        "Supported QA and Regression team for testing after each build deployment.",
        "Facilitated defect triage sessions with development teams.",
        "Provided daily test execution status updates to senior management.",
        "Participate in Scrum meetings and backlog grooming.",
        "Worked on Cross Border Payments for Cards and Non-Card based Payments.",
        "Trained new hires on Payment Switch Migration Flows.",
        "Worked on Payment Rails like Cards, SWIFT (MT103,MT202,MT202COV)."
      ],
      "technologies": []
    },
    {
      "company": "Pine Labs",
      "role": "Sr QA Cum Product Owner",
      "start_date": "Jan 2022",
      "end_date": "June 2022",
      "duration": "Jan 2022 – June 2022",
      "location": "Hyderabad",
      "responsibilities": [
        "Owned product backlog and prioritized features based on business needs.",
        "Collaborated with development teams to define functional specifications.",
        "Led end-to-end integration testing for BNPL solutions.",
        "Managed stakeholder expectations and communication.",
        "Oversaw UAT and production deployment.",
        "Conducted root cause analysis on production issues."
      ],
      "technologies": []
    },
    {
      "company": "Capgemini",
      "role": "Consultant",
      "start_date": "May 2021",
      "end_date": "Dec 2021",
      "duration": "May 2021 – Dec 2021",
      "location": "Hyderabad",
      "responsibilities": [
        "Gathered and analyzed business requirements, translating them into BRDs, FSDs, user stories, and acceptance criteria for core banking modules and retail payment workflows.",
        "Conducted gap analysis, impact assessments, and process mapping to support system modernization and compliance initiatives.",
        "Collaborated with technical teams, business stakeholders, and third-party vendors to ensure accurate requirement translation and solution alignment.",
        "Assisted in UAT, functional testing, and validation of transactions across SWIFT MT103,MT202,MT202COV, NEFT, and RTGS payment systems.",
        "Created process diagrams, flowcharts, and documentation to communicate workflows, system changes, and technical designs effectively."
      ],
      "technologies": []
    },
    {
      "company": "National Payments Corporation of India",
      "role": "Senior Associate",
      "start_date": "Jan 2017",
      "end_date": "May 2021",
      "duration": "Jan 2017 – May 2021",
      "location": "Hyderabad",
      "responsibilities": [
        "Gathered, analyzed, and documented business, functional, and technical requirements for payment switch migration projects.",
        "Performed gap analysis between legacy and new payment switch systems to identify discrepancies.",
        "Designed AS-IS and TO-BE process flows for transaction authorization, routing, clearing, settlement, and reconciliation.",
        "Defined business rules for transaction life-cycles, authorization, clearing, and settlement workflows.",
        "Supported payment gateway integration's, API-based solutions, and fraud detection mechanisms.",
        "Conducted load and stress testing to validate switch performance under peak transaction volumes.",
        "Coordinated production environment setup and facilitated handover sessions with production teams during switch migration.",
        "Collaborated with vendors to clarify requirements, ensuring on-time delivery of system integration's.",
        "Designed and executed functional and integration test cases, validating ISO8583 message formats and end-to-end flows.",
        "Managed defects using JIRA and Excel, ensuring timely resolution and retesting.",
        "Provided post-migration support by monitoring transaction success rates, system performance, and error handling.",
        "Conducted root cause analysis (RCA) on production issues, implementing corrective actions.",
        "Worked on IMPS migration from ISO8583 protocol to ISO20022 XML protocol(similar).",
        "Acted as a liaison with banks, resolving technical queries and suggesting improvements for product efficiency."
      ],
      "technologies": []
    }
  ],
  "education": [
    {
      "institution": "Gayatri Vidya Parishad, Andhra University, Visakhapatnam, India",
      "degree": "Bachelor of Engineering",
      "field_of_study": "ECE",
      "start_year": null,
      "graduation_year": "2015",
      "grade_or_gpa": null
    }
  ],
  "certifications": [
    {
      "name": "Certified Scrum Product Owner (CSPO)",
      "issuer": null,
      "issue_year": "2025"
    },
    {
      "name": "Fundamentals of SWIFT MT & ISO20022",
      "issuer": "MVLCO",
      "issue_year": "2020"
    },
    {
      "name": "Trained in Embedded Systems",
      "issuer": "Vector India",
      "issue_year": "2016"
    }
  ],
  "projects": [
    {
      "name": "SMT-Validator and Mastercard Nexus Switch Migration",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "PayLater Mastercard Installments (BNPL)",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Core Banking & Retail Processing System",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Upgradation of AEPS Services from V2.0 to V2.5",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "IMPS Service Migration from IST to Bharat Switch(UPI Common Code)",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Integration of FRM Module",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Migration of Payment Switch from ITM to IST",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Implementation of LM Service for ATM, IMPS, and AEPS",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Implementation of Fraud Detection system",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    },
    {
      "name": "Certification Testing with member banks",
      "description": null,
      "role": null,
      "technologies": [],
      "url": null
    }
  ],
  "languages": []
}
```

## Field-by-field results

`correct_mapping` is provisional AI analyst source-block agreement, not independent human truth. `citation_error` can coexist with correct value content. Analyst source references supplement the evaluation; they do not retroactively repair the raw provider response. Null/empty fields are retained for inspection; absence and ambiguity reasons are in the JSON. The CSV/JSON contain full values and exact quote text; the table abbreviates long values.

| Field | LLM value | Mapping assessment | Raw citation assessment | Analyst source IDs |
|---|---|---|---|---|
| `/contact/full_name` | A MADHAVI | correct_mapping | citation_supported | e0:0:9 |
| `/contact/email` | madhavi.aradhyula03@gmail.com | correct_mapping | citation_supported | e1:0:29 |
| `/contact/phone` | +91-9494916311 | correct_mapping | citation_supported | e2:0:14 |
| `/contact/location` | None | not_populated | not_populated |  |
| `/contact/linkedin_url` | linkedin.com/in/madhavi-av-a3ba34b0 | correct_mapping | citation_supported | e3:0:35 |
| `/contact/github_url` | None | not_populated | not_populated |  |
| `/contact/portfolio_url` | None | not_populated | not_populated |  |
| `/professional_title` | Business Analyst | correct_mapping | citation_supported | e4:0:22 |
| `/summary` | Results-driven professional with 8 years of experience in business analysis, product ownership, and quality assurance within the digital payments industry. Hands-on exposure to requirement gathering, writing user stories, acceptance criteria, and fun… | correct_mapping | citation_supported | e5:21:139, e5:139:254, e5:254:371, e5:371:486, e5:486:597, e5:597:716, e5:716:824, e5:824:835 |
| `/total_experience_years` | 8.0 | correct_mapping | citation_supported | e5:21:139 |
| `/skills/technical_skills/0` | ISO8583 | correct_mapping | citation_supported | e71:0:111 |
| `/skills/technical_skills/1` | ISO20022 XML | correct_mapping | citation_supported | e75:0:81 |
| `/skills/technical_skills/2` | BPMN | correct_mapping | citation_supported | e22:0:30 |
| `/skills/tools_and_platforms/0` | Linux | correct_mapping | citation_supported | e14:19:52 |
| `/skills/tools_and_platforms/1` | Windows | correct_mapping | citation_supported | e14:19:52 |
| `/skills/tools_and_platforms/2` | FINSIM | correct_mapping | citation_supported | e15:0:48 |
| `/skills/tools_and_platforms/3` | BOSS | correct_mapping | citation_supported | e15:0:48 |
| `/skills/tools_and_platforms/4` | MSGSIM | correct_mapping | citation_supported | e15:0:48 |
| `/skills/tools_and_platforms/5` | T3 | correct_mapping | citation_supported | e15:0:48 |
| `/skills/tools_and_platforms/6` | Postman | correct_mapping | citation_supported | e15:0:48 |
| `/skills/tools_and_platforms/7` | Oracle | correct_mapping | citation_supported | e16:0:44 |
| `/skills/tools_and_platforms/8` | Postgres | correct_mapping | citation_supported | e16:0:44 |
| `/skills/tools_and_platforms/9` | Redis | correct_mapping | citation_supported | e16:0:44 |
| `/skills/tools_and_platforms/10` | Cassandra | correct_mapping | citation_supported | e16:0:44 |
| `/skills/tools_and_platforms/11` | Kafka | correct_mapping | citation_supported | e17:0:23 |
| `/skills/tools_and_platforms/12` | IST Switch | correct_mapping | citation_supported | e18:0:50 |
| `/skills/tools_and_platforms/13` | Bharat Switch | correct_mapping | citation_supported | e18:0:50 |
| `/skills/tools_and_platforms/14` | Nexus | correct_mapping | citation_supported | e18:0:50 |
| `/skills/tools_and_platforms/15` | JIRA | correct_mapping | citation_supported | e19:0:39 |
| `/skills/tools_and_platforms/16` | ALM | correct_mapping | citation_supported | e19:0:39 |
| `/skills/tools_and_platforms/17` | Excel | correct_mapping | citation_supported | e19:0:39 |
| `/skills/tools_and_platforms/18` | Apache Tomcat9 | correct_mapping | citation_supported | e20:0:35 |
| `/skills/tools_and_platforms/19` | Nginx | correct_mapping | citation_supported | e20:0:35 |
| `/skills/tools_and_platforms/20` | Confluence | correct_mapping | citation_supported | e21:0:38 |
| `/skills/tools_and_platforms/21` | Teams | correct_mapping | citation_supported | e5:254:371 |
| `/skills/tools_and_platforms/22` | Draw.io | correct_mapping | citation_supported | e22:0:30 |
| `/skills/tools_and_platforms/23` | MS Visio | correct_mapping | citation_supported | e22:0:30 |
| `/skills/domain_and_functional/0` | Business Analysis & Requirement Gathering | correct_mapping | citation_supported | e6:19:60 |
| `/skills/domain_and_functional/1` | BRD/FSD Documentation and Writing User Stories | correct_mapping | citation_supported | e7:0:46 |
| `/skills/domain_and_functional/2` | Stakeholder & Vendor Management | correct_mapping | citation_supported | e8:0:31 |
| `/skills/domain_and_functional/3` | Process Modelling (AS-IS / TO-BE) | correct_mapping | citation_supported | e9:0:33 |
| `/skills/domain_and_functional/4` | Agile & Scrum (CSPO Certified) | correct_mapping | citation_supported | e10:0:30 |
| `/skills/domain_and_functional/5` | Payment Switch Migration | correct_mapping | citation_supported | e11:0:24 |
| `/skills/domain_and_functional/6` | Regulatory & Compliance Requirements | correct_mapping | citation_supported | e12:0:36 |
| `/skills/domain_and_functional/7` | Product Ownership & Backlog Management | correct_mapping | citation_supported | e13:0:38 |
| `/skills/soft_skills` | [] | not_populated | not_populated |  |
| `/skills/all_skills/0` | ISO8583 | correct_mapping | citation_error | e71:0:111 |
| `/skills/all_skills/1` | ISO20022 XML | correct_mapping | citation_error | e75:0:81 |
| `/skills/all_skills/2` | BPMN | correct_mapping | citation_error | e22:0:30 |
| `/skills/all_skills/3` | Linux | correct_mapping | citation_error | e14:19:52 |
| `/skills/all_skills/4` | Windows | correct_mapping | citation_error | e14:19:52 |
| `/skills/all_skills/5` | FINSIM | correct_mapping | citation_error | e15:0:48 |
| `/skills/all_skills/6` | BOSS | correct_mapping | citation_error | e15:0:48 |
| `/skills/all_skills/7` | MSGSIM | correct_mapping | citation_error | e15:0:48 |
| `/skills/all_skills/8` | T3 | correct_mapping | citation_error | e15:0:48 |
| `/skills/all_skills/9` | Postman | correct_mapping | citation_error | e15:0:48 |
| `/skills/all_skills/10` | Oracle | correct_mapping | citation_error | e16:0:44 |
| `/skills/all_skills/11` | Postgres | correct_mapping | citation_error | e16:0:44 |
| `/skills/all_skills/12` | Redis | correct_mapping | citation_error | e16:0:44 |
| `/skills/all_skills/13` | Cassandra | correct_mapping | citation_error | e16:0:44 |
| `/skills/all_skills/14` | Kafka | correct_mapping | citation_error | e17:0:23 |
| `/skills/all_skills/15` | IST Switch | correct_mapping | citation_error | e18:0:50 |
| `/skills/all_skills/16` | Bharat Switch | correct_mapping | citation_error | e18:0:50 |
| `/skills/all_skills/17` | Nexus | correct_mapping | citation_error | e18:0:50 |
| `/skills/all_skills/18` | JIRA | correct_mapping | citation_error | e19:0:39 |
| `/skills/all_skills/19` | ALM | correct_mapping | citation_error | e19:0:39 |
| `/skills/all_skills/20` | Excel | correct_mapping | citation_error | e19:0:39 |
| `/skills/all_skills/21` | Apache Tomcat9 | correct_mapping | citation_error | e20:0:35 |
| `/skills/all_skills/22` | Nginx | correct_mapping | citation_error | e20:0:35 |
| `/skills/all_skills/23` | Confluence | correct_mapping | citation_error | e21:0:38 |
| `/skills/all_skills/24` | Teams | correct_mapping | citation_error | e5:254:371 |
| `/skills/all_skills/25` | Draw.io | correct_mapping | citation_error | e22:0:30 |
| `/skills/all_skills/26` | MS Visio | correct_mapping | citation_error | e22:0:30 |
| `/skills/all_skills/27` | Business Analysis & Requirement Gathering | correct_mapping | citation_error | e6:19:60 |
| `/skills/all_skills/28` | BRD/FSD Documentation and Writing User Stories | correct_mapping | citation_error | e7:0:46 |
| `/skills/all_skills/29` | Stakeholder & Vendor Management | correct_mapping | citation_error | e8:0:31 |
| `/skills/all_skills/30` | Process Modelling (AS-IS / TO-BE) | correct_mapping | citation_error | e9:0:33 |
| `/skills/all_skills/31` | Agile & Scrum (CSPO Certified) | correct_mapping | citation_error | e10:0:30 |
| `/skills/all_skills/32` | Payment Switch Migration | correct_mapping | citation_error | e11:0:24 |
| `/skills/all_skills/33` | Regulatory & Compliance Requirements | correct_mapping | citation_error | e12:0:36 |
| `/skills/all_skills/34` | Product Ownership & Backlog Management | correct_mapping | citation_error | e13:0:38 |
| `/experience/0/company` | Tech Mahindra | correct_mapping | citation_supported | e24:0:58 |
| `/experience/0/role` | Business Analyst cum UAT Tester | correct_mapping | citation_supported | e24:0:58 |
| `/experience/0/start_date` | Aug 2022 | correct_mapping | citation_supported | e24:58:153 |
| `/experience/0/end_date` | Present | correct_mapping | citation_supported | e24:58:153 |
| `/experience/0/duration` | Aug 2022 – Present | correct_mapping | citation_supported | e24:58:153 |
| `/experience/0/location` | Hyderabad | correct_mapping | citation_supported | e24:58:153 |
| `/experience/0/responsibilities/0` | Gathered, analyzed, and documented business requirements. | correct_mapping | citation_supported | e27:0:57 |
| `/experience/0/responsibilities/1` | Converted requirements into user stories, Prepared functional workflows. | correct_mapping | citation_supported | e28:0:72 |
| `/experience/0/responsibilities/2` | Executed test plans and validated transaction processing across payment systems for Authorization flows which includes ATM,POS,MDES transactions. | correct_mapping | citation_supported | e29:0:110, e29:110:145 |
| `/experience/0/responsibilities/3` | Supported QA and Regression team for testing after each build deployment. | correct_mapping | citation_supported | e30:0:73 |
| `/experience/0/responsibilities/4` | Facilitated defect triage sessions with development teams. | correct_mapping | citation_supported | e31:0:58 |
| `/experience/0/responsibilities/5` | Provided daily test execution status updates to senior management. | correct_mapping | citation_supported | e32:0:66 |
| `/experience/0/responsibilities/6` | Participate in Scrum meetings and backlog grooming. | correct_mapping | citation_supported | e33:0:51 |
| `/experience/0/responsibilities/7` | Worked on Cross Border Payments for Cards and Non-Card based Payments. | correct_mapping | citation_supported | e34:0:70 |
| `/experience/0/responsibilities/8` | Trained new hires on Payment Switch Migration Flows. | correct_mapping | citation_supported | e35:0:52 |
| `/experience/0/responsibilities/9` | Worked on Payment Rails like Cards, SWIFT (MT103,MT202,MT202COV). | correct_mapping | citation_supported | e36:0:65 |
| `/experience/0/technologies` | [] | not_populated | not_populated |  |
| `/experience/1/company` | Pine Labs | correct_mapping | citation_supported | e37:0:46 |
| `/experience/1/role` | Sr QA Cum Product Owner | correct_mapping | citation_supported | e37:0:46 |
| `/experience/1/start_date` | Jan 2022 | correct_mapping | citation_supported | e37:46:149 |
| `/experience/1/end_date` | June 2022 | correct_mapping | citation_supported | e37:46:149 |
| `/experience/1/duration` | Jan 2022 – June 2022 | correct_mapping | citation_supported | e37:46:149 |
| `/experience/1/location` | Hyderabad | correct_mapping | citation_supported | e24:58:153 |
| `/experience/1/responsibilities/0` | Owned product backlog and prioritized features based on business needs. | correct_mapping | citation_supported | e39:0:71 |
| `/experience/1/responsibilities/1` | Collaborated with development teams to define functional specifications. | correct_mapping | citation_supported | e40:0:72 |
| `/experience/1/responsibilities/2` | Led end-to-end integration testing for BNPL solutions. | correct_mapping | citation_supported | e41:0:54 |
| `/experience/1/responsibilities/3` | Managed stakeholder expectations and communication. | correct_mapping | citation_supported | e42:0:51 |
| `/experience/1/responsibilities/4` | Oversaw UAT and production deployment. | correct_mapping | citation_supported | e43:0:38 |
| `/experience/1/responsibilities/5` | Conducted root cause analysis on production issues. | correct_mapping | citation_supported | e44:0:51 |
| `/experience/1/technologies` | [] | not_populated | not_populated |  |
| `/experience/2/company` | Capgemini | correct_mapping | citation_supported | e45:0:33 |
| `/experience/2/role` | Consultant | correct_mapping | citation_supported | e45:0:33 |
| `/experience/2/start_date` | May 2021 | correct_mapping | citation_supported | e45:33:135 |
| `/experience/2/end_date` | Dec 2021 | correct_mapping | citation_supported | e45:33:135 |
| `/experience/2/duration` | May 2021 – Dec 2021 | correct_mapping | citation_supported | e45:33:135 |
| `/experience/2/location` | Hyderabad | correct_mapping | citation_supported | e24:58:153 |
| `/experience/2/responsibilities/0` | Gathered and analyzed business requirements, translating them into BRDs, FSDs, user stories, and acceptance criteria for core banking modules and retail payment workflows. | correct_mapping | citation_supported | e47:0:108, e47:108:171 |
| `/experience/2/responsibilities/1` | Conducted gap analysis, impact assessments, and process mapping to support system modernization and compliance initiatives. | correct_mapping | citation_supported | e48:0:100, e48:100:123 |
| `/experience/2/responsibilities/2` | Collaborated with technical teams, business stakeholders, and third-party vendors to ensure accurate requirement translation and solution alignment. | correct_mapping | citation_supported | e49:0:113, e49:113:148 |
| `/experience/2/responsibilities/3` | Assisted in UAT, functional testing, and validation of transactions across SWIFT MT103,MT202,MT202COV, NEFT, and RTGS payment systems. | correct_mapping | citation_supported | e50:0:109, e50:109:134 |
| `/experience/2/responsibilities/4` | Created process diagrams, flowcharts, and documentation to communicate workflows, system changes, and technical designs effectively. | correct_mapping | citation_supported | e51:0:102, e51:102:132 |
| `/experience/2/technologies` | [] | not_populated | not_populated |  |
| `/experience/3/company` | National Payments Corporation of India | correct_mapping | citation_supported | e52:0:68 |
| `/experience/3/role` | Senior Associate | correct_mapping | citation_supported | e52:0:68 |
| `/experience/3/start_date` | Jan 2017 | correct_mapping | citation_supported | e52:68:119 |
| `/experience/3/end_date` | May 2021 | correct_mapping | citation_supported | e45:33:135 |
| `/experience/3/duration` | Jan 2017 – May 2021 | correct_mapping | citation_supported | e52:68:119 |
| `/experience/3/location` | Hyderabad | correct_mapping | citation_supported | e24:58:153 |
| `/experience/3/responsibilities/0` | Gathered, analyzed, and documented business, functional, and technical requirements for payment switch migration projects. | correct_mapping | citation_supported | e63:0:103, e63:103:122 |
| `/experience/3/responsibilities/1` | Performed gap analysis between legacy and new payment switch systems to identify discrepancies. | correct_mapping | citation_supported | e64:0:95 |
| `/experience/3/responsibilities/2` | Designed AS-IS and TO-BE process flows for transaction authorization, routing, clearing, settlement, and reconciliation. | correct_mapping | citation_supported | e65:0:105, e65:105:120 |
| `/experience/3/responsibilities/3` | Defined business rules for transaction life-cycles, authorization, clearing, and settlement workflows. | correct_mapping | citation_supported | e66:0:102 |
| `/experience/3/responsibilities/4` | Supported payment gateway integration's, API-based solutions, and fraud detection mechanisms. | correct_mapping | citation_supported | e67:0:93 |
| `/experience/3/responsibilities/5` | Conducted load and stress testing to validate switch performance under peak transaction volumes. | correct_mapping | citation_supported | e68:0:96 |
| `/experience/3/responsibilities/6` | Coordinated production environment setup and facilitated handover sessions with production teams during switch migration. | correct_mapping | citation_supported | e69:0:111, e69:111:121 |
| `/experience/3/responsibilities/7` | Collaborated with vendors to clarify requirements, ensuring on-time delivery of system integration's. | correct_mapping | citation_supported | e70:0:101 |
| `/experience/3/responsibilities/8` | Designed and executed functional and integration test cases, validating ISO8583 message formats and end-to-end flows. | correct_mapping | citation_supported | e71:0:111, e71:111:117 |
| `/experience/3/responsibilities/9` | Managed defects using JIRA and Excel, ensuring timely resolution and retesting. | correct_mapping | citation_supported | e72:0:79 |
| `/experience/3/responsibilities/10` | Provided post-migration support by monitoring transaction success rates, system performance, and error handling. | correct_mapping | citation_supported | e73:0:112 |
| `/experience/3/responsibilities/11` | Conducted root cause analysis (RCA) on production issues, implementing corrective actions. | correct_mapping | citation_supported | e74:0:90 |
| `/experience/3/responsibilities/12` | Worked on IMPS migration from ISO8583 protocol to ISO20022 XML protocol(similar). | correct_mapping | citation_supported | e75:0:81 |
| `/experience/3/responsibilities/13` | Acted as a liaison with banks, resolving technical queries and suggesting improvements for product efficiency. | correct_mapping | citation_supported | e76:0:110 |
| `/experience/3/technologies` | [] | not_populated | not_populated |  |
| `/education/0/institution` | Gayatri Vidya Parishad, Andhra University, Visakhapatnam, India | correct_mapping | citation_supported | e80:10:113 |
| `/education/0/degree` | Bachelor of Engineering | correct_mapping | citation_supported | e80:10:113 |
| `/education/0/field_of_study` | ECE | correct_mapping | citation_supported | e80:10:113 |
| `/education/0/start_year` | None | not_populated | not_populated |  |
| `/education/0/graduation_year` | 2015 | correct_mapping | citation_supported | e80:10:113 |
| `/education/0/grade_or_gpa` | None | not_populated | not_populated |  |
| `/certifications/0/name` | Certified Scrum Product Owner (CSPO) | correct_mapping | citation_supported | e77:17:59 |
| `/certifications/0/issuer` | None | not_populated | not_populated |  |
| `/certifications/0/issue_year` | 2025 | correct_mapping | citation_supported | e77:17:59 |
| `/certifications/1/name` | Fundamentals of SWIFT MT & ISO20022 | correct_mapping | citation_supported | e78:0:49 |
| `/certifications/1/issuer` | MVLCO | correct_mapping | citation_supported | e78:0:49 |
| `/certifications/1/issue_year` | 2020 | correct_mapping | citation_supported | e78:0:49 |
| `/certifications/2/name` | Trained in Embedded Systems | correct_mapping | citation_supported | e79:0:48 |
| `/certifications/2/issuer` | Vector India | correct_mapping | citation_supported | e79:0:48 |
| `/certifications/2/issue_year` | 2016 | correct_mapping | citation_supported | e79:0:48 |
| `/projects/0/name` | SMT-Validator and Mastercard Nexus Switch Migration | correct_mapping | citation_supported | e24:58:153, e25:0:37 |
| `/projects/0/description` | None | not_populated | not_populated |  |
| `/projects/0/role` | None | not_populated | not_populated |  |
| `/projects/0/technologies` | [] | not_populated | not_populated |  |
| `/projects/0/url` | None | not_populated | not_populated |  |
| `/projects/1/name` | PayLater Mastercard Installments (BNPL) | correct_mapping | citation_supported | e37:46:149 |
| `/projects/1/description` | None | not_populated | not_populated |  |
| `/projects/1/role` | None | not_populated | not_populated |  |
| `/projects/1/technologies` | [] | not_populated | not_populated |  |
| `/projects/1/url` | None | not_populated | not_populated |  |
| `/projects/2/name` | Core Banking & Retail Processing System | correct_mapping | citation_supported | e45:33:135 |
| `/projects/2/description` | None | not_populated | not_populated |  |
| `/projects/2/role` | None | not_populated | not_populated |  |
| `/projects/2/technologies` | [] | not_populated | not_populated |  |
| `/projects/2/url` | None | not_populated | not_populated |  |
| `/projects/3/name` | Upgradation of AEPS Services from V2.0 to V2.5 | correct_mapping | citation_supported | e54:0:46 |
| `/projects/3/description` | None | not_populated | not_populated |  |
| `/projects/3/role` | None | not_populated | not_populated |  |
| `/projects/3/technologies` | [] | not_populated | not_populated |  |
| `/projects/3/url` | None | not_populated | not_populated |  |
| `/projects/4/name` | IMPS Service Migration from IST to Bharat Switch(UPI Common Code) | correct_mapping | citation_supported | e55:0:65 |
| `/projects/4/description` | None | not_populated | not_populated |  |
| `/projects/4/role` | None | not_populated | not_populated |  |
| `/projects/4/technologies` | [] | not_populated | not_populated |  |
| `/projects/4/url` | None | not_populated | not_populated |  |
| `/projects/5/name` | Integration of FRM Module | correct_mapping | citation_supported | e56:0:25 |
| `/projects/5/description` | None | not_populated | not_populated |  |
| `/projects/5/role` | None | not_populated | not_populated |  |
| `/projects/5/technologies` | [] | not_populated | not_populated |  |
| `/projects/5/url` | None | not_populated | not_populated |  |
| `/projects/6/name` | Migration of Payment Switch from ITM to IST | correct_mapping | citation_supported | e57:0:43 |
| `/projects/6/description` | None | not_populated | not_populated |  |
| `/projects/6/role` | None | not_populated | not_populated |  |
| `/projects/6/technologies` | [] | not_populated | not_populated |  |
| `/projects/6/url` | None | not_populated | not_populated |  |
| `/projects/7/name` | Implementation of LM Service for ATM, IMPS, and AEPS | correct_mapping | citation_supported | e58:0:52 |
| `/projects/7/description` | None | not_populated | not_populated |  |
| `/projects/7/role` | None | not_populated | not_populated |  |
| `/projects/7/technologies` | [] | not_populated | not_populated |  |
| `/projects/7/url` | None | not_populated | not_populated |  |
| `/projects/8/name` | Implementation of Fraud Detection system | correct_mapping | citation_supported | e59:0:40 |
| `/projects/8/description` | None | not_populated | not_populated |  |
| `/projects/8/role` | None | not_populated | not_populated |  |
| `/projects/8/technologies` | [] | not_populated | not_populated |  |
| `/projects/8/url` | None | not_populated | not_populated |  |
| `/projects/9/name` | Certification Testing with member banks | correct_mapping | citation_supported | e60:0:39 |
| `/projects/9/description` | None | not_populated | not_populated |  |
| `/projects/9/role` | None | not_populated | not_populated |  |
| `/projects/9/technologies` | [] | not_populated | not_populated |  |
| `/projects/9/url` | None | not_populated | not_populated |  |
| `/languages` | [] | not_populated | not_populated |  |
| `/experience/3/responsibilities/-` | None | missing_assignment | not_emitted | e61:0:56 |

## Predeclared critical opportunities

Degree plus field_of_study may satisfy one reference degree opportunity. Original month-year strings are accepted when the expected year matches; this does not remove date-association ambiguity. Country codes, punctuation/whitespace, labels such as CGPA and enclosing lab/organization context are normalized as documented in the main report.

| Reference | Target | Expected source fact | Actual value | Result |
|---|---|---|---|---|
| f063 | root.contact.full_name | A MADHAVI | A MADHAVI | correct_mapping |
| f064 | root.contact.email | madhavi.aradhyula03@gmail.com | madhavi.aradhyula03@gmail.com | correct_mapping |
| f065 | root.contact.phone | +91-9494916311 | +91-9494916311 | correct_mapping |
| f066 | root.professional_title | Business Analyst | Business Analyst | correct_mapping |
| f067 | root.total_experience_years | 8 | 8.0 | correct_mapping |
| f068 | experience.company | Tech Mahindra | Tech Mahindra | correct_mapping |
| f069 | experience.role | Business Analyst cum UAT Tester | Business Analyst cum UAT Tester | correct_mapping |
| f070 | experience.start_date | Aug 2022 | Aug 2022 | correct_mapping |
| f071 | experience.end_date | Present | Present | correct_mapping |
| f072 | experience.location | Hyderabad | Hyderabad | correct_mapping |
| f073 | experience.company | Pine Labs | Pine Labs | correct_mapping |
| f074 | experience.role | Sr QA Cum Product Owner | Sr QA Cum Product Owner | correct_mapping |
| f075 | experience.start_date | Jan 2022 | Jan 2022 | correct_mapping |
| f076 | experience.end_date | June 2022 | June 2022 | correct_mapping |
| f077 | experience.location | Hyderabad | Hyderabad | correct_mapping |
| f078 | experience.company | Capgemini | Capgemini | correct_mapping |
| f079 | experience.role | Consultant | Consultant | correct_mapping |
| f080 | experience.start_date | May 2021 | May 2021 | correct_mapping |
| f081 | experience.end_date | Dec 2021 | Dec 2021 | correct_mapping |
| f082 | experience.location | Hyderabad | Hyderabad | correct_mapping |
| f083 | experience.company | National Payments Corporation of India | National Payments Corporation of India | correct_mapping |
| f084 | experience.role | Senior Associate | Senior Associate | correct_mapping |
| f085 | experience.start_date | Jan 2017 | Jan 2017 | correct_mapping |
| f086 | experience.end_date | May 2021 | May 2021 | correct_mapping |
| f087 | experience.location | Hyderabad | Hyderabad | correct_mapping |
| f088 | education.degree | Bachelor of Engineering in ECE | Bachelor of Engineering | correct_mapping |
| f089 | education.graduation_year | 2015 | 2015 | correct_mapping |
| f090 | certifications.issue_year | 2025 | 2025 | correct_mapping |
| f091 | certifications.issue_year | 2020 | 2020 | correct_mapping |
| f092 | certifications.issue_year | 2016 | 2016 | correct_mapping |

## Provider missing-information statements

These are provider claims, not independent truth. Compare with field-evaluation.json for analyst disagreements and actual mapping omissions.

```json
[
  {
    "path": "/contact/location",
    "reason": "not_in_source",
    "detail": "No candidate residence location is stated; only work locations appear in experience entries.",
    "source_ids": []
  },
  {
    "path": "/contact/github_url",
    "reason": "not_in_source",
    "detail": "No GitHub URL in source.",
    "source_ids": []
  },
  {
    "path": "/contact/portfolio_url",
    "reason": "not_in_source",
    "detail": "No portfolio or personal website URL in source.",
    "source_ids": []
  },
  {
    "path": "/total_experience_years",
    "reason": "ambiguous_source",
    "detail": "Source states '8 years of experience'; treated as approximate, not computed from employment dates.",
    "source_ids": [
      "e5:21:139"
    ]
  },
  {
    "path": "/skills/soft_skills",
    "reason": "not_in_source",
    "detail": "No soft skills explicitly listed; competency items were mapped to domain_and_functional.",
    "source_ids": []
  },
  {
    "path": "/languages",
    "reason": "not_in_source",
    "detail": "No spoken languages stated; document language does not imply spoken English.",
    "source_ids": []
  },
  {
    "path": "/education/0/start_year",
    "reason": "not_in_source",
    "detail": "Only completion year 2015 is present; no start year.",
    "source_ids": [
      "e80:10:113"
    ]
  },
  {
    "path": "/education/0/degree",
    "reason": "ambiguous_source",
    "detail": "Degree line combines 'Bachelor of Engineering in ECE' with institution and year; field_of_study split out as ECE.",
    "source_ids": [
      "e80:10:113"
    ]
  },
  {
    "path": "/certifications/0/issuer",
    "reason": "not_in_source",
    "detail": "CSPO certification has no issuing organization stated.",
    "source_ids": [
      "e77:17:59"
    ]
  },
  {
    "path": "/certifications/0/name",
    "reason": "ambiguous_source",
    "detail": "Source is listed under Certifications; CSPO is presented as a certification but issuing body not verified.",
    "source_ids": [
      "e77:17:59"
    ]
  },
  {
    "path": "/certifications/2/name",
    "reason": "schema_limitation",
    "detail": "Source says 'Trained in Embedded Systems' which is training, not an independently verified professional certification; kept as a certification entry per label.",
    "source_ids": [
      "e79:0:48"
    ]
  },
  {
    "path": "/experience/3/projects",
    "reason": "ambiguous_source",
    "detail": "Key Projects listed under National Payments Corporation of India were not explicitly tied to individual dates or roles; recorded as projects with no association field in schema.",
    "source_ids": [
      "e53:0:13",
      "e54:0:46",
      "e55:0:65",
      "e57:0:43",
      "e58:0:52",
      "e59:0:40",
      "e60:0:39"
    ]
  },
  {
    "path": "/upstream_observations",
    "reason": "upstream_defect",
    "detail": "Local categories put NPCI project and responsibility blocks under 'projects' rather than 'experience'; re-associated to experience/3 based on source order.",
    "source_ids": [
      "e53:0:13",
      "e62:0:21"
    ]
  },
  {
    "path": "/projects/0..9/description|role|technologies",
    "reason": "not_in_source",
    "detail": "Project names only; no per-project descriptions, roles, or technology lists in source.",
    "source_ids": []
  }
]
```

## Provider upstream observations

```json
[
  "Local category for 'Role: Business Analyst' is needs_review; used as professional_title.",
  "Some summary/competency blocks were locally labeled summary; only competency list was mapped to domain skills.",
  "Key Projects list under NPCI was locally labeled 'projects' and not re-associated with a project-level description; associated by source order with experience/3.",
  "Awards/memberships/publications: none present. Hobbies ('Reading Books, Writing blogs') have no schema field and are preserved here only.",
  "Certification 'Trained in Embedded Systems – Vector India, 2016' appears to be training rather than professional certification.",
  "Educational education line combines institution, degree, field, city, and year in one block; graduation year extracted as 2015.",
  "Spelling/typos in source preserved in extracts such as 'Collabration Tools' and 'integration's'."
]
```
