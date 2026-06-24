"""
run_all.py  —  ONE command to rebuild EVERY crude-inventory output.

This is the single entry point. It runs the whole pipeline in order and SAVES all
deliverables to disk:

  1. Analysis + 7 figures + inventory_analysis.json + the signal JSON  (run_inventory_analysis.py)
  2. Live engine, one-shot: surprise + verdict + market cross-check     (inventory_engine.py)
  3. The explained, executed Jupyter notebook                           (build_notebook.py)
  4. The plain-English PDF                                              (build_pdf.py)

Then it prints a checklist of exactly what was written and where.

USAGE
  python analytics/run_all.py            # one-shot: build everything from the latest EIA data
  python analytics/run_all.py --watch    # Wednesday morning: WAIT for the 10:30 a.m. ET release,
                                         #   then build everything with the fresh number
  (Windows: just double-click  run_all.bat  in the repo root.)

Outputs are saved to  deliverables/  and  server/data/  — both tracked by git
(only analytics/out and analytics/cache are git-ignored, and nothing lands there).
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent          # analytics/
ROOT = HERE.parent                              # repo root
PY = sys.executable                             # the venv python running this file


def run(label: str, script: str, args=()):
    """Run one pipeline stage as a subprocess (clean, isolated). Stop on failure."""
    print("\n" + "=" * 74)
    print(f"  STEP — {label}")
    print(f"  $ {Path(PY).name} {script} {' '.join(args)}".rstrip())
    print("=" * 74, flush=True)
    t0 = time.time()
    r = subprocess.run([PY, str(HERE / script), *args], cwd=str(HERE))
    if r.returncode != 0:
        print(f"\n[run_all] STEP FAILED: {label}  (exit {r.returncode}). Stopping.")
        sys.exit(r.returncode)
    print(f"[run_all] ...done in {time.time() - t0:.0f}s")


def main():
    watch = "--watch" in sys.argv
    mode = "LIVE (--watch: waits for the Wed 10:30 ET release)" if watch else "one-shot (latest available data)"
    engine_args = ["--watch", "--interval", "60", "--timeout", "90"] if watch else []

    print("#" * 74)
    print("#  CRUDE-INVENTORY FRAMEWORK — FULL REBUILD")
    print(f"#  mode: {mode}")
    print("#" * 74)

    run("1/4  Analysis: tables + 7 figures + signal JSON", "run_inventory_analysis.py")
    run("2/4  Live engine: surprise + verdict + market cross-check", "inventory_engine.py", engine_args)
    run("3/4  Explained notebook (built + executed)", "build_notebook.py")
    run("4/4  Plain-English PDF", "build_pdf.py")

    # ---- checklist of saved outputs -------------------------------------------
    deliv = ROOT / "deliverables"
    outputs = [
        ("PDF (read this)",        deliv / "Crude_Inventory_Framework.pdf"),
        ("Explained notebook",     deliv / "notebook" / "Crude_Inventory_Framework.ipynb"),
        ("Results JSON",           deliv / "research" / "inventory_analysis.json"),
        ("Weekly data (CSV)",      deliv / "research" / "weekly_frame.csv"),
        ("Research brief",         deliv / "research" / "research_brief.md"),
        ("Live signal (dashboard)", ROOT / "server" / "data" / "inventory_signal.json"),
        ("Cross-check track record", ROOT / "server" / "data" / "inventory_signal_log.json"),
    ]
    figs = sorted((deliv / "figures").glob("*.png"))

    print("\n" + "=" * 74)
    print("  ALL OUTPUTS SAVED")
    print("=" * 74)
    for label, p in outputs:
        mark = "OK" if p.exists() else "--"
        size = f"{p.stat().st_size / 1024:.0f} KB" if p.exists() else "MISSING"
        print(f"   [{mark}] {label:26} {p.relative_to(ROOT).as_posix():46} {size}")
    print(f"   [OK] {'Figures':26} deliverables/figures/  ({len(figs)} PNGs)")
    print("=" * 74)
    print("\nOpen  deliverables/Crude_Inventory_Framework.pdf  to read the result.")
    print("To see it live on the dashboard, (re)start the server:  npm run server")


if __name__ == "__main__":
    main()
