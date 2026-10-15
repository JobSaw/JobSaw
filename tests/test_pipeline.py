"""Exercise pipeline failure handling, checkpoints, and page retries offline."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from jobsaw.application.pipeline import CvPipeline
from jobsaw.application.services import CvWriter, JobAnalyzer, ProfileSelector
from jobsaw.domain.job import HardSkills, JobAnalysis, SoftSkills, WorkScope
from jobsaw.domain.profile import ProfileData, SelectedProfileData
from jobsaw.infrastructure.mock_profile import MockProfileProvider


class PipelineTests(unittest.TestCase):
    """Verify use cases with injected collaborators rather than external calls."""

    def setUp(self):
        """Prepare a fresh run and minimal typed inputs."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.profile = ProfileData(name="Example Candidate")
        self.job = JobAnalysis(hard_skills=HardSkills(), soft_skills=SoftSkills(), work_scope=WorkScope())
        self.selected = SelectedProfileData()
        self.provider = Mock()
        self.provider.get_profile.return_value = self.profile
        self.analyzer = Mock()
        self.analyzer.analyze.return_value = self.job
        self.selector = Mock()
        self.selector.select.return_value = self.selected
        self.writer = Mock()
        self.writer.write.return_value = "LaTeX"
        self.compiler = Mock()
        self.pipeline = CvPipeline(self.analyzer, self.selector, self.writer, self.compiler)

    def _compiled(self, pages):
        """Create a stand-in PDF for each compiler invocation."""
        pdf = self.output / "04_tailored_cv.pdf"
        pdf.write_bytes(b"fake PDF")
        return pdf, pages

    def test_generation_saves_checkpoints_and_final_pdf(self):
        """A successful run keeps data and promotes the compiled PDF."""
        self.compiler.compile.side_effect = lambda _: self._compiled(1)
        final = self.pipeline.generate("Job", self.provider, self.output)
        self.assertEqual(final.name, "05_tailored_cv.pdf")
        self.assertTrue(final.exists())
        for filename in ("01_profile_data.json", "02_job_analysis.json", "03_selected_profile.json"):
            self.assertTrue((self.output / filename).exists())

    def test_multi_page_output_gets_feedback(self):
        """The writer receives measured page count before a second attempt."""
        pages = iter((2, 1))
        self.compiler.compile.side_effect = lambda _: self._compiled(next(pages))
        self.pipeline.generate("Job", self.provider, self.output)
        self.assertEqual(self.writer.write.call_count, 2)
        self.assertIn("2 pages", self.writer.write.call_args.args[-1])

    def test_page_limit_is_enforced_after_three_attempts(self):
        """Exhausted retries cannot produce an accepted final PDF."""
        self.compiler.compile.side_effect = lambda _: self._compiled(2)
        with self.assertRaisesRegex(RuntimeError, "three attempts"):
            self.pipeline.generate("Job", self.provider, self.output)
        self.assertEqual(self.writer.write.call_count, 3)
        self.assertFalse((self.output / "05_tailored_cv.pdf").exists())

    def test_compile_failure_preserves_source(self):
        """A failed compilation leaves the editable source and stops retries."""
        self.compiler.compile.side_effect = RuntimeError("syntax error")
        with self.assertRaisesRegex(RuntimeError, "syntax error"):
            self.pipeline.generate("Job", self.provider, self.output)
        self.assertTrue((self.output / "04_tailored_cv.tex").exists())
        self.writer.write.assert_called_once()

    def test_analysis_failure_preserves_profile_and_stops_selection(self):
        """Partial runs expose their completed checkpoint without fake defaults."""
        self.analyzer.analyze.side_effect = RuntimeError("quota")
        with self.assertRaisesRegex(RuntimeError, "quota"):
            self.pipeline.generate("Job", self.provider, self.output)
        self.assertTrue((self.output / "01_profile_data.json").exists())
        self.selector.select.assert_not_called()

    def test_retry_skips_analysis_and_selection(self):
        """Document recovery uses saved typed inputs only."""
        self.pipeline.select("Job", self.provider, self.output)
        self.analyzer.reset_mock()
        self.selector.reset_mock()
        self.compiler.compile.side_effect = lambda _: self._compiled(1)
        self.pipeline.retry(self.output)
        self.analyzer.analyze.assert_not_called()
        self.selector.select.assert_not_called()

    def test_job_analyzer_does_not_swallow_model_errors(self):
        """Model failures propagate to callers."""
        model = Mock()
        model.structured.side_effect = RuntimeError("quota")
        with self.assertRaisesRegex(RuntimeError, "quota"):
            JobAnalyzer(model).analyze("Job")

    def test_selector_rejects_invented_items(self):
        """A schema-valid selection must still reference real profile facts."""
        model = Mock()
        model.structured.return_value = SelectedProfileData(selected_hard_skills=["Invented"])
        with self.assertRaisesRegex(ValueError, "absent from the profile"):
            ProfileSelector(model).select(self.profile, self.job)

    def test_selector_accepts_exact_demo_items(self):
        """Existing facts are accepted without changing their names."""
        model = Mock()
        profile = MockProfileProvider().get_profile()
        model.structured.return_value = SelectedProfileData(selected_hard_skills=["Python"])
        self.assertEqual(ProfileSelector(model).select(profile, self.job).selected_hard_skills, ["Python"])

    def test_writer_rejects_unresolved_placeholders(self):
        """Incomplete model documents fail before reaching the compiler."""
        model = Mock()
        model.text.return_value = r"\documentclass{article} <<FULL_NAME>> \end{document}"
        writer = CvWriter(model, r"\documentclass{article}\end{document}", "Rules")
        with self.assertRaisesRegex(ValueError, "placeholders"):
            writer.write(self.profile, self.job, self.selected)
