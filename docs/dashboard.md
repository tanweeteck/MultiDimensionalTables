# Dashboard

One page, ten widgets, top-to-bottom. Built using Bitable's Dashboard view (or Airtable Interfaces / NocoDB Dashboards).

## Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  PULSE: [Open Tasks] [Overdue] [Blocked] [Open S0/S1 Bugs]         │  KPI cards
├──────────────────────────────────┬─────────────────────────────────┤
│  Tasks by Owner Area (stacked)   │  Per-person workload (bar)      │
├──────────────────────────────────┼─────────────────────────────────┤
│  Bug Severity Distribution (donut)│  Bug Burn-down (line, 30d)     │
├──────────────────────────────────┼─────────────────────────────────┤
│  Sprint Progress (gauge)         │  Feature Pipeline Funnel         │
├──────────────────────────────────┼─────────────────────────────────┤
│  Throughput (Tasks Done / week)  │  Community Sentiment (donut)    │
├──────────────────────────────────┴─────────────────────────────────┤
│  Roadmap Strip — next 3 Milestones with Progress %                 │
└────────────────────────────────────────────────────────────────────┘
```

## Widget specs

| # | Widget | Source table | Chart | Aggregation / Filter |
|---|---|---|---|---|
| 1 | Open Tasks | Tasks | KPI count | `Status != Done` |
| 2 | Overdue | Tasks | KPI count, red threshold > 0 | `Due Date < TODAY() AND Status != Done` |
| 3 | Blocked | Tasks | KPI count, red threshold > 0 | `Status = Blocked` |
| 4 | Open S0/S1 Bugs | Bugs | KPI count, red threshold > 0 | `Severity IN (S0,S1) AND Status NOT IN (Verified, Closed, Won't Fix)` |
| 5 | Tasks by Owner Area | Tasks | Stacked bar | x = `Owner Area`, stack = `Status`, filter `Status != Done` |
| 6 | Per-person workload | Tasks | Horizontal bar | x = count, y = `Assignee`, filter `Status != Done` |
| 7 | Bug Severity Distribution | Bugs | Donut | by `Severity`, filter `Status NOT IN (Verified, Closed, Won't Fix)` |
| 8 | Bug Burn-down | Bugs | Line, 30 days | series A = open count by day, series B = closed-cumulative |
| 9 | Sprint Progress | Milestones | Gauge | `Progress %` of row where `Status = Active` |
| 10 | Feature Pipeline Funnel | Features | Funnel / horizontal bar | counts by `Status` in order Idea→Discovery→Planned→In Dev→Beta→Shipped |
| 11 | Throughput | Tasks | Line, 8 weeks | count where `Completed Date IN week N` |
| 12 | Community Sentiment | Community Feedback | Donut | by `Sentiment`, filter `Received Date >= TODAY() - 30` |
| 13 | Roadmap Strip | Milestones | Table widget | next 3 rows where `End Date >= TODAY()`, sorted by `Start Date` asc, columns: `Milestone`, `End Date`, `Progress %`, `Owner` |

## Refresh

- Bitable Dashboards refresh on data change automatically.
- For deeper analytics (e.g. bug-aging cohort), export to a Bitable "Statistics" view rather than over-loading the Dashboard.

## Standup ritual

At each daily standup, scan the dashboard top-down:

1. Are any **red KPIs** present? If yes, that becomes the first agenda item.
2. **Per-person workload** — anyone underwater? Re-balance.
3. **Sprint Progress** — on track for the milestone end date?
4. **Community Sentiment** — any negative spike? UO reports.

If a red KPI persists for two consecutive standups, create a Task to address it.
