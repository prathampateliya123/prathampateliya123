#!/usr/bin/env python3
"""
Generate dynamic ASCII-style GitHub profile card SVGs.

Fetches live stats from the GitHub API and produces dark_mode.svg
and light_mode.svg in the repository root.

Usage:
  Local:    python scripts/generate_card.py
  Actions:  triggered by .github/workflows/profile-card.yml
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_esc


# ╔══════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION — edit these to match your profile           ║
# ╚══════════════════════════════════════════════════════════════╝
USERNAME  = "prathampateliya123"
LOCATION  = "india"
COMPANY   = "abox agency"
LANGUAGES = "JavaScript, HTML"
WEBSITE   = "https://prratham-dev.vercel.app/"
# ───────────────────────────────────────────────────────────────

COL = 62          # character‑width of the card content area

THEMES = {
    "dark": dict(
        bg="#0d1117",   border="#30363d",
        heading="#58a6ff", rule="#3d444d",
        label="#ffa657",   dots="#484f58",
        value="#c9d1d9",   number="#79c0ff",
    ),
    "light": dict(
        bg="#ffffff",   border="#d0d7de",
        heading="#0969da", rule="#d0d7de",
        label="#953800",   dots="#8c959f",
        value="#24292f",   number="#0550ae",
    ),
}


# ── GitHub API ───────────────────────────────────────────────────

def _get(url):
    """Fetch JSON from the GitHub REST API."""
    hdrs = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        hdrs["Authorization"] = f"Bearer {tok}"
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as exc:
        print(f"⚠  {url} → {exc}", file=sys.stderr)
        return None


def fetch_stats():
    """Return a dict with uptime, repos, stars, commits, followers."""
    user = _get(f"https://api.github.com/users/{USERNAME}")
    if not user:
        sys.exit("❌ Cannot reach GitHub API")

    # ── uptime ──
    born = datetime.strptime(
        user["created_at"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc)
    d = (datetime.now(timezone.utc) - born).days
    y, d = divmod(d, 365)
    m, d = divmod(d, 30)
    parts = []
    if y:
        parts.append(f"{y} year{'s' * (y != 1)}")
    if m:
        parts.append(f"{m} month{'s' * (m != 1)}")
    parts.append(f"{d} day{'s' * (d != 1)}")
    uptime = ", ".join(parts)

    repos_n   = user.get("public_repos", 0)
    followers = user.get("followers", 0)

    # ── total stars ──
    stars, pg = 0, 1
    while True:
        rs = _get(
            f"https://api.github.com/users/{USERNAME}"
            f"/repos?per_page=100&page={pg}"
        )
        if not rs:
            break
        stars += sum(r.get("stargazers_count", 0) for r in rs)
        if len(rs) < 100:
            break
        pg += 1

    # ── total commits (search API) ──
    c = _get(
        f"https://api.github.com/search/commits"
        f"?q=author:{USERNAME}&per_page=1"
    )
    commits = c.get("total_count", 0) if c else 0

    return dict(
        uptime=uptime, repos=repos_n, stars=stars,
        commits=commits, followers=followers,
    )


# ── SVG builder ──────────────────────────────────────────────────

def _dots(n):
    return "." * max(1, n)


def _section(title):
    """Spans for a ── Section Header ──────── line."""
    bar = "─" * (COL - len(title) - 2)
    return [("rule", "─"), ("heading", f" {title} "), ("rule", bar)]


def _kv(label, value, vcol="value"):
    """Spans for a `. Label: ...... value` line."""
    l = f". {label}: "
    v = f" {value}"
    return [("label", l), ("dots", _dots(COL - len(l) - len(v))), (vcol, v)]


def _stat_row(l1, v1, l2, v2):
    """Spans for a two‑column stat line with a | divider."""
    half = (COL - 5) // 2                # 5 chars for "  |  "
    la, va = f". {l1}: ", f" {v1}"
    lb, vb = f". {l2}: ", f" {v2}"
    return [
        ("label", la), ("dots", _dots(half - len(la) - len(va))), ("number", va),
        ("rule", "  |  "),
        ("label", lb), ("dots", _dots(half - len(lb) - len(vb))), ("number", vb),
    ]


def build_svg(theme, stats):
    """Return the complete SVG string for the given theme."""
    t   = THEMES[theme]
    FNT = "'Consolas','Menlo','DejaVu Sans Mono',monospace"
    FS  = 15          # font‑size (px)
    LH  = 24          # line‑height (px)
    PX  = 40          # horizontal padding
    PY  = 48          # vertical padding

    # Collect rows: (spans, vertical_gap_multiplier)
    rows = []
    def add(spans, gap=1.0):
        rows.append((spans, gap))

    add(_section(f"{USERNAME}@github"))
    add(_kv("Uptime",    stats["uptime"]))
    add(_kv("Location",  LOCATION))
    add(_kv("Company",   COMPANY))
    add(_kv("Languages", LANGUAGES), gap=1.5)

    add(_section("Contact"))
    add(_kv("Website", WEBSITE))
    add(_kv("GitHub",  f"github.com/{USERNAME}"), gap=1.5)

    add(_section("GitHub Stats"))
    add(_stat_row("Repos",   stats["repos"],   "Stars",     stats["stars"]))
    add(_stat_row("Commits", stats["commits"], "Followers", stats["followers"]))

    # Position every row
    y = PY
    positioned = []
    for spans, gap in rows:
        positioned.append((y, spans))
        y += int(LH * gap)

    W = PX * 2 + int(COL * FS * 0.601)
    H = y + PY - LH + 8

    # ── assemble SVG ──
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"',
        f'  viewBox="0 0 {W} {H}" role="img"',
        f'  aria-label="GitHub profile card for {xml_esc(USERNAME)}">',
        f'  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}"',
        f'    rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>',
    ]

    for row_y, spans in positioned:
        tspans = "".join(
            f'<tspan fill="{t[role]}">{xml_esc(str(txt))}</tspan>'
            for role, txt in spans
        )
        out.append(
            f'  <text x="{PX}" y="{row_y}"'
            f' font-family="{FNT}" xml:space="preserve"'
            f' font-size="{FS}">{tspans}</text>'
        )

    out.append("</svg>")
    return "\n".join(out)


# ── main ─────────────────────────────────────────────────────────

def main():
    # Write SVGs to the repo root (one level up from scripts/)
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))

    print("🔄 Fetching GitHub stats …")
    stats = fetch_stats()
    print(f"📊 {json.dumps(stats, indent=2)}")

    for theme in ("dark", "light"):
        svg  = build_svg(theme, stats)
        path = os.path.join(root, f"{theme}_mode.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"✅ Generated {path}")


if __name__ == "__main__":
    main()
