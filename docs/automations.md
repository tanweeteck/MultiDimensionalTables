# Automations

Twelve automations cover the team's notification needs and the GitHub sync. Each is expressed as `trigger / condition / action` and maps 1:1 to Lark Bitable's automation builder, Airtable Automations, and NocoDB webhooks.

## Channels referenced

- `#dev` — the developer group chat (all 3 members + future contributors)
- `#community` — the community-facing chat (UO-led)
- `DM` — direct message to a member

The Lark group/chat IDs are stored once in Bitable as **Automation Constants** (a small reference table — see Setup Guide §6) and referenced by name to keep automations portable.

---

## A1 — On Task status change → DM the assignee

**Satisfies the user's first stated requirement.**

- **Trigger**: `Tasks` row updated, field `Status` changed
- **Condition**: `Assignee` is not empty
- **Action**: Send Lark DM to `Assignee.Lark Handle`

> 📌 `{Task.Title}` ({Task ID})
> Status: `{old}` → `{new}`
> Open: {Bitable row link}

---

## A2 — On Task complete → notify the developer group

**Satisfies the user's second stated requirement.**

- **Trigger**: `Tasks` row updated, `Status` changed to `Done`
- **Conditions**: previous status was not `Done` (avoid re-fires)
- **Actions** (in order):
  1. Set `Completed Date = NOW()`
  2. Send Lark group message to `#dev`:

> ✅ {Assignee.Name} completed **{Task.Title}** ({Task ID})
> Type: {Type} · Sprint: {Sprint} · Effort: {Actual Effort}d
> {Bitable row link}

---

## A3 — On Task assignment change → DM the new assignee

- **Trigger**: `Tasks` updated, `Assignee` changed
- **Condition**: new `Assignee` not empty
- **Action**: DM new assignee:

> You've been assigned **{Task.Title}** ({Task ID}) by {Modifier.Name}.
> Priority {Priority} · Due {Due Date}
> {row link}

---

## A4 — New Critical (S0) Bug → @all in #dev

- **Trigger**: `Bugs` row created
- **Condition**: `Severity = S0-Critical`
- **Action**: post to `#dev` with `@all`:

> 🚨 **S0 Bug filed**: {Bug.Title} ({Bug ID})
> Reporter: {Reporter} · Affected: {Affected Version}
> {row link}

(Also fires when `Severity` is *changed to* S0 on an existing row.)

---

## A5 — Daily 09:00 → due-soon reminder

- **Trigger**: schedule, every weekday 09:00 local
- **Query**: `Tasks` where `Due Date <= TODAY() + 1 AND Status != Done`
- **Action**: for each row, DM `Assignee` (or `Backup` if `Assignee.Status = Away`):

> ⏰ Due {tomorrow|today}: **{Task.Title}** ({Task ID})

---

## A6 — Daily 09:00 → overdue escalation

- **Trigger**: schedule, every weekday 09:00 local (runs after A5)
- **Query**: `Tasks` where `Due Date < TODAY() AND Status != Done`
- **Actions**:
  1. DM `Assignee` (or `Backup`)
  2. DM the area lead (the most senior member with matching `Role`)

> 🟥 **OVERDUE**: {Task.Title} ({Task ID}) — was due {Due Date}.

---

## A7 — New Community Feedback → DM UO

- **Trigger**: `Community Feedback` row created
- **Action**: DM the on-duty UO member:

> 📬 New {Type} from {Source}: "{Summary[:80]}…"
> Triage: {row link}

---

## A8 — Feature shipped → notify DCO + dev group

- **Trigger**: `Features` updated, `Status` changed to `Shipped`
- **Actions**:
  1. Create `Tasks` row: `Type = Doc`, `Title = "Write release notes for {Feature.Name}"`, `Assignee = DCO member`, `Priority = P1`, `Due = today + 2`
  2. Post to `#dev`:

> 🎉 Feature shipped: **{Feature.Name}** ({Feature ID})
> Owner: {Owner} · Milestone: {Target Milestone}
> Release notes Task created and assigned to {DCO member}.

---

## A9 — Milestone released → seed Releases row + DM DCO

- **Trigger**: `Milestones` updated, `Status` changed to `Released`
- **Actions**:
  1. Create `Releases` row: `Linked Milestone = {row}`, `Tag Date = TODAY()`, `Version = {Milestone.Milestone}` parsed
  2. DM the DCO member:

> 🏷️ {Milestone} marked Released. Draft highlights: {Releases row link}

---

## A10 — GitHub issue opened → create row in Tasks or Bugs

- **Trigger**: GitHub Actions webhook (see [`github-sync.md`](github-sync.md)) calls Bitable Open API
- **Routing**:
  - label includes `bug` → `Bugs` table
  - label includes `enhancement` or `feature` → `Features` (and a child Task)
  - else → `Tasks` table
- **Mapping**:
  - `assignee.login` → Members.GitHub Handle → `Assignee` link
  - Issue body → `Description`
  - Issue # → sync key

Idempotent on Issue # (upsert).

---

## A11 — GitHub issue closed → mark row done

- **Trigger**: GitHub `issues.closed` webhook
- **Action**: find row by Issue #; set `Status = Done` (Tasks) / `Status = Closed` (Bugs); set `Completed Date` / `Fixed Date`.

---

## A12 — Row marked Done in Bitable → close GitHub issue

- **Trigger**: `Tasks.Status → Done` OR `Bugs.Status → Fixed`
- **Condition**: `GitHub Issue #` is not empty
- **Action**: Bitable automation calls GitHub REST API `PATCH /repos/{owner}/{repo}/issues/{n}` with `state: closed`, plus a comment:

> Closed via Bitable: {Task ID|Bug ID} by {Modifier.Name}.

---

## Linter automation (optional but recommended)

Soft warnings to keep the schema clean:

- Task in `In Progress` with no `Assignee` → DM the modifier
- Task `Type = Bug` with no `Linked Bug` → DM the modifier
- Bug `Status = Fixed` with empty `Root Cause` → block the change (or warn)

Set these up as low-priority automations after A1–A12 are working.
