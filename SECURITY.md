# Security

Do not report credentials or private data in an issue. Contact the repository owner privately with the affected file and commit identifier, but never repeat the secret value.

If a secret may have been committed:

1. Revoke or rotate it immediately at the provider.
2. Remove it from the working tree and repository history.
3. Review logs and provider usage for abuse.
4. Add or improve a regression check.

Generated reports are untrusted drafts. Human review is required before publication. Source text is also untrusted input and must not override system or application instructions.

Before a remote push, run the maintained scanner against the index, working tree, and reachable history:

```powershell
python .agents/skills/industry-morning-report-maintainer/scripts/privacy_scan.py . --history
```

The scanner reports only the location, line number, and finding type; it does not print matched secret values. Pattern scanning cannot recognize every possible credential, private fact, proprietary source, or re-encoded value, so it complements rather than replaces staged-diff review, GitHub secret scanning, and credential rotation after exposure.
