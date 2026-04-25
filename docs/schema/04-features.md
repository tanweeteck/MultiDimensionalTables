# Table: Features

Discovery → ship pipeline. RICE-prioritized.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Feature ID | Auto-number with prefix | ✓ | Format: `F-{0001}` |
| Name | Text | ✓ | |
| Problem Statement | Long text | ✓ | What user pain does this address |
| Owner | Link → Members | ✓ | Usually a PD member |
| Owner Area | Lookup | auto | `Owner.Role` |
| Status | Single-select | ✓ | `Idea`, `Discovery`, `Planned`, `In Dev`, `Beta`, `Shipped`, `Dropped` |
| Reach | Number |   | RICE — users impacted per quarter |
| Impact | Number (1–3) |   | RICE — 0.25 / 0.5 / 1 / 2 / 3 |
| Confidence (%) | Number |   | RICE — 0–100 |
| Effort (d) | Number |   | RICE — person-days |
| RICE Score | Formula | auto | `Reach * Impact * (Confidence/100) / Effort` |
| Target Milestone | Link → Milestones |   | When you plan to ship |
| Acceptance Criteria | Long text |   | Bullet list |
| Linked Tasks | Reverse-link from Tasks | auto | |
| Tasks Total | Rollup count | auto | |
| Tasks Done | Rollup count | auto | filter `Status = Done` |
| Progress % | Formula | auto | `Tasks Done / Tasks Total * 100` |
| Created | Created time | auto | |
| Updated | Modified time | auto | |
| GitHub Discussion URL | URL |   | Linked discussion or RFC |

## Status flow

```
Idea ──► Discovery ──► Planned ──► In Dev ──► Beta ──► Shipped
   │                                              │
   └──► Dropped ◄─────────────────────────────────┘
```

## Notes

- `Status → Shipped` triggers automation **A8** (DCO release-notes Task + dev group post).
- Sort the `Top by RICE` view descending on `RICE Score` for a default-priority backlog.
- `Progress %` uses Bitable's count-rollup; if the platform lacks count-with-filter rollups, use a hidden formula on Tasks (`IF(Status="Done", 1, 0)`) and sum-rollup it.
