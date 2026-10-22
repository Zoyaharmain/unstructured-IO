# DDhanush.pdf — five-resume schema pilot

Selection: One-page two-column software resume; projects and programming languages misclassified locally; academic grades and certification providers.

Saved input: `reports/pilot100-additional-llm-20261021-025143/deepseek/documents/9337120c3e0b0a7c7303.json` → `local_sections`. Pages: [1]. Source blocks: 63. No new extraction/block detection was run. Original PDF was not independently examined for this evaluation.

Correctly maps two work records, three projects, academic grades and three course providers from blocks with faulty local labels. Spoken languages remain empty. Professional headline Software Engineer is taken from a job role rather than an explicit headline, so its headline interpretation is ambiguous. The chief failures are missing/incorrect field citations, especially all_skills duplicates and misaligned technical-skill indices.

- Critical-field agreement proxy: **25/25 = 100.0%**.
- Same-block local heuristic baseline on the same critical set: **7/25**.
- Raw field citation contract: **94/153 = 61.44%**.
- Populated-value source-block assessment: {"correct_mapping": 152, "not_populated": 16, "ambiguous": 1}.
- Human-verified/PDF-verified accuracy: **not established**.

## Complete mapping output

[Mapping JSON](mapping.json) · [Unmodified provider mapping and citations](mapping-raw.json) · [Full provider envelope/usage](response-envelope.json) · [Saved source blocks](source-blocks.md) · [Every evaluated field](field-evaluation.json)

