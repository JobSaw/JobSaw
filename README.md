# JobSaw

Analyze job descriptions, select relevant candidate facts, and generate tailored
one-page PDF CVs with Gemini. This is a small command-line application. Scraping,
web interfaces, and databases are outside its current scope.

## Setup

Requires Python 3.11+. PDF commands also require TeX Live or MiKTeX with `pdflatex`
on PATH and the template packages, including `sourcesanspro` and `fontawesome5`.
Analysis and selection do not require LaTeX.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows, activate with `.venv\Scripts\activate` and copy `.env.example` to
`.env`. Set `GEMINI_API_KEY` using a key from
[Google AI Studio](https://aistudio.google.com/apikey).

Set `GEMINI_MODEL` explicitly; the supplied `.env.example` selects
`gemini-3.1-flash-lite`. Google's
[pricing page](https://ai.google.dev/gemini-api/docs/pricing) lists free input/output
and paid text prices of $0.25/$1.50 per million input/output tokens. Older
2.5 models can be unavailable to newly created projects despite pricing listings. Keep your Google project on the free tier for free-only
usage; the model selection does not control billing. Free-tier content may be
used by Google to improve its products.

`GEMINI_API_KEY` and `GEMINI_MODEL` are required. Settings read `.env` in the current
working directory, with process environment variables taking precedence. Loading
configuration does not mutate the process environment. `GEMINI_REQUEST_INTERVAL` sets seconds between
calls (default 12). Check actual project quotas in
[AI Studio](https://ai.google.dev/gemini-api/docs/rate-limits). Pacing does not
prevent daily or token quotas from being exceeded. Quota failures stop the run
with an actionable message. No automatic model switching is performed.

## Commands

Run from the repository root:

```bash
# Three specialized Gemini extraction calls.
python -m jobsaw analyze examples/job_description.txt

# Select from an explicitly requested fictional profile.
python -m jobsaw select examples/job_description.txt --demo

# Five calls normally; at most seven with page shortening retries.
python -m jobsaw generate examples/job_description.txt --demo

# Save a profile example, edit it, then use real candidate data.
mkdir -p user_data
python -m jobsaw demo-profile > user_data/profile.json
python -m jobsaw generate examples/job_description.txt --profile user_data/profile.json

# Regenerate from saved JSON, without repeating extraction.
python -m jobsaw retry output/<run-directory>

# Compile corrected LaTeX without a key or Gemini call.
python -m jobsaw compile output/<run-directory>
```

Use `-` as the job argument to read stdin. `--output PATH` on analyze/select/generate
specifies a new run directory; existing directories are rejected to protect earlier
runs. Personal files in `user_data/*.json` are ignored by Git.

Optionally install with `python -m pip install -e .` to use `jobsaw` instead of
`python -m jobsaw`. The old root-level scripts have been removed.

## Architecture

```text
jobsaw/
  cli.py                    # CLI and composition root
  config.py                 # Environment configuration
  domain/
    job.py                  # Job schemas
    profile.py              # Candidate and selection schemas
  application/
    ports.py                # Model/provider/compiler interfaces
    prompts.py              # Specialized task instructions
    services.py             # Analyzer, selector, and writer
    pipeline.py             # CV workflow and checkpoints
  infrastructure/
    gemini.py               # Official SDK adapter and shared pacing
    profile_file.py         # JSON profile provider
    mock_profile.py         # Explicit demo provider
    latex.py                # PDF compiler adapter
  resources/                # Packaged template and LaTeX instructions
examples/
tests/
```

Dependencies flow **CLI → application → domain**. Infrastructure implements the
application's small Protocol interfaces. The composition root creates one Gemini
adapter and injects it into the services. Domain models do not import external
SDKs or filesystem adapters.

Patterns used for the current workflow:

- **Ports and adapters:** external systems stay behind interfaces.
- **Dependency injection:** services receive collaborators.
- **Strategy:** JSON and demo providers share one contract.
- **Facade:** CvPipeline coordinates selection, generation, and recovery.

LangChain, Ollama, unused scraping dependencies, duplicated entry points, and old
agent rules have been removed. No framework container or event bus is needed.

Each extraction requests schema-constrained JSON and validates it with Pydantic.
Failures propagate instead of silently producing empty requirements. Selection
checks that all returned items belong to the profile. The writer gets the full
profile for supporting facts and contact details, plus the selected subset and
job analysis. Missing fields must remain empty. Generated prose is not fully
fact-checked; review the finished CV before using it.

## Outputs and recovery

Completed stages are saved immediately:

```text
output/<timestamp>/
  run.log
  01_profile_data.json
  02_job_analysis.json
  03_selected_profile.json
  04_tailored_cv.tex
  05_tailored_cv.pdf
```

Analyze saves only the analysis and log; select saves all three JSON files.
The compiler runs twice with shell escape disabled and requires a known page
count. Generation allows two shortening retries and accepts a final PDF only if
it has exactly one page. Compilation errors stop immediately and leave the
source for manual correction. Retry and compile logs append to the original log.

## Tests

### Compare three tailored CVs

`examples/profile.json` is a large fictional profile with web development,
cloud/platform, and Unity game-development experience. The three fictional jobs
in `examples/jobs/` target different subsets of that same profile. The JSON file
is an editable snapshot of the built-in demo profile.

```bash
python -m jobsaw generate examples/jobs/01_full_stack.txt --profile examples/profile.json --output output/full_stack
python -m jobsaw generate examples/jobs/02_cloud_platform.txt --profile examples/profile.json --output output/cloud_platform
python -m jobsaw generate examples/jobs/03_unity_gameplay.txt --profile examples/profile.json --output output/unity_gameplay
```

Run sequentially. Each folder contains `05_tailored_cv.pdf` and
`03_selected_profile.json`, which explains the selection. Expect web/payment
experience for the first role, cloud/data-ingestion experience for the second,
and the older published-game experience for the third. Generated wording may
vary. These commands use your configured Gemini key; they are not offline tests.
Choose new output names when repeating a run, since existing directories are
rejected. If LaTeX fails, correct the saved `.tex` and use `compile`, or use `retry`
to regenerate it from checkpoints.

### Offline checks

```bash
python -m unittest discover -s tests -v
```

Tests use fake models/compilers, consume no API quota, and require no LaTeX.
Live generation requires the external services described above.
