"""
make_reports.py — build the explanatory PDF reports from their markdown sources.

The repo's strategy/project explainers live as markdown (the maintainable source of
truth); this script renders each to a matching PDF so the written and PDF versions
never drift. Pure-Python toolchain (markdown -> HTML -> PDF via xhtml2pdf), no system
dependencies.

  Run:  .venv\\Scripts\\python make_reports.py            # build all
        .venv\\Scripts\\python make_reports.py STRATEGY     # build one (substring match)
"""
from __future__ import annotations

import sys
from pathlib import Path

import markdown as md
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parent

# (markdown source, output pdf) — relative to repo root.
REPORTS = [
    ("docs/PROJECT_REPORT.md", "PROJECT_REPORT.pdf"),
    ("docs/FINAL_BACKTESTING_REPORT.md", "FINAL_BACKTESTING_REPORT.pdf"),
    ("docs/Voltaire_Terminal_Project_Submission.md", "Voltaire_Terminal_Project_Submission.pdf"),
    ("docs/STRATEGY.md", "Backtesting/STRATEGY.pdf"),
]

CSS = """
@page { size: A4; margin: 1.8cm 1.7cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5px; color: #1a1a1a; line-height: 1.45; }
h1 { font-size: 21px; color: #0b3d5c; margin: 0 0 2px 0; padding-bottom: 4px; border-bottom: 2px solid #0b3d5c; }
h2 { font-size: 15px; color: #0b3d5c; margin: 16px 0 4px 0; padding-top: 4px; border-top: 1px solid #d0d7de; }
h3 { font-size: 12.5px; color: #16527a; margin: 11px 0 3px 0; }
h4 { font-size: 11px; color: #333; margin: 9px 0 2px 0; }
p  { margin: 4px 0; }
ul, ol { margin: 4px 0 4px 0; padding-left: 18px; }
li { margin: 1.5px 0; }
strong { color: #0b3d5c; }
em { color: #444; }
code { font-family: "Courier New", monospace; font-size: 9.5px; background: #f3f5f7; color: #b1004e; padding: 0 2px; }
pre { background: #f3f5f7; border: 1px solid #e1e4e8; padding: 7px 9px; font-family: "Courier New", monospace;
      font-size: 9px; color: #24292e; margin: 6px 0; }
pre code { background: transparent; color: #24292e; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 7px 0; font-size: 9.5px; }
th { background: #0b3d5c; color: #ffffff; text-align: left; padding: 4px 7px; border: 1px solid #0b3d5c; }
td { padding: 4px 7px; border: 1px solid #cdd5dd; }
tr:nth-child(even) td { background: #f6f8fa; }
blockquote { margin: 6px 0; padding: 5px 11px; border-left: 3px solid #2a9d8f; background: #f1f8f6; color: #234; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 12px 0; }
a { color: #16527a; text-decoration: none; }
"""

EXTS = ["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"]


def build(src: Path, out: Path) -> bool:
    html_body = md.markdown(src.read_text(encoding="utf8"), extensions=EXTS)
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html_body}</body></html>"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        res = pisa.CreatePDF(html, dest=f, encoding="utf-8")
    return not res.err


def main():
    only = sys.argv[1:]
    for src_rel, out_rel in REPORTS:
        if only and not any(o.lower() in src_rel.lower() or o.lower() in out_rel.lower() for o in only):
            continue
        src, out = ROOT / src_rel, ROOT / out_rel
        if not src.exists():
            print(f"  [skip] {src_rel} (source not found)")
            continue
        ok = build(src, out)
        kb = round(out.stat().st_size / 1024) if out.exists() else 0
        print(f"  [{'ok' if ok else 'ERR'}] {src_rel}  ->  {out_rel}  ({kb} KB)")


if __name__ == "__main__":
    main()
