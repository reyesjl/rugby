# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Export video summaries from the `videos` table to a standalone HTML page.

Usage:
    python ops/export_summaries_html.py              # writes summaries.html (default)
    python ops/export_summaries_html.py --out report.html --limit 100

Environment Variables (same as rest of project):
    DB_USER / DB_PASS / DB_NAME / DB_HOST / DB_PORT

Design goals:
    * Zero extra dependencies (uses psycopg already in project deps)
    * Graceful fallback if DB unavailable (prints warning, exits 1)
    * Compact, readable table with expandable full summary text
    * Small inline JS/CSS (no external network calls)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import os
import sys
from typing import Any

import psycopg
from dotenv import load_dotenv

load_dotenv()


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export video summaries to HTML")
    p.add_argument("--out", default="summaries.html", help="Output HTML file path")
    p.add_argument(
        "--limit", type=int, default=500, help="Max rows to export (default 500)"
    )
    p.add_argument(
        "--order",
        choices=["id", "path"],
        default="id",
        help="Ordering column (default: id desc)",
    )
    p.add_argument(
        "--asc", action="store_true", help="Use ascending order (default desc)"
    )
    p.add_argument(
        "--no-embedding", action="store_true", help="Skip embedding length column"
    )
    return p.parse_args(argv)


def _connect() -> Any:
    if psycopg is None:  # pragma: no cover - only when dependency missing
        raise SystemExit("psycopg not installed – cannot export")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "postgres")
    DB_NAME = os.getenv("DB_NAME", "videos_db")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    try:
        return psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            options="-c client_min_messages=WARNING -c application_name=export_summaries",
        )
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(
            f"DB connect failed for user '{DB_USER}' host '{DB_HOST}:{DB_PORT}' db '{DB_NAME}': {e}"
        ) from e


def fetch_rows(limit: int, order: str, asc: bool) -> list[tuple[Any, ...]]:
    with _connect() as conn, conn.cursor() as cur:
        direction = "ASC" if asc else "DESC"
        if order == "id":
            cur.execute(
                f"SELECT id, path, summary, embedding FROM videos ORDER BY id {direction} LIMIT %s",
                (limit,),
            )
        else:
            cur.execute(
                f"SELECT id, path, summary, embedding FROM videos ORDER BY path {direction} LIMIT %s",
                (limit,),
            )
        return list(cur.fetchall())


def build_html(rows: list[tuple[Any, ...]], show_embedding: bool) -> str:
    generated = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    head = """
<!DOCTYPE html>
<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\" />\n<title>Video Summaries</title>\n<style>
body { font-family: system-ui, Arial, sans-serif; margin: 1.2rem; background:#f8f9fb; }
h1 { margin-top:0; }
table { border-collapse: collapse; width:100%; font-size: 14px; }
th, td { border:1px solid #d0d7de; padding:6px 8px; vertical-align: top; }
th { background:#eef1f4; text-align:left; position: sticky; top:0; }
tr:nth-child(even) { background:#fcfcfe; }
.path { font-family: monospace; max-width:400px; word-break:break-all; }
.summary-short { cursor:pointer; color:#0366d6; }
.summary-full { display:none; white-space: pre-wrap; background:#fff; border:1px solid #d0d7de; padding:8px; margin-top:4px; }
.meta { font-size:12px; color:#555; }
footer { margin-top:2rem; font-size:12px; color:#666; }
button.copy { float:right; font-size:11px; }
</style>\n<script>
function toggle(id){const full=document.getElementById('full-'+id);if(!full)return;full.style.display= full.style.display==='none'?'block':'none';}
function copyText(id){const full=document.getElementById('full-'+id); if(!full)return; navigator.clipboard.writeText(full.innerText);}
</script>\n</head>\n<body>
"""
    parts = [
        head,
        f"<h1>Video Summaries</h1><div class='meta'>Generated {generated} • Rows: {len(rows)}</div>",
    ]
    parts.append(
        "<table><thead><tr><th>ID</th><th>Path</th><th>Summary (click to expand)</th>"
    )
    if show_embedding:
        parts.append("<th>Embed Dim</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        vid, path, summary, embedding = row
        short = (summary[:160] + "…") if len(summary) > 160 else summary
        esc_short = html.escape(short)
        esc_full = html.escape(summary)
        embed_dim = len(embedding) if show_embedding and embedding is not None else ""  # type: ignore[arg-type]
        parts.append("<tr>")
        parts.append(f"<td>{vid}</td>")
        parts.append(f"<td class='path'>{html.escape(path)}</td>")
        parts.append(
            f"<td><div class='summary-short' onclick=\"toggle('{vid}')\">{esc_short}</div>"
            f"<div class='summary-full' id='full-{vid}'><button class='copy' onclick=\"copyText('{vid}')\">Copy</button>{esc_full}</div></td>"
        )
        if show_embedding:
            parts.append(f"<td style='text-align:right'>{embed_dim}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    parts.append(
        "<footer>Minimal export • Reload script to refresh • Click summary to toggle full text.</footer>"
    )
    parts.append("</body></html>")
    return "".join(parts)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        rows = fetch_rows(limit=max(1, args.limit), order=args.order, asc=args.asc)
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Failed to fetch rows: {e}", file=sys.stderr)
        return 1
    html_doc = build_html(rows, show_embedding=not args.no_embedding)
    try:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html_doc)
    except OSError as e:
        print(f"[ERROR] Could not write {args.out}: {e}", file=sys.stderr)
        return 1
    print(f"Wrote {args.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
