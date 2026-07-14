---
name: industry-morning-report
description: Operate and review an installed industry-morning-report project. Use when Codex needs to configure an industry profile, check the local environment, collect sources, run a dry run, generate a human-reviewed draft, inspect source health, record anonymized review metrics, or guide a non-developer through daily morning-report operations. Do not use for changing application code, repository security, CI, releases, or dependency maintenance; use industry-morning-report-maintainer for those tasks.
---

# Industry Morning Report Operator

Operate an existing morning-report clone safely. Version: 0.2.0.

## Locate the project

Run `git rev-parse --show-toplevel` from the user's current directory and use the returned path as `PROJECT_ROOT`. If it fails or the root does not contain `pyproject.toml` and `morning_report/`, ask the user to open the cloned project directory. Never derive the project root from this Skill's installation directory.

## Choose the workflow

### Set up or verify

1. Read `README.md` and the selected `profiles/*.json` file.
2. Run `python -m morning_report doctor`.
3. Check only whether required environment variables exist; never display their values.
4. Run `python -m morning_report run --dry-run` before the first LLM call.

### Generate a draft

1. Confirm the user wants to incur an LLM request before the first real generation on a new machine or provider.
2. Run `python -m morning_report run`.
3. Open the generated draft from `data/reports/`.
4. Apply the checklist in [review-workflow.md](references/review-workflow.md).
5. Do not publish or send the draft without explicit approval.

### Create or edit an industry profile

Read [profile-schema.md](references/profile-schema.md). Keep industry knowledge in `profiles/*.json`; do not modify Python for ordinary profile changes. To create a skeleton, run the `create_profile.py` script located next to this Skill and then replace its placeholder source before a dry run.

### Diagnose an operational failure

Check, in order:

1. `python -m morning_report doctor`;
2. UTF-8 logs under `logs/`, without copying possible secrets into chat;
3. `data/last_run_status.json`;
4. `data/source_health.json`;
5. the newest snapshot and recovery buffer;
6. LLM validation errors;
7. the scheduled task's exit code and timeout.

Do not clear caches first. Preserve materials when generation fails. Escalate code defects, repeated parser failures, security findings, or repository changes to `industry-morning-report-maintainer`.

## Respect approval boundaries

Obtain explicit approval before calling an LLM for the first time, installing or changing a scheduled task, deleting retained data, publishing or sending a report, or transmitting material to another service. Never display, log, copy, commit, or transmit a token.
