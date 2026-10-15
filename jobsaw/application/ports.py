"""Small interfaces separating application logic from external systems."""

from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import BaseModel

from jobsaw.domain.profile import ProfileData

T = TypeVar("T", bound=BaseModel)


class LanguageModel(Protocol):
    """Generate validated data or document text."""

    def structured(self, instruction: str, content: str, schema: type[T]) -> T:
        """Return a response validated against the supplied schema."""
        ...

    def text(self, instruction: str, content: str) -> str:
        """Return generated document text."""
        ...


class ProfileProvider(Protocol):
    """Load a candidate profile from a replaceable source."""

    def get_profile(self) -> ProfileData:
        """Return the full candidate profile."""
        ...


class PdfCompiler(Protocol):
    """Compile a document and report its page count."""

    def compile(self, source: Path) -> tuple[Path, int]:
        """Return the compiled PDF and its page count."""
        ...
