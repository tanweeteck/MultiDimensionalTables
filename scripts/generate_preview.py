#!/usr/bin/env python3
"""
Generate preview.html from seeds/*.csv + the schema defined in build_nocodb.py.
No running NocoDB required — works in CI.

Output: preview.html in the project root.
"""

from __future__ import annotations
import csv, html, sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[1]
SEEDS  = ROOT / "seeds"
OUTPUT = ROOT / "preview.html"

# ── Schema (mirrors build_nocodb.py) ─────────────────────────────────────────
TABLES = [
    {
        "name": "Members",
        "title_col": "Name",
        "csv": "members.csv",
        "select": {"Role": ["PD","DCO","UO"], "Status": ["Active","Away"]},
        "multi":  {"Focus Areas": True},
        "links":  [],
        "lookups": [],
        "formulas": [],
    },
    {
        "name": "Tasks",
        "title_col": "Title",
        "csv": "tasks.csv",
        "select": {
            "Type":     ["Feature","Bug","Doc","DevOps","Community","Support"],
            "Status":   ["Backlog","Planned","In Progress","Review","Blocked","Done"],
            "Priority": ["P0","P1","P2","P3"],
        },
        "multi": {"Tags": True},
        "links":   ["Assignee → Members", "Sprint → Milestones",
                    "Linked Feature → Features", "Linked Bug → Bugs"],
        "lookups": ["Owner Area (via Assignee → Members.Role)"],
        "formulas": [],
    },
    {
        "name": "Bugs",
        "title_col": "Title",
        "csv": "bugs.csv",
        "select": {
            "Severity":       ["S0-Critical","S1-High","S2-Medium","S3-Low"],
            "Status":         ["New","Triaged","In Progress","Fixed","Verified","Closed","Won't Fix"],
            "Reproducibility":["Always","Sometimes","Once"],
        },
        "multi": {},
        "links":   ["Assignee → Members", "Reporter (FB) → Community Feedback",
                    "Linked Task (auto) → Tasks"],
        "lookups": ["Owner Area (via Assignee → Members.Role)"],
        "formulas": [],
    },
    {
        "name": "Features",
        "title_col": "Name",
        "csv": "features.csv",
        "select": {
            "Status": ["Idea","Discovery","Planned","In Dev","Beta","Shipped","Dropped"],
        },
        "multi": {},
        "links":   ["Owner → Members", "Target Milestone → Milestones",
                    "Linked Tasks (auto) → Tasks"],
        "lookups": ["Owner Area (via Owner → Members.Role)"],
        "formulas": ["RICE Score = Reach × Impact × (Confidence% / 100) / Effort"],
    },
    {
        "name": "Milestones",
        "title_col": "Milestone",
        "csv": "milestones.csv",
        "select": {"Status": ["Planning","Active","Released","Postponed"]},
        "multi": {},
        "links":   ["Owner → Members", "Linked Tasks (auto) → Tasks",
                    "Linked Features (auto) → Features"],
        "lookups": [],
        "formulas": [],
    },
    {
        "name": "Community Feedback",
        "title_col": "Summary",
        "csv": "community_feedback.csv",
        "select": {
            "Source":    ["GitHub Issue","GitHub Discussion","Discord","X","Email","Survey","Other"],
            "Type":      ["Bug Report","Feature Request","Question","Praise"],
            "Sentiment": ["Positive","Neutral","Negative"],
            "Status":    ["New","Triaged","Converted","Closed"],
        },
        "multi": {},
        "links":   ["Triaged By → Members", "Linked Feature → Features",
                    "Linked Bugs (auto) → Bugs"],
        "lookups": [],
        "formulas": [],
    },
    {
        "name": "Releases",
        "title_col": "Version",
        "csv": "releases.csv",
        "select": {},
        "multi": {},
        "links":   ["Linked Milestone → Milestones"],
        "lookups": [],
        "formulas": [],
    },
]

