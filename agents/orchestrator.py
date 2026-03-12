"""
orchestrator -- Coordinates the three specialized agents.

Runs the HardSkillsAgent, SoftSkillsAgent, and WorkScopeAgent
sequentially (to respect free-tier rate limits) and merges their
outputs into a single JobAnalysis result.
"""

import logging

from agents.hard_skills_agent import HardSkillsAgent
from agents.models import JobAnalysis
from agents.soft_skills_agent import SoftSkillsAgent
from agents.work_scope_agent import WorkScopeAgent

logger = logging.getLogger(__name__)


class JobAnalysisOrchestrator:
    """Top-level coordinator that runs the full analysis pipeline.

    Usage:
        orchestrator = JobAnalysisOrchestrator()
        result = orchestrator.analyze(raw_job_text)
        print(result.model_dump_json(indent=2))
    """

    def __init__(self) -> None:
        self._hard_skills_agent = HardSkillsAgent()
        self._soft_skills_agent = SoftSkillsAgent()
        self._work_scope_agent = WorkScopeAgent()

    def analyze(self, job_description: str) -> JobAnalysis:
        """Run all three agents and return the combined analysis.

        Agents run sequentially to stay within Gemini free-tier
        rate limits. Each agent is independent -- failure in one
        does not affect the others (errors are logged and defaults
        are used).

        Args:
            job_description: Raw job listing text (e.g. copy-pasted
                             from LinkedIn).

        Returns:
            JobAnalysis with hard_skills, soft_skills, and work_scope.
        """
        logger.info("Starting job analysis pipeline...")

        # --- Hard Skills ---
        try:
            hard_skills = self._hard_skills_agent.extract(job_description)
        except Exception:
            logger.exception("HardSkillsAgent failed; using defaults.")
            from agents.models import HardSkills
            hard_skills = HardSkills()

        # --- Soft Skills ---
        try:
            soft_skills = self._soft_skills_agent.extract(job_description)
        except Exception:
            logger.exception("SoftSkillsAgent failed; using defaults.")
            from agents.models import SoftSkills
            soft_skills = SoftSkills()

        # --- Work Scope ---
        try:
            work_scope = self._work_scope_agent.extract(job_description)
        except Exception:
            logger.exception("WorkScopeAgent failed; using defaults.")
            from agents.models import WorkScope
            work_scope = WorkScope()

        result = JobAnalysis(
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            work_scope=work_scope,
        )
        logger.info("Job analysis pipeline complete.")
        return result
