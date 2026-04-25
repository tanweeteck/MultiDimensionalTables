# Table: Community Feedback

UO's inbox. Rows graduate into Bugs or Features (or close as Question / Praise).

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Feedback ID | Auto-number with prefix | ✓ | Format: `FB-{0001}` |
| Source | Single-select | ✓ | `GitHub Issue`, `GitHub Discussion`, `Discord`, `X`, `Email`, `Survey`, `Other` |
| Source URL | URL |   | Original link |
| Reporter Handle | Text |   | External handle / name |
| Type | Single-select | ✓ | `Bug Report`, `Feature Request`, `Question`, `Praise` |
| Summary | Long text | ✓ | One-paragraph distillation |
| Sentiment | Single-select |   | `Positive`, `Neutral`, `Negative` |
| Status | Single-select | ✓ | `New`, `Triaged`, `Converted`, `Closed` |
| Triaged By | Link → Members |   | Usually a UO member |
| Linked Bug | Link → Bugs |   | Set when converted |
| Linked Feature | Link → Features |   | Set when converted |
| Received Date | Created time | auto | |
| Closed Date | Date |   | Filled when status hits `Closed` |

## Triage flow

```
New ──► Triaged ──► Converted ──► (linked Bug/Feature carries on)
                 │
                 └──► Closed (Question answered, or Praise archived)
```

## Notes

- New rows trigger automation **A7**: DM to the on-duty UO member.
- The **Community Sentiment** dashboard widget is a donut over `Sentiment` for the last 30 days.
- Only UO writes to this table day-to-day; PD/DCO read it for context.
