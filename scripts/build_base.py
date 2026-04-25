#!/usr/bin/env python3
"""
Build the OSS PMS base in Lark / Feishu Bitable.

Creates 7 tables (Members, Tasks, Bugs, Features, Milestones,
Community Feedback, Releases) with all fields, links, lookups,
formulas and views, in an existing empty Bitable base.

Required env vars:
  LARK_APP_ID, LARK_APP_SECRET   - Custom app credentials
  LARK_BITABLE_APP_TOKEN         - The base's app_token (from base URL)

Optional:
  LARK_REGION  - "intl" (default, open.larksuite.com) or "cn" (open.feishu.cn)

Re-running is idempotent: existing tables/fields/views are skipped.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

REGION = os.environ.get("LARK_REGION", "intl")
BASE_URL = (
    "https://open.larksuite.com/open-apis"
    if REGION == "intl"
    else "https://open.feishu.cn/open-apis"
)

# --- Field type constants (Lark Bitable Open API) -----------------------------
T_TEXT, T_NUMBER, T_SELECT, T_MULTI = 1, 2, 3, 4
T_DATE, T_CHECKBOX, T_USER, T_PHONE = 5, 7, 11, 13
T_URL, T_ATTACH, T_LINK, T_LOOKUP, T_FORMULA = 15, 17, 18, 19, 20
T_CREATED_TIME, T_MODIFIED_TIME, T_AUTONUM = 1001, 1002, 1005

# --- View type constants ------------------------------------------------------
V_GRID, V_KANBAN, V_GALLERY, V_GANTT, V_CALENDAR, V_FORM = (
    "grid", "kanban", "gallery", "gantt", "calendar", "form",
)


# --- Tiny HTTP client ---------------------------------------------------------
def http(method: str, path: str, token: str | None = None, data=None) -> dict:
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url}\n  {e.code} {msg}") from None


def auth() -> str:
    r = http("POST", "/auth/v3/tenant_access_token/internal", data={
        "app_id": os.environ["LARK_APP_ID"],
        "app_secret": os.environ["LARK_APP_SECRET"],
    })
    if r.get("code") != 0:
        raise SystemExit(f"Auth failed: {r}")
    return r["tenant_access_token"]


# --- Schema -------------------------------------------------------------------
# Fields are declared in three passes so dependencies resolve cleanly:
#   pass 1: primitive fields (text, number, select, date, …)
#   pass 2: linked-record fields  (need target tables to exist)
#   pass 3: lookup + formula      (need linked fields to exist)

def opts(*names):
    return {"options": [{"name": n} for n in names]}


PASS1 = {
    "Members": [
        ("Name", T_TEXT, None),
        ("Role", T_SELECT, opts("PD", "DCO", "UO")),
        ("Status", T_SELECT, opts("Active", "Away")),
        ("Lark Handle", T_TEXT, None),
        ("Slack Handle", T_TEXT, None),
        ("Discord Handle", T_TEXT, None),
        ("GitHub Handle", T_TEXT, None),
        ("Email", T_TEXT, None),
        ("Focus Areas", T_MULTI, opts("Frontend", "Backend", "Docs", "DevRel",
                                       "Triage", "Support", "Community", "API")),
    ],
    "Tasks": [
        ("Task ID", T_AUTONUM, {"auto_serial": {"type": "custom", "options": [
            {"type": "fixed_text", "value": "T-"},
            {"type": "auto_increment_number", "value": "0000"},
        ]}}),
        ("Title", T_TEXT, None),
        ("Description", T_TEXT, None),
        ("Type", T_SELECT, opts("Feature", "Bug", "Doc", "DevOps",
                                 "Community", "Support")),
        ("Status", T_SELECT, opts("Backlog", "Planned", "In Progress",
                                   "Review", "Blocked", "Done")),
        ("Priority", T_SELECT, opts("P0", "P1", "P2", "P3")),
        ("Estimated Effort (d)", T_NUMBER, {"formatter": "0.0"}),
        ("Actual Effort (d)", T_NUMBER, {"formatter": "0.0"}),
        ("Due Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("Completed Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("Created Time", T_CREATED_TIME, None),
        ("Last Modified", T_MODIFIED_TIME, None),
        ("GitHub Issue #", T_NUMBER, {"formatter": "0"}),
        ("GitHub URL", T_URL, None),
        ("Tags", T_MULTI, opts("frontend", "backend", "docs", "good-first-issue")),
    ],
    "Bugs": [
        ("Bug ID", T_AUTONUM, {"auto_serial": {"type": "custom", "options": [
            {"type": "fixed_text", "value": "B-"},
            {"type": "auto_increment_number", "value": "0000"},
        ]}}),
        ("Title", T_TEXT, None),
        ("Severity", T_SELECT, opts("S0-Critical", "S1-High", "S2-Medium", "S3-Low")),
        ("Status", T_SELECT, opts("New", "Triaged", "In Progress", "Fixed",
                                   "Verified", "Closed", "Won't Fix")),
        ("Repro Steps", T_TEXT, None),
        ("Expected", T_TEXT, None),
        ("Actual", T_TEXT, None),
        ("Reproducibility", T_SELECT, opts("Always", "Sometimes", "Once")),
        ("Reporter (Free)", T_TEXT, None),
        ("Affected Version", T_TEXT, None),
        ("Found Date", T_CREATED_TIME, None),
        ("Fixed Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("Verified Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("Root Cause", T_TEXT, None),
        ("Resolution", T_TEXT, None),
        ("GitHub Issue #", T_NUMBER, {"formatter": "0"}),
        ("GitHub URL", T_URL, None),
    ],
    "Features": [
        ("Feature ID", T_AUTONUM, {"auto_serial": {"type": "custom", "options": [
            {"type": "fixed_text", "value": "F-"},
            {"type": "auto_increment_number", "value": "0000"},
        ]}}),
        ("Name", T_TEXT, None),
        ("Problem Statement", T_TEXT, None),
        ("Status", T_SELECT, opts("Idea", "Discovery", "Planned", "In Dev",
                                   "Beta", "Shipped", "Dropped")),
        ("Reach", T_NUMBER, {"formatter": "0"}),
        ("Impact", T_NUMBER, {"formatter": "0.0"}),
        ("Confidence (%)", T_NUMBER, {"formatter": "0"}),
        ("Effort (d)", T_NUMBER, {"formatter": "0.0"}),
        ("Acceptance Criteria", T_TEXT, None),
        ("Created", T_CREATED_TIME, None),
        ("Updated", T_MODIFIED_TIME, None),
        ("GitHub Discussion URL", T_URL, None),
    ],
    "Milestones": [
        ("Milestone", T_TEXT, None),
        ("Goal", T_TEXT, None),
        ("Start Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("End Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("Status", T_SELECT, opts("Planning", "Active", "Released", "Postponed")),
        ("Release Notes URL", T_URL, None),
        ("GitHub Milestone #", T_NUMBER, {"formatter": "0"}),
    ],
    "Community Feedback": [
        ("Feedback ID", T_AUTONUM, {"auto_serial": {"type": "custom", "options": [
            {"type": "fixed_text", "value": "FB-"},
            {"type": "auto_increment_number", "value": "0000"},
        ]}}),
        ("Source", T_SELECT, opts("GitHub Issue", "GitHub Discussion",
                                    "Discord", "X", "Email", "Survey", "Other")),
        ("Source URL", T_URL, None),
        ("Reporter Handle", T_TEXT, None),
        ("Type", T_SELECT, opts("Bug Report", "Feature Request",
                                  "Question", "Praise")),
        ("Summary", T_TEXT, None),
        ("Sentiment", T_SELECT, opts("Positive", "Neutral", "Negative")),
        ("Status", T_SELECT, opts("New", "Triaged", "Converted", "Closed")),
        ("Received Date", T_CREATED_TIME, None),
        ("Closed Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
    ],
    "Releases": [
        ("Version", T_TEXT, None),
        ("Tag Date", T_DATE, {"date_formatter": "yyyy/MM/dd"}),
        ("Highlights", T_TEXT, None),
        ("Breaking Changes", T_TEXT, None),
        ("GitHub Release URL", T_URL, None),
        ("Announcement Posted", T_CHECKBOX, None),
    ],
}

# (table, field_name, target_table)
LINK_FIELDS = [
    ("Tasks", "Assignee", "Members"),
    ("Tasks", "Sprint", "Milestones"),
    ("Tasks", "Linked Feature", "Features"),
    ("Tasks", "Linked Bug", "Bugs"),
    ("Tasks", "Depends On", "Tasks"),
    ("Bugs", "Assignee", "Members"),
    ("Bugs", "Reporter (FB)", "Community Feedback"),
    ("Bugs", "Linked Task", "Tasks"),
    ("Features", "Owner", "Members"),
    ("Features", "Target Milestone", "Milestones"),
    ("Milestones", "Owner", "Members"),
    ("Community Feedback", "Triaged By", "Members"),
    ("Community Feedback", "Linked Bug", "Bugs"),
    ("Community Feedback", "Linked Feature", "Features"),
    ("Releases", "Linked Milestone", "Milestones"),
]

# Lookup fields: (table, field_name, link_field_on_this_table, target_field_in_linked_table)
LOOKUP_FIELDS = [
    ("Tasks", "Owner Area", "Assignee", "Role"),
    ("Bugs", "Owner Area", "Assignee", "Role"),
    ("Features", "Owner Area", "Owner", "Role"),
]

# Formula fields: (table, field_name, expression)
FORMULA_FIELDS = [
    ("Features", "RICE Score",
     "[Reach] * [Impact] * ([Confidence (%)] / 100) / [Effort (d)]"),
]

# Views: (table, view_name, view_type)
VIEWS = [
    ("Tasks", "Kanban by Status", V_KANBAN),
    ("Tasks", "Calendar by Due Date", V_CALENDAR),
    ("Tasks", "Gantt by Sprint", V_GANTT),
    ("Tasks", "All Tasks", V_GRID),
    ("Bugs", "Open Bugs", V_KANBAN),
    ("Bugs", "By Severity", V_GRID),
    ("Features", "Pipeline", V_KANBAN),
    ("Features", "Roadmap", V_GANTT),
    ("Milestones", "Timeline", V_GANTT),
    ("Community Feedback", "Inbox", V_GRID),
    ("Community Feedback", "By Type", V_KANBAN),
    ("Releases", "Shipped", V_GRID),
]


# --- Bitable helpers ----------------------------------------------------------
def list_tables(token: str, app: str) -> list[dict]:
    r = http("GET", f"/bitable/v1/apps/{app}/tables?page_size=100", token=token)
    return r["data"]["items"]


def list_fields(token: str, app: str, table_id: str) -> list[dict]:
    out, page = [], None
    while True:
        path = f"/bitable/v1/apps/{app}/tables/{table_id}/fields?page_size=100"
        if page:
            path += f"&page_token={page}"
        r = http("GET", path, token=token)
        out.extend(r["data"]["items"])
        page = r["data"].get("page_token")
        if not page:
            break
    return out


def list_views(token: str, app: str, table_id: str) -> list[dict]:
    r = http("GET", f"/bitable/v1/apps/{app}/tables/{table_id}/views?page_size=100",
             token=token)
    return r["data"]["items"]


def create_table(token: str, app: str, name: str) -> str:
    r = http("POST", f"/bitable/v1/apps/{app}/tables", token=token,
             data={"table": {"name": name}})
    return r["data"]["table_id"]


def create_field(token: str, app: str, table_id: str, spec: dict) -> str:
    r = http("POST", f"/bitable/v1/apps/{app}/tables/{table_id}/fields",
             token=token, data=spec)
    return r["data"]["field"]["field_id"]


def create_view(token: str, app: str, table_id: str, name: str, vtype: str) -> str:
    r = http("POST", f"/bitable/v1/apps/{app}/tables/{table_id}/views",
             token=token, data={"view_name": name, "view_type": vtype})
    return r["data"]["view"]["view_id"]


# --- Build orchestration ------------------------------------------------------
def build():
    app = os.environ["LARK_BITABLE_APP_TOKEN"]
    token = auth()
    print(f"Authed.  Region={REGION}  Base={app[:10]}…")

    # --- Tables ---------------------------------------------------------------
    existing_tables = {t["name"]: t["table_id"] for t in list_tables(token, app)}
    table_ids: dict[str, str] = {}
    for tname in PASS1.keys():
        if tname in existing_tables:
            table_ids[tname] = existing_tables[tname]
            print(f"  ~ table  {tname:24s}  (exists)")
        else:
            table_ids[tname] = create_table(token, app, tname)
            print(f"  + table  {tname:24s}  {table_ids[tname]}")
            time.sleep(0.2)

    # Cache field maps per table for re-runs
    field_maps: dict[str, dict[str, str]] = {
        t: {f["field_name"]: f["field_id"] for f in list_fields(token, app, tid)}
        for t, tid in table_ids.items()
    }

    # --- Pass 1: primitive fields --------------------------------------------
    print("\nPass 1: primitive fields")
    for tname, fields in PASS1.items():
        tid = table_ids[tname]
        for fname, ftype, prop in fields:
            if fname in field_maps[tname]:
                continue
            spec = {"field_name": fname, "type": ftype}
            if prop is not None:
                spec["property"] = prop
            try:
                fid = create_field(token, app, tid, spec)
                field_maps[tname][fname] = fid
                print(f"  + {tname}.{fname}  ({ftype})")
                time.sleep(0.15)
            except RuntimeError as e:
                print(f"  ! {tname}.{fname}  FAILED: {e}")

    # --- Pass 2: linked-record fields ----------------------------------------
    print("\nPass 2: linked-record fields")
    for tname, fname, target in LINK_FIELDS:
        if fname in field_maps[tname]:
            continue
        if target not in table_ids:
            print(f"  ! {tname}.{fname} → {target}  target missing")
            continue
        spec = {"field_name": fname, "type": T_LINK,
                "property": {"table_id": table_ids[target]}}
        try:
            fid = create_field(token, app, table_ids[tname], spec)
            field_maps[tname][fname] = fid
            print(f"  + {tname}.{fname} → {target}")
            time.sleep(0.15)
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}  FAILED: {e}")

    # --- Pass 3: lookup fields -----------------------------------------------
    print("\nPass 3: lookup fields")
    for tname, fname, link_field, target_field in LOOKUP_FIELDS:
        if fname in field_maps[tname]:
            continue
        link_fid = field_maps[tname].get(link_field)
        if not link_fid:
            print(f"  ! {tname}.{fname}  missing link field {link_field}")
            continue
        # Resolve target table from the link field's metadata
        target_tname = next(
            (t for tn, fn, t in LINK_FIELDS if tn == tname and fn == link_field),
            None,
        )
        if not target_tname:
            print(f"  ! {tname}.{fname}  cannot resolve target table")
            continue
        target_fid = field_maps.get(target_tname, {}).get(target_field)
        if not target_fid:
            print(f"  ! {tname}.{fname}  target field {target_tname}.{target_field} missing")
            continue
        spec = {
            "field_name": fname,
            "type": T_LOOKUP,
            "property": {
                "target_table": table_ids[target_tname],
                "target_field": target_fid,
            },
        }
        try:
            fid = create_field(token, app, table_ids[tname], spec)
            field_maps[tname][fname] = fid
            print(f"  + {tname}.{fname}  (lookup of {target_tname}.{target_field})")
            time.sleep(0.15)
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}  FAILED: {e}")

    # --- Pass 3b: formula fields ---------------------------------------------
    print("\nPass 3b: formula fields")
    for tname, fname, expr in FORMULA_FIELDS:
        if fname in field_maps[tname]:
            continue
        spec = {"field_name": fname, "type": T_FORMULA,
                "property": {"formula_expression": expr}}
        try:
            fid = create_field(token, app, table_ids[tname], spec)
            field_maps[tname][fname] = fid
            print(f"  + {tname}.{fname}  formula")
            time.sleep(0.15)
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}  FAILED: {e}")

    # --- Views ----------------------------------------------------------------
    print("\nViews")
    for tname, vname, vtype in VIEWS:
        tid = table_ids[tname]
        existing = {v["view_name"] for v in list_views(token, app, tid)}
        if vname in existing:
            print(f"  ~ {tname}.{vname}  (exists)")
            continue
        try:
            vid = create_view(token, app, tid, vname, vtype)
            print(f"  + {tname}.{vname}  ({vtype})")
            time.sleep(0.15)
        except RuntimeError as e:
            print(f"  ! {tname}.{vname}  FAILED: {e}")

    print("\nDone.")
    print("\nManual follow-ups (not exposed via Open API):")
    print("  • View filters / sort / group        → docs/views.md")
    print("  • Dashboard widgets                  → docs/dashboard.md")
    print("  • Automations (A1–A12)               → docs/automations.md")
    print("  • Rollup fields on Features/Milestones (Tasks Total / Done / Progress %)")
    print("    Configure these in the UI per docs/schema/04-features.md")


if __name__ == "__main__":
    missing = [k for k in ("LARK_APP_ID", "LARK_APP_SECRET", "LARK_BITABLE_APP_TOKEN")
               if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}")
    build()
