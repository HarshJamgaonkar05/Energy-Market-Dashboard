"""
build_summary_pdf.py — render the one-page internship summary to PDF.

Reads INTERNSHIP_SUMMARY.md at the repo root and renders it with the same
markdown + xhtml2pdf toolchain and house CSS the other deliverable PDFs use, so
the look matches Crude_Inventory_Framework.pdf / Phase4_Release_Lab_Explained.pdf.

Run:  .venv/Scripts/python analytics/build_summary_pdf.py
Output: deliverables/Internship_Summary.pdf
"""
from __future__ import annotations

from pathlib import Path

import markdown
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "deliverables" / "summary_onepager.md"
OUT = ROOT / "deliverables" / "Internship_Summary.pdf"


def build() -> None:
    md = SRC.read_text(encoding="utf-8")
    # Normalise glyphs base-14 Helvetica (WinAnsi) cannot render.
    md = (md.replace("σ", " s.d.").replace("→", "->").replace("×", "x")
            .replace("≈", "~").replace("≥", ">=").replace("≤", "<=")
            .replace("’", "'").replace("‑", "-"))

    html_body = markdown.markdown(
        md, extensions=["tables", "fenced_code", "sane_lists"]
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><style>
      @page {{ size: A4; margin: 1.7cm 1.8cm; }}
      body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10.5px; line-height: 1.55; color: #1f2937; text-align: justify; }}
      h1 {{ font-size: 20px; color: #0f172a; margin: 0 0 3px 0; text-align: left; }}
      h1 + p {{ font-size: 11px; color: #475569; margin: 0 0 10px 0; text-align: left; }}
      h2 {{ font-size: 13.5px; color: #1e3a8a; margin: 16px 0 6px 0; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; text-align: left; }}
      h3 {{ font-size: 11px; color: #1e3a8a; margin: 10px 0 4px 0; text-align: left; }}
      p {{ margin: 8px 0; }}
      hr {{ border: none; border-top: 1px solid #cbd5e1; margin: 10px 0; }}
      table {{ width: 100%; border-collapse: collapse; margin: 7px 0; font-size: 9px; }}
      th {{ background: #1e293b; color: #fff; text-align: left; padding: 4px 6px; }}
      td {{ border: 1px solid #e2e8f0; padding: 4px 6px; vertical-align: top; }}
      tr:nth-child(even) td {{ background: #f8fafc; }}
      blockquote {{ background: #eff6ff; border-left: 3px solid #2563eb; margin: 7px 0; padding: 5px 9px; }}
      code, pre {{ font-family: Courier, monospace; font-size: 9px; }}
      strong {{ color: #0f172a; }}
      ol, ul {{ margin: 5px 0 5px 0; }}
      li {{ margin: 3px 0; }}
    </style></head><body>
      {html_body}
    </body></html>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "wb") as fh:
        result = pisa.CreatePDF(html, dest=fh)
    if result.err:
        print(f"  PDF had {result.err} error(s)")
    else:
        print(f"  -> {OUT}  ({round(OUT.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    build()
