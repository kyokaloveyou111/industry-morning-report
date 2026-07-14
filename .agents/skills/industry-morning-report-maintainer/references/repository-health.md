# Repository health

Run these read-only checks when GitHub CLI is available:

```powershell
gh run list --limit 10
gh api repos/{owner}/{repo}/code-scanning/alerts
gh api repos/{owner}/{repo}/dependabot/alerts
gh api repos/{owner}/{repo}/secret-scanning/alerts
gh api repos/{owner}/{repo}/branches/main/protection
```

Do not print alert secrets or authorization details. Summarize alert type, severity, state, affected path, and remediation.

Release readiness requires:

- clean working tree;
- unit tests and CI passing;
- both Skills structurally valid;
- privacy scan including Git history passing;
- CodeQL and Dependabot reviewed;
- protected default branch intact;
- no generated or private artifacts in the Git index.
