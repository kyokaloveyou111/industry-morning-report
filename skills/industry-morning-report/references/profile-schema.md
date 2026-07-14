# Profile schema

Profiles live in `profiles/*.json`. Copy `profiles/template.json` instead of editing the engine for a new industry.

## Required fields

- `id`: Lowercase profile identifier.
- `display_name`: Human-readable industry name used in prompts and report titles.
- `keywords`: Narrow terms used to retain relevant source items.
- `sections`: Ordered objects with `title` and `instructions`.
- `sources`: RSS or web source objects.

## Quality controls

- `minimum_materials`: Refuse generation below this count.
- `maximum_prompt_materials`: Bound prompt size.
- `minimum_citations`: Require this many supplied URLs in the report.
- `minimum_section_chars`: Reject nearly empty sections.
- `minimum_report_chars` and `maximum_report_chars`: Bound report length after removing whitespace.
- `used_url_retention_days`: Avoid recently published URLs.
- `snapshot_retention_days`: Delete old material snapshots during successful runs.

## Source objects

RSS source:

```json
{
  "type": "rss",
  "name": "Example News",
  "url": "https://example.com/feed.xml",
  "max_items": 30,
  "category": "industry"
}
```

Web source:

```json
{
  "type": "web",
  "name": "Example News",
  "url": "https://example.com/news",
  "selector": "article h2 a",
  "max_items": 30,
  "category": "industry"
}
```

Use public HTTP(S) URLs only. Never place cookies, tokens, internal hostnames, credentials, or signed URLs in a profile.

## Category rules

Each optional rule contains `category`, `keywords`, and optional `tags`. The first matching rule wins. Keep keywords specific enough to avoid moving most articles into one category.

