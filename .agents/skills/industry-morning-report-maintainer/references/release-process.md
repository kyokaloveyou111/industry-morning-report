# Release process

Use semantic versions. Keep these values aligned:

- root `VERSION`;
- `morning_report.__version__`;
- `project.version` in `pyproject.toml`;
- version text in both Skill bodies.

## Prepare

1. Review changes since the last release.
2. Run unit tests, Skill validation, privacy scan with `--history`, and GitHub health checks.
3. Confirm migration notes for profile or state-format changes.
4. Create a Pull Request and obtain the required review or authorized owner merge.

## Distribute

Repository-scoped Skills under `.agents/skills` update with `git pull`. A globally installed copy does not update automatically. Explain that the user must remove or rename the old installed folder before an explicit reinstall; never delete it without approval.

Create a GitHub release only with explicit approval. Do not attach runtime data, logs, reports, caches, or credential files.
