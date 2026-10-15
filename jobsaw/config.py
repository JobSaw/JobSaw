"""Parse runtime configuration without constructing clients or mutating os.environ."""

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

DEFAULT_REQUEST_INTERVAL = 12.0

@dataclass(frozen=True)
class Settings:
    """Validated immutable settings; the deployment must choose its model."""

    # Excluding credentials from repr prevents accidental disclosure in diagnostics.
    api_key: str = field(repr=False)
    model: str
    request_interval: float = DEFAULT_REQUEST_INTERVAL

    def __post_init__(self) -> None:
        """Validate direct construction as well as environment-based construction."""
        if not self.api_key.strip():
            raise ValueError("Set GEMINI_API_KEY in your environment or .env file.")
        if not self.model.strip():
            raise ValueError("Set GEMINI_MODEL in your environment or .env file.")
        if not math.isfinite(self.request_interval) or not 0 <= self.request_interval <= 60:
            raise ValueError("GEMINI_REQUEST_INTERVAL must be between 0 and 60 seconds.")

    @classmethod
    def from_env(cls, env_file: Path = Path('.env'),
                 environ: Mapping[str, str] | None = None) -> "Settings":
        """Read the working directory's .env; process variables take precedence."""
        # An explicit path avoids discovering a different .env beside installed code.
        # Keep configuration loading local so tests and embedded callers stay isolated.
        values = {**dotenv_values(env_file), **(os.environ if environ is None else environ)}
        try:
            interval = float(values.get("GEMINI_REQUEST_INTERVAL", DEFAULT_REQUEST_INTERVAL))
        except (ValueError, TypeError) as exc:
            raise ValueError("GEMINI_REQUEST_INTERVAL must be a number of seconds.") from exc
        return cls(
            api_key=(values.get("GEMINI_API_KEY") or "").strip(),
            model=(values.get("GEMINI_MODEL") or "").strip(),
            request_interval=interval,
        )
