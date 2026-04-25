#!/usr/bin/env python3
"""
Seed the OSS PMS base from the CSVs in seeds/.

Imports rows for: Members, Milestones, Features, Tasks, Bugs.
Resolves linked-record fields by display value (e.g. "Alice Chen" →
the Members record id).

Required env vars:
  LARK_APP_ID, LARK_APP_SECRET, LARK_BITABLE_APP_TOKEN
Optional:
  LARK_REGION  - "intl" (default) or "cn"

Run AFTER build_base.py — depends on the schema being in place.
Re-running is idempotent: rows whose primary text already exists are skipped.
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

REGION = os.environ.get("LARK_REGION", "intl")
BASE_URL = (
    "https://open.larksuite.com/open-apis"
    if REGION == "intl"
    else "https://open.feishu.cn/open-apis"
)

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"

# Order matters: link targets must exist before linkers.
SEED_ORDER = [
    ("Members", "members.csv", "Name"),
    ("Milestones", "milestones.csv", "Milestone"),
    ("Features", "features.csv", "Name"),
    ("Tasks", "tasks.csv", "Title"),
    ("Bugs", "bugs.csv", "Title"),
]

# CSV column → (Bitable field name, link target table, target dedup column)
# A truthy "link target table" means the cell value should be resolved to a
# record_id in that table.
LINK_COLUMNS = {
    "Tasks": {
        "Assignee": ("Members", "Name"),
        "Sprint": ("Milestones", "Milestone"),
        "Linked Feature": ("Features", "Name"),
        "Linked Bug": ("Bugs", "Title"),
    },
    "Bugs": {
        "Assignee": ("Members", "Name"),
    },
    "Features": {
        "Owner": ("Members", "Name"),
        "Target Milestone": ("Milestones", "Milestone"),
    },
    "Milestones": {
        "Owner": ("Members", "Name"),
    },
}

MULTI_SELECT_COLUMNS = {
    "Members": {"Focus Areas"},
    "Tasks": {"Tags"},
}


# --- HTTP --------------------------------------------------------------------
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
    return r["tenant_access_token"]


# --- Bitable helpers ---------------------------------------------------------
def list_tables(token, app):
    r = http("GET", f"/bitable/v1/apps/{app}/tables?page_size=100", token=token)
    return {t["name"]: t["table_id"] for t in r["data"]["items"]}


def list_records(token, app, table_id):
    out, page = [], None
    while True:
        path = f"/bitable/v1/apps/{app}/tables/{table_id}/records?page_size=500"
        if page:
            path += f"&page_token={page}"
        r = http("GET", path, token=token)
        out.extend(r["data"].get("items", []))
        page = r["data"].get("page_token")
        if not page:
            break
    return out


def create_record(token, app, table_id, fields):
    r = http("POST", f"/bitable/v1/apps/{app}/tables/{table_id}/records",
             token=token, data={"fields": fields})
    return r["data"]["record"]["record_id"]


# --- Coercion ----------------------------------------------------------------
def coerce_cell(value: str, table: str, column: str, link_index: dict):
    """Convert a CSV cell to whatever Bitable's record API wants."""
    if value == "":
        return None

    # Linked record → list of record IDs
    link_spec = LINK_COLUMNS.get(table, {}).get(column)
    if link_spec:
        target_table, dedup_col = link_spec
        rid = link_index.get(target_table, {}).get(value)
        return [rid] if rid else None

    # Multi-select → list of strings
    if column in MULTI_SELECT_COLUMNS.get(table, set()):
        return [v.strip() for v in value.split(",") if v.strip()]

    # Numeric-looking columns
    lower = column.lower()
    if any(k in lower for k in ("number", "issue #", "milestone #",
                                  "(d)", "reach", "impact", "confidence",
                                  "effort")):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value

    return value


def seed():
    app = os.environ["LARK_BITABLE_APP_TOKEN"]
    token = auth()
    tables = list_tables(token, app)
    missing = [t for t, _, _ in SEED_ORDER if t not in tables]
    if missing:
        sys.exit(f"Missing tables in base: {missing}.  Run build_base.py first.")

    # link_index[Table][display_value] = record_id  – built incrementally
    link_index: dict[str, dict[str, str]] = {}

    for table, csv_name, dedup_col in SEED_ORDER:
        table_id = tables[table]
        path = SEEDS / csv_name
        if not path.exists():
            print(f"  ~ {table}: no seed file at {path}, skipping")
            continue

        existing = list_records(token, app, table_id)
        existing_keys = {
            (r.get("fields", {}).get(dedup_col) or "").strip()
            for r in existing
        }
        # Build link_index entry from existing rows so cross-CSV links work
        link_index.setdefault(table, {})
        for r in existing:
            key = (r.get("fields", {}).get(dedup_col) or "").strip()
            if key:
                link_index[table][key] = r["record_id"]

        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        added = 0
        for row in rows:
            key = row.get(dedup_col, "").strip()
            if not key or key in existing_keys:
                continue
            fields = {}
            for col, raw in row.items():
                v = coerce_cell(raw, table, col, link_index)
                if v is not None:
                    fields[col] = v
            try:
                rid = create_record(token, app, table_id, fields)
                link_index[table][key] = rid
                existing_keys.add(key)
                added += 1
                time.sleep(0.1)
            except RuntimeError as e:
                print(f"  ! {table}: row '{key}' FAILED: {e}")

        print(f"  + {table}: +{added} rows  (existing {len(existing)})")

    print("\nSeed complete.")


if __name__ == "__main__":
    missing = [k for k in ("LARK_APP_ID", "LARK_APP_SECRET", "LARK_BITABLE_APP_TOKEN")
               if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}")
    seed()
