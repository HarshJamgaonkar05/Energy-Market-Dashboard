# ============================================================================
# Build a styled PDF from a markdown file.
# ----------------------------------------------------------------------------
# Renders the markdown to styled, print-ready HTML and prints it to PDF with
# headless Chrome. Chrome writes to a temp folder first and we copy the result
# into place, because writing a binary straight into a OneDrive-synced folder can
# race with the sync client.
#
# Usage:
#   python make_report_pdf.py                       # builds PROJECT_REPORT.pdf (default)
#   python make_report_pdf.py Backtesting/STRATEGY.md  # builds Backtesting/STRATEGY.pdf
#   python make_report_pdf.py a.md b.md ...         # builds each alongside its .md
# ============================================================================
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
DEFAULT_MD = HERE / "PROJECT_REPORT.md"

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = """
@page { size: A4; margin: 20mm 18mm 22mm; }
:root {
  --ink: #14181f; --muted: #5b6675; --navy: #0b2545; --navy2: #1e3a5f;
  --accent: #c2680c; --accent-soft: #fcf6ee; --line: #e7ebf0; --line2: #d7dee6;
  --code-bg: #f4f6f9; --code-ink: #b03636;
}
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
  color: var(--ink); line-height: 1.65; font-size: 11pt; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  text-rendering: optimizeLegibility;
}

/* ---- Title block (cover-style first heading) ---- */
h1 {
  font-size: 27pt; color: var(--navy); margin: 0 0 2px; line-height: 1.12;
  letter-spacing: -0.5px; font-weight: 700; padding-bottom: 14px;
  border-bottom: 3px solid var(--accent);
}
h1 + h3 {
  color: var(--accent); font-weight: 600; font-size: 13.5pt;
  margin: 14px 0 4px; letter-spacing: 0.1px; border: none; padding: 0;
}
h1 + h3::before { content: none; }

/* ---- Section headings ---- */
h2 {
  font-size: 17pt; color: var(--navy); margin: 32px 0 10px; padding: 0 0 7px 14px;
  position: relative; border-bottom: 1px solid var(--line);
  page-break-after: avoid; line-height: 1.25; font-weight: 700;
}
h2::before {
  content: ""; position: absolute; left: 0; top: 2px; bottom: 9px; width: 5px;
  border-radius: 3px; background: var(--accent);
}
h3 {
  font-size: 12.8pt; color: var(--navy2); margin: 22px 0 6px; font-weight: 650;
  page-break-after: avoid; line-height: 1.3;
}

p { margin: 9px 0; }
strong { color: var(--navy); font-weight: 650; }
em { color: var(--muted); }
a { color: #1d4ed8; text-decoration: none; border-bottom: 1px solid #c7d6f7; }

/* ---- Lists ---- */
ul, ol { margin: 9px 0 9px 2px; padding-left: 24px; }
li { margin: 5px 0; padding-left: 3px; }
li::marker { color: var(--accent); font-weight: 600; }

/* ---- Rules / dividers ---- */
hr { border: none; border-top: 1px solid var(--line2); margin: 30px 0; }

/* ---- Inline + block code ---- */
code {
  background: var(--code-bg); padding: 1.5px 6px; border-radius: 4px; font-size: 9.4pt;
  color: var(--code-ink); font-family: "Consolas", "SF Mono", "Courier New", monospace;
  border: 1px solid var(--line);
}
pre {
  background: #0f1b2d; color: #e6edf6; padding: 13px 16px; border-radius: 8px;
  overflow-x: auto; margin: 14px 0; font-size: 9.2pt; line-height: 1.55;
  page-break-inside: avoid; box-shadow: inset 0 0 0 1px rgba(255,255,255,.04);
}
pre code { background: none; border: none; color: inherit; padding: 0; font-size: inherit; }

/* ---- Callout / quote cards ---- */
blockquote {
  margin: 14px 0; padding: 11px 16px 11px 16px; background: var(--accent-soft);
  border: 1px solid #f0e2cf; border-left: 4px solid var(--accent);
  color: #43361f; border-radius: 6px; page-break-inside: avoid;
}
blockquote p { margin: 5px 0; }
blockquote strong { color: #7a4a12; }

/* ---- Tables ---- */
table {
  border-collapse: separate; border-spacing: 0; width: 100%; margin: 16px 0;
  font-size: 9.8pt; page-break-inside: avoid;
  border: 1px solid var(--line2); border-radius: 8px; overflow: hidden;
}
thead th {
  background: var(--navy); color: #fff; text-align: left; padding: 9px 12px;
  font-weight: 600; font-size: 9.6pt; letter-spacing: 0.2px; border: none;
}
td { padding: 8px 12px; border-top: 1px solid var(--line); vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f9fc; }
tbody tr:first-child td { border-top: none; }
td:first-child, th:first-child { padding-left: 14px; }

/* ---- Spacing polish ---- */
h2 { page-break-before: auto; }
p + ul, p + ol { margin-top: 2px; }
"""

HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>{css}</style></head><body>{body}</body></html>"""


def build(md_path: Path):
    md_path = md_path if md_path.is_absolute() else (HERE / md_path)
    if not md_path.exists():
        sys.exit(f"missing {md_path}")
    pdf_path = md_path.with_suffix(".pdf")
    body = markdown.markdown(
        md_path.read_text(encoding="utf8"),
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )

    tmp = Path(tempfile.mkdtemp())
    html_path = tmp / "report.html"
    pdf_tmp = tmp / "report.pdf"
    html_path.write_text(HTML.format(css=CSS, body=body), encoding="utf8")

    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_tmp}", html_path.as_uri(),
    ], check=True, timeout=120)

    if not pdf_tmp.exists() or pdf_tmp.stat().st_size == 0:
        sys.exit("Chrome produced no PDF")
    shutil.copy(pdf_tmp, pdf_path)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK -> {pdf_path}  ({pdf_path.stat().st_size/1024:.0f} KB)")


def main():
    if not Path(CHROME).exists():
        sys.exit(f"Chrome not found at {CHROME}")
    targets = [Path(a) for a in sys.argv[1:]] or [DEFAULT_MD]
    for md in targets:
        build(md)


if __name__ == "__main__":
    main()
