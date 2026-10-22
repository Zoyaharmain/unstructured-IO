"""Schema Mapping Specification and Registry for Resume Parsing."""

from __future__ import annotations

from typing import Any
from .models import ResumeSchema


SCHEMA_MAPPING_SPECIFICATION: list[dict[str, Any]] = [
    {
        "field": "contact.full_name",
        "target_type": "string",
        "required": True,
        "source_section": "Header / Personal Details",
        "validation_rule": "Non-empty string, length 2-60 chars, stripped of section keywords",
        "description": "Candidate's full name, extracted from the top header of the resume.",
        "example": "Jayesh Yadav",
    },
    {
        "field": "contact.email",
        "target_type": "string (email)",
        "required": True,
        "source_section": "Header / Contact Info",
        "validation_rule": "Valid standard RFC email format matching regex ^[\\w.-]+@[\\w.-]+\\.\\w+$",
        "description": "Candidate's primary contact email address.",
        "example": "jayeshyadavpimr2022@gmail.com",
    },
    {
        "field": "contact.phone",
        "target_type": "string (phone)",
        "required": True,
        "source_section": "Header / Contact Info",
        "validation_rule": "Phone number string with optional international country code (+91, +1, etc.)",
        "description": "Candidate's telephone / mobile phone number.",
        "example": "+91-8839814257",
    },
    {
        "field": "contact.location",
        "target_type": "string | null",
        "required": False,
        "source_section": "Header / Contact Info",
        "validation_rule": "City, State, or Country format",
        "description": "Candidate's residential location or work city.",
        "example": "Hyderabad, India",
    },
    {
        "field": "contact.linkedin_url",
        "target_type": "string (url) | null",
        "required": False,
        "source_section": "Header / Contact Info",
        "validation_rule": "Valid LinkedIn profile URL matching linkedin.com/in/...",
        "description": "URL to candidate's LinkedIn profile.",
        "example": "https://linkedin.com/in/jayeshyadav",
    },
    {
        "field": "professional_title",
        "target_type": "string | null",
        "required": False,
        "source_section": "Header / Subtitle",
        "validation_rule": "1-2 lines summarizing primary designation or role title",
        "description": "Candidate's target headline or most recent job title.",
        "example": "Senior Analyst — Hedge Fund Accounting & Portfolio Data Operations",
    },
    {
        "field": "summary",
        "target_type": "string | null",
        "required": False,
        "source_section": "Professional Summary / Profile / Objective",
        "validation_rule": "Paragraph text (typically 50-800 characters)",
        "description": "Executive bio, professional overview, or career objective.",
        "example": "Results-driven Senior Fund Accounting professional with 4+ years...",
    },
    {
        "field": "total_experience_years",
        "target_type": "float | null",
        "required": False,
        "source_section": "Summary / Experience Calculation",
        "validation_rule": "Numeric float >= 0.0, derived from explicit text ('14+ years') or date span",
        "description": "Total professional experience in years.",
        "example": 4.5,
    },
    {
        "field": "skills.technical_skills",
        "target_type": "array[string]",
        "required": False,
        "source_section": "Skills / Technical Competencies",
        "validation_rule": "List of programming languages, architectures, and algorithms",
        "description": "Technical programming languages and core software competencies.",
        "example": ["Python", "SQL", "ETL"],
    },
    {
        "field": "skills.tools_and_platforms",
        "target_type": "array[string]",
        "required": False,
        "source_section": "Skills / Tools & Technologies",
        "validation_rule": "List of databases, cloud providers, ERP systems, and developer tools",
        "description": "Software platforms, developer tools, and operational systems.",
        "example": ["Power BI", "Geneva Accounting Engine", "Advanced Excel"],
    },
    {
        "field": "skills.domain_and_functional",
        "target_type": "array[string]",
        "required": False,
        "source_section": "Skills / Domain Expertise",
        "validation_rule": "List of industry specializations, financial products, or regulatory frameworks",
        "description": "Functional domain knowledge (e.g. Hedge Funds, KYC, NAV, Derivatives).",
        "example": ["Prime Broker Reconciliation", "NAV Finalization", "OTC Derivatives"],
    },
    {
        "field": "skills.all_skills",
        "target_type": "array[string]",
        "required": False,
        "source_section": "Skills (Aggregated)",
        "validation_rule": "Deduplicated combined list of all extracted skill strings",
        "description": "Complete list of candidate skills across all categories.",
        "example": ["Python", "SQL", "Geneva", "Power BI"],
    },
    {
        "field": "experience",
        "target_type": "array[WorkExperience]",
        "required": False,
        "source_section": "Professional Experience / Work History",
        "validation_rule": "Array of objects with company, role, duration, and responsibilities list",
        "description": "Complete chronological employment records with bullet points.",
        "example": [
            {
                "company": "Arcesium India Private Limited",
                "role": "Senior Analyst",
                "start_date": "Dec 2022",
                "end_date": "Present",
                "duration": "Dec 2022 – Present",
                "responsibilities": ["Managed daily reconciliations across 12+ funds..."],
            }
        ],
    },
    {
        "field": "education",
        "target_type": "array[Education]",
        "required": False,
        "source_section": "Education / Academic Qualifications",
        "validation_rule": "Array of objects with institution, degree, and graduation year",
        "description": "University, college, and higher education degree qualifications.",
        "example": [
            {
                "institution": "Prestige Institute of Management & Research",
                "degree": "MBA – Finance & Data Analytics",
                "graduation_year": "2022",
            }
        ],
    },
    {
        "field": "certifications",
        "target_type": "array[Certification]",
        "required": False,
        "source_section": "Certifications / Licenses",
        "validation_rule": "Array of objects with certification name and issuing body",
        "description": "Professional accreditations and credentials.",
        "example": [{"name": "PSM-I Scrum Master", "issuer": "Scrum.org"}],
    },
    {
        "field": "projects",
        "target_type": "array[Project]",
        "required": False,
        "source_section": "Projects / Key Engagements",
        "validation_rule": "Array of objects with project title, role, and description",
        "description": "Major projects or strategic initiatives led by candidate.",
        "example": [{"name": "Fund Launch Automation", "role": "Lead FinOps Analyst"}],
    },
]


def get_full_schema_mapping() -> dict[str, Any]:
    """Returns the full schema mapping definition and OpenAPI/JSON Schema."""
    return {
        "title": "Resume Schema Mapping Specification",
        "version": "2.0.0",
        "target_model": "ResumeSchema",
        "fields_count": len(SCHEMA_MAPPING_SPECIFICATION),
        "mapping_specification": SCHEMA_MAPPING_SPECIFICATION,
        "json_schema": ResumeSchema.model_json_schema(),
    }

