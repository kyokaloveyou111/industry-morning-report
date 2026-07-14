---
name: industry-morning-report
description: Configure, operate, diagnose, secure, and iteratively improve the industry-morning-report project. Use when Codex needs to create an industry profile, add or repair RSS/web sources, run collection or draft generation, investigate scheduled-run failures, validate AI citations and section quality, protect tokens and local privacy, or prepare a reviewed project change for teammates.
---

# Industry Morning Report

Operate the configurable morning-report application while preserving human review and strict privacy boundaries. Treat the repository containing this skill at `../..` as the project root.

## Follow the workflow

1. Inspect the selected profile and run `python -m morning_report doctor`.
2. For collection or source work, run `python -m morning_report run --dry-run` before calling an LLM.
3. For generation work, preserve the validation gate: never save a draft containing invented URLs, missing sections, or cross-section URL reuse.
4. Run `python -m unittest discover -s tests -v` after code changes.
5. Run `python skills/industry-morning-report/scripts/privacy_scan.py .` before any commit or handoff.
6. Present changed files, test results, and privacy-scan results for human review.

## Respect approval boundaries

Proceed locally with reversible configuration, diagnostics, code edits, and tests. Obtain explicit approval before:

- pushing to a remote repository;
- creating or changing a remote repository;
- installing or changing a scheduled task;
- deleting retained user data;
- publishing or sending a generated report;
- making a private repository public.

Never display, log, copy, commit, or transmit a token. Read secrets only from documented environment-variable names. Redact exceptions before logging them. Never inspect secret values merely to confirm that they exist.

Keep report publication human-gated. The application produces drafts only; do not add unattended external publishing unless the user explicitly changes this policy.

## Manage profiles

Read [profile-schema.md](references/profile-schema.md) before creating or substantially editing a profile. Keep industry knowledge in `profiles/*.json`; do not hard-code it in the Python engine. Start from `profiles/template.json` and use a lowercase, filesystem-safe profile ID.

When adding a source:

- prefer a stable RSS feed;
- use a narrow CSS selector for web sources;
- verify the source yields relevant items in a dry run;
- preserve per-source health tracking;
- avoid bypassing authentication, paywalls, robots controls, or access restrictions.

## Diagnose failures

Check, in order:

1. `python -m morning_report doctor` output;
2. UTF-8 logs in `logs/` without echoing secret values;
3. `data/source_health.json` for consecutive failures;
4. the newest material snapshot and recovery buffer;
5. LLM validation errors;
6. the scheduled task's exit code and timeout.

Do not clear caches as a first response. The article cache and buffer are recovery mechanisms. Preserve collected materials when generation fails.

## Evolve safely

Keep changes small and reviewable. Add regression tests for every reliability or privacy bug. Do not weaken validation to make a failing draft pass. Update `SOP.md` and profile documentation when behavior changes.

For threat boundaries and prohibited repository content, read [security-boundaries.md](references/security-boundaries.md).

