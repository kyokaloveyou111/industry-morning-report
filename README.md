# Industry Morning Report

A configurable, privacy-safe generator for evidence-grounded Chinese industry morning-report drafts. Industry knowledge lives in JSON profiles, so the same engine can support LED displays or another industry without code changes.

The application creates drafts only. Every report must be reviewed by a person before publication.

Current version: `0.2.0`.

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
python -m morning_report --version
python -m morning_report collect
python -m morning_report generate
python -m morning_report cleanup --days 30
```

After a reviewer saves the final copy, optional anonymized quality metrics can be recorded:

```powershell
python -m morning_report record-review --draft data/reports/draft.md --final path/to/reviewed.md --rating 4 --category factual --category source
```

The metrics file contains timestamps, counts, ratings, similarity, and SHA-256 digests. It does not contain report text, source URLs, or review notes.

## Configure another industry

Copy `profiles/template.json`, replace its keywords, sections, and public sources, then select it:

```powershell
$env:MORNING_REPORT_PROFILE = "profiles/your-industry.json"
python -m morning_report doctor
python -m morning_report run --dry-run
```

The bundled Skill can also create a safe starter profile:

```powershell
python .agents/skills/industry-morning-report/scripts/create_profile.py semiconductor "半导体行业" --keyword 半导体 --keyword semiconductor
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
python .agents/skills/industry-morning-report-maintainer/scripts/privacy_scan.py . --history
python C:\path\to\skill-creator\scripts\quick_validate.py .agents/skills/industry-morning-report
python C:\path\to\skill-creator\scripts\quick_validate.py .agents/skills/industry-morning-report-maintainer
```

The privacy scan recognizes common secret formats, credential assignments, private keys, personal Windows paths, forbidden runtime files, exact staged content, and reachable Git history. It is a defensive check, not proof that no private data exists; a human must still review the staged diff and repository history before publishing.

## Use with Codex

The repository contains two repository-scoped Skills. Open the cloned repository as the current workspace so Codex can discover them automatically:

- `$industry-morning-report` handles setup, profiles, dry runs, generation, diagnosis, and human review.
- `$industry-morning-report-maintainer` handles code changes, tests, privacy audits, CI, pull requests, and releases.

Both Skills locate the project from the current Git worktree, so they do not assume a particular folder on a teammate's computer. A repository-scoped Skill updates when the teammate pulls the repository. A separately copied global Skill does not update automatically and must be reinstalled explicitly.

## Team workflow

The project uses the MIT license, so teammates may use, modify, and redistribute their own copies while keeping the license notice. Prepare changes on a feature branch, run the tests and privacy checks, and submit a pull request. Keep the official default branch protected with required pull requests, owner review, and required tests.
