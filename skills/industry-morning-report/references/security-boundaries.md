# Security boundaries

## Never commit

- `.env` or any credential file;
- API keys, tokens, cookies, authorization headers, or signed URLs;
- generated reports, source snapshots, caches, buffers, logs, or lock files;
- usernames, personal email addresses, local absolute paths, or machine identifiers;
- private company sources, internal prompts, customer data, or unpublished business rules.

## Secret handling

Read keys from environment variables. Check only whether a variable exists; never print its value. Pass caught errors through the redaction helper before logging or displaying them. Use fake keys in tests and ensure tests cannot reach real external services.

## External actions

Require human approval before pushing code, changing repository visibility, installing scheduled tasks, deleting retained data, or publishing reports. A successful draft is not authorization to publish it.

## Repository governance

The MIT license allows colleagues to modify their own copies. Protect the official default branch separately with repository permissions, required pull requests, required owner approval, and required tests. Configure these controls only when the repository owner approves remote setup.

