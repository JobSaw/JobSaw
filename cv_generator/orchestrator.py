"""
orchestrator -- Coordinates the CV generation pipeline.

Executes the profile extraction architecture to get selected data,
reads the LaTeX template, runs the CvWriterAgent, saves all intermediates
to a timestamped output folder, and compiles the final PDF.
"""

import datetime
import json
import logging
import os
from typing import Tuple

from cv_generator.compiler import LatexCompiler
from cv_generator.cv_writer_agent import CvWriterAgent
from profile.models import ProfileData, SelectedProfileData
from profile.orchestrator import ProfileExtractionOrchestrator
from profile.provider import ProfileProvider

logger = logging.getLogger(__name__)


class CvGenerationOrchestrator:
    """Coordinator for the full end-to-end CV generation process.

    Usage:
        orchestrator = CvGenerationOrchestrator(MockProfileProvider(), "templates/cv_template.tex")
        pdf_path = orchestrator.run(job_description_text)
    """

    def __init__(self, provider: ProfileProvider, template_path: str) -> None:
        """Initialize pipeline with data source and template.

        Args:
            provider: Profile data source (e.g., MockProfileProvider).
            template_path: Path to the stripped LaTeX template.
        """
        self._profile_orchestrator = ProfileExtractionOrchestrator(provider)
        self._writer_agent = CvWriterAgent()
        self._compiler = LatexCompiler()
        self._template_path = template_path

    def _create_output_dir(self) -> str:
        """Create a timestamped output directory for this run."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_dir = os.path.join(os.getcwd(), "output", timestamp)
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def run(self, job_description: str) -> str:
        """Execute CV generation and return the path to the PDF.

        Args:
            job_description: The raw job listing text.

        Returns:
            Absolute path to the compiled CV PDF.
        """
        import time

        out_dir = self._create_output_dir()
        logger.info("Starting CV Generation Pipeline. Output dir: %s", out_dir)

        t_total_start = time.time()

        # 1. Run the existing profile extraction pipeline (streams JSON to out_dir automatically)
        selected, profile, job_analysis = self._profile_orchestrator.run(job_description, out_dir=out_dir)

        # 2. Read template
        logger.info("Reading LaTeX template: %s", self._template_path)
        with open(self._template_path, "r", encoding="utf-8") as f:
            latex_template = f.read()

        max_retries = 2
        feedback_msg = ""
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.warning(
                    "Feedback loop triggered (Attempt %d/%d). Instructing AI to shorten CV limit to 1 page.",
                    attempt, max_retries
                )
                print(f"\n[Feedback Loop Triggered! (Attempt {attempt}/{max_retries})] The generated CV was multiple pages. Asking the AI to condense it...")
            
            logger.info("Generating tailored LaTeX content...")
            t0 = time.time()
            tailored_latex = self._writer_agent.generate(
                latex_template=latex_template,
                profile_json=profile.model_dump_json(indent=2),
                selected_json=selected.model_dump_json(indent=2),
                job_analysis_json=job_analysis.model_dump_json(indent=2),
                feedback=feedback_msg,
            )
            logger.info("Tailored LaTeX generated in %.2fs.", time.time() - t0)

            # 3. Save the generated .tex immediately
            tex_path = os.path.join(out_dir, "04_tailored_cv.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(tailored_latex)
            logger.info("Tailored LaTeX saved to: %s", tex_path)

            # 4. Compile the PDF
            logger.info("Compiling LaTeX to PDF...")
            t0 = time.time()
            try:
                pdf_path, num_pages = self._compiler.compile(tex_path, out_dir)
                
                if num_pages > 1 and attempt < max_retries:
                    logger.warning("Generated CV is %d pages. Initiating feedback loop.", num_pages)
                    feedback_msg = (
                        "FEEDBACK FROM LAST RUN: Your previous LaTeX output was "
                        f"{num_pages} pages long. This exceeds the 1-page limit. "
                        "You MUST condense the content to fit exactly onto 1 page. "
                        "1. Rephrase bullet points to be single, short lines to prevent text wrapping. "
                        "2. Delete the least important bullet points from your experiences. "
                        "3. If it is still too long, delete the oldest experience completely. "
                        "Do your best to keep the most important information while strictly adhering to the 1-page limit."
                    )
                    continue # Retry generating

                # Optional: rename PDF to match sequence numbering for consistency
                final_pdf_path = os.path.join(out_dir, "05_tailored_cv.pdf")
                if os.path.exists(final_pdf_path):
                    os.remove(final_pdf_path) # in case it exists somehow
                os.rename(pdf_path, final_pdf_path)
                
                t_total = time.time() - t_total_start
                logger.info("PDF compiled in %.2fs.", time.time() - t0)
                logger.info("CV Generation complete in %.2fs total: %s", t_total, final_pdf_path)
                return final_pdf_path
            except Exception as e:
                logger.error("PDF compilation failed. The raw .tex is available in '%s'.", tex_path)
                raise e

