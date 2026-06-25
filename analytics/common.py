"""
Shared helpers for the Phase 2 analytics batch layer.

Paths, unit conversions, dotenv parsing and the small Yahoo / EIA fetch clients
the panel builder and downstream steps reuse. Kept dependency-light (pandas,
numpy, requests) so `build_panel.py` runs even before the heavier ML libs land.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

# ---- Paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent          # repo root
ANALYTICS = ROOT / "analytics"
OUT_DIR = ANALYTICS / "out"                            # intermediate artifacts (panel)
CACHE_DIR = ANALYTICS / "cache"                        # raw EIA/Yahoo response cache
DATA_DIR = ROOT / "server" / "data"                    # where Node loads JSON from
HISTORY_JSON = DATA_DIR / "history.json"
ENV_FILE = ROOT / "server" / ".env"

for d in (OUT_DIR, CACHE_DIR, CACHE_DIR / "eia", CACHE_DIR / "yahoo"):
    d.mkdir(parents=True, exist_ok=True)

# ---- Unit conversions to $/bbl (mirrors server/compute/markets.js) ---------
GAL_PER_BBL = 42.0           # Heating Oil / RBOB: $/gal -> $/bbl  (x42)
BBL_PER_MT_GASOIL = 7.45     # Gas Oil: $/mt -> $/bbl  (/7.45)


def to_bbl(series_unit: str, vals):
    """Convert a price (pandas Series or scalar) in its native unit to $/bbl."""
    if series_unit == "$/gal":
        return vals * GAL_PER_BBL
    if series_unit == "$/mt":
        return vals / BBL_PER_MT_GASOIL
    return vals  # already $/bbl


# ---- dotenv (no extra dependency) ------------------------------------------
def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    # Fall back to real environment variables when there is no server/.env file —
    # e.g. on Hugging Face Spaces, where EIA_API_KEY is injected as a Space secret
    # (the same value the Node server reads from process.env). The file wins locally.
    for k in ("EIA_API_KEY", "PORT"):
        if not env.get(k) and os.environ.get(k):
            env[k] = os.environ[k].strip()
    return env


# ---- Yahoo chart client (mirrors server/sources/yahoo.js) ------------------
_YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Voltaire analytics batch)"}


def yahoo_daily(symbol: str, rng: str = "5y", cache_hours: float = 6.0):
    """Daily closes for `symbol` as {iso: close}. Cached to disk; returns {} on failure."""
    cache = CACHE_DIR / "yahoo" / f"{symbol.replace('=', '_').replace('^', '_')}_{rng}.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < cache_hours * 3600:
        return json.loads(cache.read_text())
    url = f"{_YAHOO_BASE}/{symbol}?range={rng}&interval=1d&includePrePost=false"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        ts = result.get("timestamp", []) or []
        closes = result["indicators"]["quote"][0].get("close", []) or []
        out = {}
        for t, c in zip(ts, closes):
            if c is None:
                continue
            iso = time.strftime("%Y-%m-%d", time.gmtime(t))
            out[iso] = round(float(c), 4)
        if out:
            cache.write_text(json.dumps(out))
        return out
    except Exception as e:  # noqa: BLE001 — batch step degrades gracefully
        print(f"  [yahoo] {symbol} failed ({e}); column will be NaN")
        return {}


def yahoo_intraday(symbol: str, interval: str = "5m", rng: str = "60d", cache_hours: float = 1.0):
    """Intraday bars for `symbol` as list[(epoch_seconds:int, close:float)] oldest→newest.
    Used to measure the live release-day reaction PATH (5-min closes). Yahoo limits the
    fine intervals to ~60 days, which always covers the latest weekly EIA release.
    Returns [] on failure."""
    cache = CACHE_DIR / "yahoo" / f"{symbol.replace('=', '_').replace('^', '_')}_{interval}_{rng}.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < cache_hours * 3600:
        return [tuple(x) for x in json.loads(cache.read_text())]
    url = (f"{_YAHOO_BASE}/{symbol}?range={rng}&interval={interval}"
           f"&includePrePost=false")
    try:
        r = requests.get(url, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        ts = result.get("timestamp", []) or []
        closes = result["indicators"]["quote"][0].get("close", []) or []
        out = [(int(t), round(float(c), 4)) for t, c in zip(ts, closes) if c is not None]
        if out:
            cache.write_text(json.dumps(out))
        return out
    except Exception as e:  # noqa: BLE001
        print(f"  [yahoo] intraday {symbol} failed ({e}); reaction path will be empty")
        return []


# ---- EIA v2 series client (mirrors server/sources/eia.js) ------------------
_EIA_BASE = "https://api.eia.gov/v2/seriesid"


def eia_series(series_id: str, key: str, length: int = 300, cache_hours: float = 12.0):
    """Fetch an EIA legacy series id -> list[(period, value)] oldest→newest. {} via [] on failure."""
    cache = CACHE_DIR / "eia" / f"{series_id}_{length}.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < cache_hours * 3600:
        return [tuple(x) for x in json.loads(cache.read_text())]
    if not key:
        print(f"  [eia] no API key; {series_id} will be NaN")
        return []
    url = (
        f"{_EIA_BASE}/{series_id}?api_key={key}"
        f"&sort[0][column]=period&sort[0][direction]=desc&length={length}"
    )
    try:
        r = requests.get(url, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        rows = r.json()["response"]["data"]
        out = [(d["period"], float(d["value"])) for d in rows if d.get("value") is not None]
        out.reverse()  # chronological
        if out:
            cache.write_text(json.dumps(out))
        return out
    except Exception as e:  # noqa: BLE001
        print(f"  [eia] {series_id} failed ({e}); column will be NaN")
        return []
