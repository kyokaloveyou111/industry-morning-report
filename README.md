# Industry Morning Report

A configurable, privacy-safe generator for evidence-grounded Chinese industry morning-report drafts. Industry knowledge lives in JSON profiles, so the same engine can support LED displays or another industry without code changes.

The application creates drafts only. Every report must be reviewed by a person before publication.

## Safety defaults

- API keys are read from environment variables and redacted from logs.
- Runtime data, reports, caches, logs, `.env`, and local paths are excluded from Git.
- Failed generation keeps collected materials for the next retry.
- Drafts are rejected if they invent URLs, omit sections, reuse a URL across sections, or lack citations.
- Remote pushes, scheduled-task installation, data deletion, and publication require owner approval.

## Install

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Set secrets as user environment variables; do not place real values in committed files:

```powershell
$env:MORNING_REPORT_LLM_PROVIDER = "anthropic"
$env:MORNING_REPORT_LLM_MODEL = "your-enabled-model"
$env:ANTHROPIC_API_KEY = "your-private-key"
```

For an OpenAI-compatible endpoint, select `openai` and set `OPENAI_API_KEY`; set `OPENAI_BASE_URL` only when needed. Local Ollama-style generation uses provider `local` and does not require a key.

## Run

Start with a collection-only dry run:

```powershell
python -m morning_report doctor
python -m morning_report run --dry-run
```

Generate a validated draft:

```powershell
python -m morning_report run
```

Drafts appear under `data/reports/`. Review every fact, number, company name, date, and source before publishing.

Other commands:

```powershell
python -m morning_report collect
python -m morning_report generate
python -m morning_report cleanup --days 30
```

## Configure another industry

Copy `profiles/template.json`, replace its keywords, sections, and public sources, then select it:

```powershell
$env:MORNING_REPORT_PROFILE = "profiles/your-industry.json"
python -m morning_report doctor
python -m morning_report run --dry-run
```

The bundled Skill can also create a safe starter profile:

```powershell
python skills/industry-morning-report/scripts/create_profile.py semiconductor "半导体行业" --keyword 半导体 --keyword semiconductor
```

Replace the placeholder feed before running it.

The included `profiles/led.json` is the first working profile.

## Windows scheduling

Review `scripts/setup_scheduled_task.ps1` before running it. Installing or replacing a scheduled task changes the local system and should require explicit owner approval.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_scheduled_task.ps1
```

The task uses a 20-minute runner timeout, prevents overlapping application runs, writes UTF-8 rotating logs, and returns the Python exit code to Task Scheduler.

## Test and privacy-check

```powershell
python -m unittest discover -s tests -v
python skills/industry-morning-report/scripts/privacy_scan.py .
python C:\path\to\skill-creator\scripts\quick_validate.py skills/industry-morning-report
```

## Team workflow

The project uses the MIT license, so teammates may modify their own copies. Protect the official default branch in GitHub with required pull requests, required owner approval, and required tests. Remote governance is configured only after the repository owner approves upload.
