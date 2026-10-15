"""Official Gemini SDK adapter with structured output and request pacing."""

import time

from google import genai
from google.genai import errors, types

from jobsaw.application.ports import T
from jobsaw.config import Settings


class GeminiModel:
    """Share one client and pacing budget across all pipeline stages."""

    def __init__(self, settings: Settings) -> None:
        """Initialize a Developer API client with bounded HTTP requests."""
        self._client = genai.Client(
            api_key=settings.api_key,
            http_options=types.HttpOptions(timeout=120_000),
        )
        self._model = settings.model
        self._interval = settings.request_interval
        self._last_request: float | None = None

    def close(self) -> None:
        """Release HTTP resources when the CLI exits."""
        self._client.close()

    def _generate(self, instruction: str, content: str, schema: type[T] | None = None) -> str:
        """Pace calls and reject failed or empty responses."""
        if self._last_request is not None:
            delay = self._interval - (time.monotonic() - self._last_request)
            if delay > 0:
                time.sleep(delay)
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.0 if schema else 0.3,
            max_output_tokens=8192,
            response_mime_type="application/json" if schema else "text/plain",
            response_schema=schema,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        self._last_request = time.monotonic()
        # Tasks never invoke tools; disabling AFC keeps requests predictable.
        try:
            response = self._client.models.generate_content(
                model=self._model, contents=content, config=config,
            )
        except errors.APIError as exc:
            if exc.code == 404:
                raise RuntimeError(
                    f"Gemini model '{self._model}' is unavailable for this project. "
                    "Set GEMINI_MODEL to an available model in .env "
                    "or the process environment. "
                    f"Google's explanation: {exc.message}"
                ) from exc
            if exc.code == 429:
                raise RuntimeError(
                    "Gemini quota exceeded. Check your limits in AI Studio; "
                    "retry later or increase GEMINI_REQUEST_INTERVAL. "
                    "The retry command requires all three JSON checkpoints; "
                    "if extraction did not finish, start a new run later."
                ) from exc
            raise RuntimeError(f"Gemini request failed (HTTP {exc.code}).") from exc
        if not response.candidates or response.candidates[0].finish_reason != types.FinishReason.STOP:
            raise RuntimeError("Gemini did not complete the response; no result was accepted.")
        if not response.text or not response.text.strip():
            raise RuntimeError("Gemini returned an empty response.")
        return response.text.strip()

    def structured(self, instruction: str, content: str, schema: type[T]) -> T:
        """Request schema-constrained JSON and validate it with Pydantic."""
        return schema.model_validate_json(self._generate(instruction, content, schema))

    def text(self, instruction: str, content: str) -> str:
        """Generate raw text for the document writer."""
        return self._generate(instruction, content)
