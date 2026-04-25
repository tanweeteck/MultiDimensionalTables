#!/usr/bin/env python3
"""
Bootstrap the OSS PMS inside a local NocoDB instance.

Run via:  make build
      or: python3 scripts/build_nocodb.py

No external dependencies — pure Python stdlib.

What this script does:
  1. Waits for NocoDB to be healthy
  2. Creates the admin user on first run (signs in on subsequent runs)
  3. Creates the "OSS PMS" project (idempotent)
  4. Pass 1  — creates 7 tables
  5. Pass 2  — adds primitive fields (text, number, select, date, url, formula …)
  6. Pass 3  — adds linked-record fields between tables
  7. Pass 4  — adds lookup fields that depend on links
  8. Pass 5  — creates Kanban / Grid / Gallery views per table
  9. Pass 6  — bulk-inserts seed rows from seeds/*.csv, then wires links
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
NOCODB_URL = os.environ.get("NOCODB_URL", "http://localhost:8080")
ADMIN_EMAIL = os.environ.get("NOCODB_EMAIL", "admin@oss-pms.local")
ADMIN_PASS = os.environ.get("NOCODB_PASSWORD", "Admin1234!")
PROJECT_NAME = "OSS PMS"
ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"

# ---------------------------------------------------------------------------
# NocoDB UI Types
UI_TEXT = "SingleLineText"
UI_LONG = "LongText"
UI_NUM = "Number"
UI_SELECT = "SingleSelect"
UI_MULTI = "MultiSelect"
UI_DATE = "Date"
UI_CHECK = "Checkbox"
UI_URL = "URL"
UI_EMAIL = "Email"
UI_LINK = "LinkToAnotherRecord"
UI_LOOKUP = "Lookup"
UI_FORMULA = "Formula"
UI_CREATED = "CreatedTime"
UI_MODIFIED = "LastModifiedTime"

# View types
VT_GRID = 3
VT_KANBAN = 4
VT_GALLERY = 1


def sel(*opts: str) -> str:
    """Format select options: "'opt1','opt2',..."."""
    return ",".join(f"'{o}'" for o in opts)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def http(method: str, path: str, token: str | None = None, data=None) -> dict:
    url = f"{NOCODB_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["xc-auth"] = token
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}  [{e.code}]  {msg}") from None


def wait_ready(max_tries: int = 40) -> None:
    print("Waiting for NocoDB…", end="", flush=True)
    for i in range(max_tries):
        try:
            http("GET", "/api/v1/health")
            print(" ready.")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(3)
    print()
    sys.exit("NocoDB did not become ready.  Is 'docker compose up -d' running?")


def login() -> str:
    try:
        r = http("POST", "/api/v1/auth/user/signup",
                 data={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        print(f"  Admin user created ({ADMIN_EMAIL})")
        return r["token"]
    except RuntimeError as e:
        if "already" in str(e).lower() or "exist" in str(e).lower():
            r = http("POST", "/api/v1/auth/user/signin",
                     data={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
            return r["token"]
        raise


# ---------------------------------------------------------------------------
# Meta helpers
# ---------------------------------------------------------------------------
def get_or_create_project(token: str) -> str:
    r = http("GET", "/api/v1/db/meta/projects/", token=token)
    for p in r.get("list", []):
        if p["title"] == PROJECT_NAME:
            print(f"  ~ project  '{PROJECT_NAME}'  (exists)")
            return p["id"]
    r = http("POST", "/api/v1/db/meta/projects/",
             token=token, data={"title": PROJECT_NAME})
    pid = r["id"]
    print(f"  + project  '{PROJECT_NAME}'  {pid}")
    return pid


def list_tables(token: str, pid: str) -> dict[str, dict]:
    r = http("GET", f"/api/v1/db/meta/projects/{pid}/tables", token=token)
    return {t["title"]: t for t in r.get("list", [])}


def get_or_create_table(token: str, pid: str, name: str,
                         existing: dict[str, dict]) -> str:
    if name in existing:
        return existing[name]["id"]
    r = http("POST", f"/api/v1/db/meta/projects/{pid}/tables",
             token=token, data={"title": name})
    tid = r["id"]
    print(f"  + table  {name:26s}  {tid}")
    time.sleep(0.3)
    return tid


def list_fields(token: str, tid: str) -> dict[str, dict]:
    r = http("GET", f"/api/v1/db/meta/tables/{tid}/fields", token=token)
    return {f["title"]: f for f in r.get("list", [])}


def rename_field(token: str, fid: str, new_name: str) -> None:
    http("PATCH", f"/api/v1/db/meta/fields/{fid}",
         token=token, data={"title": new_name})


def create_field(token: str, tid: str, title: str, uidt: str,
                  extra: dict | None = None) -> str:
    body: dict = {"title": title, "uidt": uidt}
    if extra:
        body.update(extra)
    r = http("POST", f"/api/v1/db/meta/tables/{tid}/fields",
             token=token, data=body)
    fid = r.get("id", "")
    time.sleep(0.15)
    return fid


def list_views(token: str, tid: str) -> dict[str, dict]:
    r = http("GET", f"/api/v1/db/meta/tables/{tid}/views", token=token)
    return {v["title"]: v for v in r.get("list", [])}


def create_view(token: str, tid: str, title: str, vtype: int) -> None:
    try:
        http("POST", f"/api/v1/db/meta/tables/{tid}/views",
             token=token, data={"title": title, "type": vtype})
        time.sleep(0.15)
    except RuntimeError as e:
        print(f"      ! view '{title}' failed: {e}")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
# Each table entry:
#   "title_field" : the field to rename the auto-created 'Title' column to
#   "fields"      : list of (name, uidt, extra_kwargs) for additional fields
SCHEMA: dict[str, dict] = {
    "Members": {
        "title_field": "Name",
        "fields": [
            ("Role", UI_SELECT, {"dtxp": sel("PD", "DCO", "UO")}),
            ("Status", UI_SELECT, {"dtxp": sel("Active", "Away")}),
            ("Lark Handle",    UI_TEXT, {}),
            ("Slack Handle",   UI_TEXT, {}),
            ("Discord Handle", UI_TEXT, {}),
            ("GitHub Handle",  UI_TEXT, {}),
            ("Email",          UI_EMAIL, {}),
            ("Focus Areas", UI_MULTI, {"dtxp": sel(
                "Frontend", "Backend", "Docs", "DevRel",
                "Triage", "Support", "Community", "API")}),
        ],
    },
    "Tasks": {
        "title_field": "Title",
        "fields": [
            ("Description", UI_LONG, {}),
            ("Type", UI_SELECT, {"dtxp": sel(
                "Feature", "Bug", "Doc", "DevOps", "Community", "Support")}),
            ("Status", UI_SELECT, {"dtxp": sel(
                "Backlog", "Planned", "In Progress", "Review", "Blocked", "Done")}),
            ("Priority", UI_SELECT, {"dtxp": sel("P0", "P1", "P2", "P3")}),
            ("Estimated Effort (d)", UI_NUM, {}),
            ("Actual Effort (d)",    UI_NUM, {}),
            ("Due Date",       UI_DATE, {}),
            ("Completed Date", UI_DATE, {}),
            ("GitHub Issue #", UI_NUM, {}),
            ("GitHub URL",     UI_URL, {}),
            ("Tags", UI_MULTI, {"dtxp": sel(
                "frontend", "backend", "docs", "good-first-issue")}),
            ("Created",  UI_CREATED, {}),
            ("Modified", UI_MODIFIED, {}),
        ],
    },
    "Bugs": {
        "title_field": "Title",
        "fields": [
            ("Severity", UI_SELECT, {"dtxp": sel(
                "S0-Critical", "S1-High", "S2-Medium", "S3-Low")}),
            ("Status", UI_SELECT, {"dtxp": sel(
                "New", "Triaged", "In Progress", "Fixed",
                "Verified", "Closed", "Won't Fix")}),
            ("Repro Steps",     UI_LONG, {}),
            ("Expected",        UI_LONG, {}),
            ("Actual",          UI_LONG, {}),
            ("Reproducibility", UI_SELECT, {"dtxp": sel(
                "Always", "Sometimes", "Once")}),
            ("Reporter (Free)",  UI_TEXT, {}),
            ("Affected Version", UI_TEXT, {}),
            ("Fixed Date",    UI_DATE, {}),
            ("Verified Date", UI_DATE, {}),
            ("Root Cause", UI_LONG, {}),
            ("Resolution", UI_LONG, {}),
            ("GitHub Issue #", UI_NUM, {}),
            ("GitHub URL",     UI_URL, {}),
            ("Found",    UI_CREATED, {}),
            ("Modified", UI_MODIFIED, {}),
        ],
    },
    "Features": {
        "title_field": "Name",
        "fields": [
            ("Problem Statement", UI_LONG, {}),
            ("Status", UI_SELECT, {"dtxp": sel(
                "Idea", "Discovery", "Planned", "In Dev",
                "Beta", "Shipped", "Dropped")}),
            ("Reach",           UI_NUM, {}),
            ("Impact",          UI_NUM, {}),
            ("Confidence (%)",  UI_NUM, {}),
            ("Effort (d)",      UI_NUM, {}),
            ("Acceptance Criteria", UI_LONG, {}),
            ("GitHub Discussion URL", UI_URL, {}),
            ("Created",  UI_CREATED, {}),
            ("Modified", UI_MODIFIED, {}),
        ],
    },
    "Milestones": {
        "title_field": "Milestone",
        "fields": [
            ("Goal",       UI_LONG, {}),
            ("Start Date", UI_DATE, {}),
            ("End Date",   UI_DATE, {}),
            ("Status", UI_SELECT, {"dtxp": sel(
                "Planning", "Active", "Released", "Postponed")}),
            ("Release Notes URL",  UI_URL, {}),
            ("GitHub Milestone #", UI_NUM, {}),
        ],
    },
    "Community Feedback": {
        "title_field": "Summary",
        "fields": [
            ("Source", UI_SELECT, {"dtxp": sel(
                "GitHub Issue", "GitHub Discussion",
                "Discord", "X", "Email", "Survey", "Other")}),
            ("Source URL",       UI_URL, {}),
            ("Reporter Handle",  UI_TEXT, {}),
            ("Type", UI_SELECT, {"dtxp": sel(
                "Bug Report", "Feature Request", "Question", "Praise")}),
            ("Sentiment", UI_SELECT, {"dtxp": sel(
                "Positive", "Neutral", "Negative")}),
            ("Status", UI_SELECT, {"dtxp": sel(
                "New", "Triaged", "Converted", "Closed")}),
            ("Closed Date", UI_DATE, {}),
            ("Received",  UI_CREATED, {}),
            ("Modified",  UI_MODIFIED, {}),
        ],
    },
    "Releases": {
        "title_field": "Version",
        "fields": [
            ("Tag Date",           UI_DATE, {}),
            ("Highlights",         UI_LONG, {}),
            ("Breaking Changes",   UI_LONG, {}),
            ("GitHub Release URL", UI_URL, {}),
            ("Announcement Posted", UI_CHECK, {}),
        ],
    },
}

# (source_table, field_name, target_table, link_type)
# link_type: "mm" = many-to-many  |  "bt" = belongs-to (one-to-many from target side)
# One entry per relationship pair — NocoDB auto-creates the reverse field.
LINKS: list[tuple[str, str, str, str]] = [
    ("Tasks",              "Assignee",        "Members",            "mm"),
    ("Tasks",              "Sprint",          "Milestones",         "mm"),
    ("Tasks",              "Linked Feature",  "Features",           "mm"),
    ("Tasks",              "Linked Bug",      "Bugs",               "mm"),
    ("Bugs",               "Assignee",        "Members",            "mm"),
    ("Bugs",               "Reporter (FB)",   "Community Feedback", "mm"),
    ("Features",           "Owner",           "Members",            "mm"),
    ("Features",           "Target Milestone","Milestones",         "mm"),
    ("Milestones",         "Owner",           "Members",            "mm"),
    ("Community Feedback", "Triaged By",      "Members",            "mm"),
    ("Community Feedback", "Linked Feature",  "Features",           "mm"),
    ("Releases",           "Linked Milestone","Milestones",         "mm"),
]

# (table, field_name, link_field_on_same_table, field_to_look_up_in_linked_table)
LOOKUPS: list[tuple[str, str, str, str]] = [
    ("Tasks", "Owner Area", "Assignee", "Role"),
    ("Bugs",  "Owner Area", "Assignee", "Role"),
    ("Features", "Owner Area", "Owner", "Role"),
]

FORMULA_FIELDS: list[tuple[str, str, str]] = [
    ("Features", "RICE Score",
     "({Reach} * {Impact} * ({Confidence (%)} / 100)) / {Effort (d)}"),
]

# (table, view_name, view_type)
VIEWS: list[tuple[str, str, int]] = [
    ("Tasks",              "All Tasks",          VT_GRID),
    ("Tasks",              "Kanban by Status",   VT_KANBAN),
    ("Bugs",               "All Bugs",           VT_GRID),
    ("Bugs",               "Open Bugs",          VT_KANBAN),
    ("Features",           "All Features",       VT_GRID),
    ("Features",           "Pipeline",           VT_KANBAN),
    ("Milestones",         "Timeline",           VT_GRID),
    ("Community Feedback", "Inbox",              VT_GRID),
    ("Community Feedback", "By Type",            VT_KANBAN),
    ("Releases",           "Shipped",            VT_GRID),
    ("Members",            "Team",               VT_GRID),
]

# Seed files: (table_name, csv_file, primary_column_in_csv)
SEED_ORDER: list[tuple[str, str, str]] = [
    ("Members",            "members.csv",  "Name"),
    ("Milestones",         "milestones.csv", "Milestone"),
    ("Features",           "features.csv", "Name"),
    ("Tasks",              "tasks.csv",    "Title"),
    ("Bugs",               "bugs.csv",     "Title"),
    ("Community Feedback", "community_feedback.csv", "Summary"),
]

# CSV columns that link to another table: {table: {csv_col: (linked_table, linked_col)}}
SEED_LINKS: dict[str, dict[str, tuple[str, str]]] = {
    "Tasks": {
        "Assignee":       ("Members",   "Name"),
        "Sprint":         ("Milestones","Milestone"),
        "Linked Feature": ("Features",  "Name"),
    },
    "Bugs": {
        "Assignee": ("Members", "Name"),
    },
    "Features": {
        "Owner":            ("Members",    "Name"),
        "Target Milestone": ("Milestones", "Milestone"),
    },
    "Milestones": {
        "Owner": ("Members", "Name"),
    },
}

MULTI_SELECT_COLS: dict[str, set[str]] = {
    "Members": {"Focus Areas"},
    "Tasks":   {"Tags"},
}


# ---------------------------------------------------------------------------
# Data API helpers
# ---------------------------------------------------------------------------
def bulk_insert(token: str, pid: str, tid: str,
                rows: list[dict]) -> list[dict]:
    r = http("POST", f"/api/v1/db/data/noco/{pid}/{tid}/bulk",
             token=token, data=rows)
    return r if isinstance(r, list) else []


def list_records(token: str, pid: str, tid: str) -> list[dict]:
    out, page = [], 1
    while True:
        r = http("GET",
                 f"/api/v1/db/data/noco/{pid}/{tid}?limit=500&where=&page={page}",
                 token=token)
        items = r.get("list", [])
        out.extend(items)
        if not r.get("pageInfo", {}).get("isLastPage", True):
            page += 1
        else:
            break
    return out


def link_records(token: str, pid: str, tid: str, row_id: int,
                  field_id: str, linked_ids: list[int]) -> None:
    """Attach linked record IDs to a mm field on a row."""
    body = [{"Id": lid} for lid in linked_ids]
    http("POST",
         f"/api/v1/db/data/noco/{pid}/{tid}/{row_id}/mm/{field_id}",
         token=token, data=body)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build() -> None:
    wait_ready()

    print("\n── Auth ──────────────────────────────────────────────")
    token = login()

    print("\n── Project ───────────────────────────────────────────")
    pid = get_or_create_project(token)

    # ── Pass 1: tables ────────────────────────────────────────────────────
    print("\n── Pass 1: tables ────────────────────────────────────")
    existing_tables = list_tables(token, pid)
    table_ids: dict[str, str] = {}
    for tname in SCHEMA:
        table_ids[tname] = get_or_create_table(token, pid, tname, existing_tables)
        if tname in existing_tables:
            print(f"  ~ table  {tname}")

    # ── Pass 2: primitive fields ───────────────────────────────────────────
    print("\n── Pass 2: primitive fields ──────────────────────────")
    field_maps: dict[str, dict[str, dict]] = {}
    for tname, cfg in SCHEMA.items():
        tid = table_ids[tname]
        fm = list_fields(token, tid)

        # Rename the auto-created 'Title' field if needed
        title_target = cfg["title_field"]
        if "Title" in fm and title_target not in fm:
            rename_field(token, fm["Title"]["id"], title_target)
            fm[title_target] = {**fm.pop("Title"), "title": title_target}
            print(f"  ~ {tname}.Title → {title_target}")

        # Create additional fields
        for fname, uidt, extra in cfg["fields"]:
            if fname in fm:
                continue
            fid = create_field(token, tid, fname, uidt, extra or None)
            fm[fname] = {"id": fid, "title": fname, "uidt": uidt}
            print(f"  + {tname}.{fname}  ({uidt})")

        field_maps[tname] = list_fields(token, tid)  # refresh

    # ── Pass 3: linked-record fields ──────────────────────────────────────
    print("\n── Pass 3: link fields ───────────────────────────────")
    for src, fname, tgt, ltype in LINKS:
        fm = field_maps[src]
        if fname in fm:
            continue
        try:
            fid = create_field(token, table_ids[src], fname, UI_LINK, {
                "colOptions": {
                    "type": ltype,
                    "parentId": table_ids[src],
                    "childId": table_ids[tgt],
                },
            })
            print(f"  + {src}.{fname} → {tgt}  ({ltype})")
        except RuntimeError as e:
            print(f"  ! {src}.{fname} → {tgt}  FAILED: {e}")

    # Refresh field maps so lookup pass has link field IDs
    for tname in SCHEMA:
        field_maps[tname] = list_fields(token, table_ids[tname])

    # ── Pass 4: lookup + formula fields ───────────────────────────────────
    print("\n── Pass 4: lookup + formula ──────────────────────────")
    for tname, fname, link_field, target_field in LOOKUPS:
        if fname in field_maps[tname]:
            continue
        link_fid = field_maps[tname].get(link_field, {}).get("id")
        if not link_fid:
            print(f"  ! {tname}.{fname}  missing link field '{link_field}'")
            continue
        tgt_tname = next(
            (t for _, lf, t, _ in LINKS if _ == tname and lf == link_field),
            None,
        )
        if not tgt_tname:
            # search without position binding
            tgt_tname = next(
                (t for s, lf, t, _ in LINKS if s == tname and lf == link_field),
                None,
            )
        if not tgt_tname:
            print(f"  ! {tname}.{fname}  cannot resolve target table")
            continue
        tgt_fid = field_maps.get(tgt_tname, {}).get(target_field, {}).get("id")
        if not tgt_fid:
            print(f"  ! {tname}.{fname}  target field {tgt_tname}.{target_field} missing")
            continue
        try:
            create_field(token, table_ids[tname], fname, UI_LOOKUP, {
                "colOptions": {
                    "fk_relation_column_id": link_fid,
                    "fk_lookup_column_id": tgt_fid,
                },
            })
            print(f"  + {tname}.{fname}  (lookup of {tgt_tname}.{target_field})")
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}  FAILED: {e}")

    for tname, fname, expr in FORMULA_FIELDS:
        if fname in field_maps[tname]:
            continue
        try:
            create_field(token, table_ids[tname], fname, UI_FORMULA, {
                "colOptions": {"formula_raw": expr},
            })
            print(f"  + {tname}.{fname}  (formula)")
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}  FAILED: {e}")

    # ── Pass 5: views ─────────────────────────────────────────────────────
    print("\n── Pass 5: views ─────────────────────────────────────")
    for tname, vname, vtype in VIEWS:
        existing = list_views(token, table_ids[tname])
        if vname in existing:
            print(f"  ~ {tname}.{vname}")
            continue
        create_view(token, table_ids[tname], vname, vtype)
        print(f"  + {tname}.{vname}")

    # ── Pass 6: seed data ─────────────────────────────────────────────────
    print("\n── Pass 6: seed data ─────────────────────────────────")
    # Maps  table_name → {display_value → row_id}  for link resolution
    record_index: dict[str, dict[str, int]] = {}

    for tname, csv_name, dedup_col in SEED_ORDER:
        path = SEEDS / csv_name
        if not path.exists():
            print(f"  ~ {tname}: {csv_name} not found, skipping")
            continue

        tid = table_ids[tname]
        existing = list_records(token, pid, tid)
        existing_keys = {
            str(r.get("fields", r).get(dedup_col, r.get(dedup_col, ""))).strip()
            for r in existing
        }
        # Build the record index from rows already in NocoDB
        record_index.setdefault(tname, {})
        for r in existing:
            fields = r.get("fields", r)
            key = str(fields.get(dedup_col, r.get(dedup_col, ""))).strip()
            row_id = r.get("Id") or r.get("id")
            if key and row_id:
                record_index[tname][key] = int(row_id)

        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # Separate primitive values from link values
        link_spec = SEED_LINKS.get(tname, {})
        multi_cols = MULTI_SELECT_COLS.get(tname, set())

        primitive_rows: list[dict] = []
        link_rows: list[dict] = []   # parallel: {col: [display_values]}

        for row in rows:
            key = row.get(dedup_col, "").strip()
            if not key or key in existing_keys:
                continue
            prim: dict = {}
            links: dict = {}
            for col, raw in row.items():
                raw = raw.strip()
                if not raw:
                    continue
                if col in link_spec:
                    links[col] = [v.strip() for v in raw.split(";") if v.strip()]
                elif col in multi_cols:
                    prim[col] = raw  # NocoDB accepts comma-separated string for MultiSelect
                else:
                    prim[col] = raw
            primitive_rows.append(prim)
            link_rows.append(links)

        if not primitive_rows:
            print(f"  ~ {tname}: nothing new to insert")
            continue

        inserted = bulk_insert(token, pid, tid, primitive_rows)
        print(f"  + {tname}: inserted {len(inserted)} rows")

        # Build record index from newly inserted rows for downstream link resolution
        for rec in inserted:
            fields = rec.get("fields", rec)
            key = str(fields.get(dedup_col, rec.get(dedup_col, ""))).strip()
            row_id = rec.get("Id") or rec.get("id")
            if key and row_id:
                record_index[tname][key] = int(row_id)

        # Wire links for newly inserted rows
        # Re-fetch to get stable IDs after bulk insert
        refreshed = {
            str(r.get("fields", r).get(dedup_col, r.get(dedup_col, ""))).strip(): r
            for r in list_records(token, pid, tid)
        }
        fm = list_fields(token, tid)

        for prim, links in zip(primitive_rows, link_rows):
            key = str(prim.get(dedup_col, "")).strip()
            rec = refreshed.get(key)
            if not rec or not links:
                continue
            row_id = rec.get("Id") or rec.get("id")
            if not row_id:
                continue
            for col, display_values in links.items():
                fid = fm.get(col, {}).get("id")
                if not fid:
                    print(f"      ! link field '{col}' not found on {tname}")
                    continue
                tgt_tname, tgt_col = link_spec[col]
                linked_ids = [
                    record_index.get(tgt_tname, {}).get(v)
                    for v in display_values
                ]
                linked_ids = [i for i in linked_ids if i]
                if linked_ids:
                    try:
                        link_records(token, pid, tid, row_id, fid, linked_ids)
                    except RuntimeError as e:
                        print(f"      ! link {tname}#{row_id}.{col}: {e}")

    print(f"""
── Done ──────────────────────────────────────────────
  NocoDB UI   →  {NOCODB_URL}
  Email       →  {ADMIN_EMAIL}
  Password    →  {ADMIN_PASS}

Manual follow-ups (not available via API):
  • Rollup fields  (Tasks Total / Done / Progress %)     → add in UI per docs/schema/04-features.md
  • Dashboard      (charts, KPIs)                        → docs/dashboard.md
  • Automations    (12 webhook/notification rules)       → docs/automations.md
""")


if __name__ == "__main__":
    build()
