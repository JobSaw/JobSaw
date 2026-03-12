# JobSaw

AI-powered CV generator and job-scraper harness.

## Job Description Analyzer

A chain of three specialized Gemini-powered agents that parse raw, messy job
descriptions (e.g. copy-pasted from LinkedIn) and extract structured data.

### Agents

| Agent | Output |
|---|---|
| **Hard Skills Extractor** | Programming languages, frameworks, tools, databases, other technical skills |
| **Soft Skills Extractor** | Communication, leadership, teamwork, etc. |
| **Work Scope Predictor** | Day-to-day summary, key responsibilities, projects/domains, team structure |

### Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
#    Edit .env and set GEMINI_API_KEY=<your-key>
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
  config.py                  .env loader + LLM factory (gemini-2.0-flash-lite)
  models.py                  Pydantic output schemas
  prompts.py                 Prompt templates per agent
  hard_skills_agent.py       Hard skills extraction chain
  soft_skills_agent.py       Soft skills extraction chain
  work_scope_agent.py        Work scope prediction chain
  orchestrator.py            Sequential pipeline coordinator
```

### Configuration

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key | *(required)* |

The model used is `gemini-2.0-flash-lite` (cheapest Gemini option, free-tier compatible).