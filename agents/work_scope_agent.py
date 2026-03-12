"""
work_scope_agent -- Predicts or extracts the scope of work from job descriptions.

Uses a LangChain chain (prompt + LLM + JSON parser) to return a
structured WorkScope object.
"""

import json
import logging

from agents.config import get_llm
from agents.models import WorkScope
from agents.prompts import WORK_SCOPE_PROMPT

logger = logging.getLogger(__name__)


class WorkScopeAgent:
    """Specialized agent for predicting the day-to-day work scope."""

    def __init__(self) -> None:
        self._llm = get_llm()
        self._chain = WORK_SCOPE_PROMPT | self._llm

    def extract(self, job_description: str) -> WorkScope:
        """Parse raw job text and return predicted work scope.

        Args:
            job_description: Raw, unprocessed job listing text.

        Returns:
            WorkScope model with responsibilities, projects, and team info.
        """
        logger.info("Running WorkScopeAgent...")
        response = self._chain.invoke({"job_description": job_description})
        raw = response.content.strip()

        # Strip markdown code fences if the model added them anyway.
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        result = WorkScope(**data)
        logger.info("WorkScopeAgent complete.")
        return result
