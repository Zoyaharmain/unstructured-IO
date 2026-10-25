"""Comprehensive Pydantic models for Structured Resume Schema and Schema Mapping Specification."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Candidate Contact Information
# ---------------------------------------------------------------------------
class ContactInfo(BaseModel):
    full_name: str = Field(description="Candidate's full legal or professional name")
    email: str = Field(description="Primary contact email address")
    phone: str = Field(description="Contact phone number including country code if available")
    location: str | None = Field(default=None, description="City, state, or country of residence")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="GitHub or code repository URL")
    portfolio_url: str | None = Field(default=None, description="Personal website or portfolio URL")


# ---------------------------------------------------------------------------
# 2. Work Experience Records
# ---------------------------------------------------------------------------
class WorkExperience(BaseModel):
    company: str = Field(description="Company, employer, or client organization name")
    role: str = Field(description="Designation, position, or job title")
    start_date: str | None = Field(default=None, description="Employment start date (e.g. 'Jan 2021', '2020')")
    end_date: str | None = Field(default=None, description="Employment end date (e.g. 'Present', 'Dec 2024')")
    duration: str | None = Field(default=None, description="Total duration or date range string")
    location: str | None = Field(default=None, description="Job location (city/country or Remote)")
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities, achievements, and impact bullet points",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies, tools, or frameworks utilized in this role",
    )


# ---------------------------------------------------------------------------
# 3. Education Records
# ---------------------------------------------------------------------------
class Education(BaseModel):
    institution: str = Field(description="University, college, school, or issuing academy name")
    degree: str = Field(description="Degree or diploma (e.g. 'B.Tech', 'MBA', 'B.Sc', 'Master of Science')")
    field_of_study: str | None = Field(default=None, description="Major, department, or specialization")
    start_year: str | None = Field(default=None, description="Start year")
    graduation_year: str | None = Field(default=None, description="Graduation or completion year")
    grade_or_gpa: str | None = Field(default=None, description="GPA, grade, honors, or percentage")


# ---------------------------------------------------------------------------
# 4. Skills Categorization
# ---------------------------------------------------------------------------
class CategorizedSkills(BaseModel):
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Programming languages, algorithms, data structures, and core engineering skills",
    )
    tools_and_platforms: list[str] = Field(
        default_factory=list,
        description="Developer tools, cloud platforms, IDEs, databases, and enterprise software",
    )
    domain_and_functional: list[str] = Field(
        default_factory=list,
        description="Domain expertise, methodologies (e.g. Agile, Banking, FinOps, Risk, Accounting)",
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Communication, leadership, project management, and collaborative skills",
    )
    all_skills: list[str] = Field(
        default_factory=list,
        description="Flat deduplicated list of all extracted skills",
    )


# ---------------------------------------------------------------------------
# 5. Projects & Certifications
# ---------------------------------------------------------------------------
class Project(BaseModel):
    name: str = Field(description="Project title or system name")
    description: str | None = Field(default=None, description="Summary of project goals and achievements")
    role: str | None = Field(default=None, description="Candidate's role in the project")
    technologies: list[str] = Field(default_factory=list, description="Technologies and libraries used")
    url: str | None = Field(default=None, description="Live URL or repository link")


class Certification(BaseModel):
    name: str = Field(description="Certification, license, or course title")
    issuer: str | None = Field(default=None, description="Issuing organization (e.g. AWS, Scrum Alliance, Oracle)")
    issue_year: str | None = Field(default=None, description="Year or date of certification")


# ---------------------------------------------------------------------------
# 6. Master Resume Schema (Instructor Target Model)
# ---------------------------------------------------------------------------
class ResumeSchema(BaseModel):
    contact: ContactInfo = Field(description="Candidate contact details and social profiles")
    professional_title: str | None = Field(
        default=None,
        description="Candidate's professional headline, primary title, or specialization",
    )
    summary: str | None = Field(
        default=None,
        description="Professional summary, executive bio, or objective statement",
    )
    total_experience_years: float | None = Field(
        default=None,
        description="Estimated total professional work experience in years",
    )
    skills: CategorizedSkills = Field(
        default_factory=CategorizedSkills,
        description="Structured and categorized candidate skills",
    )
    experience: list[WorkExperience] = Field(
        default_factory=list,
        description="Complete chronological employment history",
    )
    education: list[Education] = Field(
        default_factory=list,
        description="Academic education and degree qualifications",
    )
    certifications: list[Certification] = Field(
        default_factory=list,
        description="Professional certifications, licenses, and accreditations",
    )
    projects: list[Project] = Field(
        default_factory=list,
        description="Key projects, client engagements, or open-source work",
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Languages known or spoken",
    )


# ---------------------------------------------------------------------------
# 7. Schema Mapping & Inspection Models
# ---------------------------------------------------------------------------
class FieldMappingDetail(BaseModel):
    field_name: str
    target_type: str
    is_required: bool
    is_extracted: bool
    source_section: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    description: str
    source_status: str = Field(default="present_and_extracted")


class SchemaMappingReport(BaseModel):
    fields_populated: int
    total_fields: int
    completion_percentage: float
    field_details: list[FieldMappingDetail]


# ---------------------------------------------------------------------------
# 8. HTTP Requests & Responses
# ---------------------------------------------------------------------------
class ParsePathRequest(BaseModel):
    path: str = Field(
        ...,
        description="Path to resume file (Windows e.g. C:\\..., WSL e.g. /mnt/c/..., or filename)",
        examples=["_Jayesh Yadav-CV.pdf", "C:\\Users\\LENOVO\\...\\resume.pdf"],
    )
    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    provider: str = Field(default="openai", description="Provider (openai, gemini, groq, ollama)")
    api_key: str | None = Field(default=None, description="Optional API key override")


class ParseTextRequest(BaseModel):
    text: str = Field(..., description="Raw resume text body to parse")
    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    provider: str = Field(default="openai", description="Provider (openai, gemini, groq, ollama)")
    api_key: str | None = Field(default=None, description="Optional API key override")


class ParseResponse(BaseModel):
    success: bool
    source: str
    extraction_mode: str  # 'llm_instructor' or 'section_heuristic_parser'
    data: ResumeSchema
    schema_mapping: SchemaMappingReport
    raw_sections: dict[str, str] = Field(
        default_factory=dict,
        description="Segmented raw resume text sections (summary, experience, education, skills, etc.)",
    )
    meta: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    instructor_version: str
    openai_key_configured: bool
    supported_formats: list[str]
    supported_providers: list[str]
