# JobSaw

AI-powered CV generator. This repository contains a small LaTeX-based CV renderer that
accepts a canonical JSON model (`models/cv_model.json`) and produces a PDF using a
LaTeX template (`templates/CV`).

## Requirements

- Python 3.8+
- A working LaTeX distribution (TeX Live, MiKTeX, or MacTeX). On Windows, MiKTeX or TeX Live are recommended.
- `latexmk` available on PATH (usually provided by your LaTeX distribution).

There are no additional Python packages required for the current code. Verify `latexmk` is available by running:

```powershell
latexmk --version
```

If the command is not found, install/enable `latexmk` via your TeX distribution or add it to your PATH.

## How to test locally

From the repository root (Windows PowerShell):

```powershell
# builds output/victor_cv.pdf using the test data embedded in orchestor.py
python orchestor.py

# Optionally specify a different model, output file or templates dir
python orchestor.py models/cv_model.json output/victor_cv.pdf templates/CV
```

PDF and temporary build artifacts are ignored by `.gitignore` by default. The canonical JSON template lives in `models/cv_model.json`. The fully populated test data is intentionally embedded in `orchestor.py` for local testing; when you are ready to use a single source of truth, move the populated JSON back to `models/cv_model.json`.

## Notes

- The generator copies the `templates/CV` contents into a temporary working directory when compiling so that `altacv.cls` and supporting files are available.
- If LaTeX build fails because content is too long (more than one page), shorten bullet items or adjust the template.

