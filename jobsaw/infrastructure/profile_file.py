"""Load real profile data from a local JSON file."""

from pathlib import Path

from jobsaw.domain.profile import ProfileData


class JsonProfileProvider:
    """Profile provider using the domain schema as its file contract."""

    def __init__(self, path: Path) -> None:
        """Store the input file location."""
        self._path = path

    def get_profile(self) -> ProfileData:
        """Read and validate the candidate's JSON profile."""
        return ProfileData.model_validate_json(self._path.read_text(encoding="utf-8"))
