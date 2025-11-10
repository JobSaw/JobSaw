# JobSaw

AI-powered CV generator and job-scraper harness. This repo converts a canonical
JSON CV model into a one-page PDF using an AltaCV LaTeX template and includes a
lightweight scraper + pipeline to extract job/page text that can be used to
populate or score CV items.

## What changed (quick summary)
- The canonical model moved to `models/output_models/cv_model.json`.
- The scraper now supports BeautifulSoup (if installed) and returns in-memory
	page dicts (`{'url','text'}`) instead of writing files.
- `user_data/*.json` contains your personal data but is ignored by git; a
	`.gitkeep` preserves the folder. See `.gitignore`.
- `templates/CV/` is preserved in the repo via `.gitkeep` while actual
	template files are ignored (so you can keep local `.tex`/`.cls` files without
	committing them).

## Requirements
- Python 3.8+
- A LaTeX distribution (TeX Live, MiKTeX, or MacTeX) with `latexmk` on PATH.
- Optional (recommended for scraping/parsing):
	- `beautifulsoup4`, `lxml` — for robust HTML parsing
	- `requests` — convenient HTTP fetching (the project currently uses urllib but requests is useful)
	- `langchain` — optional, for LLM orchestration if you choose to use LangChain agents

Dependencies are listed in `requirements.txt`.

### Notes about system Python / PEP 668
Some OS Python installations (Debian/Ubuntu/WSL) are "externally managed" and
reject system-wide pip installs. Always create and use a virtual environment
for development (commands below). Do not use `--break-system-packages` unless
you understand the risk.

## Setup (local development)
Choose the correct commands for your shell.

PowerShell (Windows):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r .\requirements.txt
```

WSL / Bash / Zsh:
```bash
python3 -m venv .venv --upgrade-deps
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Fish shell (WSL/macOS with fish):
```fish
python3 -m venv .venv --upgrade-deps
source .venv/bin/activate.fish
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If you see pip import errors after creating the venv, recreate it with
`--upgrade-deps` or run `python -m ensurepip --upgrade` then upgrade pip.

## How to run

Scraper-only (no PDF, default):
```powershell
python orchestor.py
```
This will attempt to scrape the links listed in `orchestor.py`'s `link_list`.
On failure it will prompt you to paste page content (finish with a line
containing only `END`). The script prints full scraped page text and exits.

Generate PDF (opt-in):
```powershell
python orchestor.py --generate-pdf
```
Or specify model/output/templates explicitly:
```powershell
python orchestor.py models/output_models/cv_model.json output/victor_cv.pdf templates/CV --generate-pdf
```

## Project structure (relevant files)
- `orchestor.py` — entrypoint / harness. Loads model, optionally scrapes pages,
	runs the pipeline and calls the LaTeX generator.
- `latex_module/latex_pdf_creator.py` — builds LaTeX from the JSON model and runs `latexmk`.
- `scrapper_module/scrapper_script.py` — fetches pages and extracts visible text
	(uses BeautifulSoup if installed, otherwise falls back to a builtin parser).
- `models/output_models/cv_model.json` — canonical CV schema/template.
- `models/about_models/` — per-section templates (no personal PII).
- `user_data/*.json` — your personal CV data (ignored by git).
- `templates/CV/` — local LaTeX template files (kept out of git; add your local
	`altacv.cls`/`.tex` here during development).
- `requirements.txt` — Python dependencies (includes `langchain` if you plan to use it).

## Notes & recommendations
- BeautifulSoup improves parsing but does not execute JavaScript. For JS-heavy
	pages (e.g., some LinkedIn pages) consider Playwright or manual paste.
- The selection/agent pipeline is currently a simple, in-repo sequence. If you
	want LLM-driven multi-agent orchestration, LangChain is already added to
	`requirements.txt` and can be integrated as an agent layer.
- Keep `user_data/*.json` private — they are ignored by git via `.gitignore`.

## Troubleshooting
- If you get "externally-managed-environment" when installing packages, create
	and use a venv as shown above.
- If pip inside the venv fails with import errors, recreate the venv with
	`--upgrade-deps` or run `python -m ensurepip --upgrade` then upgrade pip.

## Next steps you can try
- Install requirements inside a venv and run `python orchestor.py` to test the
	scraper flow. Use `--generate-pdf` only once your LaTeX environment is ready.
- If you want, I can scaffold a small LangChain prototype (Tools + Agent) to
	run LLM scoring and selection, or scaffold a lightweight in-repo agent
	pipeline. Tell me which and I'll add the files.
