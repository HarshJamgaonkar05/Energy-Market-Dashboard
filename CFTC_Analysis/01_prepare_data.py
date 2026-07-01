"""
01_prepare_data.py
------------------
Build the merged weekly dataset for the CFTC-positioning vs WTI-price study.

DATA-SOURCE NOTE
  The file Data/CFTC 2016-2026 CL.xlsx (instrument CFTC-D_F_CL_OR_NET_1W) is,
  despite the assignment naming it "Managed Money", actually the CFTC
  **Other Reportables** net series (verified value-for-value against the official
  CFTC report, e.g. 2026-06-16 Excel=28,255 = Other-Reportables; Managed-Money
  net was 96,228). "OR" in the code = Other Reportables (MM would be "MM").

  The assignment asks about **Managed Money**, so we pull BOTH categories
  directly from the official CFTC Socrata API (free, no key) for WTI
  (contract code 067651). Managed Money is PRIMARY; Other Reportables (= the
  supplied file) is kept for comparison only.

Price
  Daily Cushing WTI spot ($/bbl) from EIA series RWTC, 2015-12 -> present.

Methodology
  * COT positions are AS-OF Tuesday close but PUBLISHED the following Friday
    (~15:30 ET). To avoid look-ahead, forward returns are entered at the Friday
    release (asof + 3 days), not the Tuesday as-of date.
  * Prices are taken "as-of" (last daily close on/before a calendar date).
  * Forward N-week return = P(entry + 7N days) / P(entry) - 1, NaN past history end.

Output
  data/weekly_merged.csv
"""
import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DATA_DIR.mkdir(exist_ok=True)
EIA_KEY = "bOOVT8gjpNpwO78C4u9xshoNFy8XIiFihVq7QnRd"
CFTC_CODE = "067651"  # NYMEX WTI-PHYSICAL (stable across CFTC market-name renames)


def _get(url: str):
    safe = urllib.parse.quote(url, safe=':/?=&$,">=')
    with urllib.request.urlopen(safe, timeout=60) as r:
        return json.load(r)


def fetch_wti_spot() -> pd.Series:
    cache = DATA_DIR / "wti_spot_daily.csv"
    if cache.exists():
        s = pd.read_csv(cache, parse_dates=["date"]).set_index("date")["price"]
        return s.sort_index()
    url = (
        "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        f"?api_key={EIA_KEY}&frequency=daily&data[0]=value"
        "&facets[series][]=RWTC&start=2015-12-01"
        "&sort[0][column]=period&sort[0][direction]=asc&offset=0&length=5000"
    )
    d = _get(url)
    df = pd.DataFrame(d["response"]["data"])[["period", "value"]]
    df.columns = ["date", "price"]
    df["date"] = pd.to_datetime(df["date"])
    df["price"] = pd.to_numeric(df["price"])
    df = df.dropna().sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df.set_index("date")["price"]


def fetch_cftc() -> pd.DataFrame:
    """Official CFTC Disaggregated Futures-only COT for WTI: MM and OR net."""
    cache = DATA_DIR / "cftc_wti_official.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["asof"])
    sel = ",".join([
        "report_date_as_yyyy_mm_dd",
        "m_money_positions_long_all", "m_money_positions_short_all",
        "other_rept_positions_long", "other_rept_positions_short",
        "open_interest_all",
    ])
    base = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
    url = (f'{base}?cftc_contract_market_code={CFTC_CODE}&$select={sel}'
           '&$where=report_date_as_yyyy_mm_dd>="2015-12-01T00:00:00"'
           '&$order=report_date_as_yyyy_mm_dd ASC&$limit=2000')
    rows = _get(url)
    df = pd.DataFrame(rows)
    for c in df.columns:
        if c != "report_date_as_yyyy_mm_dd":
            df[c] = pd.to_numeric(df[c])
    df["asof"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"].str.slice(0, 10))
    df["mm_net"] = df["m_money_positions_long_all"] - df["m_money_positions_short_all"]
    df["or_net"] = df["other_rept_positions_long"] - df["other_rept_positions_short"]
    df["oi"] = df["open_interest_all"]
    df = df[["asof", "mm_net", "or_net", "oi"]].sort_values("asof").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def asof_price(price: pd.Series, target, allow_future=True):
    if not allow_future and target > price.index.max():
        return np.nan
    sub = price.loc[:target]
    return float(sub.iloc[-1]) if len(sub) else np.nan


def add_signal_cols(df, col, prefix):
    df[f"{prefix}_chg"] = df[col].diff()
    df[f"{prefix}_z_full"] = (df[col] - df[col].mean()) / df[col].std(ddof=0)
    roll = df[col].rolling(52, min_periods=26)
    df[f"{prefix}_z_roll52"] = (df[col] - roll.mean()) / roll.std(ddof=0)
    df[f"{prefix}_pct_rank"] = df[col].rank(pct=True)
    return df


def main():
    price = fetch_wti_spot()
    cf = fetch_cftc()
    cf = cf[cf["asof"] >= "2016-01-01"].reset_index(drop=True)  # "2016 onwards"

    # release = Friday following the Tuesday as-of (CFTC publishes T+3)
    cf["release"] = cf["asof"] + pd.Timedelta(days=3)

    cf["price_asof"] = cf["asof"].apply(lambda d: asof_price(price, d))
    cf["price_entry"] = cf["release"].apply(lambda d: asof_price(price, d))
    for n in (1, 2, 4):
        fut = cf["release"] + pd.Timedelta(days=7 * n)
        p_fut = fut.apply(lambda d: asof_price(price, d, allow_future=False))
        cf[f"fwd_{n}w"] = p_fut / cf["price_entry"] - 1.0

    cf = add_signal_cols(cf, "mm_net", "mm")
    cf = add_signal_cols(cf, "or_net", "or")

    out = DATA_DIR / "weekly_merged.csv"
    cf.to_csv(out, index=False)
    print(f"wrote {out}  rows={len(cf)}")
    print(f"span: {cf['asof'].min().date()} -> {cf['asof'].max().date()}")
    print("MM net: mean {:,.0f}  range [{:,.0f}, {:,.0f}]".format(
        cf['mm_net'].mean(), cf['mm_net'].min(), cf['mm_net'].max()))
    print("OR net: mean {:,.0f}  range [{:,.0f}, {:,.0f}]".format(
        cf['or_net'].mean(), cf['or_net'].min(), cf['or_net'].max()))
    print(cf[["asof", "mm_net", "or_net", "price_asof", "fwd_1w", "fwd_4w"]].tail(3).to_string())
    print("fwd NaNs:", cf[["fwd_1w", "fwd_2w", "fwd_4w"]].isna().sum().to_dict())


if __name__ == "__main__":
    main()
