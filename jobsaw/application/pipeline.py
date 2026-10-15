"""Coordinate the CV use case and persist recoverable checkpoints."""

import logging
from pathlib import Path

from jobsaw.application.ports import PdfCompiler, ProfileProvider
from jobsaw.application.services import CvWriter, JobAnalyzer, ProfileSelector
from jobsaw.domain.job import JobAnalysis
from jobsaw.domain.profile import ProfileData, SelectedProfileData

logger = logging.getLogger(__name__)


def select_profile(description: str, provider: ProfileProvider, output: Path,
                   analyzer: JobAnalyzer, selector: ProfileSelector
                   ) -> tuple[ProfileData, JobAnalysis, SelectedProfileData]:
    """Run selection without requiring document-writing or PDF dependencies."""
    if not description.strip():
        raise ValueError("Job description must not be empty.")
    output.mkdir(parents=True, exist_ok=True)
    profile = provider.get_profile()
    # Save each completed stage before starting another external request.
    (output / "01_profile_data.json").write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Analyzing job requirements...")
    job = analyzer.analyze(description)
    (output / "02_job_analysis.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Selecting relevant profile facts...")
    selected = selector.select(profile, job)
    (output / "03_selected_profile.json").write_text(selected.model_dump_json(indent=2), encoding="utf-8")
    return profile, job, selected


class CvPipeline:
    """Application facade composed from injected services and adapters."""

    def __init__(self, analyzer: JobAnalyzer, selector: ProfileSelector,
                 writer: CvWriter, compiler: PdfCompiler) -> None:
        """Store the collaborators required for the CV workflow."""
        self._analyzer = analyzer
        self._selector = selector
        self._writer = writer
        self._compiler = compiler

    def select(self, description: str, provider: ProfileProvider,
               output: Path) -> tuple[ProfileData, JobAnalysis, SelectedProfileData]:
        """Load, analyze, and select, saving each completed stage."""
        return select_profile(description, provider, output, self._analyzer, self._selector)

    def generate(self, description: str, provider: ProfileProvider, output: Path) -> Path:
        """Execute the full pipeline and return an accepted one-page PDF."""
        profile, job, selected = self.select(description, provider, output)
        return self._render(profile, job, selected, output)

    def retry(self, output: Path) -> Path:
        """Regenerate the document using an existing run's JSON checkpoints."""
        profile = ProfileData.model_validate_json((output / "01_profile_data.json").read_text(encoding="utf-8"))
        job = JobAnalysis.model_validate_json((output / "02_job_analysis.json").read_text(encoding="utf-8"))
        selected = SelectedProfileData.model_validate_json((output / "03_selected_profile.json").read_text(encoding="utf-8"))
        return self._render(profile, job, selected, output)

    def _render(self, profile: ProfileData, job: JobAnalysis,
                selected: SelectedProfileData, output: Path) -> Path:
        """Attempt writing at most three times, using page count as feedback."""
        feedback = ""
        for attempt in range(3):
            logger.info("Writing and compiling CV (attempt %d/3)...", attempt + 1)
            source = output / "04_tailored_cv.tex"
            source.write_text(self._writer.write(profile, job, selected, feedback), encoding="utf-8")
            pdf, pages = self._compiler.compile(source)
            if pages == 1:
                # Promote a PDF only after validating the one-page constraint.
                # A failed retry leaves the previous accepted PDF intact.
                final = output / "05_tailored_cv.pdf"
                pdf.replace(final)
                return final
            feedback = (
                f"Last output was {pages} pages. Shorten bullets and remove less "
                "relevant content or older experience to fit exactly one page."
            )
        raise RuntimeError("CV still exceeds one page after three attempts. Edit the saved .tex and use compile.")
