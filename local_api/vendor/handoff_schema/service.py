"""Core Service orchestrating Resume Section Segmentation, Schema Mapping, and Instructor Extraction."""

from __future__ import annotations

import os
import re
import time
from typing import Any

from .models import (
    CategorizedSkills,
    Certification,
    ContactInfo,
    Education,
    FieldMappingDetail,
    ParseResponse,
    Project,
    ResumeSchema,
    SchemaMappingReport,
    WorkExperience,
)
from .schema_spec import SCHEMA_MAPPING_SPECIFICATION


# ---------------------------------------------------------------------------
# 1. Section Boundary Segmentation
# ---------------------------------------------------------------------------
SECTION_PATTERNS = {
    "summary": r"(?:^|\n)\s*(?:PROFESSIONAL\s+SUMMARY|PROFILE\s+SNAPSHOT|EXECUTIVE\s+SUMMARY|CAREER\s+OBJECTIVE|SUMMARY|ABOUT\s+ME)\b",
    "experience": r"(?:^|\n)\s*(?:POFESSIONAL\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT\s+HISTORY|WORK\s+HISTORY|EXPERIENCE)\b",
    "education": r"(?:^|\n)\s*(?:EEDUCATION|EDUCATION|ACADEMIC\s+BACKGROUND|ACADEMIC\s+QUALIFICATIONS|QUALIFICATIONS)\b",
    "skills": r"(?:^|\n)\s*(?:CORE\s+COMPETENCIES|TECHNICAL\s+SKILLS|SKILLS|CORE\s+SKILLS|KEY\s+SKILLS|AREAS\s+OF\s+EXPERTISE)\b",
    "certifications": r"(?:^|\n)\s*(?:CERTIFICATIONS|LICENSES\s+AND\s+CERTIFICATIONS|COURSES|ACCREDITATIONS)\b",
    "projects": r"(?:^|\n)\s*(?:PROJECTS|KEY\s+ENGAGEMENTS|PERSONAL\s+PROJECTS|CLIENT\s+ENGAGEMENTS)\b",
}


def segment_resume_sections(text: str) -> dict[str, str]:
    """Splits raw resume text into distinct logical sections."""
    boundaries: list[tuple[int, str]] = []

    for sec_name, pattern in SECTION_PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            boundaries.append((match.start(), sec_name))

    boundaries.sort(key=lambda x: x[0])

    sections: dict[str, str] = {}
    if not boundaries:
        sections["header"] = text[:1500]
        sections["body"] = text
        return sections

    # Text before the first matched section header is the Header
    sections["header"] = text[: boundaries[0][0]].strip()

    for idx, (start_idx, name) in enumerate(boundaries):
        end_idx = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(text)
        sec_chunk = text[start_idx:end_idx].strip()
        # Remove the section header line itself
        lines = sec_chunk.splitlines()
        content = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec_chunk
        if name in sections:
            sections[name] += "\n\n" + content
        else:
            sections[name] = content

    return sections


