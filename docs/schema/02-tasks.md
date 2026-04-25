# Table: Tasks

Central hub. Most automations and 80% of daily activity live here.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Task ID | Auto-number with prefix | ✓ | Format: `T-{0001}` |
| Title | Text | ✓ | One-line summary |
| Description | Long text |   | Markdown, mirrored from GitHub issue body when synced |
| Type | Single-select | ✓ | `Feature`, `Bug`, `Doc`, `DevOps`, `Community`, `Support` |
| Status | Single-select | ✓ | `Backlog`, `Planned`, `In Progress`, `Review`, `Blocked`, `Done` |
| Priority | Single-select | ✓ | `P0`, `P1`, `P2`, `P3` |
| Assignee | Link → Members | ✓ | Single |
| Owner Area | Lookup | auto | `Assignee.Role` |
| Sprint | Link → Milestones |   | The Milestone with `Status = Active` is the current sprint |
| Linked Feature | Link → Features |   | If this Task implements a feature |
| Linked Bug | Link → Bugs |   | If this Task fixes a bug |
| Depends On | Self-link (multi) |   | Blocking graph |
| Estimated Effort (d) | Number |   | Days, decimal allowed |
| Actual Effort (d) | Number |   | Filled at completion |
| Due Date | Date |   | Local time |
| Completed Date | Date | auto | Set by automation A2 when `Status → Done` |
| Created Time | Created time | auto | |
| Last Modified | Modified time | auto | |
| GitHub Issue # | Number |   | Sync key, unique |
| GitHub URL | URL |   | Convenience link |
| Tags | Multi-select |   | Free-form |

## Status flow

```
Backlog ──► Planned ──► In Progress ──► Review ──► Done
                            │              │
                            ▼              │
                        Blocked ◄──────────┘
```

- `Blocked` is reachable from any active state. Automation A1 fires on every status change.
- `Done` is terminal except for re-opens (rare).

## Validation rules

- A Task in `In Progress` must have an `Assignee`.
- A Task with `Type = Bug` should have `Linked Bug` populated.
- A Task with `Type = Feature` should have `Linked Feature` populated.

These are enforced as Bitable form-view validations (when teams use forms) and as soft-warning automations otherwise — see `automations.md` for the linter automation.

## Relationships

- `Assignee` → Members
- `Sprint` → Milestones
- `Linked Feature` → Features
- `Linked Bug` → Bugs
- `Depends On` → Tasks (self)
