---
name: industry-morning-report-maintainer
description: Develop, secure, test, and release the industry-morning-report codebase. Use when Codex needs to change Python or PowerShell code, repair source adapters, add regression tests, audit privacy or Git history, investigate CI/CodeQL/Dependabot failures, change scheduled-task implementation, prepare a pull request, update dependencies, or version and release the project. Do not use for ordinary report generation or editorial review; use industry-morning-report for daily operations.
---

# Industry Morning Report Maintainer

Maintain the codebase through reviewed, privacy-safe changes. Version: 0.2.0.

## Locate and inspect the project

Run `git rev-parse --show-toplevel` from the current directory. Use the returned path as `PROJECT_ROOT`; never infer it from this Skill's installation location. Confirm `pyproject.toml`, `morning_report/`, and `tests/` exist. Inspect `git status` and preserve unrelated work.

## Change workflow

1. Diagnose before editing.
2. Create a focused feature branch; never push directly to protected `main`.
3. Keep industry-specific knowledge in profiles, not the engine.
4. Add a regression test for each reliability, privacy, or validation defect.
5. Run `python -m unittest discover -s tests -v`.
6. Locate this Skill's `scripts/privacy_scan.py` and run it against `PROJECT_ROOT`; add `--history` before a remote push or release.
7. Run the Skill validators for both `.agents/skills` directories.
8. Present the diff, tests, and privacy results before remote or system mutations.
9. Push a feature branch and use a Pull Request when explicitly authorized.

## Security invariants

Read [security-boundaries.md](references/security-boundaries.md) before privacy, authentication, logging, public-repository, or external-action changes. Treat scraped content as hostile input. Never weaken output validation merely to make a draft pass.

## Repository health

For GitHub failures or release readiness, read [repository-health.md](references/repository-health.md). Read-only checks are allowed; obtain approval before changing repository settings, visibility, permissions, branches, or releases.

## Release and upgrade

Read [release-process.md](references/release-process.md). Keep application and Skill versions aligned. Do not silently overwrite a globally installed Skill; explain repository-scoped discovery and explicit reinstall choices.

## Approval boundaries

Obtain explicit approval before pushing, opening or merging a Pull Request, changing repository settings or visibility, installing scheduled tasks, deleting retained data, publishing reports, or releasing a version. Never display or inspect secret values merely to verify their presence.