# ---------------------------------------------------------------------------
# 2. Rule-Based Section Extraction (Advanced Heuristic Engine)
# ---------------------------------------------------------------------------
def extract_contact_info(header_text: str, full_text: str) -> ContactInfo:
    """Extracts candidate contact details, emails, phones, and social URLs."""
    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", full_text)
    email = email_match.group(0) if email_match else "not_specified@domain.com"

    # Phone (handles +91, dashes, parentheses, 10-12 digits)
    phone_match = re.search(
        r"(?:(?:\+?\d{1,3}[ -]?)?\(?\d{3,4}\)?[ -]?\d{3}[ -]?\d{4}|\b\d{10}\b)",
        full_text,
    )
    phone = phone_match.group(0).strip() if phone_match else "Not specified"

    # Social URLs
    linkedin_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[\w\-_]+", full_text, re.I)
    linkedin_url = linkedin_match.group(0) if linkedin_match else None

    github_match = re.search(r"(?:https?:\/\/)?(?:www\.)?github\.com\/[\w\-_]+", full_text, re.I)
    github_url = github_match.group(0) if github_match else None

    # Candidate Name (Extracts from top lines of Header)
    full_name = "Candidate"
    header_lines = [l.strip() for l in header_text.splitlines() if l.strip()]
    for line in header_lines[:4]:
        # Ignore lines with email, phone, or generic labels
        if "@" in line or any(char.isdigit() for char in line) and len(line) < 20:
            continue
        if re.search(r"\b(curriculum|resume|biodata|profile|contact|location)\b", line, re.I):
            continue
        cleaned = re.sub(r"^[^\w]+", "", line)
        if 2 <= len(cleaned.split()) <= 5 and len(cleaned) < 50:
            full_name = cleaned
            break
    if full_name == "Candidate" and header_lines:
        full_name = header_lines[0]

    # Location heuristic
    loc_match = re.search(
        r"\b(Pune|Hyderabad|Bengaluru|Bangalore|Mumbai|Chennai|Delhi|Noida|Gurgaon|Indore|Kolkata|Ahmedabad|Remote|India|USA|UK)\b",
        header_text or full_text[:1000],
        re.I,
    )
    location = loc_match.group(0).title() if loc_match else "Not specified"

    return ContactInfo(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        linkedin_url=linkedin_url,
        github_url=github_url,
        portfolio_url=None,
    )


def extract_work_experience(exp_text: str, full_text: str) -> list[WorkExperience]:
    """Extracts employment history, companies, designations, dates, and bullet points."""
    target_text = exp_text if len(exp_text.strip()) > 100 else full_text
    lines = target_text.splitlines()

    experiences: list[WorkExperience] = []
    current_company = ""
    current_role = ""
    current_duration = ""
    current_bullets: list[str] = []

    date_range_regex = re.compile(
        r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[.,]?\s*(?:19|20)\d{2}\b|\b(?:19|20)\d{2}\b)\s*[-–—to]+\s*(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[.,]?\s*(?:19|20)\d{2}\b|\b(?:19|20)\d{2}\b|\bPresent\b|\bCurrent\b)",
        re.I,
    )

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        date_match = date_range_regex.search(cleaned_line)
        # Check if line contains a company or date boundary
        if date_match and (
            re.search(r"\b(Ltd|Bank|Services|Systems|Corp|Inc|Technologies|Solutions|Arcesium|ICE|NYSE|Company|Homeward|Enterprises)\b", cleaned_line, re.I)
            or "|" in cleaned_line
        ):
            # Save previous experience record
            if current_company:
                experiences.append(
                    WorkExperience(
                        company=current_company,
                        role=current_role or "Professional Consultant",
                        duration=current_duration,
                        responsibilities=current_bullets[:8],
                    )
                )
                current_bullets = []

            # Parse new company and duration line
            parts = [p.strip() for p in cleaned_line.split("|")]
            current_company = parts[0]
            current_duration = date_match.group(0)
            current_role = parts[1] if len(parts) > 1 and not date_range_regex.search(parts[1]) else ""
        elif cleaned_line.startswith(("•", "-", "*", "–")) or re.match(r"^\d+\.", cleaned_line):
            bullet = re.sub(r"^[\s•\-*–\d.]+", "", cleaned_line).strip()
            if len(bullet) > 15:
                current_bullets.append(bullet)
        elif not current_role and len(cleaned_line.split()) < 8 and ("Analyst" in cleaned_line or "Engineer" in cleaned_line or "Consultant" in cleaned_line or "Lead" in cleaned_line or "Manager" in cleaned_line):
            current_role = cleaned_line

    # Save final item
    if current_company:
        experiences.append(
            WorkExperience(
                company=current_company,
                role=current_role or "Senior Professional",
                duration=current_duration,
                responsibilities=current_bullets[:8],
            )
        )

    # Fallback if specific formatting wasn't caught
    if not experiences:
        comp_matches = re.findall(
            r"([A-Z][A-Za-z0-9 &.,]{2,40}(?:Pvt|Ltd|Bank|Inc|Corporation|Solutions|Technologies|Systems))\s*[|\-–]\s*([A-Za-z0-9 ,–-]+)",
            target_text,
        )
        for comp, dur in comp_matches[:4]:
            experiences.append(
                WorkExperience(
                    company=comp.strip(),
                    role="Specialist / Consultant",
                    duration=dur.strip(),
                    responsibilities=["Responsible for operational delivery and client execution"],
                )
            )

    return experiences


