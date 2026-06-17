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
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
  color: #1a1d24; line-height: 1.62; font-size: 11.2pt; max-width: 100%;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 25pt; color: #0b1f3a; margin: 0 0 4px; line-height: 1.15; letter-spacing: -0.4px; }
h1 + h3 { color: #c2410c; font-weight: 600; font-size: 13pt; margin: 0 0 8px; }
h1 { border-bottom: 3px solid #d97706; padding-bottom: 10px; }
h2 { font-size: 18pt; color: #0b1f3a; margin: 30px 0 8px; padding-top: 8px;
     border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; page-break-after: avoid; }
h3 { font-size: 13.5pt; color: #1e3a5f; margin: 20px 0 6px; page-break-after: avoid; }
p { margin: 8px 0; }
strong { color: #0b1f3a; }
em { color: #475569; }
a { color: #1d4ed8; text-decoration: none; }
ul, ol { margin: 8px 0 8px 4px; padding-left: 22px; }
li { margin: 4px 0; }
hr { border: none; border-top: 1px solid #cbd5e1; margin: 26px 0; }
code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 9.6pt;
       color: #b91c1c; font-family: "Consolas", "Courier New", monospace; }
blockquote {
  margin: 12px 0; padding: 10px 16px; background: #fff8ed;
  border-left: 4px solid #d97706; color: #3f3320; border-radius: 0 4px 4px 0;
}
blockquote p { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 10pt;
        page-break-inside: avoid; }
th { background: #0b1f3a; color: #fff; text-align: left; padding: 7px 10px; font-weight: 600; }
td { padding: 6px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
h2 { page-break-before: auto; }
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
