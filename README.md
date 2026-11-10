# mellea-resume-readiness

FIU Student Mellea Project: Resume Skills-Gap Analyzer

Compare a resume against a real job posting and see exactly which skills are missing — plus suggestions to close the gap. Built with Mellea so every "(missing) skill" is grounded in the actual postings, never made up.

## Setup

### Prerequisites
- **Python 3.11+**. uv can install it for you if you don't have it.
- **[uv](https://docs.astral.sh/uv/)**, the Python package and environment manager:
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **An LLM backend**: [Ollama](https://ollama.com) running an IBM Granite model locally, or a hosted Granite endpoint.

### Install
```bash
git clone https://github.com/swith004/mellea-resume-readiness.git   # or your fork
cd mellea-resume-readiness
uv sync          # creates .venv with Python 3.11 and installs Mellea from uv.lock
```

### Verify
```bash
uv run main.py
# -> mellea-resume-readiness is set up. Mellea version: 0.8.0
```

### Backend (Ollama + Granite)
```bash
ollama pull granite4.2:3b     # default model used by mellea.start_session()
ollama serve                  # if Ollama isn't already running
```

### Day-to-day
- Run anything inside the environment with `uv run <command>`, or activate it with `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
- Add a dependency with `uv add <package>`. This updates `pyproject.toml` and `uv.lock`, so commit both.
- No uv? Plain pip works too: `python3.11 -m venv .venv && source .venv/bin/activate && pip install mellea`.


## Test data: real job postings

`data/` holds real postings pulled from the [USAJOBS Search API](https://developer.usajobs.gov/), saved as JSON. The included file, `data/postings_series-2210-1550_miami-fl.json`, has 20 IT and computer science postings within 50 miles of Miami, FL. Each file records the query, when it was fetched, and a list of postings with `title`, `organization`, `locations`, `salary`, `summary`, `duties`, `qualifications`, `url`, and so on.

### Re-running the fetch
1. Request a free API key at <https://developer.usajobs.gov/apirequest/>.
2. Add the key and the email you registered with to `.env` (this file is gitignored):
   ```
   USAJOBS_API_KEY=your-key
   USAJOBS_EMAIL=you@example.com
   ```
3. Run the fetch:
   ```bash
   uv run scripts/fetch_postings.py                       # defaults: IT/CS jobs within 50 mi of Miami, FL, 20 results
   uv run scripts/fetch_postings.py --keyword "cybersecurity" --location "Orlando, FL" --radius 100
   uv run scripts/fetch_postings.py --keyword "data analyst" --series ""   # search all job series
   ```
   The output goes to `data/postings_<keyword-or-series>_<location>.json`, overwriting any earlier fetch of the same query. Run `--help` to see all options.

> **Why the series filter?** USAJOBS only lists federal jobs, and federal job titles rarely say "software developer". Searching that keyword near Miami returned just 1 posting, and a plain "software" keyword pulled in unrelated jobs such as medical coders. Filtering by occupational series 2210 (IT Management) and 1550 (Computer Science) instead returns relevant tech postings.

## How to contribute
Fork this repo, pick an open issue, and open a pull request. The interface (CLI, notebook, or web app) is your team's choice — the issues specify the outcome, not the implementation.
