# Human review workflow

Review every generated draft before publication.

## Verify facts

- Open every cited URL.
- Confirm company, person, date, figure, unit, currency, and product claims.
- Confirm the cited page supports the sentence, not merely the topic.
- Separate sourced facts from analysis and forecasts.
- Reject circular reporting and multiple outlets repeating one unsupported claim.

## Verify composition

- Confirm every configured section is present and useful.
- Remove cross-section event duplication even when URLs differ.
- Check recency and geographic balance.
- Confirm the final key signal follows from cited evidence.
- Remove internal, personal, customer, or unpublished information.

## Record anonymized quality metrics

After saving the reviewed copy, run:

```powershell
python -m morning_report record-review --draft <draft.md> --final <reviewed.md> --rating 1-5
```

This stores counts and hashes only, not report text. Do not add confidential notes.
