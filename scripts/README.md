# Builder scripts

Two scripts, no dependencies (Python 3.10+ stdlib only).

| Script | Purpose |
|---|---|
| `build_base.py` | Creates the 7 tables, fields (primitive / linked / lookup / formula), and base views in an empty Bitable base. Idempotent. |
| `seed_base.py` | Imports the CSVs from `seeds/` into the base, resolving linked-record cells by display value. Idempotent. |

## Prerequisites

1. A **Lark / Feishu Custom App** with these scopes:
   - `bitable:app` (read/write Bitable data)
   - `im:message`, `im:chat` (only needed for automation A1–A9 later; not required for these scripts)
2. An **empty Bitable base** you control. From the base URL, copy the `app_token` segment — it's the long token after `/base/`.
3. The Custom App must be **added as a collaborator** with edit permission on the base, otherwise the API returns `99991663 NoPermission`.

## Region

Both scripts default to the international endpoint (`open.larksuite.com`). For mainland-China Feishu (`open.feishu.cn`), set:

```bash
export LARK_REGION=cn
```

## Run

```bash
export LARK_APP_ID=cli_xxx
export LARK_APP_SECRET=xxx
export LARK_BITABLE_APP_TOKEN=bascnxxx       # the empty base
# export LARK_REGION=cn                      # optional, default 'intl'

python3 scripts/build_base.py     # ~1 min; creates schema
python3 scripts/seed_base.py      # ~30 s; imports 16 sample rows
```

Sample output from `build_base.py`:

```
Authed.  Region=intl  Base=bascnabcde…
  + table  Members                    tblxxxxxx
  + table  Tasks                      tblyyyyyy
  …
Pass 1: primitive fields
  + Members.Name  (1)
  + Members.Role  (3)
  …
Pass 2: linked-record fields
  + Tasks.Assignee → Members
  + Tasks.Sprint → Milestones
  …
Pass 3: lookup fields
  + Tasks.Owner Area  (lookup of Members.Role)
  …
Views
  + Tasks.Kanban by Status  (kanban)
  …
Done.
```

## What's automated vs. manual

| Layer | Automated by these scripts | Do in UI |
|---|---|---|
| 7 tables | ✅ | |
| ~80 primitive fields (text / number / select / date / url / autonumber / created/modified time) | ✅ | |
| 15 linked-record fields | ✅ | |
| 3 lookup fields (`Owner Area` on Tasks/Bugs/Features) | ✅ | |
| 1 formula field (`RICE Score`) | ✅ | |
| 12 base views (Kanban / Gantt / Calendar / Grid scaffolding) | ✅ | Configure filters/sort/group per `docs/views.md` |
| Rollups (`Tasks Total` / `Tasks Done` / `Progress %`) on Features & Milestones | ❌ | Add via UI per `docs/schema/04-features.md` (not exposed via Open API) |
| Dashboard widgets | ❌ | Build per `docs/dashboard.md` |
| Automations A1–A12 | ❌ | Build per `docs/automations.md` |

The two unchecked rows are limitations of the Lark Bitable Open API — rollups, dashboards, and automations are not exposed for programmatic creation. The scripts get you ~85% of the way there in two minutes; the remaining UI steps take ~15 minutes following `docs/setup-guide.md` §3, §5, §7.

## Re-running

Both scripts are idempotent on re-run:

- `build_base.py` skips tables / fields / views that already exist by name.
- `seed_base.py` skips rows whose primary text (e.g. `Name`, `Title`, `Milestone`) already exists in the table.

So if a single field fails (rare — usually a permission or quota issue), fix the cause and re-run. Only the missing pieces will be created.

## Failure modes

| Error | Cause | Fix |
|---|---|---|
| `99991663 NoPermission` | Custom App not added to the base | Add the app as a collaborator with edit access |
| `1254032 Field type not supported` | Region mismatch on a property field | Toggle `LARK_REGION` |
| `1254005 FieldNameDuplicated` | Re-run after partial failure | Already handled by idempotency; ignore |
| `1254607 LinkTableNotFound` | Target of a link field hasn't been created yet | Re-run; pass-2 will pick it up |
| Lookup creation fails | API differences across regions | Add the 3 lookup fields manually (Members.Role) — takes <1 min |
