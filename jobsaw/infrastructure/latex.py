"""Compile LaTeX using a locally installed pdflatex executable."""

import re
import shutil
import subprocess
from pathlib import Path


class LatexCompiler:
    """Run two compiler passes and require a known PDF page count."""

    def compile(self, source: Path) -> tuple[Path, int]:
        """Compile source in its directory, raising on any failed pass."""
        executable = shutil.which("pdflatex")
        if not executable:
            raise RuntimeError("Install TeX Live or MiKTeX with pdflatex on PATH.")
        source = source.resolve()
        command = [
            executable, "-interaction=nonstopmode", "-halt-on-error",
            "-file-line-error", "-no-shell-escape", source.name,
        ]
        output = ""
        # A second pass resolves references; retain failure logs for manual repair.
        for _ in range(2):
            result = subprocess.run(
                command, cwd=source.parent, capture_output=True,
                text=True, timeout=120,
            )
            output = result.stdout
            if result.returncode:
                raise RuntimeError(f"LaTeX compilation failed:\n{output[-2000:]}")
        match = re.search(r"Output written on .*?\((\d+)\s+page", output, re.DOTALL)
        pdf = source.with_suffix(".pdf")
        if not pdf.exists() or not match:
            raise RuntimeError("Compiler did not produce a PDF with a known page count.")
        for extension in (".aux", ".log", ".out"):
            source.with_suffix(extension).unlink(missing_ok=True)
        return pdf, int(match.group(1))