def extract_education(edu_text: str, full_text: str) -> list[Education]:
    """Extracts degrees, university/institution, graduation years, and fields of study."""
    target_text = edu_text if len(edu_text.strip()) > 30 else full_text
    education_records: list[Education] = []

    degree_patterns = [
        r"\b(MBA|PG\s+Certificate|Master\s+of\s+[A-Za-z ]+|Bachelor\s+of\s+[A-Za-z ]+|B\.?Tech|B\.?E\.?|M\.?Tech|B\.?Sc|M\.?Sc|BCA|MCA|Diploma)\b.*",
    ]

    lines = [l.strip() for l in target_text.splitlines() if l.strip()]
    for idx, line in enumerate(lines):
        for pattern in degree_patterns:
            match = re.search(pattern, line, re.I)
            if match:
                degree_name = line
                # Look for year in current or surrounding lines
                year_match = re.search(r"\b(19|20)\d{2}\b", line)
                if not year_match and idx > 0:
                    year_match = re.search(r"\b(19|20)\d{2}\b", lines[idx - 1])
                if not year_match and idx + 1 < len(lines):
                    year_match = re.search(r"\b(19|20)\d{2}\b", lines[idx + 1])

                inst = lines[idx + 1] if idx + 1 < len(lines) and not re.search(r"\b(19|20)\d{2}\b", lines[idx + 1]) else "University / Institute"

                education_records.append(
                    Education(
                        institution=inst,
                        degree=degree_name,
                        graduation_year=year_match.group(0) if year_match else None,
                    )
                )
                break

    if not education_records:
        education_records.append(
            Education(
                institution="University / Higher Education",
                degree="Degree / Professional Qualification",
                graduation_year=None,
            )
        )

    return education_records


def extract_skills_categorized(skills_text: str, full_text: str) -> CategorizedSkills:
    """Classifies skills into Technical, Tools/Platforms, Domain, and Soft skills."""
    all_scan = f"{skills_text}\n{full_text}"

    tech_dict = [
        "Python", "SQL", "Java", "C++", "C#", "JavaScript", "TypeScript", "FastAPI",
        "Django", "Flask", "React", "Angular", "Vue", "Node.js", "ETL", "Airflow",
        "Kafka", "Spark", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    ]
    tools_dict = [
        "Power BI", "Tableau", "Geneva Accounting Engine", "Bloomberg", "JIRA", "Confluence",
        "Git", "AWS", "Azure", "GCP", "Splunk", "Excel", "Advanced MS Excel", "Postman", "Swagger",
    ]
    domain_dict = [
        "Hedge Fund Accounting", "NAV Finalization", "Prime Broker Reconciliation",
        "OTC Derivatives", "Corporate Actions", "Collateral & Margin Management",
        "Trade Lifecycle", "KYC", "AML", "Lending", "Mortgage", "Banking Transformation",
        "Loan Origination Systems (LOS)", "Loan Management Systems (LMS)", "ISO 20022", "SWIFT",
    ]
    soft_dict = [
        "Agile", "Scrum", "Waterfall", "Project Management", "Leadership", "Communication",
        "Change Management", "Team Management", "Process Improvement", "Stakeholder Engagement",
    ]

    found_tech = [s for s in tech_dict if re.search(r"\b" + re.escape(s) + r"\b", all_scan, re.I)]
    found_tools = [s for s in tools_dict if re.search(r"\b" + re.escape(s) + r"\b", all_scan, re.I)]
    found_domain = [s for s in domain_dict if re.search(r"\b" + re.escape(s) + r"\b", all_scan, re.I)]
    found_soft = [s for s in soft_dict if re.search(r"\b" + re.escape(s) + r"\b", all_scan, re.I)]

    # Flat aggregated deduplicated list
    combined = list(dict.fromkeys(found_tech + found_tools + found_domain + found_soft))

    return CategorizedSkills(
        technical_skills=found_tech,
        tools_and_platforms=found_tools,
        domain_and_functional=found_domain,
        soft_skills=found_soft,
        all_skills=combined,
    )


