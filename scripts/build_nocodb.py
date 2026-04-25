#!/usr/bin/env python3
"""
Bootstrap the OSS PMS inside a local NocoDB instance.

Tested against NocoDB 2026.04.x (v2 API).

Run via:  make build
      or: python3 scripts/build_nocodb.py

No external dependencies — pure Python stdlib.

Passes:
  1  Wait for NocoDB ready + auth
  2  Create "OSS PMS" base inside the Default Workspace
  3  Create 7 tables (primary column inline, no post-rename needed)
  4  Add primitive columns per table
  5  Add Links columns between tables
  6  Add Lookup + Formula columns
  7  Create views (grid, kanban)
  8  Seed from seeds/*.csv, then wire link relations
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

NOCODB_URL   = os.environ.get("NOCODB_URL",       "http://localhost:8080")
ADMIN_EMAIL  = os.environ.get("NOCODB_EMAIL",     "admin@oss-pms.local")
ADMIN_PASS   = os.environ.get("NOCODB_PASSWORD",  "Admin1234!")
PROJECT_NAME = "OSS PMS"
ROOT  = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"

# ── UI types ──────────────────────────────────────────────────────────────────
UI_TEXT    = "SingleLineText"
UI_LONG    = "LongText"
UI_NUM     = "Number"
UI_SELECT  = "SingleSelect"
UI_MULTI   = "MultiSelect"
UI_DATE    = "Date"
UI_CHECK   = "Checkbox"
UI_URL     = "URL"
UI_EMAIL   = "Email"
UI_LINK    = "Links"           # modern UIType (replaces LinkToAnotherRecord)
UI_LOOKUP  = "Lookup"
UI_FORMULA = "Formula"

# colours recycled round-robin for select options
_COLOURS = [
    "#cfdffe","#fee2e2","#dcfce7","#fef9c3","#f3e8ff",
    "#ffedd5","#e0f2fe","#fce7f3","#d1fae5","#ede9fe",
]
def _colour(i: int) -> str:
    return _COLOURS[i % len(_COLOURS)]

def opts(*names: str) -> list[dict]:
    return [{"title": n, "color": _colour(i)} for i, n in enumerate(names)]


# ── HTTP helper ───────────────────────────────────────────────────────────────
def http(method: str, path: str, token: str | None = None, data=None) -> dict:
    url = f"{NOCODB_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["xc-auth"] = token
    body = json.dumps(data).encode() if data is not None else None
    req  = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}  [{e.code}]  {msg}") from None


def wait_ready(max_tries: int = 40) -> None:
    print("Waiting for NocoDB…", end="", flush=True)
    for _ in range(max_tries):
        try:
            http("GET", "/api/v1/health")
            print(" ready.")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(3)
    print()
    sys.exit("NocoDB not ready. Is 'docker compose up -d' running?")


def login() -> str:
    try:
        r = http("POST", "/api/v1/auth/user/signup",
                 data={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        print(f"  created admin  {ADMIN_EMAIL}")
        return r["token"]
    except RuntimeError as e:
        if "already" in str(e).lower() or "exist" in str(e).lower():
            r = http("POST", "/api/v1/auth/user/signin",
                     data={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
            return r["token"]
        raise


# ── Schema ────────────────────────────────────────────────────────────────────
# title_col  : the primary (row-title) column name
# columns    : additional columns [(title, uidt, extra_kwargs)]
#              For SingleSelect/MultiSelect: extra = {"colOptions": {"options": [...]}}
#              For Number/Formula/etc: extra = {...} merged into the column body

SCHEMA: dict[str, dict] = {
    "Members": {
        "title_col": "Name",
        "columns": [
            ("Role",   UI_SELECT, {"colOptions": {"options": opts("PD","DCO","UO")}}),
            ("Status", UI_SELECT, {"colOptions": {"options": opts("Active","Away")}}),
            ("Lark Handle",    UI_TEXT, {}),
            ("Slack Handle",   UI_TEXT, {}),
            ("Discord Handle", UI_TEXT, {}),
            ("GitHub Handle",  UI_TEXT, {}),
            ("Email",          UI_EMAIL, {}),
            ("Focus Areas", UI_MULTI, {"colOptions": {"options": opts(
                "Frontend","Backend","Docs","DevRel",
                "Triage","Support","Community","API")}}),
        ],
    },
    "Tasks": {
        "title_col": "Title",
        "columns": [
            ("Description", UI_LONG, {}),
            ("Type",   UI_SELECT, {"colOptions": {"options": opts(
                "Feature","Bug","Doc","DevOps","Community","Support")}}),
            ("Status", UI_SELECT, {"colOptions": {"options": opts(
                "Backlog","Planned","In Progress","Review","Blocked","Done")}}),
            ("Priority", UI_SELECT, {"colOptions": {"options": opts("P0","P1","P2","P3")}}),
            ("Estimated Effort (d)", UI_NUM, {}),
            ("Actual Effort (d)",    UI_NUM, {}),
            ("Due Date",       UI_DATE, {}),
            ("Completed Date", UI_DATE, {}),
            ("GitHub Issue #", UI_NUM, {}),
            ("GitHub URL",     UI_URL, {}),
            ("Tags", UI_MULTI, {"colOptions": {"options": opts(
                "frontend","backend","docs","good-first-issue")}}),
        ],
    },
    "Bugs": {
        "title_col": "Title",
        "columns": [
            ("Severity", UI_SELECT, {"colOptions": {"options": opts(
                "S0-Critical","S1-High","S2-Medium","S3-Low")}}),
            ("Status", UI_SELECT, {"colOptions": {"options": opts(
                "New","Triaged","In Progress","Fixed","Verified","Closed","Won't Fix")}}),
            ("Repro Steps",      UI_LONG, {}),
            ("Expected",         UI_LONG, {}),
            ("Actual",           UI_LONG, {}),
            ("Reproducibility",  UI_SELECT, {"colOptions": {"options": opts(
                "Always","Sometimes","Once")}}),
            ("Reporter (Free)",  UI_TEXT, {}),
            ("Affected Version", UI_TEXT, {}),
            ("Fixed Date",    UI_DATE, {}),
            ("Verified Date", UI_DATE, {}),
            ("Root Cause", UI_LONG, {}),
            ("Resolution", UI_LONG, {}),
            ("GitHub Issue #", UI_NUM, {}),
            ("GitHub URL",     UI_URL, {}),
        ],
    },
    "Features": {
        "title_col": "Name",
        "columns": [
            ("Problem Statement", UI_LONG, {}),
            ("Status", UI_SELECT, {"colOptions": {"options": opts(
                "Idea","Discovery","Planned","In Dev","Beta","Shipped","Dropped")}}),
            ("Reach",          UI_NUM, {}),
            ("Impact",         UI_NUM, {}),
            ("Confidence (%)", UI_NUM, {}),
            ("Effort (d)",     UI_NUM, {}),
            ("Acceptance Criteria",   UI_LONG, {}),
            ("GitHub Discussion URL", UI_URL,  {}),
        ],
    },
    "Milestones": {
        "title_col": "Milestone",
        "columns": [
            ("Goal",       UI_LONG, {}),
            ("Start Date", UI_DATE, {}),
            ("End Date",   UI_DATE, {}),
            ("Status", UI_SELECT, {"colOptions": {"options": opts(
                "Planning","Active","Released","Postponed")}}),
            ("Release Notes URL",  UI_URL, {}),
            ("GitHub Milestone #", UI_NUM, {}),
        ],
    },
    "Community Feedback": {
        "title_col": "Summary",
        "columns": [
            ("Source", UI_SELECT, {"colOptions": {"options": opts(
                "GitHub Issue","GitHub Discussion","Discord","X","Email","Survey","Other")}}),
            ("Source URL",      UI_URL,  {}),
            ("Reporter Handle", UI_TEXT, {}),
            ("Type", UI_SELECT, {"colOptions": {"options": opts(
                "Bug Report","Feature Request","Question","Praise")}}),
            ("Sentiment", UI_SELECT, {"colOptions": {"options": opts(
                "Positive","Neutral","Negative")}}),
            ("Status", UI_SELECT, {"colOptions": {"options": opts(
                "New","Triaged","Converted","Closed")}}),
            ("Closed Date", UI_DATE, {}),
        ],
    },
    "Releases": {
        "title_col": "Version",
        "columns": [
            ("Tag Date",           UI_DATE,  {}),
            ("Highlights",         UI_LONG,  {}),
            ("Breaking Changes",   UI_LONG,  {}),
            ("GitHub Release URL", UI_URL,   {}),
            ("Announcement Posted", UI_CHECK, {}),
        ],
    },
}

# (source_table, field_name, target_table, link_type)
# One entry per pair — NocoDB auto-creates the reverse.
LINKS: list[tuple[str, str, str, str]] = [
    ("Tasks",              "Assignee",         "Members",            "mm"),
    ("Tasks",              "Sprint",           "Milestones",         "mm"),
    ("Tasks",              "Linked Feature",   "Features",           "mm"),
    ("Tasks",              "Linked Bug",       "Bugs",               "mm"),
    ("Bugs",               "Assignee",         "Members",            "mm"),
    ("Bugs",               "Reporter (FB)",    "Community Feedback", "mm"),
    ("Features",           "Owner",            "Members",            "mm"),
    ("Features",           "Target Milestone", "Milestones",         "mm"),
    ("Milestones",         "Owner",            "Members",            "mm"),
    ("Community Feedback", "Triaged By",       "Members",            "mm"),
    ("Community Feedback", "Linked Feature",   "Features",           "mm"),
    ("Releases",           "Linked Milestone", "Milestones",         "mm"),
]

# (table, col_name, link_col_on_same_table, field_in_linked_table)
LOOKUPS: list[tuple[str, str, str, str]] = [
    ("Tasks",    "Owner Area", "Assignee", "Role"),
    ("Bugs",     "Owner Area", "Assignee", "Role"),
    ("Features", "Owner Area", "Owner",    "Role"),
]

FORMULA_COLS: list[tuple[str, str, str]] = [
    ("Features", "RICE Score",
     "({Reach} * {Impact} * ({Confidence (%)} / 100)) / {Effort (d)}"),
]

# (table, view_title, endpoint_suffix)
VIEWS: list[tuple[str, str, str]] = [
    ("Tasks",              "All Tasks",        "grids"),
    ("Tasks",              "Kanban by Status", "kanbans"),
    ("Bugs",               "All Bugs",         "grids"),
    ("Bugs",               "Open Bugs",        "kanbans"),
    ("Features",           "All Features",     "grids"),
    ("Features",           "Pipeline",         "kanbans"),
    ("Milestones",         "Timeline",         "grids"),
    ("Community Feedback", "Inbox",            "grids"),
    ("Community Feedback", "By Type",          "kanbans"),
    ("Releases",           "Shipped",          "grids"),
    ("Members",            "Team",             "grids"),
]

# Seed config
SEED_ORDER: list[tuple[str, str, str]] = [
    ("Members",            "members.csv",            "Name"),
    ("Milestones",         "milestones.csv",          "Milestone"),
    ("Features",           "features.csv",            "Name"),
    ("Tasks",              "tasks.csv",               "Title"),
    ("Bugs",               "bugs.csv",                "Title"),
    ("Community Feedback", "community_feedback.csv",  "Summary"),
]

# {table: {csv_col: (linked_table, linked_title_col)}}
SEED_LINKS: dict[str, dict[str, tuple[str, str]]] = {
    "Tasks":    {"Assignee":       ("Members",    "Name"),
                 "Sprint":         ("Milestones", "Milestone"),
                 "Linked Feature": ("Features",   "Name")},
    "Bugs":     {"Assignee":       ("Members",    "Name")},
    "Features": {"Owner":          ("Members",    "Name"),
                 "Target Milestone": ("Milestones", "Milestone")},
    "Milestones": {"Owner":        ("Members",    "Name")},
}

MULTI_COLS: dict[str, set[str]] = {
    "Members": {"Focus Areas"},
    "Tasks":   {"Tags"},
}


# ── Meta helpers ──────────────────────────────────────────────────────────────
def get_workspace_id(token: str) -> str:
    r = http("GET", "/api/v1/workspaces", token=token)
    return r["list"][0]["id"]


def get_or_create_base(token: str, ws: str) -> str:
    r = http("GET",  f"/api/v2/meta/workspaces/{ws}/bases", token=token)
    for b in r.get("list", []):
        if b["title"] == PROJECT_NAME:
            print(f"  ~ base  '{PROJECT_NAME}'  (exists)")
            return b["id"]
    r = http("POST", f"/api/v2/meta/workspaces/{ws}/bases",
             token=token, data={"title": PROJECT_NAME})
    print(f"  + base  '{PROJECT_NAME}'  {r['id']}")
    return r["id"]


def list_tables(token: str, base_id: str) -> dict[str, str]:
    r = http("GET", f"/api/v2/meta/bases/{base_id}/tables", token=token)
    return {t["title"]: t["id"] for t in r.get("list", [])}


def create_table(token: str, base_id: str, title: str, title_col: str) -> str:
    r = http("POST", f"/api/v2/meta/bases/{base_id}/tables", token=token, data={
        "title":      title,
        "table_name": title,
        "columns":    [{"title": title_col, "uidt": UI_TEXT, "pv": True}],
    })
    print(f"  + table  {title}")
    time.sleep(0.3)
    return r["id"]


def get_columns(token: str, tid: str) -> dict[str, dict]:
    r = http("GET", f"/api/v2/meta/tables/{tid}", token=token)
    return {c["title"]: c for c in r.get("columns", [])}


def add_column(token: str, tid: str, title: str, uidt: str,
               extra: dict | None = None) -> str:
    body: dict = {"title": title, "uidt": uidt}
    if extra:
        body.update(extra)
    r = http("POST", f"/api/v2/meta/tables/{tid}/columns", token=token, data=body)
    # Response is the whole table; find column by title
    for c in r.get("columns", []):
        if c["title"] == title:
            time.sleep(0.12)
            return c["id"]
    time.sleep(0.12)
    return ""


def get_views(token: str, tid: str) -> set[str]:
    r = http("GET", f"/api/v2/meta/tables/{tid}/views", token=token)
    return {v["title"] for v in r.get("list", [])}


def create_view(token: str, tid: str, title: str, endpoint: str) -> None:
    try:
        http("POST", f"/api/v2/meta/tables/{tid}/{endpoint}",
             token=token, data={"title": title})
        time.sleep(0.15)
    except RuntimeError as e:
        print(f"    ! view '{title}': {e}")


# ── Data helpers ──────────────────────────────────────────────────────────────
def list_records(token: str, tid: str) -> list[dict]:
    out, page = [], 1
    while True:
        r = http("GET", f"/api/v2/tables/{tid}/records?limit=500&page={page}",
                 token=token)
        out.extend(r.get("list", []))
        if r.get("pageInfo", {}).get("isLastPage", True):
            break
        page += 1
    return out


def insert_records(token: str, tid: str, rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    r = http("POST", f"/api/v2/tables/{tid}/records", token=token, data=rows)
    return r if isinstance(r, list) else [r]


def link_row(token: str, tid: str, col_id: str,
             row_id: int, target_ids: list[int]) -> None:
    body = [{"Id": i} for i in target_ids]
    http("POST",
         f"/api/v2/tables/{tid}/links/{col_id}/records/{row_id}",
         token=token, data=body)


# ── Build ─────────────────────────────────────────────────────────────────────
def build() -> None:
    wait_ready()

    print("\n── Auth ──────────────────────────────────────────────")
    token = login()

    print("\n── Base ──────────────────────────────────────────────")
    ws    = get_workspace_id(token)
    bid   = get_or_create_base(token, ws)

    # ── Pass 1: tables ────────────────────────────────────────────────────
    print("\n── Pass 1: tables ────────────────────────────────────")
    existing = list_tables(token, bid)
    tids: dict[str, str] = {}
    for tname, cfg in SCHEMA.items():
        if tname in existing:
            tids[tname] = existing[tname]
            print(f"  ~ table  {tname}")
        else:
            tids[tname] = create_table(token, bid, tname, cfg["title_col"])

    # ── Pass 2: primitive columns ─────────────────────────────────────────
    print("\n── Pass 2: primitive columns ─────────────────────────")
    col_maps: dict[str, dict[str, dict]] = {}
    for tname, cfg in SCHEMA.items():
        cm = get_columns(token, tids[tname])
        for title, uidt, extra in cfg["columns"]:
            if title in cm:
                continue
            fid = add_column(token, tids[tname], title, uidt, extra or None)
            cm[title] = {"id": fid, "title": title, "uidt": uidt}
            print(f"  + {tname}.{title}")
        col_maps[tname] = get_columns(token, tids[tname])   # refresh

    # ── Pass 3: link columns ──────────────────────────────────────────────
    print("\n── Pass 3: link columns ──────────────────────────────")
    for src, fname, tgt, ltype in LINKS:
        cm = col_maps[src]
        if fname in cm:
            continue
        try:
            add_column(token, tids[src], fname, UI_LINK, {
                "type":     ltype,
                "parentId": tids[src],
                "childId":  tids[tgt],
            })
            print(f"  + {src}.{fname} → {tgt}")
        except RuntimeError as e:
            print(f"  ! {src}.{fname}: {e}")

    # Refresh so lookup pass has link column IDs
    for tname in SCHEMA:
        col_maps[tname] = get_columns(token, tids[tname])

    # ── Pass 4: lookup + formula columns ─────────────────────────────────
    print("\n── Pass 4: lookup + formula ──────────────────────────")
    for tname, fname, link_col, target_col in LOOKUPS:
        if fname in col_maps[tname]:
            continue
        link_cid = col_maps[tname].get(link_col, {}).get("id")
        if not link_cid:
            print(f"  ! {tname}.{fname}: link col '{link_col}' missing")
            continue
        tgt_tname = next(
            (t for s, f, t, _ in LINKS if s == tname and f == link_col), None
        )
        tgt_cid = col_maps.get(tgt_tname or "", {}).get(target_col, {}).get("id")
        if not tgt_cid:
            print(f"  ! {tname}.{fname}: target col '{target_col}' missing")
            continue
        try:
            add_column(token, tids[tname], fname, UI_LOOKUP, {
                "fk_relation_column_id": link_cid,
                "fk_lookup_column_id":   tgt_cid,
            })
            print(f"  + {tname}.{fname}  (lookup → {tgt_tname}.{target_col})")
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}: {e}")

    for tname, fname, expr in FORMULA_COLS:
        if fname in col_maps[tname]:
            continue
        try:
            add_column(token, tids[tname], fname, UI_FORMULA,
                       {"formula_raw": expr})
            print(f"  + {tname}.{fname}  (formula)")
        except RuntimeError as e:
            print(f"  ! {tname}.{fname}: {e}")

    # ── Pass 5: views ─────────────────────────────────────────────────────
    print("\n── Pass 5: views ─────────────────────────────────────")
    for tname, vname, ep in VIEWS:
        existing_v = get_views(token, tids[tname])
        if vname in existing_v:
            print(f"  ~ {tname} / {vname}")
            continue
        create_view(token, tids[tname], vname, ep)
        print(f"  + {tname} / {vname}")

    # Refresh col maps for seed pass
    for tname in SCHEMA:
        col_maps[tname] = get_columns(token, tids[tname])

    # ── Pass 6: seed data ─────────────────────────────────────────────────
    print("\n── Pass 6: seed data ─────────────────────────────────")
    record_index: dict[str, dict[str, int]] = {}   # table → title → Id

    for tname, csv_name, title_col in SEED_ORDER:
        path = SEEDS / csv_name
        if not path.exists():
            print(f"  ~ {tname}: {csv_name} not found")
            continue

        tid       = tids[tname]
        link_spec = SEED_LINKS.get(tname, {})
        multi_c   = MULTI_COLS.get(tname, set())

        # Build index from rows already in NocoDB
        existing_rows = list_records(token, tid)
        record_index.setdefault(tname, {})
        existing_keys: set[str] = set()
        for r in existing_rows:
            key = str(r.get(title_col, "")).strip()
            if key:
                existing_keys.add(key)
                record_index[tname][key] = int(r["Id"])

        with path.open(newline="", encoding="utf-8") as f:
            csv_rows = list(csv.DictReader(f))

        to_insert   = []
        pending_links: list[tuple[str, dict[str, list[str]]]] = []

        for row in csv_rows:
            key = row.get(title_col, "").strip()
            if not key or key in existing_keys:
                continue
            prim: dict  = {}
            llinks: dict = {}
            for col, raw in row.items():
                raw = (raw or "").strip()
                if not raw:
                    continue
                if col in link_spec:
                    llinks[col] = [v.strip() for v in raw.split(";") if v.strip()]
                elif col in multi_c:
                    prim[col] = raw      # NocoDB accepts "a,b,c" for MultiSelect
                else:
                    prim[col] = raw
            to_insert.append(prim)
            pending_links.append((key, llinks))

        if not to_insert:
            print(f"  ~ {tname}: nothing new")
            continue

        inserted = insert_records(token, tid, to_insert)
        print(f"  + {tname}: {len(inserted)} rows")

        # Re-fetch to get stable Ids
        all_rows = list_records(token, tid)
        for r in all_rows:
            key = str(r.get(title_col, "")).strip()
            if key:
                record_index[tname][key] = int(r["Id"])

        # Wire links
        cm = col_maps[tname]
        for key, llinks in pending_links:
            src_id = record_index[tname].get(key)
            if not src_id or not llinks:
                continue
            for col, display_vals in llinks.items():
                col_meta = cm.get(col, {})
                col_id   = col_meta.get("id")
                if not col_id:
                    continue
                tgt_tname, _ = link_spec[col]
                tgt_ids = [
                    record_index.get(tgt_tname, {}).get(v)
                    for v in display_vals
                ]
                tgt_ids = [i for i in tgt_ids if i]
                if tgt_ids:
                    try:
                        link_row(token, tid, col_id, src_id, tgt_ids)
                    except RuntimeError as e:
                        print(f"    ! {tname}#{src_id}.{col}: {e}")

    print(f"""
── Done ──────────────────────────────────────────────
  Open  →  {NOCODB_URL}
  Email →  {ADMIN_EMAIL}
  Pass  →  {ADMIN_PASS}

Still manual (API doesn't support):
  • Rollup fields (Tasks Total / Done / Progress %)  → UI per docs/schema/
  • Dashboard charts / KPIs                          → docs/dashboard.md
  • Automations A1–A12                               → docs/automations.md
""")


if __name__ == "__main__":
    build()
