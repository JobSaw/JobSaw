"""
soft_skills_agent -- Extracts interpersonal/soft skills from job descriptions.

Uses a LangChain chain (prompt + LLM + JSON parser) to return a
structured SoftSkills object.
"""

import json
import logging

from agents.config import get_llm
from agents.models import SoftSkills
from agents.prompts import SOFT_SKILLS_PROMPT

logger = logging.getLogger(__name__)


class SoftSkillsAgent:
    """Specialized agent for extracting soft/interpersonal skills."""

    def __init__(self) -> None:
        self._llm = get_llm()
        self._chain = SOFT_SKILLS_PROMPT | self._llm

    def extract(self, job_description: str) -> SoftSkills:
        """Parse raw job text and return structured soft skills.

        Args:
            job_description: Raw, unprocessed job listing text.

        Returns:
            SoftSkills model with identified interpersonal skills.
        """
        logger.info("Running SoftSkillsAgent...")
        response = self._chain.invoke({"job_description": job_description})
        raw = response.content.strip()

        # Strip markdown code fences if the model added them anyway.
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        result = SoftSkills(**data)
        logger.info("SoftSkillsAgent complete.")
        return result
