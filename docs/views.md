# Views

Every view, with the filter / group / sort it should use. View names are exact — match them when configuring Bitable so deep-links from the Dashboard and automations don't break.

## Tasks (10 views)

| View | Type | Filter | Group | Sort |
|---|---|---|---|---|
| All Tasks | Grid | — | — | `Created Time` desc |
| Kanban by Status | Kanban | — | by `Status` | `Priority` asc, `Due Date` asc |
| Kanban by Assignee | Kanban | `Status != Done` | by `Assignee` | `Priority` asc |
| Calendar by Due Date | Calendar | `Status != Done` | — | by `Due Date` |
| Gantt by Sprint | Gantt | — | by `Sprint` | `Due Date` asc |
| My Tasks | Grid | `Assignee = CurrentUser AND Status != Done` | — | `Priority` asc, `Due Date` asc |
| By Area: PD | Grid | `Owner Area = PD AND Status != Done` | by `Status` | `Priority` asc |
| By Area: DCO | Grid | `Owner Area = DCO AND Status != Done` | by `Status` | `Priority` asc |
| By Area: UO | Grid | `Owner Area = UO AND Status != Done` | by `Status` | `Priority` asc |
| Blocked | Grid | `Status = Blocked` | by `Owner Area` | `Last Modified` desc |
| Overdue | Grid | `Due Date < TODAY() AND Status != Done` | by `Assignee` | `Due Date` asc |
| This Week | Grid | `Due Date <= TODAY() + 7 AND Status != Done` | by `Assignee` | `Due Date` asc |

## Bugs (5 views)

| View | Type | Filter | Group | Sort |
|---|---|---|---|---|
| Open Bugs | Kanban | `Status NOT IN (Verified, Closed, Won't Fix)` | by `Status` | `Severity` asc |
| Critical (S0) | Grid | `Severity = S0-Critical AND Status NOT IN (Closed, Won't Fix)` | — | `Found Date` desc |
| By Severity | Grid | `Status != Closed` | by `Severity` | `Found Date` desc |
| By Affected Version | Grid | — | by `Affected Version` | `Severity` asc |
| My Bugs | Grid | `Assignee = CurrentUser AND Status NOT IN (Closed, Verified)` | — | `Severity` asc |

## Features (4 views)

| View | Type | Filter | Group | Sort |
|---|---|---|---|---|
| Roadmap | Gantt | `Status NOT IN (Idea, Dropped)` | by `Target Milestone` | `Target Milestone.Start Date` asc |
| Pipeline | Kanban | — | by `Status` | `RICE Score` desc |
| Top by RICE | Grid | `Status NOT IN (Shipped, Dropped)` | — | `RICE Score` desc |
| By Area | Grid | — | by `Owner Area` | `RICE Score` desc |

## Milestones (2 views)

| View | Type | Filter | Group | Sort |
|---|---|---|---|---|
| Timeline | Gantt | — | — | `Start Date` asc |
| Active Sprint | Grid | `Status = Active` | — | — |

## Community Feedback (3 views)

| View | Type | Filter | Group | Sort |
|---|---|---|---|---|
| Inbox | Grid | `Status = New` | — | `Received Date` desc |
| By Type | Kanban | — | by `Type` | `Received Date` desc |
| Negative Sentiment | Grid | `Sentiment = Negative AND Received Date >= TODAY() - 30` | — | `Received Date` desc |

## Releases (1 view)

| View | Type | Filter | Group | Sort |
|---|---|---|---|---|
| Shipped | Grid | — | — | `Tag Date` desc |

---

## Defaults

- Each table's **first / default view** is the primary working board:
  - Tasks → `Kanban by Status`
  - Bugs → `Open Bugs`
  - Features → `Pipeline`
  - Milestones → `Timeline`
  - Community Feedback → `Inbox`
  - Releases → `Shipped`
- "My Tasks" / "My Bugs" use Bitable's `CurrentUser()` token so each member sees their own work.
