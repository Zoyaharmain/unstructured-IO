# Boovanesh Kumar.pdf — five-resume schema pilot

Selection: Dense one-page engineering resume; nested technology lists, three projects, training versus employment and detached education years.

Saved input: `reports/pilot100-additional-llm-20261021-025143/deepseek/documents/d1f9833b2606eb270600.json` → `local_sections`. Pages: [1]. Source blocks: 83. No new extraction/block detection was run. Original PDF was not independently examined for this evaluation.

Correctly maps the main employer, three project names, three degrees and course providers. Detached education years are left null rather than guessed. The trainee entry is explicitly qualified as training but represented in experience; employment policy remains ambiguous. Most list citations are on parent arrays instead of each item, so only 32 populated fields meet the strict raw contract.

- Critical-field agreement proxy: **18/18 = 100.0%**.
- Same-block local heuristic baseline on the same critical set: **10/18**.
- Raw field citation contract: **32/172 = 18.60%**.
- Populated-value source-block assessment: {"correct_mapping": 167, "not_populated": 31, "ambiguous": 5}.
- Human-verified/PDF-verified accuracy: **not established**.

## Complete mapping output

[Mapping JSON](mapping.json) · [Unmodified provider mapping and citations](mapping-raw.json) · [Full provider envelope/usage](response-envelope.json) · [Saved source blocks](source-blocks.md) · [Every evaluated field](field-evaluation.json)

