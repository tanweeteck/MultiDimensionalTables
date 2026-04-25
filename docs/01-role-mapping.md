# Role Mapping — PD / DCO / UO

Three people, three areas. Each member is the **default assignee** for the rows tagged with their area, and the **escalation target** for overdue items in that area.

## Responsibility matrix

| Area | Code | Primary tables | Primary Task types | Primary Bug severity | Notification channels |
|---|---|---|---|---|---|
| Product Development | **PD** | Features, Tasks, Bugs | Feature, Bug, DevOps | S0 / S1 / S2 | `#dev` group + DM |
| Developer Community Operations | **DCO** | Tasks, Releases | Doc, Community | S2 / S3 (docs-related) | `#dev` group + DM |
| User Operations | **UO** | Community Feedback, Bugs | Support | (triage all) | `#community` group + DM |

## Daily flow

1. **UO** opens Community Feedback inbox → triages new items → converts to Bug or Feature (or closes as Question/Praise) → notifies PD via the auto-link.
2. **PD** picks the top of `Tasks › Kanban by Status › In Progress` lane scoped to `Owner Area = PD`. Closes Bugs against current Sprint.
3. **DCO** watches `Features.Status = Shipped` → writes release notes Task → publishes changelog → posts the dev-group announcement.
4. All three look at the **Dashboard** at standup; any red KPI gets a Task created on the spot.

## Cross-area handoffs

| From → To | Trigger | Mechanism |
|---|---|---|
| UO → PD | Feedback converts to Bug | UO links the Feedback row to a new Bug; automation A7 already DMd PD |
| UO → PD | Feedback converts to Feature | UO links Feedback to Feature; PD owner picks up Discovery |
| PD → DCO | Feature ships | Automation A8 fires on `Status = Shipped`; DM to DCO + group post |
| PD → DCO | Milestone released | Automation A9 fires on `Status = Released`; DCO drafts release notes |
| DCO → UO | Doc gap reported by user | DCO links a Doc Task back to the original Feedback row |

## Coverage / out-of-office

If a member is OOO, change their row in **Members** to `Status = Away` and the related daily reminder automations (A5, A6) will route the DM to the area's backup (defined as `Members.Backup`, a self-link). The `#dev` group still receives group notifications unchanged.
