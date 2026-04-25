# OSS Project Management System

A **multi-dimensional-table** Project Management System for a 3-person open-source team, covering **Task Tracking · Bug Statistics · Feature Planning · Overall Scheduling** with native Kanban / Gantt / Calendar views, an at-a-glance Dashboard, automated notifications, and two-way GitHub sync.

[![Live preview of OSS PMS — 7 linked tables with seed data](assets/preview.png)](https://tanweeteck.github.io/MultiDimensionalTables/preview.html)

> **[→ Live Preview](https://tanweeteck.github.io/MultiDimensionalTables/preview.html)** — all 7 tables, seed data, links, lookups & RICE formula · [![Deploy Preview](https://github.com/tanweeteck/MultiDimensionalTables/actions/workflows/pages.yml/badge.svg)](https://github.com/tanweeteck/MultiDimensionalTables/actions/workflows/pages.yml)

> Designed for **Lark / Feishu Bitable** as the primary host, with drop-in equivalents for **Airtable** and **NocoDB**. See [`docs/alternatives.md`](docs/alternatives.md).

---

## Team & Areas

| Area | Code | Owns |
|---|---|---|
| Product Development | **PD** | Features, technical Tasks/Bugs |
| Developer Community Operations | **DCO** | Docs, contributor experience, release notes |
| User Operations | **UO** | Community feedback intake, user-facing triage |

Full matrix: [`docs/01-role-mapping.md`](docs/01-role-mapping.md).

---

## What you get

- **7 linked tables**: Members · Tasks · Bugs · Features · Milestones · Community Feedback · Releases
- **30+ pre-defined views** including Kanban-by-Status, Kanban-by-Assignee, Roadmap Gantt, Calendar, "My Tasks", "Overdue", "Critical Bugs"
- **One Dashboard page** with 10 widgets (KPIs, burn-down, pipeline funnel, throughput, sentiment)
- **12 automations** including the two requested by default:
  - On Task status change → DM the assignee
  - On Task complete → notify the developer group
- **Two-way GitHub sync** via a copy-pasteable GitHub Actions workflow
- **CSV seed data** to bootstrap the base in minutes

---

## Quickstart

Two paths — pick one:

### A. Scripted (≈5 minutes, recommended)

```bash
export LARK_APP_ID=cli_xxx
export LARK_APP_SECRET=xxx
export LARK_BITABLE_APP_TOKEN=bascnxxx     # an empty Bitable base you own

python3 scripts/build_base.py     # creates 7 tables, ~80 fields, 12 views
python3 scripts/seed_base.py      # imports starter rows from seeds/
```

That gets you ~85% of the system. Finish the remaining UI-only pieces (rollups, dashboard, 12 automations) following [`docs/setup-guide.md`](docs/setup-guide.md) §3, §5, §7. Details and failure modes: [`scripts/README.md`](scripts/README.md).

### B. Manual (≈30 minutes)

1. Read [`docs/00-overview.md`](docs/00-overview.md) for the big picture.
2. Follow [`docs/setup-guide.md`](docs/setup-guide.md) to build the base in Lark Bitable.
3. Import [`seeds/*.csv`](seeds/) as starter rows.
4. Drop [`.github/workflows/sync-to-bitable.yml`](.github/workflows/sync-to-bitable.yml) into your project repo and set the four required secrets.
5. Run through the checklist in [Verification](#verification).

---

## Repo layout

```
README.md                           ← you are here
docs/
  00-overview.md                    Architecture diagram + glossary
  01-role-mapping.md                PD / DCO / UO responsibility matrix
  schema/                           One file per table
    01-members.md
    02-tasks.md
    03-bugs.md
    04-features.md
    05-milestones.md
    06-community-feedback.md
    07-releases.md
  views.md                          Every view, with filter/group/sort spec
  dashboard.md                      Each widget's data source + chart type
  automations.md                    All 12 automations: trigger / condition / action
  github-sync.md                    Workflow YAML walkthrough, label routing, secrets
  setup-guide.md                    Step-by-step Lark Bitable build
  alternatives.md                   Airtable / NocoDB equivalents
scripts/
  build_base.py                     Create tables/fields/views via Open API
  seed_base.py                      Import seeds/*.csv into the base
  README.md                         Usage, env vars, idempotency notes
seeds/
  members.csv  tasks.csv  bugs.csv  features.csv  milestones.csv
.github/
  workflows/sync-to-bitable.yml     Issue ↔ Bitable sync
  ISSUE_TEMPLATE/                   Pre-filled labels feed sync routing
    bug_report.md
    feature_request.md
```

---

## Verification

After setup, the team should confirm:

1. All 7 tables exist with the field types specified in `docs/schema/`.
2. Every view in `docs/views.md` renders. Kanban-by-Status shows 6 columns; Roadmap Gantt shows date bars.
3. Dashboard's 10 widgets all populate with seed data.
4. **Automation A1**: change a Task's Status → assignee receives a Lark DM within seconds.
5. **Automation A2**: set Status to `Done` → the dev group receives a completion message; `Completed Date` is populated automatically.
6. **Automation A4**: create a Bug with `Severity = S0` → group post with `@all`.
7. **GitHub sync**: open an issue labeled `bug` → a Bug row appears in Bitable within ~1 min; close the issue → row Status flips. Reverse direction works on `Done` / `Fixed`.
8. Assigning the same Task to each of the three members causes `Owner Area` to populate correctly per role.

Capture screenshots of items 2, 3, 4, 5, and 7 into a top-of-README gallery once the base is live.
