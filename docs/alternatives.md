# Alternatives — Airtable & NocoDB

The schema is platform-agnostic. Below are the main equivalences you'll need to translate this design.

## Field-type mapping

| Concept | Lark Bitable | Airtable | NocoDB |
|---|---|---|---|
| Single-select | Single-select | Single select | Single Select |
| Multi-select | Multi-select | Multiple select | Multi Select |
| Linked record | Link | Linked record | Has Many / Belongs To |
| Lookup from link | Lookup | Lookup | Lookup |
| Rollup | Rollup | Rollup | Rollup |
| Formula | Formula | Formula | Formula |
| Auto-number with prefix | Auto-number (Format → Prefix) | Autonumber + Formula `"T-" & {AN}` | Auto Number + Formula |
| Person / Member | Member field | Collaborator | User |
| Created time / Modified time | Created time / Last modified time | Created time / Last modified time | CreatedAt / UpdatedAt |
| Date | Date | Date | DateTime |
| Attachment | Attachment | Attachment | Attachment |

## Views

| Bitable | Airtable | NocoDB |
|---|---|---|
| Grid | Grid | Grid |
| Kanban | Kanban | Kanban |
| Calendar | Calendar | Calendar |
| Gantt | Gantt (Pro) | Gantt |
| Form | Form | Form |
| Dashboard view | Interface (or chart blocks) | Dashboard |

If using **Airtable on a free plan**, Gantt is paid — substitute a Calendar view of `Milestones` keyed on `Start Date` to `End Date`, or use a third-party Gantt block.

## Automations

| Bitable Action | Airtable Action | NocoDB equivalent |
|---|---|---|
| Send Lark message | Send Slack / email / webhook | Webhook |
| Update record | Update record | Update record |
| Create record | Create record | Insert |
| Send HTTP request | Run script (`fetch()`) | Webhook |
| Schedule trigger | Scheduled trigger | Cron + webhook (external) |

For Airtable, replace the `Send Lark message` action with `Send Slack message` (Airtable has native Slack support) or with `Run script` posting to a Lark / Discord webhook.

## Notification channel translations

| Action in design | Slack | Discord |
|---|---|---|
| DM to `Assignee.Lark Handle` | DM via Slack user ID | DM via Discord user ID (requires bot DM permission) |
| Post to `#dev` group | Post to `#dev` channel via webhook | Post via Discord webhook |
| `@all` mention | `<!channel>` | `@everyone` |

For Discord, the cleanest path is a webhook URL per channel — store these in the **Constants** table the same way as Lark chat IDs.

## GitHub sync

The provided `.github/workflows/sync-to-bitable.yml` is Lark-specific. For Airtable / NocoDB:

- Replace the `tenant_access_token` step with the platform's auth (Airtable PAT / NocoDB API key).
- Replace `bitable.feishu.cn/open-apis/...` calls with:
  - Airtable: `https://api.airtable.com/v0/{baseId}/{tableId}` (`POST` to create, `PATCH` to update)
  - NocoDB: `https://{host}/api/v2/tables/{tableId}/records`
- Field-name resolution is the same — keep field names identical to this repo's spec.

## When to pick which

| Pick … | If … |
|---|---|
| **Lark Bitable** | Team uses Lark / Feishu, wants native chat notifications, free for small teams, China-friendly |
| **Airtable** | Existing Airtable / Slack stack, polished UX, willing to pay for Gantt |
| **NocoDB** | Self-hosted / open-source ethos, comfortable wiring webhooks yourself |