```json
{
  "contact": {
    "full_name": "BOOVANESH KUMAR",
    "email": "boovaneshbk123@gmail.com",
    "phone": "7708126940",
    "location": null,
    "linkedin_url": "linkedin.com/in/Boovanesh-Kumar",
    "github_url": "github.com/boovaneshkumar005",
    "portfolio_url": null
  },
  "professional_title": "Backend Developer (Golang) — Microservices | Full-Stack (Vue.js) | Cloud & DevOps (AWS, Docker)",
  "summary": "Backend Developer (Golang) with around 3 years of experience architecting Go-based microservices, distributed systems, and REST APIs, complemented by full-stack development in Vue.js and cloud/DevOps exposure (AWS, Docker, Kubernetes). Skilled in performance tuning, scalability, load balancing, and event-driven architectures, with strong production debugging experience. Experienced in Agile Scrum, working in sprint-based development with story estimation, sprint planning, and cross-functional collaboration.",
  "total_experience_years": 3.0,
  "skills": {
    "technical_skills": [
      "Go (Golang)",
      "JavaScript",
      "TypeScript",
      "Data Structures & Algorithms",
      "Microservices",
      "gRPC",
      "Protocol Buffers",
      "Kafka",
      "REST APIs",
      "Goroutines",
      "Channels",
      "Worker Pool / Fan-In / Fan-Out concurrency",
      "Event-Driven Design",
      "Distributed Systems",
      "Scalability",
      "Load Balancing",
      "Horizontal Scaling",
      "Monolith",
      "Monorepo",
      "Vue.js",
      "API Integration",
      "Dashboards",
      "ReactJS (fundamentals)"
    ],
    "tools_and_platforms": [
      "MongoDB",
      "PostgreSQL",
      "Cassandra",
      "Redis",
      "AWS (S3, Lambda, SQS, CloudWatch)",
      "Docker",
      "Kubernetes",
      "Jenkins",
      "GitLab CI/CD",
      "Linux",
      "Shell Scripting",
      "Terraform",
      "Elasticsearch",
      "Kibana",
      "APM",
      "pprof",
      "AI-assisted development tools"
    ],
    "domain_and_functional": [
      "Agile Scrum",
      "sprint planning",
      "story estimation",
      "cross-functional collaboration",
      "performance tuning"
    ],
    "soft_skills": [],
    "all_skills": [
      "Go (Golang)",
      "JavaScript",
      "TypeScript",
      "Data Structures & Algorithms",
      "Microservices",
      "gRPC",
      "Protocol Buffers",
      "Kafka",
      "REST APIs",
      "Goroutines",
      "Channels",
      "Worker Pool / Fan-In / Fan-Out concurrency",
      "Event-Driven Design",
      "Distributed Systems",
      "Scalability",
      "Load Balancing",
      "Horizontal Scaling",
      "Monolith",
      "Monorepo",
      "Vue.js",
      "API Integration",
      "Dashboards",
      "ReactJS (fundamentals)",
      "MongoDB",
      "PostgreSQL",
      "Cassandra",
      "Redis",
      "AWS (S3, Lambda, SQS, CloudWatch)",
      "Docker",
      "Kubernetes",
      "Jenkins",
      "GitLab CI/CD",
      "Linux",
      "Shell Scripting",
      "Terraform",
      "Elasticsearch",
      "Kibana",
      "APM",
      "pprof",
      "AI-assisted development tools",
      "Agile Scrum",
      "sprint planning",
      "story estimation",
      "cross-functional collaboration",
      "performance tuning"
    ]
  },
  "experience": [
    {
      "company": "Mitrahsoft",
      "role": "Software Engineer",
      "start_date": null,
      "end_date": null,
      "duration": null,
      "location": null,
      "responsibilities": [
        "Built concurrent background-job pipelines (Worker Pool, Fan-In/Fan-Out) and resolved Kubernetes pod crashes via controlled goroutine execution.",
        "Developed microservices using gRPC and Kafka-based event-driven pipelines, with Elasticsearch/Kibana/APM monitoring and alerting.",
        "Developed automated test cases for desktop application testing using Playwright (TypeScript) and RobotJS.",
        "Implemented multilingual support using go-i18n and loaded application logs into Snowflake for analytical reporting.",
        "Developed a serverless Campaign Mail Scheduler (AWS Lambda, SQS, SendGrid) for event-driven bulk email processing.",
        "Served as an LLM Trainer (Turing) on Amazon Nova prompt engineering and response evaluation, achieving ~95% unit test coverage.",
        "Delivered cross-stack features spanning Vue.js dashboards, AWS S3 file handling, OAuth integrations, and CI/CD automation (Jenkins, Docker)."
      ],
      "technologies": [
        "gRPC",
        "Kafka",
        "Elasticsearch",
        "Kibana",
        "APM",
        "Playwright",
        "TypeScript",
        "RobotJS",
        "go-i18n",
        "Snowflake",
        "AWS Lambda",
        "SQS",
        "SendGrid",
        "Vue.js",
        "AWS S3",
        "Jenkins",
        "Docker"
      ]
    },
    {
      "company": "Besant Technologies",
      "role": "Front-End Development Trainee",
      "start_date": null,
      "end_date": null,
      "duration": "6-month",
      "location": null,
      "responsibilities": [
        "Completed a 6-month intensive ReactJS front-end training program, building practice applications covering component design, state management, and API integration."
      ],
      "technologies": [
        "ReactJS"
      ]
    }
  ],
  "education": [
    {
      "institution": "Kongu Engineering College",
      "degree": "Bachelor of Engineering",
      "field_of_study": "Mechatronics",
      "start_year": null,
      "graduation_year": null,
      "grade_or_gpa": null
    },
    {
      "institution": "St. Paul's Matriculation Hr. Sec. School",
      "degree": "HSC",
      "field_of_study": null,
      "start_year": null,
      "graduation_year": null,
      "grade_or_gpa": null
    },
    {
      "institution": "St. Paul's Matriculation Hr. Sec. School",
      "degree": "SSLC",
      "field_of_study": null,
      "start_year": null,
      "graduation_year": null,
      "grade_or_gpa": null
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified Solutions Architect – Associate (Udemy)",
      "issuer": "Udemy",
      "issue_year": null
    },
    {
      "name": "Cyber Security From Beginner to Expert (Udemy)",
      "issuer": "Udemy",
      "issue_year": null
    },
    {
      "name": "Software Architecture and Design of Modern Large Scale Systems (Udemy)",
      "issuer": "Udemy",
      "issue_year": null
    }
  ],
  "projects": [
    {
      "name": "Ecommerce Application",
      "description": "Integrated Firebase Authentication with backend JWT verification (Firebase Admin SDK, Golang) and RBAC for USER/ADMIN roles; used AES encryption for sensitive data. Built a scalable Order Management and Inventory System with transactional consistency and idempotent APIs to prevent duplicate transactions. Designed a Wallet System using double-entry ledger for ACID-compliant transactions, with fraud detection, transaction validation, and audit logging. Integrated Stripe payments (sandbox), Firebase Cloud Messaging for real-time notifications, and Firestore for real-time order tracking/chat sync; built a WebSocket-based rule-driven chatbot in Golang for customer support workflows.",
      "role": null,
      "technologies": [
        "Firebase Authentication",
        "JWT",
        "Firebase Admin SDK",
        "Golang",
        "AES",
        "Stripe",
        "Firebase Cloud Messaging",
        "Firestore",
        "WebSocket"
      ],
      "url": null
    },
    {
      "name": "HRMS — Human Resource Management System",
      "description": "Improved legacy code and MongoDB query performance by adding indexes and removing nested loops, cutting report generation time from 5 minutes to 25 seconds for 1 lakh (100,000+) records. Implemented Go concurrency patterns (Worker Pool, Fan-In/Fan-Out) for background PDF and Excel report generation. Resolved Kubernetes pod crashes from high-memory jobs using controlled goroutine execution and gopsutil-based memory checks, improving scalability under load. Integrated Elasticsearch/Kibana dashboards and alerting; built AWS S3 file upload, encryption, and pre-signed URL features. Developed an Expense microservice with approval workflows and Tesseract OCR-based receipt data extraction.",
      "role": null,
      "technologies": [
        "MongoDB",
        "Go",
        "Kubernetes",
        "gopsutil",
        "Elasticsearch",
        "Kibana",
        "AWS S3",
        "Tesseract OCR"
      ],
      "url": null
    },
    {
      "name": "Freight Management System — Microservices",
      "description": "Implemented gRPC-based inter-service communication and a Kafka-driven event system for real-time parcel tracking. Built event deduplication logic and used Cadence workflow orchestration for retrying and reprocessing failed events. Generated freight bills and shipping labels via ZPL, and implemented fuel-price and carrier-discount business rules. Used PostgreSQL for transactional data and Cassandra for high-volume tracking events; managed schema migrations. Applied dependency injection (samber/do) to reduce coupling; wrote unit/integration tests using a TDD approach.",
      "role": null,
      "technologies": [
        "gRPC",
        "Kafka",
        "Cadence",
        "ZPL",
        "PostgreSQL",
        "Cassandra",
        "samber/do"
      ],
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
| `/contact/full_name` | BOOVANESH KUMAR | correct_mapping | citation_supported | e0:0:16 |
| `/contact/email` | boovaneshbk123@gmail.com | correct_mapping | citation_supported | e0:112:213 |
| `/contact/phone` | 7708126940 | correct_mapping | citation_supported | e0:112:213 |
| `/contact/location` | None | not_populated | not_populated |  |
| `/contact/linkedin_url` | linkedin.com/in/Boovanesh-Kumar | correct_mapping | citation_supported | e0:112:213 |
| `/contact/github_url` | github.com/boovaneshkumar005 | correct_mapping | citation_supported | e0:112:213 |
| `/contact/portfolio_url` | None | not_populated | not_populated |  |
| `/professional_title` | Backend Developer (Golang) — Microservices \| Full-Stack (Vue.js) \| Cloud & DevOps (AWS, Docker) | correct_mapping | citation_supported | e0:16:112 |
| `/summary` | Backend Developer (Golang) with around 3 years of experience architecting Go-based microservices, distributed systems, and REST APIs, complemented by full-stack development in Vue.js and cloud/DevOps exposure (AWS, Docker, Kubernetes). Skilled in per… | correct_mapping | citation_supported | e1:21:155, e1:155:288, e1:288:433, e1:433:534 |
| `/total_experience_years` | 3.0 | correct_mapping | citation_supported | e1:21:155 |
| `/skills/technical_skills/0` | Go (Golang) | correct_mapping | citation_error | e1:551:598 |
| `/skills/technical_skills/1` | JavaScript | correct_mapping | citation_error | e1:551:598 |
| `/skills/technical_skills/2` | TypeScript | correct_mapping | citation_error | e1:551:598 |
| `/skills/technical_skills/3` | Data Structures & Algorithms | correct_mapping | citation_error | e1:598:743 |
| `/skills/technical_skills/4` | Microservices | correct_mapping | citation_error | e0:16:112 |
| `/skills/technical_skills/5` | gRPC | correct_mapping | citation_error | e1:598:743 |
| `/skills/technical_skills/6` | Protocol Buffers | correct_mapping | citation_error | e1:598:743 |
| `/skills/technical_skills/7` | Kafka | correct_mapping | citation_error | e1:598:743 |
| `/skills/technical_skills/8` | REST APIs | correct_mapping | citation_error | e1:21:155 |
| `/skills/technical_skills/9` | Goroutines | correct_mapping | citation_error | e1:598:743 |
| `/skills/technical_skills/10` | Channels | correct_mapping | citation_error | e1:598:743 |
| `/skills/technical_skills/11` | Worker Pool / Fan-In / Fan-Out concurrency | correct_mapping | citation_error | e1:598:743, e1:743:874 |
| `/skills/technical_skills/12` | Event-Driven Design | correct_mapping | citation_error | e1:743:874 |
| `/skills/technical_skills/13` | Distributed Systems | correct_mapping | citation_error | e1:21:155 |
| `/skills/technical_skills/14` | Scalability | correct_mapping | citation_error | e1:288:433 |
| `/skills/technical_skills/15` | Load Balancing | correct_mapping | citation_error | e1:288:433 |
| `/skills/technical_skills/16` | Horizontal Scaling | correct_mapping | citation_error | e1:743:874 |
| `/skills/technical_skills/17` | Monolith | correct_mapping | citation_error | e1:743:874 |
| `/skills/technical_skills/18` | Monorepo | correct_mapping | citation_error | e1:874:885 |
| `/skills/technical_skills/19` | Vue.js | correct_mapping | citation_error | e0:16:112 |
| `/skills/technical_skills/20` | API Integration | correct_mapping | citation_error | e1:885:955 |
| `/skills/technical_skills/21` | Dashboards | correct_mapping | citation_error | e1:885:955 |
| `/skills/technical_skills/22` | ReactJS (fundamentals) | correct_mapping | citation_error | e1:885:955 |
| `/skills/tools_and_platforms/0` | MongoDB | correct_mapping | citation_error | e1:955:1004 |
| `/skills/tools_and_platforms/1` | PostgreSQL | correct_mapping | citation_error | e1:955:1004 |
| `/skills/tools_and_platforms/2` | Cassandra | correct_mapping | citation_error | e1:955:1004 |
| `/skills/tools_and_platforms/3` | Redis | correct_mapping | citation_error | e1:955:1004 |
| `/skills/tools_and_platforms/4` | AWS (S3, Lambda, SQS, CloudWatch) | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/tools_and_platforms/5` | Docker | correct_mapping | citation_error | e0:16:112 |
| `/skills/tools_and_platforms/6` | Kubernetes | correct_mapping | citation_error | e1:155:288 |
| `/skills/tools_and_platforms/7` | Jenkins | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/tools_and_platforms/8` | GitLab CI/CD | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/tools_and_platforms/9` | Linux | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/tools_and_platforms/10` | Shell Scripting | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/tools_and_platforms/11` | Terraform | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/tools_and_platforms/12` | Elasticsearch | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/tools_and_platforms/13` | Kibana | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/tools_and_platforms/14` | APM | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/tools_and_platforms/15` | pprof | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/tools_and_platforms/16` | AI-assisted development tools | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/domain_and_functional/0` | Agile Scrum | correct_mapping | citation_error | e1:288:433 |
| `/skills/domain_and_functional/1` | sprint planning | correct_mapping | citation_error | e1:433:534 |
| `/skills/domain_and_functional/2` | story estimation | correct_mapping | citation_error | e1:433:534 |
| `/skills/domain_and_functional/3` | cross-functional collaboration | correct_mapping | citation_error | e1:433:534 |
| `/skills/domain_and_functional/4` | performance tuning | correct_mapping | citation_error | e1:155:288 |
| `/skills/soft_skills` | [] | not_populated | not_populated |  |
| `/skills/all_skills/0` | Go (Golang) | correct_mapping | citation_error | e1:551:598 |
| `/skills/all_skills/1` | JavaScript | correct_mapping | citation_error | e1:551:598 |
| `/skills/all_skills/2` | TypeScript | correct_mapping | citation_error | e1:551:598 |
| `/skills/all_skills/3` | Data Structures & Algorithms | correct_mapping | citation_error | e1:598:743 |
| `/skills/all_skills/4` | Microservices | correct_mapping | citation_error | e0:16:112 |
| `/skills/all_skills/5` | gRPC | correct_mapping | citation_error | e1:598:743 |
| `/skills/all_skills/6` | Protocol Buffers | correct_mapping | citation_error | e1:598:743 |
| `/skills/all_skills/7` | Kafka | correct_mapping | citation_error | e1:598:743 |
| `/skills/all_skills/8` | REST APIs | correct_mapping | citation_error | e1:21:155 |
| `/skills/all_skills/9` | Goroutines | correct_mapping | citation_error | e1:598:743 |
| `/skills/all_skills/10` | Channels | correct_mapping | citation_error | e1:598:743 |
| `/skills/all_skills/11` | Worker Pool / Fan-In / Fan-Out concurrency | correct_mapping | citation_error | e1:598:743, e1:743:874 |
| `/skills/all_skills/12` | Event-Driven Design | correct_mapping | citation_error | e1:743:874 |
| `/skills/all_skills/13` | Distributed Systems | correct_mapping | citation_error | e1:21:155 |
| `/skills/all_skills/14` | Scalability | correct_mapping | citation_error | e1:288:433 |
| `/skills/all_skills/15` | Load Balancing | correct_mapping | citation_error | e1:288:433 |
| `/skills/all_skills/16` | Horizontal Scaling | correct_mapping | citation_error | e1:743:874 |
| `/skills/all_skills/17` | Monolith | correct_mapping | citation_error | e1:743:874 |
| `/skills/all_skills/18` | Monorepo | correct_mapping | citation_error | e1:874:885 |
| `/skills/all_skills/19` | Vue.js | correct_mapping | citation_error | e0:16:112 |
| `/skills/all_skills/20` | API Integration | correct_mapping | citation_error | e1:885:955 |
| `/skills/all_skills/21` | Dashboards | correct_mapping | citation_error | e1:885:955 |
| `/skills/all_skills/22` | ReactJS (fundamentals) | correct_mapping | citation_error | e1:885:955 |
| `/skills/all_skills/23` | MongoDB | correct_mapping | citation_error | e1:955:1004 |
| `/skills/all_skills/24` | PostgreSQL | correct_mapping | citation_error | e1:955:1004 |
| `/skills/all_skills/25` | Cassandra | correct_mapping | citation_error | e1:955:1004 |
| `/skills/all_skills/26` | Redis | correct_mapping | citation_error | e1:955:1004 |
| `/skills/all_skills/27` | AWS (S3, Lambda, SQS, CloudWatch) | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/all_skills/28` | Docker | correct_mapping | citation_error | e0:16:112 |
| `/skills/all_skills/29` | Kubernetes | correct_mapping | citation_error | e1:155:288 |
| `/skills/all_skills/30` | Jenkins | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/all_skills/31` | GitLab CI/CD | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/all_skills/32` | Linux | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/all_skills/33` | Shell Scripting | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/all_skills/34` | Terraform | correct_mapping | citation_error | e1:1004:1131 |
| `/skills/all_skills/35` | Elasticsearch | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/all_skills/36` | Kibana | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/all_skills/37` | APM | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/all_skills/38` | pprof | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/all_skills/39` | AI-assisted development tools | correct_mapping | citation_error | e1:1131:1216 |
| `/skills/all_skills/40` | Agile Scrum | correct_mapping | citation_error | e1:288:433 |
| `/skills/all_skills/41` | sprint planning | correct_mapping | citation_error | e1:433:534 |
| `/skills/all_skills/42` | story estimation | correct_mapping | citation_error | e1:433:534 |
| `/skills/all_skills/43` | cross-functional collaboration | correct_mapping | citation_error | e1:433:534 |
| `/skills/all_skills/44` | performance tuning | correct_mapping | citation_error | e1:155:288 |
| `/experience/0/company` | Mitrahsoft | correct_mapping | citation_supported | e2:0:30 |
| `/experience/0/role` | Software Engineer | correct_mapping | citation_supported | e2:0:30 |
| `/experience/0/start_date` | None | not_populated | not_populated |  |
| `/experience/0/end_date` | None | not_populated | not_populated |  |
| `/experience/0/duration` | None | not_populated | not_populated |  |
| `/experience/0/location` | None | not_populated | not_populated |  |
| `/experience/0/responsibilities/0` | Built concurrent background-job pipelines (Worker Pool, Fan-In/Fan-Out) and resolved Kubernetes pod crashes via controlled goroutine execution. | correct_mapping | citation_error | e3:0:133, e3:133:143 |
| `/experience/0/responsibilities/1` | Developed microservices using gRPC and Kafka-based event-driven pipelines, with Elasticsearch/Kibana/APM monitoring and alerting. | correct_mapping | citation_error | e4:0:129 |
| `/experience/0/responsibilities/2` | Developed automated test cases for desktop application testing using Playwright (TypeScript) and RobotJS. | correct_mapping | citation_error | e4:132:237 |
| `/experience/0/responsibilities/3` | Implemented multilingual support using go-i18n and loaded application logs into Snowflake for analytical reporting. | correct_mapping | citation_error | e4:240:355 |
| `/experience/0/responsibilities/4` | Developed a serverless Campaign Mail Scheduler (AWS Lambda, SQS, SendGrid) for event-driven bulk email processing. | correct_mapping | citation_error | e4:358:472 |
| `/experience/0/responsibilities/5` | Served as an LLM Trainer (Turing) on Amazon Nova prompt engineering and response evaluation, achieving ~95% unit test coverage. | correct_mapping | citation_error | e4:475:602 |
| `/experience/0/responsibilities/6` | Delivered cross-stack features spanning Vue.js dashboards, AWS S3 file handling, OAuth integrations, and CI/CD automation (Jenkins, Docker). | correct_mapping | citation_error | e4:605:737, e4:737:745 |
| `/experience/0/technologies/0` | gRPC | correct_mapping | citation_error | e1:598:743 |
| `/experience/0/technologies/1` | Kafka | correct_mapping | citation_error | e1:598:743 |
| `/experience/0/technologies/2` | Elasticsearch | correct_mapping | citation_error | e1:1131:1216 |
| `/experience/0/technologies/3` | Kibana | correct_mapping | citation_error | e1:1131:1216 |
| `/experience/0/technologies/4` | APM | correct_mapping | citation_error | e1:1131:1216 |
| `/experience/0/technologies/5` | Playwright | correct_mapping | citation_error | e4:132:237 |
| `/experience/0/technologies/6` | TypeScript | correct_mapping | citation_error | e1:551:598 |
| `/experience/0/technologies/7` | RobotJS | correct_mapping | citation_error | e4:132:237 |
| `/experience/0/technologies/8` | go-i18n | correct_mapping | citation_error | e4:240:355 |
| `/experience/0/technologies/9` | Snowflake | correct_mapping | citation_error | e4:240:355 |
| `/experience/0/technologies/10` | AWS Lambda | correct_mapping | citation_error | e4:358:472 |
| `/experience/0/technologies/11` | SQS | correct_mapping | citation_error | e1:1004:1131 |
| `/experience/0/technologies/12` | SendGrid | correct_mapping | citation_error | e4:358:472 |
| `/experience/0/technologies/13` | Vue.js | correct_mapping | citation_error | e0:16:112 |
| `/experience/0/technologies/14` | AWS S3 | correct_mapping | citation_error | e4:605:737 |
| `/experience/0/technologies/15` | Jenkins | correct_mapping | citation_error | e1:1004:1131 |
| `/experience/0/technologies/16` | Docker | correct_mapping | citation_error | e0:16:112 |
| `/experience/1/company` | Besant Technologies | ambiguous | citation_supported | e5:0:51 |
| `/experience/1/role` | Front-End Development Trainee | ambiguous | citation_supported | e5:0:51 |
| `/experience/1/start_date` | None | not_populated | not_populated |  |
| `/experience/1/end_date` | None | not_populated | not_populated |  |
| `/experience/1/duration` | 6-month | ambiguous | citation_supported | e6:0:130 |
| `/experience/1/location` | None | not_populated | not_populated |  |
| `/experience/1/responsibilities/0` | Completed a 6-month intensive ReactJS front-end training program, building practice applications covering component design, state management, and API integration. | ambiguous | citation_error | e6:0:130, e6:130:162 |
| `/experience/1/technologies/0` | ReactJS | ambiguous | citation_error | e1:885:955 |
| `/education/0/institution` | Kongu Engineering College | correct_mapping | citation_supported | e22:10:76 |
| `/education/0/degree` | Bachelor of Engineering | correct_mapping | citation_supported | e22:10:76 |
| `/education/0/field_of_study` | Mechatronics | correct_mapping | citation_supported | e22:10:76 |
| `/education/0/start_year` | None | not_populated | not_populated |  |
| `/education/0/graduation_year` | None | not_populated | not_populated |  |
| `/education/0/grade_or_gpa` | None | not_populated | not_populated |  |
| `/education/1/institution` | St. Paul's Matriculation Hr. Sec. School | correct_mapping | citation_supported | e22:76:123 |
| `/education/1/degree` | HSC | correct_mapping | citation_supported | e22:76:123 |
| `/education/1/field_of_study` | None | not_populated | not_populated |  |
| `/education/1/start_year` | None | not_populated | not_populated |  |
| `/education/1/graduation_year` | None | not_populated | not_populated |  |
| `/education/1/grade_or_gpa` | None | not_populated | not_populated |  |
| `/education/2/institution` | St. Paul's Matriculation Hr. Sec. School | correct_mapping | citation_supported | e22:76:123 |
| `/education/2/degree` | SSLC | correct_mapping | citation_supported | e22:123:170 |
| `/education/2/field_of_study` | None | not_populated | not_populated |  |
| `/education/2/start_year` | None | not_populated | not_populated |  |
| `/education/2/graduation_year` | None | not_populated | not_populated |  |
| `/education/2/grade_or_gpa` | None | not_populated | not_populated |  |
| `/certifications/0/name` | AWS Certified Solutions Architect – Associate (Udemy) | correct_mapping | citation_supported | e24:2:55 |
| `/certifications/0/issuer` | Udemy | correct_mapping | citation_supported | e24:2:55 |
| `/certifications/0/issue_year` | None | not_populated | not_populated |  |
| `/certifications/1/name` | Cyber Security From Beginner to Expert (Udemy) | correct_mapping | citation_supported | e24:58:104 |
| `/certifications/1/issuer` | Udemy | correct_mapping | citation_supported | e24:2:55 |
| `/certifications/1/issue_year` | None | not_populated | not_populated |  |
| `/certifications/2/name` | Software Architecture and Design of Modern Large Scale Systems (Udemy) | correct_mapping | citation_supported | e24:107:177 |
| `/certifications/2/issuer` | Udemy | correct_mapping | citation_supported | e24:2:55 |
| `/certifications/2/issue_year` | None | not_populated | not_populated |  |
| `/projects/0/name` | Ecommerce Application | correct_mapping | citation_supported | e8:0:21 |
| `/projects/0/description` | Integrated Firebase Authentication with backend JWT verification (Firebase Admin SDK, Golang) and RBAC for USER/ADMIN roles; used AES encryption for sensitive data. Built a scalable Order Management and Inventory System with transactional consistency… | correct_mapping | citation_supported | e10:0:130, e10:130:164, e11:0:127, e11:127:140, e12:0:133, e14:0:15, e14:15:141, e14:141:246 |
| `/projects/0/role` | None | not_populated | not_populated |  |
| `/projects/0/technologies/0` | Firebase Authentication | correct_mapping | citation_error | e10:0:130 |
| `/projects/0/technologies/1` | JWT | correct_mapping | citation_error | e10:0:130 |
| `/projects/0/technologies/2` | Firebase Admin SDK | correct_mapping | citation_error | e10:0:130 |
| `/projects/0/technologies/3` | Golang | correct_mapping | citation_error | e0:16:112 |
| `/projects/0/technologies/4` | AES | correct_mapping | citation_error | e10:130:164 |
| `/projects/0/technologies/5` | Stripe | correct_mapping | citation_error | e14:15:141 |
| `/projects/0/technologies/6` | Firebase Cloud Messaging | correct_mapping | citation_error | e14:15:141 |
| `/projects/0/technologies/7` | Firestore | correct_mapping | citation_error | e14:15:141 |
| `/projects/0/technologies/8` | WebSocket | correct_mapping | citation_error | e14:141:246 |
| `/projects/0/url` | None | not_populated | not_populated |  |
| `/projects/1/name` | HRMS — Human Resource Management System | correct_mapping | citation_supported | e15:0:39 |
| `/projects/1/description` | Improved legacy code and MongoDB query performance by adding indexes and removing nested loops, cutting report generation time from 5 minutes to 25 seconds for 1 lakh (100,000+) records. Implemented Go concurrency patterns (Worker Pool, Fan-In/Fan-Ou… | correct_mapping | citation_supported | e17:0:127, e17:127:187, e17:187:300, e18:2:127, e18:127:161, e18:161:284, e19:2:108 |
| `/projects/1/role` | None | not_populated | not_populated |  |
| `/projects/1/technologies/0` | MongoDB | correct_mapping | citation_error | e1:955:1004 |
| `/projects/1/technologies/1` | Go | correct_mapping | citation_error | e0:16:112 |
| `/projects/1/technologies/2` | Kubernetes | correct_mapping | citation_error | e1:155:288 |
| `/projects/1/technologies/3` | gopsutil | correct_mapping | citation_error | e18:2:127 |
| `/projects/1/technologies/4` | Elasticsearch | correct_mapping | citation_error | e1:1131:1216 |
| `/projects/1/technologies/5` | Kibana | correct_mapping | citation_error | e1:1131:1216 |
| `/projects/1/technologies/6` | AWS S3 | correct_mapping | citation_error | e4:605:737 |
| `/projects/1/technologies/7` | Tesseract OCR | correct_mapping | citation_error | e19:2:108 |
| `/projects/1/url` | None | not_populated | not_populated |  |
| `/projects/2/name` | Freight Management System — Microservices | correct_mapping | citation_supported | e20:0:41 |
| `/projects/2/description` | Implemented gRPC-based inter-service communication and a Kafka-driven event system for real-time parcel tracking. Built event deduplication logic and used Cadence workflow orchestration for retrying and reprocessing failed events. Generated freight b… | correct_mapping | citation_supported | e21:0:113, e21:116:232, e21:235:351, e21:354:466, e21:469:580 |
| `/projects/2/role` | None | not_populated | not_populated |  |
| `/projects/2/technologies/0` | gRPC | correct_mapping | citation_error | e1:598:743 |
| `/projects/2/technologies/1` | Kafka | correct_mapping | citation_error | e1:598:743 |
| `/projects/2/technologies/2` | Cadence | correct_mapping | citation_error | e21:116:232 |
| `/projects/2/technologies/3` | ZPL | correct_mapping | citation_error | e21:235:351 |
| `/projects/2/technologies/4` | PostgreSQL | correct_mapping | citation_error | e1:955:1004 |
| `/projects/2/technologies/5` | Cassandra | correct_mapping | citation_error | e1:955:1004 |
| `/projects/2/technologies/6` | samber/do | correct_mapping | citation_error | e21:469:580 |
| `/projects/2/url` | None | not_populated | not_populated |  |
| `/languages` | [] | not_populated | not_populated |  |

## Predeclared critical opportunities

Degree plus field_of_study may satisfy one reference degree opportunity. Original month-year strings are accepted when the expected year matches; this does not remove date-association ambiguity. Country codes, punctuation/whitespace, labels such as CGPA and enclosing lab/organization context are normalized as documented in the main report.

| Reference | Target | Expected source fact | Actual value | Result |
|---|---|---|---|---|
| f045 | root.contact.full_name | BOOVANESH KUMAR | BOOVANESH KUMAR | correct_mapping |
| f046 | root.contact.email | boovaneshbk123@gmail.com | boovaneshbk123@gmail.com | correct_mapping |
| f047 | root.contact.phone | 7708126940 | 7708126940 | correct_mapping |
| f048 | root.total_experience_years | 3 | 3.0 | correct_mapping |
| f049 | experience.company | Mitrahsoft | Mitrahsoft | correct_mapping |
| f050 | experience.role | Software Engineer | Software Engineer | correct_mapping |
| f051 | education.degree | Bachelor of Engineering | Bachelor of Engineering | correct_mapping |
| f052 | education.institution | Kongu Engineering College | Kongu Engineering College | correct_mapping |
| f053 | education.degree | HSC | HSC | correct_mapping |
| f054 | education.institution | St. Paul's Matriculation Hr. Sec. School | St. Paul's Matriculation Hr. Sec. School | correct_mapping |
| f055 | education.degree | SSLC | SSLC | correct_mapping |
| f056 | education.institution | St. Paul's Matriculation Hr. Sec. School | St. Paul's Matriculation Hr. Sec. School | correct_mapping |
| f057 | projects.name | Ecommerce Application | Ecommerce Application | correct_mapping |
| f058 | projects.name | HRMS — Human Resource Management System | HRMS — Human Resource Management System | correct_mapping |
| f059 | projects.name | Freight Management System — Microservices | Freight Management System — Microservices | correct_mapping |
| f060 | certifications.issuer | Udemy | Udemy | correct_mapping |
| f061 | certifications.issuer | Udemy | Udemy | correct_mapping |
| f062 | certifications.issuer | Udemy | Udemy | correct_mapping |

## Provider missing-information statements

These are provider claims, not independent truth. Compare with field-evaluation.json for analyst disagreements and actual mapping omissions.

```json
[
  {
    "path": "/contact/location",
    "reason": "not_in_source",
    "detail": "No city, state, or country of residence is stated in the source text.",
    "source_ids": []
  },
  {
    "path": "/contact/portfolio_url",
    "reason": "not_in_source",
    "detail": "No personal website or portfolio URL is present.",
    "source_ids": []
  },
  {
    "path": "/experience/0/start_date",
    "reason": "not_in_source",
    "detail": "No start date for the Mitrahsoft Software Engineer role appears in the source.",
    "source_ids": []
  },
  {
    "path": "/experience/0/end_date",
    "reason": "not_in_source",
    "detail": "No end date for the Mitrahsoft role appears in the source.",
    "source_ids": []
  },
  {
    "path": "/experience/0/location",
    "reason": "not_in_source",
    "detail": "No job location for the Mitrahsoft role is stated.",
    "source_ids": []
  },
  {
    "path": "/experience/1/start_date",
    "reason": "not_in_source",
    "detail": "No start date for the Besant Technologies trainee role appears; only a six-month program length is stated.",
    "source_ids": []
  },
  {
    "path": "/experience/1/end_date",
    "reason": "not_in_source",
    "detail": "No end date for the Besant Technologies trainee role appears.",
    "source_ids": []
  },
  {
    "path": "/experience/1/location",
    "reason": "not_in_source",
    "detail": "No location for the Besant Technologies trainee role is stated.",
    "source_ids": []
  },
  {
    "path": "/experience/1/company",
    "reason": "ambiguous_source",
    "detail": "The trainee entry is described as a 6-month intensive ReactJS training program; it is represented as work experience per local categorization but may be training rather than employment.",
    "source_ids": [
      "e5:0:51",
      "e6:0:130"
    ]
  },
  {
    "path": "/education/0/start_year",
    "reason": "not_in_source",
    "detail": "No start year is given for the Bachelor of Engineering entry.",
    "source_ids": []
  },
  {
    "path": "/education/0/graduation_year",
    "reason": "ambiguous_source",
    "detail": "The years 2022, 2018, and 2016 appear in a separate block near the education/certifications boundary but are not attached to specific degree rows, so association is uncertain.",
    "source_ids": [
      "e23:0:5",
      "e23:5:10",
      "e23:10:14"
    ]
  },
  {
    "path": "/education/1/graduation_year",
    "reason": "ambiguous_source",
    "detail": "Detached year values are not clearly associated with the HSC row.",
    "source_ids": [
      "e23:0:5",
      "e23:5:10",
      "e23:10:14"
    ]
  },
  {
    "path": "/education/2/graduation_year",
    "reason": "ambiguous_source",
    "detail": "Detached year values are not clearly associated with the SSLC row.",
    "source_ids": [
      "e23:0:5",
      "e23:5:10",
      "e23:10:14"
    ]
  },
  {
    "path": "/education/0/grade_or_gpa",
    "reason": "not_in_source",
    "detail": "No grade, GPA, or percentage is provided for the engineering degree.",
    "source_ids": []
  },
  {
    "path": "/education/1/grade_or_gpa",
    "reason": "not_in_source",
    "detail": "No grade or percentage is provided for HSC.",
    "source_ids": []
  },
  {
    "path": "/education/2/grade_or_gpa",
    "reason": "not_in_source",
    "detail": "No grade or percentage is provided for SSLC.",
    "source_ids": []
  },
  {
    "path": "/education/1/field_of_study",
    "reason": "not_in_source",
    "detail": "No field of study is stated for HSC.",
    "source_ids": []
  },
  {
    "path": "/education/2/field_of_study",
    "reason": "not_in_source",
    "detail": "No field of study is stated for SSLC.",
    "source_ids": []
  },
  {
    "path": "/certifications/0/issue_year",
    "reason": "ambiguous_source",
    "detail": "The year 2022 is detached from certification names; it is not confirmed as the issue year for the AWS certification course.",
    "source_ids": [
      "e23:0:5"
    ]
  },
  {
    "path": "/certifications/1/issue_year",
    "reason": "ambiguous_source",
    "detail": "The year 2018 is detached from certification names; association is uncertain.",
    "source_ids": [
      "e23:5:10"
    ]
  },
  {
    "path": "/certifications/2/issue_year",
    "reason": "ambiguous_source",
    "detail": "The year 2016 is detached from certification names; association is uncertain.",
    "source_ids": [
      "e23:10:14"
    ]
  },
  {
    "path": "/certifications",
    "reason": "schema_limitation",
    "detail": "Listed Udemy items are courses; they are labeled as certifications per source but are not independently verified professional qualifications.",
    "source_ids": [
      "e24:2:55",
      "e24:58:104",
      "e24:107:177"
    ]
  },
  {
    "path": "/projects/0/role",
    "reason": "not_in_source",
    "detail": "No project role is stated for the Ecommerce Application.",
    "source_ids": []
  },
  {
    "path": "/projects/1/role",
    "reason": "not_in_source",
    "detail": "No project role is stated for HRMS.",
    "source_ids": []
  },
  {
    "path": "/projects/2/role",
    "reason": "not_in_source",
    "detail": "No project role is stated for the Freight Management System.",
    "source_ids": []
  },
  {
    "path": "/projects/0/url",
    "reason": "not_in_source",
    "detail": "No project URL or repository link is provided.",
    "source_ids": []
  },
  {
    "path": "/projects/1/url",
    "reason": "not_in_source",
    "detail": "No project URL or repository link is provided.",
    "source_ids": []
  },
  {
    "path": "/projects/2/url",
    "reason": "not_in_source",
    "detail": "No project URL or repository link is provided.",
    "source_ids": []
  },
  {
    "path": "/languages",
    "reason": "not_in_source",
    "detail": "No spoken languages are stated; document language does not imply spoken English proficiency.",
    "source_ids": []
  },
  {
    "path": "/total_experience_years",
    "reason": "ambiguous_source",
    "detail": "The source states 'around 3 years of experience'; the value 3 preserves the explicit number but the 'around' qualification means it is approximate.",
    "source_ids": [
      "e1:21:155"
    ]
  }
]
```

## Provider upstream observations

```json
[
  "Years 2022, 2018, and 2016 appear as one detached block (e23:0:5, e23:5:10, e23:10:14) near the education/certifications boundary with no clear row association.",
  "Bullet separator characters (●) were split into separate blocks and are excluded from excerpts per instructions.",
  "Empty blocks e9:0:0 and e13:0:0 and e16:0:0 exist between project entries; no content extracted from them.",
  "The source lists Udemy courses under CERTIFICATIONS; their preservation as certifications follows the source label and does not verify them as professional credentials.",
  "No awards, memberships, or publications sections with dedicated schema fields appear in the provided blocks.",
  "Programming languages (Go, JavaScript, TypeScript) are placed under skills rather than spoken languages.",
  "The Besant Technologies trainee entry is a 6-month training program; work-versus-training status is not conclusively established by local categories."
]
```
