"""
cv_writer_agent -- AI agent that fills a LaTeX CV template with tailored content.

Takes the LaTeX template, the full profile, the AI-selected profile
subset, and the job analysis, then produces a complete LaTeX document
ready for compilation.
"""

import logging
import re
from pathlib import Path

from agents.config import get_llm
from cv_generator.prompts import CV_WRITER_PROMPT

logger = logging.getLogger(__name__)


class CvWriterAgent:
    """Specialized agent for generating a tailored LaTeX CV.

    Fills the template placeholders with content drawn from the
    AI-selected profile data, ensuring the result is a one-page,
    compilable LaTeX document.
    """

    def __init__(self) -> None:
        # Use a slightly higher temperature for more natural writing.
        self._llm = get_llm(temperature=0.3)
        self._chain = CV_WRITER_PROMPT | self._llm
        
        # Load LaTeX skill
        skill_path = Path(__file__).parent.parent / "agents" / "skills" / "latex_skill.md"
        try:
            self._latex_skill = skill_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("LaTeX skill file not found at %s", skill_path)
            self._latex_skill = ""

    def generate(
        self,
        latex_template: str,
        profile_json: str,
        selected_json: str,
        job_analysis_json: str,
    ) -> str:
        """Invoke the LLM to produce the filled LaTeX CV.

        Args:
            latex_template: Raw LaTeX template with <<PLACEHOLDER>> markers.
            profile_json: JSON string of the full ProfileData.
            selected_json: JSON string of the SelectedProfileData.
            job_analysis_json: JSON string of the JobAnalysis.

        Returns:
            Complete LaTeX source code as a string.
        """
        logger.info("Running CvWriterAgent...")
        logger.debug(
            "Template length: %d chars, profile: %d chars, "
            "selected: %d chars, job analysis: %d chars",
            len(latex_template),
            len(profile_json),
            len(selected_json),
            len(job_analysis_json),
        )

        response = self._chain.invoke(
            {
                "latex_skill": self._latex_skill,
                "latex_template": latex_template,
                "profile_json": profile_json,
                "selected_json": selected_json,
                "job_analysis_json": job_analysis_json,
            }
        )
        raw = response.content.strip()

        # Strip markdown code fences if the model added them.
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0].strip()

        # LaTeX Safety Net: Fix common LLM escaping failures
        # Target lone '&' symbols not already escaped or part of a command.
        # simple fix for Technical Skills sections
        raw = re.sub(r'(?<!\\)&', r'\\&', raw)

        logger.info("CvWriterAgent complete. Output: %d chars of LaTeX.", len(raw))
        logger.debug("Generated LaTeX (first 500 chars): %s", raw[:500])
        return raw
