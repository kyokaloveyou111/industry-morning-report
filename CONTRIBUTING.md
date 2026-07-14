# Contributing

Prepare changes on a branch and submit a pull request. The official default branch should require the repository owner's approval before merge.

Before requesting review:

```powershell
python -m unittest discover -s tests -v
python skills/industry-morning-report/scripts/privacy_scan.py .
```

Include the problem, behavior change, test evidence, privacy impact, and rollback notes in the pull request. Add a regression test for reliability and privacy fixes. Never weaken report validation merely to accept a failing draft.

Do not commit tokens, `.env`, runtime data, generated reports, caches, logs, personal paths, internal sources, or customer information. Report suspected secret exposure privately to the repository owner; do not open a public issue containing the secret.

