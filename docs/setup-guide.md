# Setup Guide — Lark Bitable

End-to-end build of the base. Budget ~30 minutes if you're familiar with Bitable; ~60 minutes the first time.

## Prerequisites

- A Lark / Feishu workspace and admin permission to create a Bitable.
- A Lark **Custom App** with these scopes: `bitable:app`, `bitable:app:readonly`, `im:message`, `im:chat`. Save the App ID and App Secret.
- A `#dev` group chat with the bot added; copy the chat ID. Same for `#community`.
- A GitHub repo where you'll add the sync workflow.

## §1 — Create the base & tables (10 min)

1. Create a new Bitable: name it **`OSS PMS`**.
2. Add 7 tables in this order (Bitable creates them as separate tabs):
   - `Members`
   - `Tasks`
   - `Bugs`
   - `Features`
   - `Milestones`
   - `Community Feedback`
   - `Releases`
3. For each table, copy the field list from the corresponding file in [`docs/schema/`](schema/). Field names must match exactly — the workflow and automations look them up by name.
4. For `Tasks`, `Bugs`, `Features`: enable **Auto-number with prefix** on `Task ID` / `Bug ID` / `Feature ID` (Bitable: Field properties → Format).

## §2 — Set up links (5 min)

Field links (single-direction unless noted):

| From | Field | To |
|---|---|---|
| Tasks | Assignee | Members |
| Tasks | Sprint | Milestones |
| Tasks | Linked Feature | Features |
| Tasks | Linked Bug | Bugs |
| Tasks | Depends On | Tasks (self) |
| Bugs | Assignee | Members |
| Bugs | Reporter (FB) | Community Feedback |
| Bugs | Linked Task | Tasks |
| Features | Owner | Members |
| Features | Target Milestone | Milestones |
| Milestones | Owner | Members |
| Community Feedback | Triaged By | Members |
| Community Feedback | Linked Bug | Bugs |
| Community Feedback | Linked Feature | Features |
| Releases | Linked Milestone | Milestones |

After creating each link, open the **target** table and configure the **Lookup** for `Owner Area` from the linked Member's `Role`.

## §3 — Add formulas & rollups (5 min)

| Table | Field | Formula / rollup |
|---|---|---|
| Features | `RICE Score` | Formula: `Reach * Impact * (Confidence/100) / Effort` |
| Features | `Tasks Total` | Rollup: count of `Linked Tasks` |
| Features | `Tasks Done` | Rollup: count of `Linked Tasks` where `Status = "Done"` |
| Features | `Progress %` | Formula: `IF(Tasks Total = 0, 0, Tasks Done / Tasks Total * 100)` |
| Milestones | `Tasks Total` / `Tasks Done` / `Progress %` | Same shape, over `Sprint` reverse-link |
| Tasks | `Owner Area` | Lookup of `Assignee.Role` |
| Bugs | `Owner Area` | Lookup of `Assignee.Role` |
| Features | `Owner Area` | Lookup of `Owner.Role` |

If your Bitable build doesn't support count-with-filter rollups, add a hidden helper formula on `Tasks` (`IF(Status="Done", 1, 0)`) and sum-rollup it instead.

## §4 — Create views (5 min)

In each table, add the views listed in [`docs/views.md`](views.md). Tip: clone the default grid as a base, then change view type / filter / group / sort. Set the indicated default view as the first tab.

## §5 — Build the dashboard (5 min)

1. Bitable → "+" → **Dashboard**.
2. Add widgets in the order from [`docs/dashboard.md`](dashboard.md). Each KPI card → "Indicator card"; donuts → "Pie chart"; line/bar/funnel as named.
3. Pin the dashboard to the top of the base sidebar so it opens by default.

## §6 — Constants table (2 min)

Add a small **Constants** table (it's a 7th technical table, not for daily use):

| Key | Value |
|---|---|
| `chat:dev` | `oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `chat:community` | `oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `member:on_call_uo` | `Member Record ID` |
| `github:owner` | `tanweeteck` |
| `github:repo` | `multidimensionaltables` |
| `github:pat` | (encrypted via Lark's vault if available) |

Automations look up these by `Key` so chat IDs and tokens never appear inline.

## §7 — Configure automations (10 min)

Create A1 through A9 from [`docs/automations.md`](automations.md). For each:

1. Bitable → table → **Automations** → **+ New automation**.
2. Pick the trigger (row created / row updated / scheduled).
3. Add condition(s).
4. Add actions: "Send Lark message" / "Update record" / "Create record" / "Send HTTP request" as specified.
5. Test using Bitable's "Test run" button before enabling.

A10–A12 (GitHub sync) come in §8.

## §8 — GitHub sync (5 min)

1. Copy [`.github/workflows/sync-to-bitable.yml`](../.github/workflows/sync-to-bitable.yml) into your project repo (the OSS project, not this docs repo — though it can be the same).
2. Set the secrets listed in [`docs/github-sync.md`](github-sync.md) under repo Settings → Secrets.
3. Add the issue templates from `.github/ISSUE_TEMPLATE/` to your project repo so contributors land in the right table automatically.
4. For A12 (Bitable → GitHub close), add the **Send HTTP Request** action on the relevant automations using a GitHub PAT with `issues:write` scope.
5. Open a test issue with label `bug` to verify the round-trip.

## §9 — Seed data (2 min)

Import each CSV in [`seeds/`](../seeds/) into the matching table:

- `members.csv` → Members **first** (other tables link to it)
- `milestones.csv` → Milestones
- `features.csv` → Features
- `tasks.csv` → Tasks
- `bugs.csv` → Bugs

After import, manually reconnect link cells if Bitable couldn't auto-resolve them by display value (it usually can).

## §10 — Walk-through verification

Run the verification list in the [README](../README.md#verification). Capture screenshots into the README gallery once green.

## Common gotchas

- **Auto-number prefixes** must be set before importing CSVs that contain `T-001` etc., otherwise IDs collide.
- **Bitable's "Send Lark Message" action** needs the bot added to the chat. If a message silently fails, that's the cause 95% of the time.
- The **`Owner Area` Lookup** sometimes shows blank until you save and reopen the row once after creation; this is a Bitable rendering quirk, not a logic bug.
- For the **GitHub Actions workflow**, make sure the runner has outbound access to `open.larksuite.com` (or `open.feishu.cn` for the China region). If you self-host the runner, allowlist the domain.
