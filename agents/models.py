"""
models -- Pydantic data models for agent outputs.

Defines the structured schemas that each agent returns and
the composite JobAnalysis that the orchestrator assembles.
"""

from pydantic import BaseModel, Field


class HardSkills(BaseModel):
    """Technical / hard skills extracted from a job description."""

    programming_languages: list[str] = Field(
        default_factory=list,
        description="Programming languages mentioned (e.g. Python, Java).",
    )
    frameworks_and_libraries: list[str] = Field(
        default_factory=list,
        description="Frameworks or libraries required (e.g. React, Django).",
    )
    tools_and_platforms: list[str] = Field(
        default_factory=list,
        description="Tools, platforms, or services (e.g. Docker, AWS, Git).",
    )
    databases: list[str] = Field(
        default_factory=list,
        description="Databases or data stores (e.g. PostgreSQL, Redis).",
    )
    other_technical: list[str] = Field(
        default_factory=list,
        description="Any other hard/technical skills not in the above categories.",
    )


class SoftSkills(BaseModel):
    """Soft / interpersonal skills extracted from a job description."""

    skills: list[str] = Field(
        default_factory=list,
        description="List of soft skills (e.g. communication, leadership).",
    )


class WorkScope(BaseModel):
    """Predicted or extracted scope of work for the role."""

    summary: str = Field(
        default="",
        description="One-paragraph summary of what the role involves day-to-day.",
    )
    key_responsibilities: list[str] = Field(
        default_factory=list,
        description="Primary tasks and responsibilities.",
    )
    projects_or_domains: list[str] = Field(
        default_factory=list,
        description="Specific projects, products, or domain areas you would work on.",
    )
    team_structure: str = Field(
        default="",
        description="What the team looks like, if mentioned or inferable.",
    )


class JobAnalysis(BaseModel):
    """Composite result combining all three agent outputs."""

    hard_skills: HardSkills
    soft_skills: SoftSkills
    work_scope: WorkScope
