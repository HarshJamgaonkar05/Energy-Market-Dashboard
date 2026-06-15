"""
Render PROJECT_REPORT.md into a clean, professional PDF.

Markdown -> styled HTML -> PDF (printed via Microsoft Edge / Chrome headless,
which is on every Windows machine, so no extra PDF engine is needed).

Run:  analytics/.venv/Scripts/python make_report_pdf.py
Out:  PROJECT_REPORT.pdf  (+ PROJECT_REPORT.html)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
MD = ROOT / "PROJECT_REPORT.md"
HTML = ROOT / "PROJECT_REPORT.html"
PDF = ROOT / "PROJECT_REPORT.pdf"

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, system-ui, sans-serif;
  font-size: 10.6pt; line-height: 1.55; color: #1c2430; max-width: 100%;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1, h2, h3, h4 { font-weight: 700; color: #0f1722; line-height: 1.25; }
/* Major parts start on a fresh page (but not the very first/title). */
h1 { font-size: 19pt; margin: 0 0 .5em; padding-bottom: .25em;
     border-bottom: 3px solid #e8881a; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 14pt; margin: 1.4em 0 .5em; color: #b8650a;
     border-bottom: 1px solid #e6e1d8; padding-bottom: .2em; }
h3 { font-size: 11.6pt; margin: 1.1em 0 .35em; color: #243; }
p { margin: .55em 0; }
strong { color: #0f1722; }
em { color: #475; }
a { color: #b8650a; text-decoration: none; }
ul, ol { margin: .5em 0 .7em; padding-left: 1.4em; }
li { margin: .28em 0; }
code { background: #f3f0ea; border: 1px solid #e6e1d8; border-radius: 3px;
       padding: 0 .3em; font-family: "Consolas", "SFMono-Regular", monospace;
       font-size: .9em; color: #9a4a06; }
blockquote { margin: .9em 0; padding: .5em .95em; background: #fbf6ee;
             border-left: 4px solid #e8881a; color: #3a3327; border-radius: 0 4px 4px 0; }
blockquote p { margin: .3em 0; }
table { border-collapse: collapse; width: 100%; margin: .9em 0; font-size: 9.8pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #ddd6ca; padding: 5px 9px; text-align: left;
         vertical-align: top; }
th { background: #f3ede2; color: #5a4527; font-weight: 700;
     text-transform: uppercase; font-size: 8.4pt; letter-spacing: .04em; }
tr:nth-child(even) td { background: #faf8f4; }
hr { border: none; border-top: 1px solid #e6e1d8; margin: 1.6em 0; }
h2, h3, table, blockquote, li { page-break-inside: avoid; }
/* Title block */
h1:first-of-type + p em { color: #6b7280; font-size: 11pt; }
"""


def build_html() -> str:
    body = markdown.markdown(
        MD.read_text(encoding="utf8"),
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Energy Market Project — Report</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def find_browser() -> str | None:
    # Chrome first — its classic --headless prints PDFs reliably. Edge's newer
    # --headless=new silently fails for --print-to-pdf on many versions.
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return shutil.which("chrome") or shutil.which("msedge")


def main():
    HTML.write_text(build_html(), encoding="utf8")
    print(f"  wrote {HTML.name}")
    browser = find_browser()
    if not browser:
        print("  [error] no Edge/Chrome found — open PROJECT_REPORT.html and Print > Save as PDF.")
        sys.exit(1)
    # Render to a temp file first (classic --headless writes reliably to %TEMP%,
    # whereas writing straight into the OneDrive-synced folder can be flaky), then
    # copy the finished PDF into place.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_pdf = Path(tmp) / "report.pdf"
        cmd = [
            browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--user-data-dir={Path(tmp) / 'prof'}", "--no-first-run",
            f"--print-to-pdf={tmp_pdf}", HTML.as_uri(),
        ]
        subprocess.run(cmd, timeout=120)
        if not tmp_pdf.exists() or tmp_pdf.stat().st_size == 0:
            cmd[1] = "--headless=new"            # fallback for Chrome builds that need it
            subprocess.run(cmd, timeout=120)
        if tmp_pdf.exists() and tmp_pdf.stat().st_size > 0:
            shutil.copyfile(tmp_pdf, PDF)

    if PDF.exists() and PDF.stat().st_size > 0:
        print(f"  -> {PDF.name}  ({PDF.stat().st_size // 1024} KB)  via {Path(browser).name}")
    else:
        print("  [error] PDF not produced — open PROJECT_REPORT.html and Print > Save as PDF.")
        sys.exit(1)


if __name__ == "__main__":
    main()
