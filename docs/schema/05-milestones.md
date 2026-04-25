# Table: Milestones

Sprints and release milestones. Drives the Roadmap Gantt.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Milestone | Text | ✓ | Display name, e.g. `v0.4.0 — Q2 GA` |
| Goal | Long text |   | Outcome statement |
| Start Date | Date | ✓ | Drives Gantt left edge |
| End Date | Date | ✓ | Drives Gantt right edge + due reminders |
| Status | Single-select | ✓ | `Planning`, `Active`, `Released`, `Postponed` |
| Owner | Link → Members |   | The DRI |
| Linked Features | Reverse-link from Features | auto | |
| Linked Tasks | Reverse-link from Tasks | auto | (via `Sprint`) |
| Tasks Total | Rollup count | auto | |
| Tasks Done | Rollup count | auto | filter `Status = Done` |
| Progress % | Formula | auto | `Tasks Done / Tasks Total * 100` |
| Release Notes URL | URL |   | Filled by DCO when released |
| GitHub Milestone # | Number |   | Sync key |

## Conventions

- **At most one** milestone has `Status = Active` at any time. That row is "the current sprint".
- `Status = Released` triggers automation **A9**: pre-fills a Releases row and DMs DCO to draft notes.
- Use `End Date` as the working sprint end for due-date math; the per-Task `Due Date` overrides for individual deadlines.
