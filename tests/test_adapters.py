"""Verify model and CLI boundary behavior without network or LaTeX."""

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from google.genai import errors, types

from jobsaw.cli import main
from jobsaw.config import Settings
from jobsaw.domain.job import HardSkills
from jobsaw.infrastructure.gemini import GeminiModel
from jobsaw.infrastructure.latex import LatexCompiler
from jobsaw.infrastructure.profile_file import JsonProfileProvider


class AdapterTests(unittest.TestCase):
    """Test SDK translation, environment checks, and offline commands."""

    def setUp(self):
        """Replace the SDK client with a mock."""
        client = patch("jobsaw.infrastructure.gemini.genai.Client")
        self.client = client.start().return_value
        self.addCleanup(client.stop)
        self.adapter = GeminiModel(Settings(api_key="test", model="test-model", request_interval=0))
        self.client.models.generate_content.return_value = Mock(
            text='{"programming_languages": ["Python"]}',
            candidates=[Mock(finish_reason=types.FinishReason.STOP)],
        )

    def test_structured_output_uses_sdk_schema_and_validates(self):
        """Structured tasks supply a native schema and return domain objects."""
        result = self.adapter.structured("Extract", "Job", HardSkills)
        self.assertEqual(result.programming_languages, ["Python"])
        config = self.client.models.generate_content.call_args.kwargs["config"]
        self.assertIs(config.response_schema, HardSkills)
        self.assertEqual(config.response_mime_type, "application/json")

    def test_quota_error_is_actionable(self):
        """429 responses stop the run instead of hiding quota exhaustion."""
        self.client.models.generate_content.side_effect = errors.ClientError(429, {"error": {"message": "quota"}})
        with self.assertRaisesRegex(RuntimeError, "quota exceeded"):
            self.adapter.text("Write", "CV")

    def test_missing_model_error_includes_provider_explanation(self):
        """An unavailable model error identifies the model and corrective setting."""
        self.client.models.generate_content.side_effect = errors.ClientError(
            404, {"error": {"message": "Model not available for new projects"}},
        )
        with self.assertRaisesRegex(RuntimeError, "Model not available for new projects") as result:
            self.adapter.text("Write", "CV")
        self.assertIn("GEMINI_MODEL", str(result.exception))

    def test_truncated_response_is_rejected(self):
        """Output token limits cannot silently yield incomplete documents."""
        self.client.models.generate_content.return_value.candidates[0].finish_reason = types.FinishReason.MAX_TOKENS
        with self.assertRaisesRegex(RuntimeError, "did not complete"):
            self.adapter.text("Write", "CV")

    def test_calls_share_request_pacing(self):
        """The adapter spaces successive tasks using a shared clock."""
        self.adapter._interval = 12
        with patch("jobsaw.infrastructure.gemini.time.monotonic", side_effect=[10, 15, 22]), patch("jobsaw.infrastructure.gemini.time.sleep") as sleep:
            self.adapter.text("Write", "First")
            self.adapter.text("Write", "Second")
            sleep.assert_called_once_with(7)

    def test_missing_key_fails_configuration(self):
        """Missing credentials are diagnosed before an SDK request."""
        with patch.dict(os.environ, {}, clear=True), patch("jobsaw.config.dotenv_values", return_value={}):
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
                Settings.from_env()

    def test_demo_command_does_not_construct_model(self):
        """Generating a profile example is fully offline."""
        with patch("jobsaw.cli.GeminiModel") as factory, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["demo-profile"]), 0)
        factory.assert_not_called()
        self.assertIn("Alex Johnson", output.getvalue())

    def test_invalid_configuration_does_not_create_run(self):
        """Configuration failures do not reserve an unusable output directory."""
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "job.txt"
            job.write_text("Python developer")
            output = Path(directory) / "run"
            with patch("jobsaw.cli.Settings.from_env", side_effect=ValueError("GEMINI_MODEL")), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["analyze", str(job), "--output", str(output)]), 1)
            self.assertFalse(output.exists())

    def test_selection_does_not_load_cv_resources(self):
        """Selection works even if PDF resources are unavailable."""
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "job.txt"
            job.write_text("Python developer")
            with patch("jobsaw.cli.Settings.from_env", return_value=Settings(api_key="test", model="test")), patch("jobsaw.cli.GeminiModel"), patch("jobsaw.cli.CvWriter") as writer, patch("jobsaw.cli.LatexCompiler") as compiler, patch("jobsaw.cli.select_profile") as select, contextlib.redirect_stdout(io.StringIO()):
                select.return_value = (Mock(), Mock(), Mock())
                self.assertEqual(main(["select", str(job), "--demo", "--output", str(Path(directory) / "run")]), 0)
            writer.assert_not_called()
            compiler.assert_not_called()

    def test_failure_traceback_is_written_to_log(self):
        """DEBUG tracebacks reach the file while the console stays concise."""
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "job.txt"
            job.write_text("Python developer")
            output = Path(directory) / "run"
            with patch("jobsaw.cli.Settings.from_env", return_value=Settings(api_key="test", model="test")), patch("jobsaw.cli.GeminiModel"), patch("jobsaw.cli.JobAnalyzer") as analyzer, contextlib.redirect_stderr(io.StringIO()):
                analyzer.return_value.analyze.side_effect = RuntimeError("model unavailable")
                self.assertEqual(main(["analyze", str(job), "--output", str(output)]), 1)
            log = (output / "run.log").read_text()
            self.assertIn("Traceback", log)
            self.assertIn("model unavailable", log)

    def test_json_provider_validates_file(self):
        """User-provided JSON uses the same domain contract as demo data."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text('{"name": "Candidate", "email": "example@example.com"}')
            self.assertEqual(JsonProfileProvider(path).get_profile().email, "example@example.com")

    def test_compile_command_requires_no_api_key(self):
        """Manual document recovery skips model initialization entirely."""
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "04_tailored_cv.pdf"
            pdf.write_bytes(b"fake PDF")
            with patch("jobsaw.cli.GeminiModel") as model, patch("jobsaw.cli.LatexCompiler") as compiler, contextlib.redirect_stdout(io.StringIO()):
                compiler.return_value.compile.return_value = (pdf, 1)
                self.assertEqual(main(["compile", directory]), 0)
            model.assert_not_called()
            self.assertTrue((Path(directory) / "05_tailored_cv.pdf").exists())

    def test_compiler_parses_wrapped_page_count(self):
        """Compiler accepts wrapped output and runs twice without shell escape."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cv.tex"
            source.write_text("LaTeX")
            source.with_suffix(".pdf").write_bytes(b"fake PDF")
            result = subprocess.CompletedProcess([], 0, stdout="Output written on cv.pdf\n(1 page, 123 bytes).", stderr="")
            with patch("jobsaw.infrastructure.latex.shutil.which", return_value="pdflatex"), patch("jobsaw.infrastructure.latex.subprocess.run", return_value=result) as run:
                self.assertEqual(LatexCompiler().compile(source)[1], 1)
                self.assertEqual(run.call_count, 2)
                self.assertIn("-no-shell-escape", run.call_args.args[0])

    def test_compiler_rejects_unknown_page_count(self):
        """Successful exit status alone does not prove a valid PDF."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cv.tex"
            source.write_text("LaTeX")
            source.with_suffix(".pdf").write_bytes(b"fake PDF")
            result = subprocess.CompletedProcess([], 0, stdout="No page count", stderr="")
            with patch("jobsaw.infrastructure.latex.shutil.which", return_value="pdflatex"), patch("jobsaw.infrastructure.latex.subprocess.run", return_value=result):
                with self.assertRaisesRegex(RuntimeError, "known page count"):
                    LatexCompiler().compile(source)