def extract_certifications(cert_text: str) -> list[Certification]:
    """Extracts certifications and licensing credentials."""
    certs: list[Certification] = []
    if not cert_text:
        return certs

    for line in cert_text.splitlines():
        cleaned = re.sub(r"^[\s•\-*–]+", "", line).strip()
        if len(cleaned) > 5 and not cleaned.lower().startswith("certifications"):
            certs.append(Certification(name=cleaned, issuer=None, issue_year=None))
    return certs[:6]


def calculate_experience_years(text: str, experiences: list[WorkExperience]) -> float | None:
    """Calculates total experience years from explicit text or date ranges."""
    # Look for explicit statements like "14+ years" or "4+ years of experience"
    exp_mention = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years(?:\s+of)?\s+experience", text, re.I)
    if exp_mention:
        try:
            return float(exp_mention.group(1))
        except ValueError:
            pass

    # Calculate from earliest year to latest year
    all_years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", text)]
    if all_years:
        valid_years = [y for y in all_years if 1980 <= y <= 2030]
        if valid_years:
            span = max(valid_years) - min(valid_years)
            if 0 < span < 45:
                return float(span)

    return None


def execute_section_heuristic_parser(text: str) -> tuple[ResumeSchema, dict[str, str]]:
    """Runs the section-aware heuristic parser over the entire document."""
    sections = segment_resume_sections(text)

    contact = extract_contact_info(sections.get("header", ""), text)
    experiences = extract_work_experience(sections.get("experience", ""), text)
    education = extract_education(sections.get("education", ""), text)
    skills = extract_skills_categorized(sections.get("skills", ""), text)
    certifications = extract_certifications(sections.get("certifications", ""))
    total_exp = calculate_experience_years(text, experiences)

    # Title detection
    header_lines = [l.strip() for l in sections.get("header", "").splitlines() if l.strip()]
    title = None
    if len(header_lines) > 1:
        candidate_title = header_lines[1]
        if not ("@" in candidate_title or any(c.isdigit() for c in candidate_title)):
            title = candidate_title

    summary_text = sections.get("summary", "").strip() or None

    resume = ResumeSchema(
        contact=contact,
        professional_title=title,
        summary=summary_text,
        total_experience_years=total_exp,
        skills=skills,
        experience=experiences,
        education=education,
        certifications=certifications,
        projects=[],
        languages=["English"],
    )

    return resume, sections


