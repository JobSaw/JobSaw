"""Specialized job analysis, profile selection, and document writing services."""

import json
import re

from jobsaw.application import prompts
from jobsaw.application.ports import LanguageModel
from jobsaw.domain.job import HardSkills, JobAnalysis, SoftSkills, WorkScope
from jobsaw.domain.profile import ProfileData, SelectedProfileData


class JobAnalyzer:
    """Coordinate three specialized extraction tasks; propagate failures."""

    def __init__(self, model: LanguageModel) -> None:
        """Inject the model adapter."""
        self._model = model

    def analyze(self, description: str) -> JobAnalysis:
        """Extract the job's requirements without hiding failed stages."""
        if not description.strip():
            raise ValueError("Job description must not be empty.")
        # Sequential tasks share the injected adapter's rate-limit budget.
        return JobAnalysis(
            hard_skills=self._model.structured(prompts.HARD_SKILLS, description, HardSkills),
            soft_skills=self._model.structured(prompts.SOFT_SKILLS, description, SoftSkills),
            work_scope=self._model.structured(prompts.WORK_SCOPE, description, WorkScope),
        )


class ProfileSelector:
    """Select job-relevant candidate facts."""

    def __init__(self, model: LanguageModel) -> None:
        """Inject the model adapter."""
        self._model = model

    def select(self, profile: ProfileData, job: JobAnalysis) -> SelectedProfileData:
        """Ask the model to curate the profile against the job."""
        content = json.dumps({"profile": profile.model_dump(), "job": job.model_dump()})
        selected = self._model.structured(prompts.SELECT_PROFILE, content, SelectedProfileData)
        # Valid JSON is not enough: each selection must identify a source fact.
        groups = (
            (selected.selected_hard_skills + selected.selected_soft_skills,
             {skill.name for skill in profile.skills}),
            (selected.selected_experience,
             {f"{entry.title} at {entry.company}" for entry in profile.experience}),
            (selected.selected_certifications, {entry.name for entry in profile.certifications}),
            (selected.selected_connections,
             {f"{entry.name} ({entry.title} at {entry.company})" for entry in profile.connections}),
        )
        for items, allowed in groups:
            if unknown := set(items) - allowed:
                raise ValueError(f"Selected items are absent from the profile: {sorted(unknown)}")
        return selected


class CvWriter:
    """Generate document source from the template and validated input data."""

    def __init__(self, model: LanguageModel, template: str, rules: str) -> None:
        """Accept resource content so this service is independent of the filesystem."""
        self._model = model
        self._template = template
        self._rules = rules

    def write(self, profile: ProfileData, job: JobAnalysis,
              selected: SelectedProfileData, feedback: str = "") -> str:
        """Generate complete LaTeX and reject incomplete template output."""
        content = json.dumps({
            "template": self._template, "profile": profile.model_dump(),
            "job": job.model_dump(), "selected": selected.model_dump(),
            "feedback": feedback,
        })
        raw = self._model.text(prompts.WRITE_CV + "\n" + self._rules, content).strip()
        # Tolerate a complete Markdown wrapper, but never repair arbitrary syntax.
        raw = re.sub(r"\A```(?:latex|tex)?\s*\n(.*?)\n```\Z", r"\1", raw, flags=re.DOTALL).strip()
        if not raw.startswith(r"\documentclass") or not raw.endswith(r"\end{document}"):
            raise ValueError("Model returned an incomplete LaTeX document.")
        if re.search(r"<<[A-Z_]+>>", raw):
            raise ValueError("Model left unresolved CV placeholders.")
        return raw