STATUS_COLOURS = {
    "Backlog":"#e2e8f0","Planned":"#bfdbfe","In Progress":"#bbf7d0",
    "Review":"#fef9c3","Blocked":"#fecaca","Done":"#dcfce7",
    "New":"#e0e7ff","Triaged":"#bfdbfe","Fixed":"#bbf7d0",
    "Verified":"#dcfce7","Closed":"#e2e8f0","Won't Fix":"#fecaca",
    "Idea":"#f3e8ff","Discovery":"#e0e7ff","In Dev":"#bbf7d0",
    "Beta":"#fef9c3","Shipped":"#dcfce7","Dropped":"#fecaca",
    "Planning":"#e0e7ff","Active":"#bbf7d0","Released":"#dcfce7","Postponed":"#fecaca",
    "Active":"#bbf7d0","Away":"#fecaca",
    "P0":"#fecaca","P1":"#fed7aa","P2":"#fef9c3","P3":"#dcfce7",
    "S0-Critical":"#fecaca","S1-High":"#fed7aa","S2-Medium":"#fef9c3","S3-Low":"#dcfce7",
    "Positive":"#dcfce7","Neutral":"#f1f5f9","Negative":"#fecaca",
    "Converted":"#dcfce7",
}

def badge(text: str) -> str:
    colour = STATUS_COLOURS.get(text, "#f1f5f9")
    return f'<span class="status-badge" style="background:{colour}">{html.escape(text)}</span>'


def render_cell(col: str, val: str, tdef: dict) -> str:
    if not val or not val.strip():
        return '<span class="empty">—</span>'
    if col in tdef.get("multi", {}):
        parts = [v.strip() for v in val.split(",") if v.strip()]
        return " ".join(f'<span class="tag">{html.escape(p)}</span>' for p in parts)
    if col in tdef.get("select", {}):
        return badge(val.strip())
    if val.strip().lower() in ("true","yes","1"):
        return "✅"
    if val.strip().lower() in ("false","no","0"):
        return "—"
    return html.escape(str(val))


