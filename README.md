# JobSaw

AI-powered CV generator and job-scraper harness.

## Job Description Analyzer

A chain of three specialized LLM-powered agents that parse raw, messy job
descriptions (e.g. copy-pasted from LinkedIn) and extract structured data.
Runs locally via Ollama -- no API keys or cloud services required.

### Agents

| Agent | Output |
|---|---|
| **Hard Skills Extractor** | Programming languages, frameworks, tools, databases, other technical skills |
| **Soft Skills Extractor** | Communication, leadership, teamwork, etc. |
| **Work Scope Predictor** | Day-to-day summary, key responsibilities, projects/domains, team structure |

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/download) installed and running
- A pulled model:
  ```bash
  ollama pull qwen2.5:7b
  ```

### Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows PowerShell
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# From a file
python main.py tests/sample_job_description.txt

# From stdin (pipe)
cat job_posting.txt | python main.py
```

### Architecture

```
main.py                      CLI entry point
agents/
  config.py                  LLM factory (Ollama + qwen2.5:7b)
  models.py                  Pydantic output schemas
  prompts.py                 Prompt templates per agent
  hard_skills_agent.py       Hard skills extraction chain
  soft_skills_agent.py       Soft skills extraction chain
  work_scope_agent.py        Work scope prediction chain
  orchestrator.py            Sequential pipeline coordinator
```

### Configuration

The model is configured in `agents/config.py`. Default: `qwen2.5:7b`.
Ollama must be running locally on `http://localhost:11434` (default).