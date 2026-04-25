# Overview

## Why this exists

A 3-person open-source team is shipping fast across three areas — **Product Development (PD)**, **Developer Community Operations (DCO)**, and **User Operations (UO)** — and needs a single place to track work, surface risk, and notify each other automatically. Off-the-shelf issue trackers don't combine multi-dimensional views, dashboards, and chat-native automation in one tool. **Multi-dimensional tables** (Lark Bitable / Airtable / NocoDB) do.

This system is built around four jobs:

1. **Task Tracking** — what's being worked on, by whom, status, due date.
2. **Bug Statistics** — severity, age, root-cause patterns, fix throughput.
3. **Feature Planning** — discovery → ship pipeline with RICE prioritization.
4. **Overall Scheduling** — milestone Gantt, sprint progress, release coordination.

It is intentionally small: 7 tables, ~30 views, 1 dashboard, 12 automations. Everything else is filtered views and rollups on top.

## Architecture

```
                   ┌──────────────┐
                   │   Members    │  3 rows: PD / DCO / UO
                   └──────┬───────┘
                          │ assignee / owner
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
   ┌─────────┐      ┌──────────┐       ┌──────────┐
   │  Tasks  │◄────►│   Bugs   │       │ Features │
   └────┬────┘      └────┬─────┘       └────┬─────┘
        │ sprint         │ linked task      │ target milestone
        │                ▼                  │
        │           ┌──────────┐            │
        └──────────►│Milestones│◄───────────┘
                    └──────────┘
                          ▲
                          │ converts to
                ┌──────────────────────┐
                │  Community Feedback  │  UO intake
                └──────────────────────┘
```

- **Tasks** is the central hub. Most automations and 80% of the team's daily work happen here.
- **Bugs** and **Features** link back to Tasks (a Feature has many Tasks; a Bug has at most one fix Task).
- **Milestones** group Tasks/Features into time-boxed deliverables. The Roadmap Gantt reads from here.
- **Community Feedback** is UO's inbox; rows graduate into Bugs or Features.
- **Members** is a 3-row lookup table that gives every other table its `Owner Area` for free via a Lookup field.

## Sync key strategy

| Table | Sync key with GitHub |
|---|---|
| Tasks | Issue `#number` |
| Bugs | Issue `#number` |
| Features | Discussion or Issue `#number` |
| Milestones | GitHub Milestone `#number` |

A label routes incoming issues to the right table. See [`github-sync.md`](github-sync.md) for the full routing table.

## Glossary

| Term | Meaning |
|---|---|
| **Bitable** | Lark / Feishu's multi-dimensional table product (the recommended host) |
| **Owner Area** | One of `PD` / `DCO` / `UO`; auto-filled via Lookup from Assignee.Role |
| **Sprint** | A row in the Milestones table with `Status = Active`; the team uses one at a time |
| **RICE** | Reach × Impact × Confidence ÷ Effort prioritization score (Features table) |
| **S0…S3** | Bug severity levels — S0 = production-down, S3 = cosmetic |
| **P0…P3** | Task priority — P0 = drop everything, P3 = nice-to-have |
| **DCO / PD / UO** | Three role codes (see role mapping) |
