# Table: Bugs

Tracks defects and their lifecycle. Severity-driven for triage.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Bug ID | Auto-number with prefix | ✓ | Format: `B-{0001}` |
| Title | Text | ✓ | |
| Severity | Single-select | ✓ | `S0-Critical`, `S1-High`, `S2-Medium`, `S3-Low` |
| Status | Single-select | ✓ | `New`, `Triaged`, `In Progress`, `Fixed`, `Verified`, `Closed`, `Won't Fix` |
| Repro Steps | Long text |   | Numbered list |
| Expected | Long text |   | What should happen |
| Actual | Long text |   | What happened |
| Reproducibility | Single-select |   | `Always`, `Sometimes`, `Once` |
| Reporter (FB) | Link → Community Feedback |   | If reported by a user via UO |
| Reporter (Free) | Text |   | Use when reporter isn't in Community Feedback |
| Assignee | Link → Members |   | |
| Owner Area | Lookup | auto | `Assignee.Role` |
| Affected Version | Text |   | e.g. `v0.3.1` |
| Found Date | Created time | auto | |
| Fixed Date | Date | auto | Set by automation when `Status → Fixed` |
| Verified Date | Date |   | |
| Linked Task | Link → Tasks |   | The Task that fixes it |
| Root Cause | Long text |   | Filled post-mortem |
| Resolution | Long text |   | What changed |
| GitHub Issue # | Number |   | Sync key |
| GitHub URL | URL |   | |

## Severity definitions

| Level | Definition | SLA |
|---|---|---|
| S0-Critical | Production down, data loss, security CVE | Acknowledge < 30 min, fix < 24 h |
| S1-High | Major feature broken, no workaround | Triage < 4 h, fix < 3 days |
| S2-Medium | Feature degraded, workaround exists | Triage < 1 day, fix in current sprint |
| S3-Low | Cosmetic, edge case | Backlog OK |

## Status flow

```
New ──► Triaged ──► In Progress ──► Fixed ──► Verified ──► Closed
  │                                                ▲
  └──► Won't Fix ───────────────────────────────────┘
```

## Notes

- `Severity = S0` triggers automation **A4**: a `@all` post in the dev group.
- The **Bug Burn-down** dashboard widget reads the count of `Status NOT IN (Verified, Closed, Won't Fix)` over time.