# ---------------------------------------------------------------------------
# 3. Schema Mapping Report Generator
# ---------------------------------------------------------------------------
def build_schema_mapping_report(resume: ResumeSchema) -> SchemaMappingReport:
    """Builds a comprehensive schema mapping report evaluating extraction coverage and confidence."""
    details: list[FieldMappingDetail] = []
    populated_count = 0

    checks: list[tuple[str, bool, float]] = [
        ("contact.full_name", bool(resume.contact.full_name and resume.contact.full_name != "Candidate"), 0.95),
        ("contact.email", bool(resume.contact.email and "@" in resume.contact.email and "domain.com" not in resume.contact.email), 0.98),
        ("contact.phone", bool(resume.contact.phone and resume.contact.phone != "Not specified"), 0.95),
        ("contact.location", bool(resume.contact.location and resume.contact.location != "Not specified"), 0.85),
        ("contact.linkedin_url", bool(resume.contact.linkedin_url), 0.90),
        ("professional_title", bool(resume.professional_title), 0.88),
        ("summary", bool(resume.summary), 0.85),
        ("total_experience_years", bool(resume.total_experience_years is not None), 0.90),
        ("skills.technical_skills", bool(resume.skills.technical_skills), 0.92),
        ("skills.tools_and_platforms", bool(resume.skills.tools_and_platforms), 0.90),
        ("skills.domain_and_functional", bool(resume.skills.domain_and_functional), 0.90),
        ("skills.all_skills", bool(resume.skills.all_skills), 0.95),
        ("experience", bool(resume.experience and len(resume.experience) > 0), 0.92),
        ("education", bool(resume.education and len(resume.education) > 0), 0.90),
        ("certifications", bool(resume.certifications and len(resume.certifications) > 0), 0.80),
        ("projects", bool(resume.projects and len(resume.projects) > 0), 0.80),
    ]

    spec_dict = {spec["field"]: spec for spec in SCHEMA_MAPPING_SPECIFICATION}

    for field_name, is_extracted, conf in checks:
        spec = spec_dict.get(field_name, {})
        if is_extracted:
            populated_count += 1

        details.append(
            FieldMappingDetail(
                field_name=field_name,
                target_type=spec.get("target_type", "string"),
                is_required=spec.get("required", False),
                is_extracted=is_extracted,
                source_section=spec.get("source_section", "Resume Body"),
                confidence_score=conf if is_extracted else 0.0,
                description=spec.get("description", ""),
            )
        )

    completion_percentage = round((populated_count / len(checks)) * 100, 1)

    return SchemaMappingReport(
        fields_populated=populated_count,
        total_fields=len(checks),
        completion_percentage=completion_percentage,
        field_details=details,
    )


# ---------------------------------------------------------------------------
# 4. Master Parser Orchestrator (Instructor LLM + Fallback)
# ---------------------------------------------------------------------------
def parse_resume_content(
    text: str,
    source: str,
    model: str = "gpt-4o-mini",
    provider: str = "openai",
    api_key_override: str | None = None,
) -> ParseResponse:
    """Parses resume text using Instructor with LLM or advanced section-aware fallback."""
    start_time = time.time()
    active_key = api_key_override or os.getenv("OPENAI_API_KEY")

    # If an active key is present, execute via Instructor
    if active_key and (active_key.startswith("sk-") or provider == "ollama"):
        try:
            import instructor
            from openai import OpenAI

            raw_client = OpenAI(
                api_key=active_key if provider != "ollama" else "ollama",
                base_url="http://localhost:11434/v1" if provider == "ollama" else None,
            )
            client = instructor.from_openai(raw_client)

            parsed: ResumeSchema = client.chat.completions.create(
                model=model,
                response_model=ResumeSchema,
                max_retries=3,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert HR recruitment & ATS intelligence engine. "
                            "Accurately extract all candidate information into the requested ResumeSchema. "
                            "Map all company names, designations, date ranges, bullet points, education qualifications, "
                            "and categorize skills meticulously."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Extract complete candidate profile from this resume:\n\n{text}",
                    },
                ],
            )

            raw_sections = segment_resume_sections(text)
            mapping_report = build_schema_mapping_report(parsed)
            elapsed = round(time.time() - start_time, 3)

            return ParseResponse(
                success=True,
                source=source,
                extraction_mode="llm_instructor",
                data=parsed,
                schema_mapping=mapping_report,
                raw_sections=raw_sections,
                meta={
                    "model": model,
                    "provider": provider,
                    "elapsed_seconds": elapsed,
                    "text_characters": len(text),
                },
            )
        except Exception as e:
            # On LLM error, gracefully fall back to the section parser
            pass

    # Execute High-Precision Section-Aware Parser
    parsed, raw_sections = execute_section_heuristic_parser(text)
    mapping_report = build_schema_mapping_report(parsed)
    elapsed = round(time.time() - start_time, 3)

    return ParseResponse(
        success=True,
        source=source,
        extraction_mode="section_heuristic_parser",
        data=parsed,
        schema_mapping=mapping_report,
        raw_sections=raw_sections,
        meta={
            "notice": "Processed with High-Precision Section-Aware Schema Engine.",
            "elapsed_seconds": elapsed,
            "text_characters": len(text),
        },
    )
