"""
hard_skills_agent -- Extracts technical/hard skills from job descriptions.

Uses a LangChain chain (prompt + LLM + JSON parser) to return a
structured HardSkills object.
"""

import json
import logging

from agents.config import get_llm
from agents.models import HardSkills
from agents.prompts import HARD_SKILLS_PROMPT

logger = logging.getLogger(__name__)


class HardSkillsAgent:
    """Specialized agent for extracting hard/technical skills."""

    def __init__(self) -> None:
        self._llm = get_llm()
        self._chain = HARD_SKILLS_PROMPT | self._llm

    def extract(self, job_description: str) -> HardSkills:
        """Parse raw job text and return structured hard skills.

        Args:
            job_description: Raw, unprocessed job listing text.

        Returns:
            HardSkills model with categorised technical requirements.
        """
        logger.info("Running HardSkillsAgent...")
        response = self._chain.invoke({"job_description": job_description})
        raw = response.content.strip()

        # Strip markdown code fences if the model added them anyway.
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        result = HardSkills(**data)
        logger.info("HardSkillsAgent complete.")
        return result
