# Morning Report SOP

## Daily workflow

1. Run collection and generation at the configured morning time.
2. Confirm the command exited successfully and a new draft exists.
3. Review the draft manually.
4. Publish only after the reviewer approves it.

## Mandatory review

For every cited item, verify:

- the link opens and points to the claimed source;
- the title, company, person, date, figure, unit, and currency match the source;
- analysis is clearly distinguishable from reported facts;
- no event appears in more than one section;
- the information is recent enough for the intended report;
- private or internal information is absent.

For the complete report, verify:

- every configured section is present and useful;
- domestic and international coverage is balanced when materials allow;
- there is no unsupported forecast or fabricated specificity;
- the final key-signal line reflects the evidence;
- Markdown links and formatting are intact.

## Failure handling

Run:

```powershell
python -m morning_report doctor
```

Then inspect `logs/morning-report.log` and `data/source_health.json`. A source with three consecutive failures or zero-result runs needs review. Do not delete caches first: the buffer and article cache preserve material after a failed generation.

If collection has too few materials:

1. Confirm network access.
2. Check per-source health.
3. Test source feeds or CSS selectors.
4. Add a stable public RSS source if appropriate.
5. Use manual research only with explicit source links and normal editorial review.

If generation fails validation, do not bypass validation. Correct the profile, supplied materials, prompt instructions, or model configuration and retry.

## Weekly maintenance

- Review source health and remove persistently irrelevant sources.
- Sample reports for false claims and weak keyword matches.
- Run the full test suite and privacy scan after changes.
- Update profiles rather than hard-coding industry rules.
- Review disk retention and logs; use the cleanup command rather than deleting data ad hoc.

## Change approval

Local code changes and tests may be prepared without publication. Require the repository owner's approval before pushing, installing a scheduled task, deleting retained user data, publishing a report, or changing repository visibility.

