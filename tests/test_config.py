"""Configuration precedence and failure checks without real credentials."""

import os
import tempfile
import unittest
from pathlib import Path

from jobsaw.config import Settings


class SettingsTests(unittest.TestCase):
    """Configuration comes from explicit external values and remains isolated."""

    def setUp(self):
        """Use a private .env fixture, never the developer's actual key."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / ".env"
        self.path.write_text("GEMINI_API_KEY=file-key\nGEMINI_MODEL=file-model\n", encoding="utf-8")

    def test_model_is_read_from_file(self):
        """The configuration file owns model choice."""
        self.assertEqual(Settings.from_env(self.path, environ={}).model, "file-model")

    def test_process_values_override_file(self):
        """Explicit process settings have precedence over .env."""
        settings = Settings.from_env(self.path, environ={"GEMINI_MODEL": "process-model"})
        self.assertEqual(settings.model, "process-model")

    def test_missing_model_has_no_fallback(self):
        """A key alone cannot silently select a hard-coded model."""
        self.path.write_text("GEMINI_API_KEY=file-key\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "GEMINI_MODEL"):
            Settings.from_env(self.path, environ={})

    def test_loading_does_not_mutate_environment(self):
        """Multiple loads cannot contaminate other callers."""
        before = dict(os.environ)
        Settings.from_env(self.path, environ={})
        self.assertEqual(dict(os.environ), before)

    def test_invalid_interval_reports_setting(self):
        """Malformed or nonfinite intervals fail at configuration time."""
        for value in ("bad", "nan", "inf", "-1", "61", ""):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "GEMINI_REQUEST_INTERVAL"):
                Settings.from_env(self.path, environ={"GEMINI_REQUEST_INTERVAL": value})

    def test_direct_construction_is_validated_and_hides_key(self):
        """Injected settings follow the same rules and do not expose secrets."""
        with self.assertRaisesRegex(ValueError, "GEMINI_MODEL"):
            Settings(api_key="test-key", model=" ")
        self.assertNotIn("test-key", repr(Settings(api_key="test-key", model="test-model")))