def generate() -> str:
    total_rows  = 0
    total_links = sum(len(t["links"]) for t in TABLES)

    table_blocks = []
    for tdef in TABLES:
        path = SEEDS / tdef["csv"]
        rows: list[dict] = []
        cols: list[str]  = []
        if path.exists():
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                cols   = list(reader.fieldnames or [])
                rows   = list(reader)
        total_rows += len(rows)

        # Build meta badges
        meta_html = ""
        for lnk in tdef["links"]:
            meta_html += f'<span class="mbadge link">⟶ {html.escape(lnk)}</span>'
        for lkp in tdef["lookups"]:
            meta_html += f'<span class="mbadge lookup">⊕ {html.escape(lkp)}</span>'
        for frm in tdef["formulas"]:
            meta_html += f'<span class="mbadge formula">ƒ {html.escape(frm)}</span>'

        # Table rows
        skip_cols = {c for c in cols if "handle" in c.lower() and c != tdef["title_col"]}
        vis_cols  = [c for c in cols if c not in skip_cols][:8]  # cap at 8 for readability

        rows_html = ""
        if rows:
            header = "".join(f"<th>{html.escape(c)}</th>" for c in vis_cols)
            body   = ""
            for r in rows:
                cells = "".join(
                    f"<td>{render_cell(c, r.get(c,''), tdef)}</td>"
                    for c in vis_cols
                )
                body += f"<tr>{cells}</tr>"
            rows_html = f"""
            <div class="tbl-wrap">
              <table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>
            </div>"""
        else:
            rows_html = '<p class="empty" style="padding:.5rem 0">No seed data yet.</p>'

        table_blocks.append(f"""
    <section class="card">
      <div class="card-head">
        <span class="card-title">{html.escape(tdef['name'])}</span>
        <span class="row-count">{len(rows)} row{'s' if len(rows)!=1 else ''}</span>
      </div>
      {'<div class="meta-row">'+meta_html+'</div>' if meta_html else ''}
      {rows_html}
    </section>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OSS PMS – Preview</title>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,-apple-system,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh}}

    /* ── Header ── */
    .hero{{background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#a855f7 100%);
           color:#fff;padding:2.5rem 2rem 2rem}}
    .hero h1{{font-size:1.9rem;font-weight:800;letter-spacing:-.03em}}
    .hero p{{margin-top:.4rem;opacity:.85;font-size:.95rem;max-width:580px}}
    .hero-sub{{margin-top:1.2rem;font-size:.8rem;opacity:.7;
               background:rgba(255,255,255,.15);display:inline-block;
               padding:.3rem .75rem;border-radius:99px}}

    /* ── Stats bar ── */
    .stats{{display:flex;gap:.75rem;padding:1.25rem 2rem;flex-wrap:wrap;
            background:#fff;border-bottom:1px solid #e2e8f0}}
    .stat{{text-align:center;padding:.5rem 1rem}}
    .stat .n{{font-size:1.6rem;font-weight:800;color:#6366f1;line-height:1}}
    .stat .l{{font-size:.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-top:.2rem}}

    /* ── Cards ── */
    .grid{{padding:1.5rem 2rem;display:grid;gap:1.25rem}}
    .card{{background:#fff;border:1px solid #e2e8f0;border-radius:.875rem;
           overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
    .card-head{{display:flex;align-items:center;justify-content:space-between;
                padding:.85rem 1.1rem;border-bottom:1px solid #f1f5f9;background:#fafbff}}
    .card-title{{font-weight:700;font-size:1rem;color:#1e293b}}
    .row-count{{font-size:.75rem;color:#94a3b8;background:#f1f5f9;
                padding:.2rem .6rem;border-radius:99px}}
    .meta-row{{display:flex;flex-wrap:wrap;gap:.35rem;padding:.6rem 1.1rem;
               background:#fafafa;border-bottom:1px solid #f1f5f9}}
    .mbadge{{font-size:.7rem;font-weight:600;padding:.25rem .6rem;
             border-radius:99px;white-space:nowrap}}
    .mbadge.link{{background:#dbeafe;color:#1d4ed8}}
    .mbadge.lookup{{background:#fce7f3;color:#9d174d}}
    .mbadge.formula{{background:#fef9c3;color:#854d0e}}

    /* ── Table ── */
    .tbl-wrap{{overflow-x:auto}}
    table{{width:100%;border-collapse:collapse;font-size:.82rem}}
    th{{text-align:left;padding:.55rem .9rem;font-size:.7rem;font-weight:600;
        text-transform:uppercase;letter-spacing:.06em;color:#64748b;
        background:#f8fafc;border-bottom:1px solid #e2e8f0;white-space:nowrap}}
    td{{padding:.55rem .9rem;border-top:1px solid #f1f5f9;
        max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
        vertical-align:middle}}
    tr:hover td{{background:#f8faff}}
    .status-badge{{display:inline-block;padding:.2rem .55rem;border-radius:99px;
                   font-size:.72rem;font-weight:600}}
    .tag{{display:inline-block;padding:.15rem .45rem;border-radius:4px;
          font-size:.7rem;background:#f1f5f9;color:#475569;margin:.1rem}}
    .empty{{color:#cbd5e1;font-size:.82rem}}

    /* ── Footer ── */
    footer{{text-align:center;padding:2rem;font-size:.8rem;color:#94a3b8;
            border-top:1px solid #e2e8f0;margin-top:1rem}}
    a{{color:#6366f1;text-decoration:none}}
    a:hover{{text-decoration:underline}}

    @media(max-width:600px){{
      .hero h1{{font-size:1.4rem}}
      .stats{{gap:.4rem;padding:.75rem 1rem}}
      .grid{{padding:1rem}}
    }}
  </style>
</head>
<body>

<div class="hero">
  <h1>OSS PMS</h1>
  <p>Open-source project management system built on NocoDB — 7 linked tables covering the full contributor lifecycle.</p>
  <span class="hero-sub">Static preview · run <code>make build</code> locally for the live interactive UI</span>
</div>

<div class="stats">
  <div class="stat"><div class="n">{len(TABLES)}</div><div class="l">Tables</div></div>
  <div class="stat"><div class="n">{total_rows}</div><div class="l">Seed rows</div></div>
  <div class="stat"><div class="n">{total_links}</div><div class="l">Link fields</div></div>
  <div class="stat"><div class="n">3</div><div class="l">Lookups</div></div>
  <div class="stat"><div class="n">1</div><div class="l">Formula</div></div>
  <div class="stat"><div class="n">11</div><div class="l">Views</div></div>
</div>

<div class="grid">
  {''.join(table_blocks)}
</div>

<footer>
  Generated from <a href="https://github.com/tanweeteck/MultiDimensionalTables">tanweeteck/MultiDimensionalTables</a> ·
  Run <code>make build</code> for the full interactive NocoDB UI
</footer>

</body>
</html>"""


if __name__ == "__main__":
    out = generate()
    OUTPUT.write_text(out, encoding="utf-8")
    print(f"Written {len(out):,} bytes → {OUTPUT}")
