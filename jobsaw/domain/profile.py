"""Candidate facts and job-specific selections, independent of data providers."""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Profile building blocks
# ---------------------------------------------------------------------------

class ProfileSkill(BaseModel):
    """A single skill entry on a person's profile."""

    name: str = Field(description="Canonical skill name (e.g. 'Python', 'Leadership').")
    proficiency: str = Field(
        default="Intermediate",
        description="Self-assessed proficiency: Beginner, Intermediate, Advanced, Expert.",
    )
    years: float = Field(
        default=0.0,
        description="Years of experience with this skill.",
    )


class ProfileExperience(BaseModel):
    """A single work-experience entry."""

    title: str = Field(description="Job title held.")
    company: str = Field(description="Employer or client name.")
    duration: str = Field(description="Duration string, e.g. 'Jan 2021 - Dec 2023'.")
    description: str = Field(
        default="",
        description="Free-text description of responsibilities and achievements.",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies and tools used in this role.",
    )


class ProfileConnection(BaseModel):
    """A professional connection / reference."""

    name: str = Field(description="Full name of the connection.")
    title: str = Field(default="", description="Current job title.")
    company: str = Field(default="", description="Current employer.")
    relationship: str = Field(
        default="Colleague",
        description="Nature of the relationship (e.g. 'Manager', 'Colleague', 'Mentor').",
    )


class ProfileCertification(BaseModel):
    """A professional certification or accreditation."""

    name: str = Field(description="Certification name.")
    issuer: str = Field(default="", description="Issuing organization.")
    year: int = Field(default=0, description="Year obtained.")


class ProfileEducation(BaseModel):
    """An education entry."""

    degree: str = Field(description="Degree title (e.g. 'B.Sc. Computer Science').")
    institution: str = Field(description="University or school name.")
    year: int = Field(default=0, description="Graduation year.")


# ---------------------------------------------------------------------------
# Composite profile
# ---------------------------------------------------------------------------

class ProfileData(BaseModel):
    """Complete profile of a person, aggregating all sections."""

    name: str = Field(description="Full name of the profile owner.")
    # Empty optional contact fields represent missing data, never invented values.
    location: str = ""
    phone: str = ""
    email: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    summary: str = Field(
        default="",
        description="Professional summary / headline.",
    )
    skills: list[ProfileSkill] = Field(
        default_factory=list,
        description="All skills listed on the profile.",
    )
    experience: list[ProfileExperience] = Field(
        default_factory=list,
        description="Work experience entries, most recent first.",
    )
    education: list[ProfileEducation] = Field(
        default_factory=list,
        description="Education history.",
    )
    certifications: list[ProfileCertification] = Field(
        default_factory=list,
        description="Professional certifications.",
    )
    connections: list[ProfileConnection] = Field(
        default_factory=list,
        description="Professional connections / references.",
    )


# ---------------------------------------------------------------------------
# AI-selected output
# ---------------------------------------------------------------------------

class SelectedProfileData(BaseModel):
    """AI-curated subset of a profile, tailored to a specific job.

    ProfileSelector validates these names against the source profile. String
    references keep checkpoints readable; stable IDs can replace them if needed.
    """

    selected_hard_skills: list[str] = Field(
        default_factory=list,
        description="Profile hard skills that match or strengthen the candidacy.",
    )
    selected_soft_skills: list[str] = Field(
        default_factory=list,
        description="Profile soft skills that match or strengthen the candidacy.",
    )
    selected_experience: list[str] = Field(
        default_factory=list,
        description=(
            "Titles or short descriptions of experience entries deemed relevant. "
            "Each entry should reference the original experience by title + company."
        ),
    )
    selected_certifications: list[str] = Field(
        default_factory=list,
        description="Certification names that add value for the target role.",
    )
    selected_connections: list[str] = Field(
        default_factory=list,
        description=(
            "Names of connections who could serve as references or provide "
            "a warm introduction relevant to the target role."
        ),
    )
    relevance_rationale: str = Field(
        default="",
        description=(
            "Brief explanation of why these items were selected and how they "
            "align with the job requirements."
        ),
    )
