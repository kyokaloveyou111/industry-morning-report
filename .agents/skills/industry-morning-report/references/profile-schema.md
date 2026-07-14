# Profile schema

Profiles live in `profiles/*.json`. Copy `profiles/template.json` or use the bundled profile creator instead of editing the engine for a new industry.

## Required fields

- `id`: Lowercase letters, digits, and hyphens; maximum 63 characters.
- `display_name`: Human-readable industry name.
- `keywords`: Non-empty, narrow relevance terms.
- `sections`: Ordered, uniquely titled objects with `title` and `instructions`.
- `sources`: At least one public HTTP(S) RSS or web source without embedded credentials.

A web source also requires a CSS `selector`. Never place cookies, tokens, internal hostnames, credentials, or signed URLs in a profile.

## Quality controls

- `minimum_materials`: Refuse generation below this count.
- `maximum_prompt_materials`: Bound prompt size and cost.
- `minimum_citations`: Require supplied source URLs.
- `minimum_section_chars`: Reject nearly empty sections.
- `minimum_report_chars` and `maximum_report_chars`: Bound report length after whitespace removal.
- `used_url_retention_days`: Avoid recently published URLs.
- `snapshot_retention_days`: Remove old material snapshots after successful runs.

## Source objects

RSS source:

```json
{"type":"rss","name":"Example News","url":"https://example.com/feed.xml","max_items":30,"category":"industry"}
```

Web source:

```json
{"type":"web","name":"Example News","url":"https://example.com/news","selector":"article h2 a","max_items":30,"category":"industry"}
```

## Category rules

Each optional rule contains `category`, `keywords`, and optional `tags`. The first matching rule wins. Verify category distribution during a dry run; broad keywords can silently move most articles into one section.