```json
{
  "contact": {
    "full_name": "D Dhanush",
    "email": "dhanushdevaraj17@gmail.com",
    "phone": "9380249870",
    "location": null,
    "linkedin_url": "https://www.linkedin.com/in/d-dhanush-a733521b3/",
    "github_url": "https://github.com/ddhanushd",
    "portfolio_url": null
  },
  "professional_title": "Software Engineer",
  "summary": null,
  "total_experience_years": null,
  "skills": {
    "technical_skills": [
      "Java",
      "Python",
      "JavaScript",
      "SQL",
      "Core Java",
      "Spring Boot",
      "Spring",
      "Spring Security",
      "Hibernate",
      "JPA",
      "JUnit",
      "Mockito",
      "Angular",
      "Microservices",
      "REST APIs",
      "HTML/CSS",
      "SOLID Principles",
      "Design Patterns",
      "OAuth2",
      "JWT",
      "LLMs",
      "Ollama"
    ],
    "tools_and_platforms": [
      "MySQL",
      "PostgreSQL",
      "MongoDB",
      "Redis",
      "Docker",
      "AWS",
      "Maven",
      "Git",
      "GitHub",
      "Postman",
      "Swagger",
      "Okta",
      "Feign Client",
      "Spring Cloud API Gateway",
      "Eureka Server"
    ],
    "domain_and_functional": [
      "AI Integration",
      "Circuit Breaker patterns"
    ],
    "soft_skills": [],
    "all_skills": [
      "Java",
      "Python",
      "JavaScript",
      "SQL",
      "Core Java",
      "Spring Boot",
      "Spring",
      "Spring Security",
      "Hibernate",
      "JPA",
      "JUnit",
      "Mockito",
      "Angular",
      "Microservices",
      "REST APIs",
      "HTML/CSS",
      "SOLID Principles",
      "Design Patterns",
      "OAuth2",
      "JWT",
      "LLMs",
      "Ollama",
      "MySQL",
      "PostgreSQL",
      "MongoDB",
      "Redis",
      "Docker",
      "AWS",
      "Maven",
      "Git",
      "GitHub",
      "Postman",
      "Swagger",
      "Okta",
      "Feign Client",
      "Spring Cloud API Gateway",
      "Eureka Server",
      "AI Integration",
      "Circuit Breaker patterns"
    ]
  },
  "experience": [
    {
      "company": "CitiusTech Health Technologies Pvt. Ltd.",
      "role": "Software Engineer",
      "start_date": "July 2022",
      "end_date": "September 2023",
      "duration": "July 2022 – September 2023",
      "location": "Bangalore",
      "responsibilities": [
        "Developed and maintained RESTful APIs using Spring Boot, enhancing application functionality and boosting performance by 30%.",
        "Designed Microservices architecture, boosting scalability by 40% and optimizing resource allocation, while collaborating with cross-functional teams.",
        "Integrated software components, resolving critical bugs and reducing downtime by 25%, improving system stability and development efficiency."
      ],
      "technologies": [
        "Spring Boot",
        "Microservices",
        "REST APIs"
      ]
    },
    {
      "company": "Independent Projects",
      "role": "Freelance Java Developer",
      "start_date": "October 2023",
      "end_date": "Present",
      "duration": "October 2023 – Present",
      "location": null,
      "responsibilities": [
        "Built scalable microservices with Spring Boot & Spring Security (JWT, Okta OAuth2), and containerized applications using Docker for deployment on AWS, reducing deployment effort by 30%.",
        "Engineered a PDF Q&A pipeline with chunk extraction, embedding storage in DB, and integrated Ollama LLM for AI-driven responses, improving retrieval accuracy by 25%.",
        "Explored performance enhancements by integrating Redis caching into full-stack apps with Angular & JavaScript, accelerating response speed by 20%."
      ],
      "technologies": [
        "Spring Boot",
        "Spring Security",
        "JWT",
        "Okta",
        "OAuth2",
        "Docker",
        "AWS",
        "Redis",
        "Angular",
        "JavaScript",
        "Ollama"
      ]
    }
  ],
  "education": [
    {
      "institution": "M S Ramaiah Institute of Technology",
      "degree": "B.E.",
      "field_of_study": "Electronics and Communication Engineering",
      "start_year": "August 2018",
      "graduation_year": "July 2022",
      "grade_or_gpa": "CGPA: 7.85/10"
    },
    {
      "institution": "Sarvodaya PU College",
      "degree": "Intermediate (PUC)",
      "field_of_study": "Science",
      "start_year": "June 2016",
      "graduation_year": "May 2018",
      "grade_or_gpa": "Percentage: 89.83%"
    }
  ],
  "certifications": [
    {
      "name": "Java Backend: Spring Core, Spring MVC, Spring Boot, Spring JPA and REST, and Docker on Pluralsight Bootcamp and Certification badge.",
      "issuer": "Pluralsight",
      "issue_year": null
    },
    {
      "name": "MongoDB Developer’s Toolkit: CRUD Mastery with Java on GeeksforGeeks.",
      "issuer": "GeeksforGeeks",
      "issue_year": null
    },
    {
      "name": "Java (Basic) on HackerRank.",
      "issuer": "HackerRank",
      "issue_year": null
    }
  ],
  "projects": [
    {
      "name": "Healthcare Patient Management System",
      "description": "Crafted a microservices-based system for managing patient data and appointments for 10,000+ patients, optimizing MySQL and PostgreSQL queries for enhanced performance. Collaborated with senior engineers to improve system scalability and reduce processing time by 25%, ensuring smooth integration during QA/UAT phases. Resolved production issues, minimizing system downtime by 15% and maintaining stable performance.",
      "role": null,
      "technologies": [
        "MySQL",
        "PostgreSQL",
        "Microservices"
      ],
      "url": null
    },
    {
      "name": "Hotel Rating Microservices Application",
      "description": "Architected a microservices-based solution for core services (User, Rating, Hotel), improving scalability by 40% and reducing communication latency by 30% through REST APIs, Feign Client, and Spring Cloud API Gateway. Deployed Eureka Server for service discovery and implemented Circuit Breaker patterns, ensuring 99.9% uptime and enhancing system reliability by 25%. Secured microservices with OAuth2 and Okta, optimizing performance with Redis caching and improving response times by 25%.",
      "role": null,
      "technologies": [
        "REST APIs",
        "Feign Client",
        "Spring Cloud API Gateway",
        "Eureka Server",
        "OAuth2",
        "Okta",
        "Redis"
      ],
      "url": null
    },
    {
      "name": "Stock Market Investing Application",
      "description": "Constructed a Spring Boot application to manage stock portfolios for 500+ users. Architected JWT authentication and created RESTful APIs for CRUD operations, handling 100+ requests daily. Leveraged JPA to optimize database interactions, ensuring data integrity and reducing errors by 30%.",
      "role": null,
      "technologies": [
        "Spring Boot",
        "JWT",
        "REST APIs",
        "JPA"
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
| `/contact/full_name` | D Dhanush | correct_mapping | citation_supported | e0:0:9 |
| `/contact/email` | dhanushdevaraj17@gmail.com | correct_mapping | citation_supported | e1:0:60 |
| `/contact/phone` | 9380249870 | correct_mapping | citation_supported | e1:0:60 |
| `/contact/location` | None | not_populated | not_populated |  |
| `/contact/linkedin_url` | https://www.linkedin.com/in/d-dhanush-a733521b3/ | correct_mapping | citation_supported | e1:60:157 |
| `/contact/github_url` | https://github.com/ddhanushd | correct_mapping | citation_supported | e1:60:157 |
| `/contact/portfolio_url` | None | not_populated | not_populated |  |
| `/professional_title` | Software Engineer | ambiguous | citation_supported | e6:16:87 |
| `/summary` | None | not_populated | not_populated |  |
| `/total_experience_years` | None | not_populated | not_populated |  |
| `/skills/technical_skills/0` | Java | correct_mapping | citation_supported | e2:7:58 |
| `/skills/technical_skills/1` | Python | correct_mapping | citation_supported | e2:7:58 |
| `/skills/technical_skills/2` | JavaScript | correct_mapping | citation_supported | e2:7:58 |
| `/skills/technical_skills/3` | SQL | correct_mapping | citation_supported | e2:7:58 |
| `/skills/technical_skills/4` | Core Java | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/5` | Spring Boot | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/6` | Spring | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/7` | Spring Security | correct_mapping | citation_error | e12:25:139 |
| `/skills/technical_skills/8` | Hibernate | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/9` | JPA | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/10` | JUnit | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/11` | Mockito | correct_mapping | citation_supported | e3:0:95 |
| `/skills/technical_skills/12` | Angular | correct_mapping | citation_error | e3:0:95 |
| `/skills/technical_skills/13` | Microservices | correct_mapping | citation_error | e5:0:107 |
| `/skills/technical_skills/14` | REST APIs | correct_mapping | citation_error | e5:0:107 |
| `/skills/technical_skills/15` | HTML/CSS | correct_mapping | citation_error | e5:0:107 |
| `/skills/technical_skills/16` | SOLID Principles | correct_mapping | citation_error | e5:0:107 |
| `/skills/technical_skills/17` | Design Patterns | correct_mapping | citation_error | e5:0:107 |
| `/skills/technical_skills/18` | OAuth2 | correct_mapping | citation_error | e12:25:139 |
| `/skills/technical_skills/19` | JWT | correct_mapping | citation_error | e12:25:139 |
| `/skills/technical_skills/20` | LLMs | correct_mapping | citation_error | e5:0:107 |
| `/skills/technical_skills/21` | Ollama | correct_mapping | citation_error | e5:0:107 |
| `/skills/tools_and_platforms/0` | MySQL | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/1` | PostgreSQL | correct_mapping | citation_supported | e17:113:167 |
| `/skills/tools_and_platforms/2` | MongoDB | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/3` | Redis | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/4` | Docker | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/5` | AWS | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/6` | Maven | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/7` | Git | correct_mapping | citation_supported | e1:60:157 |
| `/skills/tools_and_platforms/8` | GitHub | correct_mapping | citation_supported | e1:60:157 |
| `/skills/tools_and_platforms/9` | Postman | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/10` | Swagger | correct_mapping | citation_supported | e4:0:91 |
| `/skills/tools_and_platforms/11` | Okta | correct_mapping | citation_supported | e12:25:139 |
| `/skills/tools_and_platforms/12` | Feign Client | correct_mapping | citation_supported | e21:117:217 |
| `/skills/tools_and_platforms/13` | Spring Cloud API Gateway | correct_mapping | citation_supported | e21:117:217 |
| `/skills/tools_and_platforms/14` | Eureka Server | correct_mapping | citation_supported | e22:0:109 |
| `/skills/domain_and_functional/0` | AI Integration | correct_mapping | citation_supported | e5:0:107 |
| `/skills/domain_and_functional/1` | Circuit Breaker patterns | correct_mapping | citation_supported | e22:0:109 |
| `/skills/soft_skills` | [] | not_populated | not_populated |  |
| `/skills/all_skills/0` | Java | correct_mapping | citation_error | e2:7:58 |
| `/skills/all_skills/1` | Python | correct_mapping | citation_error | e2:7:58 |
| `/skills/all_skills/2` | JavaScript | correct_mapping | citation_error | e2:7:58 |
| `/skills/all_skills/3` | SQL | correct_mapping | citation_error | e2:7:58 |
| `/skills/all_skills/4` | Core Java | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/5` | Spring Boot | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/6` | Spring | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/7` | Spring Security | correct_mapping | citation_error | e12:25:139 |
| `/skills/all_skills/8` | Hibernate | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/9` | JPA | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/10` | JUnit | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/11` | Mockito | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/12` | Angular | correct_mapping | citation_error | e3:0:95 |
| `/skills/all_skills/13` | Microservices | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/14` | REST APIs | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/15` | HTML/CSS | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/16` | SOLID Principles | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/17` | Design Patterns | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/18` | OAuth2 | correct_mapping | citation_error | e12:25:139 |
| `/skills/all_skills/19` | JWT | correct_mapping | citation_error | e12:25:139 |
| `/skills/all_skills/20` | LLMs | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/21` | Ollama | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/22` | MySQL | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/23` | PostgreSQL | correct_mapping | citation_error | e17:113:167 |
| `/skills/all_skills/24` | MongoDB | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/25` | Redis | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/26` | Docker | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/27` | AWS | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/28` | Maven | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/29` | Git | correct_mapping | citation_error | e1:60:157 |
| `/skills/all_skills/30` | GitHub | correct_mapping | citation_error | e1:60:157 |
| `/skills/all_skills/31` | Postman | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/32` | Swagger | correct_mapping | citation_error | e4:0:91 |
| `/skills/all_skills/33` | Okta | correct_mapping | citation_error | e12:25:139 |
| `/skills/all_skills/34` | Feign Client | correct_mapping | citation_error | e21:117:217 |
| `/skills/all_skills/35` | Spring Cloud API Gateway | correct_mapping | citation_error | e21:117:217 |
| `/skills/all_skills/36` | Eureka Server | correct_mapping | citation_error | e22:0:109 |
| `/skills/all_skills/37` | AI Integration | correct_mapping | citation_error | e5:0:107 |
| `/skills/all_skills/38` | Circuit Breaker patterns | correct_mapping | citation_error | e22:0:109 |
| `/experience/0/company` | CitiusTech Health Technologies Pvt. Ltd. | correct_mapping | citation_supported | e6:16:87 |
| `/experience/0/role` | Software Engineer | correct_mapping | citation_supported | e6:16:87 |
| `/experience/0/start_date` | July 2022 | correct_mapping | citation_supported | e7:0:26 |
| `/experience/0/end_date` | September 2023 | correct_mapping | citation_supported | e7:0:26 |
| `/experience/0/duration` | July 2022 – September 2023 | correct_mapping | citation_supported | e7:0:26 |
| `/experience/0/location` | Bangalore | correct_mapping | citation_supported | e6:16:87 |
| `/experience/0/responsibilities/0` | Developed and maintained RESTful APIs using Spring Boot, enhancing application functionality and boosting performance by 30%. | correct_mapping | citation_supported | e7:29:134, e8:0:19 |
| `/experience/0/responsibilities/1` | Designed Microservices architecture, boosting scalability by 40% and optimizing resource allocation, while collaborating with cross-functional teams. | correct_mapping | citation_supported | e9:0:107, e9:107:149 |
| `/experience/0/responsibilities/2` | Integrated software components, resolving critical bugs and reducing downtime by 25%, improving system stability and development efficiency. | correct_mapping | citation_supported | e10:0:117, e10:117:140 |
| `/experience/0/technologies/0` | Spring Boot | correct_mapping | citation_supported | e3:0:95 |
| `/experience/0/technologies/1` | Microservices | correct_mapping | citation_supported | e5:0:107 |
| `/experience/0/technologies/2` | REST APIs | correct_mapping | citation_error | e5:0:107 |
| `/experience/1/company` | Independent Projects | correct_mapping | citation_supported | e11:0:47 |
| `/experience/1/role` | Freelance Java Developer | correct_mapping | citation_supported | e11:0:47 |
| `/experience/1/start_date` | October 2023 | correct_mapping | citation_supported | e12:0:22 |
| `/experience/1/end_date` | Present | correct_mapping | citation_supported | e12:0:22 |
| `/experience/1/duration` | October 2023 – Present | correct_mapping | citation_supported | e12:0:22 |
| `/experience/1/location` | None | not_populated | not_populated |  |
| `/experience/1/responsibilities/0` | Built scalable microservices with Spring Boot & Spring Security (JWT, Okta OAuth2), and containerized applications using Docker for deployment on AWS, reducing deployment effort by 30%. | correct_mapping | citation_supported | e12:25:139, e13:0:70 |
| `/experience/1/responsibilities/1` | Engineered a PDF Q&A pipeline with chunk extraction, embedding storage in DB, and integrated Ollama LLM for AI-driven responses, improving retrieval accuracy by 25%. | correct_mapping | citation_supported | e14:0:108, e14:108:165 |
| `/experience/1/responsibilities/2` | Explored performance enhancements by integrating Redis caching into full-stack apps with Angular & JavaScript, accelerating response speed by 20%. | correct_mapping | citation_supported | e15:0:111, e15:111:146 |
| `/experience/1/technologies/0` | Spring Boot | correct_mapping | citation_supported | e3:0:95 |
| `/experience/1/technologies/1` | Spring Security | correct_mapping | citation_supported | e12:25:139 |
| `/experience/1/technologies/2` | JWT | correct_mapping | citation_supported | e12:25:139 |
| `/experience/1/technologies/3` | Okta | correct_mapping | citation_supported | e12:25:139 |
| `/experience/1/technologies/4` | OAuth2 | correct_mapping | citation_error | e12:25:139 |
| `/experience/1/technologies/5` | Docker | correct_mapping | citation_error | e4:0:91 |
| `/experience/1/technologies/6` | AWS | correct_mapping | citation_error | e4:0:91 |
| `/experience/1/technologies/7` | Redis | correct_mapping | citation_error | e4:0:91 |
| `/experience/1/technologies/8` | Angular | correct_mapping | citation_error | e3:0:95 |
| `/experience/1/technologies/9` | JavaScript | correct_mapping | citation_error | e2:7:58 |
| `/experience/1/technologies/10` | Ollama | correct_mapping | citation_error | e5:0:107 |
| `/education/0/institution` | M S Ramaiah Institute of Technology | correct_mapping | citation_supported | e26:60:95 |
| `/education/0/degree` | B.E. | correct_mapping | citation_supported | e26:10:60 |
| `/education/0/field_of_study` | Electronics and Communication Engineering | correct_mapping | citation_supported | e26:10:60 |
| `/education/0/start_year` | August 2018 | correct_mapping | citation_supported | e27:0:24 |
| `/education/0/graduation_year` | July 2022 | correct_mapping | citation_supported | e7:0:26 |
| `/education/0/grade_or_gpa` | CGPA: 7.85/10 | correct_mapping | citation_supported | e27:24:37 |
| `/education/1/institution` | Sarvodaya PU College | correct_mapping | citation_supported | e28:29:49 |
| `/education/1/degree` | Intermediate (PUC) | correct_mapping | citation_supported | e28:0:29 |
| `/education/1/field_of_study` | Science | correct_mapping | citation_supported | e28:0:29 |
| `/education/1/start_year` | June 2016 | correct_mapping | citation_supported | e29:0:21 |
| `/education/1/graduation_year` | May 2018 | correct_mapping | citation_supported | e29:0:21 |
| `/education/1/grade_or_gpa` | Percentage: 89.83% | correct_mapping | citation_supported | e29:21:39 |
| `/certifications/0/name` | Java Backend: Spring Core, Spring MVC, Spring Boot, Spring JPA and REST, and Docker on Pluralsight Bootcamp and Certification badge. | correct_mapping | citation_supported | e31:0:99, e31:99:132 |
| `/certifications/0/issuer` | Pluralsight | correct_mapping | citation_supported | e31:0:99 |
| `/certifications/0/issue_year` | None | not_populated | not_populated |  |
| `/certifications/1/name` | MongoDB Developer’s Toolkit: CRUD Mastery with Java on GeeksforGeeks. | correct_mapping | citation_supported | e32:2:71 |
| `/certifications/1/issuer` | GeeksforGeeks | correct_mapping | citation_supported | e32:2:71 |
| `/certifications/1/issue_year` | None | not_populated | not_populated |  |
| `/certifications/2/name` | Java (Basic) on HackerRank. | correct_mapping | citation_supported | e32:74:101 |
| `/certifications/2/issuer` | HackerRank | correct_mapping | citation_supported | e32:74:101 |
| `/certifications/2/issue_year` | None | not_populated | not_populated |  |
| `/projects/0/name` | Healthcare Patient Management System | correct_mapping | citation_supported | e16:13:52 |
| `/projects/0/description` | Crafted a microservices-based system for managing patient data and appointments for 10,000+ patients, optimizing MySQL and PostgreSQL queries for enhanced performance. Collaborated with senior engineers to improve system scalability and reduce proces… | correct_mapping | citation_supported | e17:0:113, e17:113:167, e18:0:109, e18:109:149, e19:0:97 |
| `/projects/0/role` | None | not_populated | not_populated |  |
| `/projects/0/technologies/0` | MySQL | correct_mapping | citation_supported | e4:0:91 |
| `/projects/0/technologies/1` | PostgreSQL | correct_mapping | citation_supported | e17:113:167 |
| `/projects/0/technologies/2` | Microservices | correct_mapping | citation_supported | e5:0:107 |
| `/projects/0/url` | None | not_populated | not_populated |  |
| `/projects/1/name` | Hotel Rating Microservices Application | correct_mapping | citation_supported | e20:0:41 |
| `/projects/1/description` | Architected a microservices-based solution for core services (User, Rating, Hotel), improving scalability by 40% and reducing communication latency by 30% through REST APIs, Feign Client, and Spring Cloud API Gateway. Deployed Eureka Server for servi… | correct_mapping | citation_supported | e21:0:117, e21:117:217, e22:0:109, e22:109:149, e23:0:109, e23:109:122 |
| `/projects/1/role` | None | not_populated | not_populated |  |
| `/projects/1/technologies/0` | REST APIs | correct_mapping | citation_supported | e5:0:107 |
| `/projects/1/technologies/1` | Feign Client | correct_mapping | citation_supported | e21:117:217 |
| `/projects/1/technologies/2` | Spring Cloud API Gateway | correct_mapping | citation_supported | e21:117:217 |
| `/projects/1/technologies/3` | Eureka Server | correct_mapping | citation_supported | e22:0:109 |
| `/projects/1/technologies/4` | OAuth2 | correct_mapping | citation_supported | e12:25:139 |
| `/projects/1/technologies/5` | Okta | correct_mapping | citation_supported | e12:25:139 |
| `/projects/1/technologies/6` | Redis | correct_mapping | citation_supported | e4:0:91 |
| `/projects/1/url` | None | not_populated | not_populated |  |
| `/projects/2/name` | Stock Market Investing Application | correct_mapping | citation_supported | e24:0:37 |
| `/projects/2/description` | Constructed a Spring Boot application to manage stock portfolios for 500+ users. Architected JWT authentication and created RESTful APIs for CRUD operations, handling 100+ requests daily. Leveraged JPA to optimize database interactions, ensuring data… | correct_mapping | citation_supported | e25:0:80, e25:83:189, e25:192:292 |
| `/projects/2/role` | None | not_populated | not_populated |  |
| `/projects/2/technologies/0` | Spring Boot | correct_mapping | citation_supported | e3:0:95 |
| `/projects/2/technologies/1` | JWT | correct_mapping | citation_supported | e12:25:139 |
| `/projects/2/technologies/2` | REST APIs | correct_mapping | citation_error | e5:0:107 |
| `/projects/2/technologies/3` | JPA | correct_mapping | citation_supported | e3:0:95 |
| `/projects/2/url` | None | not_populated | not_populated |  |
| `/languages` | [] | not_populated | not_populated |  |

## Predeclared critical opportunities

Degree plus field_of_study may satisfy one reference degree opportunity. Original month-year strings are accepted when the expected year matches; this does not remove date-association ambiguity. Country codes, punctuation/whitespace, labels such as CGPA and enclosing lab/organization context are normalized as documented in the main report.

| Reference | Target | Expected source fact | Actual value | Result |
|---|---|---|---|---|
| f020 | root.contact.full_name | D Dhanush | D Dhanush | correct_mapping |
| f021 | root.contact.email | dhanushdevaraj17@gmail.com | dhanushdevaraj17@gmail.com | correct_mapping |
| f022 | root.contact.phone | 9380249870 | 9380249870 | correct_mapping |
| f023 | root.contact.linkedin_url | https://www.linkedin.com/in/d-dhanush-a733521b3/ | https://www.linkedin.com/in/d-dhanush-a733521b3/ | correct_mapping |
| f024 | root.contact.github_url | https://github.com/ddhanushd | https://github.com/ddhanushd | correct_mapping |
| f025 | experience.company | CitiusTech Health Technologies Pvt. Ltd. | CitiusTech Health Technologies Pvt. Ltd. | correct_mapping |
| f026 | experience.role | Software Engineer | Software Engineer | correct_mapping |
| f027 | experience.start_date | July 2022 | July 2022 | correct_mapping |
| f028 | experience.end_date | September 2023 | September 2023 | correct_mapping |
| f029 | experience.company | Independent Projects | Independent Projects | correct_mapping |
| f030 | experience.role | Freelance Java Developer | Freelance Java Developer | correct_mapping |
| f031 | experience.start_date | October 2023 | October 2023 | correct_mapping |
| f032 | experience.end_date | Present | Present | correct_mapping |
| f033 | education.degree | B.E. in Electronics and Communication Engineering | B.E. | correct_mapping |
| f034 | education.institution | M S Ramaiah Institute of Technology | M S Ramaiah Institute of Technology | correct_mapping |
| f035 | education.graduation_year | 2022 | July 2022 | correct_mapping |
| f036 | education.grade_or_gpa | 7.85/10 | CGPA: 7.85/10 | correct_mapping |
| f037 | education.degree | Intermediate (PUC) – Science | Intermediate (PUC) | correct_mapping |
| f038 | education.institution | Sarvodaya PU College | Sarvodaya PU College | correct_mapping |
| f039 | education.graduation_year | 2018 | May 2018 | correct_mapping |
| f040 | education.grade_or_gpa | 89.83% | Percentage: 89.83% | correct_mapping |
| f041 | projects.name | Healthcare Patient Management System | Healthcare Patient Management System | correct_mapping |
| f042 | projects.name | Hotel Rating Microservices Application | Hotel Rating Microservices Application | correct_mapping |
| f043 | projects.name | Stock Market Investing Application | Stock Market Investing Application | correct_mapping |
| f044 | certifications.issuer | HackerRank | HackerRank | correct_mapping |

## Provider missing-information statements

These are provider claims, not independent truth. Compare with field-evaluation.json for analyst disagreements and actual mapping omissions.

```json
[
  {
    "path": "/contact/location",
    "reason": "not_in_source",
    "detail": "No city/state/country of residence is stated in the source contact block.",
    "source_ids": []
  },
  {
    "path": "/professional_title",
    "reason": "ambiguous_source",
    "detail": "No explicit headline section exists; 'Software Engineer' is taken from the first job title row.",
    "source_ids": [
      "e6:16:87"
    ]
  },
  {
    "path": "/summary",
    "reason": "not_in_source",
    "detail": "The resume contains no professional summary or objective statement.",
    "source_ids": []
  },
  {
    "path": "/total_experience_years",
    "reason": "not_in_source",
    "detail": "No explicit statement of total years of experience is present; tenure was not calculated.",
    "source_ids": []
  },
  {
    "path": "/languages",
    "reason": "not_in_source",
    "detail": "No spoken languages are listed. The 'Languages' skill label was programming languages only and was mapped to skills.",
    "source_ids": [
      "e2:7:58"
    ]
  },
  {
    "path": "/skills/soft_skills",
    "reason": "not_in_source",
    "detail": "No soft skills are explicitly listed as skills; 'collaborating with cross-functional teams' appears only within a responsibility bullet.",
    "source_ids": []
  },
  {
    "path": "/certifications/0/name",
    "reason": "ambiguous_source",
    "detail": "Source describes a Pluralsight bootcamp and certification badge; listed as a course/certification item without independent verification.",
    "source_ids": [
      "e31:0:99",
      "e31:99:132"
    ]
  },
  {
    "path": "/certifications/1/name",
    "reason": "ambiguous_source",
    "detail": "GeeksforGeeks item appears to be a course/toolkit; represented as stated without independent verification.",
    "source_ids": [
      "e32:2:71"
    ]
  },
  {
    "path": "/certifications/2/name",
    "reason": "ambiguous_source",
    "detail": "HackerRank 'Java (Basic)' is a skill test/badge; represented as stated.",
    "source_ids": [
      "e32:74:101"
    ]
  },
  {
    "path": "/experience/1/company",
    "reason": "ambiguous_source",
    "detail": "'Independent Projects' indicates freelance self-employment rather than a named employer.",
    "source_ids": [
      "e11:0:47"
    ]
  },
  {
    "path": "/projects/0/role",
    "reason": "not_in_source",
    "detail": "No explicit candidate project role is stated beyond collaborative description.",
    "source_ids": []
  },
  {
    "path": "/projects/1/role",
    "reason": "not_in_source",
    "detail": "No explicit candidate project role is stated.",
    "source_ids": []
  },
  {
    "path": "/projects/2/role",
    "reason": "not_in_source",
    "detail": "No explicit candidate project role is stated.",
    "source_ids": []
  },
  {
    "path": "/education/0/field_of_study",
    "reason": "ambiguous_source",
    "detail": "Degree line and institution line share one source block; field 'Electronics and Communication Engineering' follows 'B.E. in'.",
    "source_ids": [
      "e26:10:60"
    ]
  },
  {
    "path": "/education/0/start_year, /education/0/graduation_year",
    "reason": "ambiguous_source",
    "detail": "Date range appears in a separate block from the degree/institution rows; association is inferred by adjacency.",
    "source_ids": [
      "e27:0:24"
    ]
  },
  {
    "path": "/education/1/start_year, /education/1/graduation_year",
    "reason": "ambiguous_source",
    "detail": "Date range appears in a separate block from the PUC row; association is inferred by adjacency.",
    "source_ids": [
      "e29:0:21"
    ]
  },
  {
    "path": "/experience/1/location",
    "reason": "not_in_source",
    "detail": "No location is given for the freelance role.",
    "source_ids": []
  },
  {
    "path": "/total_experience_years ambiguity",
    "reason": "ambiguous_source",
    "detail": "Experience dates span July 2022–September 2023 and October 2023–Present with no explicit total; do not treat any calculated value as source-stated.",
    "source_ids": [
      "e7:0:26",
      "e12:0:22"
    ]
  }
]
```

## Provider upstream observations

```json
[
  "Source blocks contain (cid:NNN) glyph artifacts in the contact/icons line (e.g., (cid:263), (cid:294), (cid:93), (cid:97)); contact values were extracted around them.",
  "Local categories mislabel skill lines as 'languages' and project entries as 'experience'; mapping used source order and content rather than local labels.",
  "Resume has no dedicated summary, spoken-language, soft-skill, or portfolio sections; schema slots left empty.",
  "No awards, memberships, or publications sections are present in the provided blocks; nothing required preservation there.",
  "The 'Skills' section label block 'Skills ' (e2:0:7) and section headers ('Work Experience', 'Project Work', 'Education', 'Certifications') are headers only and were not treated as data values.",
  "Project descriptions in source have no explicit role/employer attribution; kept as projects, not as additional employment records.",
  "Certifications line 0 describes bootcamp plus certification badge; source is ambiguous about formal certification status and is preserved verbatim rather than normalized."
]
```
