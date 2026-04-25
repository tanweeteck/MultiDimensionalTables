# Table: Members

A 3-row lookup table that powers `Owner Area` everywhere else and routes notifications.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Name | Text | ✓ | Display name |
| Role | Single-select | ✓ | Options: `PD`, `DCO`, `UO` |
| Status | Single-select |   | Options: `Active`, `Away`. Drives reminder routing |
| Backup | Self-link |   | Used when `Status = Away` |
| Lark Handle | Text | ✓ | `@open_id` or `email` for Lark API DMs |
| Slack Handle | Text |   | For optional Slack mirror |
| Discord Handle | Text |   | For optional Discord mirror |
| GitHub Handle | Text | ✓ | Sync key — must match `assignee.login` from GitHub events |
| Email | Email |   | Fallback channel |
| Focus Areas | Multi-select |   | Free-form tags: `Frontend`, `Docs`, `Triage`, etc. |
| Avatar | Attachment |   | Optional |

## Relationships

- Reverse-linked from `Tasks.Assignee`, `Bugs.Assignee`, `Features.Owner`, `Milestones.Owner`, `Community Feedback.Triaged By`.

## Notes

- Keep `Role` immutable per row. If someone shifts areas, create a new Members row and re-point links — the dashboards group on `Owner Area`, which is a Lookup of `Role`.
- `GitHub Handle` is case-sensitive in the sync workflow; store exactly as it appears on github.com.
