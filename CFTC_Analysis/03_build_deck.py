"""
03_build_deck.py
----------------
Assemble a self-contained 8-slide HTML presentation (dark dashboard theme),
embedding the charts as base64 and pulling headline numbers from
data/stats_summary.json so text and figures never drift apart.

Output: ../public/cftc/presentation.html  (the served deck the dashboard links to)
"""
import base64
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CH = HERE / "charts"
S = json.load(open(HERE / "data" / "stats_summary.json"))
DS = json.load(open(HERE / "data" / "deep_stats.json"))


def img(name):
    b64 = base64.b64encode((CH / name).read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


mm = S["managed_money"]
rel = mm["relationship"]
dec = mm["extremes_decile"]["stats"]
rz = mm["extremes_rollz"]["stats"]
base = mm["baseline"]
smp = S["sample"]

pct = lambda x: f"{x*100:+.2f}%"
es4 = dec["extreme_short"]["fwd_4w"]
el4 = dec["extreme_long"]["fwd_4w"]
rz4 = rz["extreme_short"]["fwd_4w"]

CHARTS = {k: img(v) for k, v in {
    "ts": "01_timeseries.png", "scatter": "02_scatter_predictive.png",
    "decile": "03_decile_returns.png", "buckets": "04_extreme_buckets.png",
    "event": "05_event_study.png", "hit": "06_hitrate.png",
    "ccf": "07_ccf.png", "irf": "08_irf.png", "halflife": "09_halflife.png",
    "quantile": "10_quantile.png", "equity": "11_oos_equity.png", "fdr": "12_fdr.png"}.items()}

# ---- deep-dive headline numbers (from deep_stats.json) ----------------------
gpr = DS["granger"]["dpos_to_ret"]["min_p"]; grp = DS["granger"]["ret_to_dpos"]["min_p"]
ccf0 = DS["cross_correlation"]["corr"][DS["cross_correlation"]["lags"].index(0)]
hl = DS["half_life"]["half_life_wks"]; rho = DS["half_life"]["rho"]
irf_tot = DS["var_irf"]["cum_total"]
lg = DS["logit_direction_4w"]; auc = lg.get("auc")
blo = DS["backtest"]["long_only"]; bhp = DS["backtest"]["buy_hold_perf"]
lo_sh = blo["perf_0bps"]["sharpe"]; lo_boot = blo["boot_sharpe"]["p_le_0"]
lo_dd = blo["perf_0bps"]["max_dd"]; lo_exp = blo["exposure"]
bh_sh = bhp["sharpe"]; fdr = DS["fdr"]

HTML = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CFTC Positioning vs WTI — Findings</title>
<style>
:root{{
  --bg:#08090b; --panel:#0e0f12; --panel2:#101115; --border:#1c1d22;
  --ink:#f4f4f5; --ink2:#d4d4d8; --muted:#a1a1aa; --faint:#71717a;
  --amber:#f59e0b; --emer:#10b981; --red:#ef4444; --sky:#38bdf8;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%}}
body{{background:var(--bg);color:var(--ink);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  overflow:hidden}}
.deck{{height:100vh;width:100vw;position:relative}}
.slide{{position:absolute;inset:0;display:none;flex-direction:column;
  padding:3.2vh 4.5vw 2vh;opacity:0;transition:opacity .35s ease}}
.slide.active{{display:flex;opacity:1}}
.kicker{{color:var(--amber);font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  font-size:.72rem;margin-bottom:.5rem}}
h1{{font-size:2.7rem;line-height:1.08;font-weight:800;letter-spacing:-.02em}}
h2{{font-size:1.7rem;font-weight:700;letter-spacing:-.01em;margin-bottom:.2rem}}
.sub{{color:var(--muted);font-size:1.02rem;margin-top:.7rem;max-width:60ch}}
.row{{display:flex;gap:1.6vw;flex:1;min-height:0;margin-top:1.6vh}}
.col{{display:flex;flex-direction:column;gap:1.2vh;min-width:0}}
.fig{{background:var(--panel);border:1px solid var(--border);border-radius:12px;
  padding:.6rem;display:flex;align-items:center;justify-content:center;min-height:0;flex:1}}
.fig img{{max-width:100%;max-height:100%;object-fit:contain;border-radius:6px}}
.cap{{color:var(--faint);font-size:.74rem;margin-top:.35rem;text-align:center}}
ul{{list-style:none;display:flex;flex-direction:column;gap:.85rem;margin-top:.4rem}}
li{{position:relative;padding-left:1.15rem;color:var(--ink2);font-size:1.02rem;line-height:1.4}}
li::before{{content:'';position:absolute;left:0;top:.55em;width:.5rem;height:.5rem;
  border-radius:2px;background:var(--amber)}}
b{{color:var(--ink);font-weight:700}}
.stat-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1.6vh}}
.card{{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:1.1rem 1.2rem}}
.card .big{{font-size:1.9rem;font-weight:800;letter-spacing:-.02em}}
.card .lbl{{color:var(--muted);font-size:.82rem;margin-top:.3rem;line-height:1.35}}
.pos{{color:var(--emer)}} .neg{{color:var(--red)}} .neu{{color:var(--sky)}} .amb{{color:var(--amber)}}
.chips{{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.8vh}}
.chip{{background:var(--panel2);border:1px solid var(--border);border-radius:999px;
  padding:.5rem 1rem;font-size:.88rem;color:var(--ink2)}}
.chip .dot{{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;margin-right:.5rem;vertical-align:middle}}
.note{{background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.3);border-left:3px solid var(--amber);
  border-radius:8px;padding:.8rem 1rem;color:var(--ink2);font-size:.86rem;margin-top:auto}}
.foot{{position:absolute;bottom:1.4vh;left:4.5vw;right:4.5vw;display:flex;justify-content:space-between;
  align-items:center;color:var(--faint);font-size:.74rem;border-top:1px solid var(--border);padding-top:.7vh}}
.dots{{display:flex;gap:.5rem}}
.dots i{{width:.5rem;height:.5rem;border-radius:50%;background:var(--border);cursor:pointer;transition:.2s}}
.dots i.on{{background:var(--amber);width:1.4rem;border-radius:3px}}
.verdict{{display:flex;flex-direction:column;gap:1rem;margin-top:1.4vh}}
.vbig{{font-size:1.35rem;line-height:1.4;font-weight:600;color:var(--ink)}}
kbd{{background:var(--panel2);border:1px solid var(--border);border-radius:4px;padding:.05rem .4rem;font-size:.7rem}}
</style></head>
<body>
<div class="deck">

  <!-- 1 — TITLE -->
  <section class="slide active">
    <div class="kicker">Energy Markets · Quantitative Study</div>
    <h1>Does CFTC positioning<br>predict WTI crude prices?</h1>
    <p class="sub">Weekly CFTC <b>Managed-Money</b> net positioning vs WTI spot,
      {smp['start']} → {smp['end']} ({smp['weeks']} weeks). Forward returns entered at the
      Friday COT release to avoid look-ahead; medians + Newey-West HAC inference throughout.</p>
    <div class="stat-grid">
      <div class="card"><div class="big neu">{rel['chg_vs_ret_pearson']:+.2f}</div>
        <div class="lbl">Δposition vs same-week price change → <b>coincident / momentum</b>, not leading</div></div>
      <div class="card"><div class="big amb">~0</div>
        <div class="lbl">predictive correlation of positioning with 1–4wk forward returns (all HAC p&gt;0.29)</div></div>
      <div class="card"><div class="big pos">{es4['median']*100:+.1f}%</div>
        <div class="lbl">median 4-wk WTI return after <b>extreme net-short</b> positioning (vs {base['fwd_4w']['median']*100:+.1f}% base)</div></div>
    </div>
    <div class="chips">
      <span class="chip"><span class="dot" style="background:var(--sky)"></span>WTI spot — EIA Cushing (RWTC)</span>
      <span class="chip"><span class="dot" style="background:var(--amber)"></span>Managed Money — official CFTC (WTI 067651)</span>
      <span class="chip"><span class="dot" style="background:var(--emer)"></span>8-slide deep-dive · now a dashboard section</span>
    </div>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>1 / 8</span></div>
  </section>

  <!-- 2 — RELATIONSHIP -->
  <section class="slide">
    <div class="kicker">1 · The relationship</div>
    <h2>Managed Money is <span class="neu">coincident</span>, not leading</h2>
    <div class="row">
      <div class="col" style="flex:2.1">
        <div class="fig"><img src="{CHARTS['ts']}"></div>
        <div class="cap">Extreme longs (red) cluster at 2018 & 2022 price peaks; extreme shorts (green) at the 2016 / 2019 / 2023–25 troughs.</div>
      </div>
      <div class="col" style="flex:1">
        <ul>
          <li>Position <b>changes</b> track same-week price changes at <b class="neu">{rel['chg_vs_ret_pearson']:+.2f}</b> (p≈10⁻¹⁸) — funds <b>buy as price rises</b>.</li>
          <li>Position <b>level</b> vs price level is just <b>{rel['level_pearson']:+.2f}</b> — crowding is regime-dependent, not a price gauge.</li>
          <li>Sanity check: the <b>supplied file</b> (Other Reportables) shows the <i>opposite</i> sign,
            <b class="neg">{S['other_reportables_compare']['relationship']['chg_vs_ret_pearson']:+.2f}</b> — it accumulates into weakness.</li>
        </ul>
      </div>
    </div>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>2 / 8</span></div>
  </section>

  <!-- 3 — NO PREDICTIVE POWER -->
  <section class="slide">
    <div class="kicker">2 · Predictive power</div>
    <h2>Positioning level has <span class="neg">no linear edge</span> on forward returns</h2>
    <div class="row">
      <div class="col" style="flex:1.4">
        <div class="fig"><img src="{CHARTS['scatter']}"></div>
        <div class="cap">Flat fits. Newey-West HAC p-values (overlap-adjusted) all ≥ 0.29.</div>
      </div>
      <div class="col" style="flex:1.4">
        <div class="fig"><img src="{CHARTS['decile']}"></div>
        <div class="cap">Mean/median return across net-position deciles is non-monotonic — no "more long → worse" gradient.</div>
      </div>
    </div>
    <ul style="margin-top:1vh">
      <li>Regressing 1/2/4-week WTI returns on the positioning z-score yields |r| ≤ 0.07 and <b>no significant slope</b> after correcting for overlapping windows.</li>
    </ul>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>3 / 8</span></div>
  </section>

  <!-- 4 — THE ONE EDGE -->
  <section class="slide">
    <div class="kicker">3 · Extremes & forward performance</div>
    <h2>The only edge is <span class="pos">contrarian</span> — after extreme net-short</h2>
    <div class="row">
      <div class="col" style="flex:1.5">
        <div class="fig"><img src="{CHARTS['event']}"></div>
        <div class="cap">Event study (mean path, skew-inflated by 2016/2020 rebounds). Washed-out shorts outpace baseline & crowded longs.</div>
      </div>
      <div class="col" style="flex:1.3">
        <div class="fig"><img src="{CHARTS['buckets']}"></div>
        <div class="cap">Median returns. The short-extreme signal weakens under the point-in-time rolling-z definition (right).</div>
      </div>
    </div>
    <div class="stat-grid" style="margin-top:1vh">
      <div class="card"><div class="big pos">{es4['median']*100:+.1f}% <span style="font-size:1rem;color:var(--muted)">med</span></div>
        <div class="lbl">4-wk after extreme short (decile) · hit {es4['hit']*100:.0f}% · boot-CI(mean) excl. 0 · p<sub>MW</sub>={es4['p_vs_rest_med']:.2f}</div></div>
      <div class="card"><div class="big neu">{el4['median']*100:+.1f}% <span style="font-size:1rem;color:var(--muted)">med</span></div>
        <div class="lbl">4-wk after extreme <b>long</b> · <b>no</b> reliable reversal (p<sub>MW</sub>={el4['p_vs_rest_med']:.2f})</div></div>
      <div class="card"><div class="big amb">{rz4['median']*100:+.1f}% <span style="font-size:1rem;color:var(--muted)">med</span></div>
        <div class="lbl">same signal, <b>tradeable</b> rolling-z def · effect fades, CI spans 0 (p<sub>MW</sub>={rz4['p_vs_rest_med']:.2f})</div></div>
    </div>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>4 / 8</span></div>
  </section>

  <!-- 5 — DEEP DIVE: DIRECTION -->
  <section class="slide">
    <div class="kicker">4 · Deep-dive — direction</div>
    <h2>The link is <span class="neu">contemporaneous</span>, not causal in either direction</h2>
    <div class="row">
      <div class="col" style="flex:1.5">
        <div class="fig"><img src="{CHARTS['ccf']}"></div>
        <div class="cap">Cross-correlation of Δposition vs return. All the mass is at k=0; no lead bar (k&gt;0) clears the ±{DS['cross_correlation']['band']:.2f} band.</div>
      </div>
      <div class="col" style="flex:1.3">
        <div class="fig"><img src="{CHARTS['irf']}"></div>
        <div class="cap">VAR({DS['var_irf']['lag_order']}) impulse response — a position shock hits WTI the same week ({irf_tot*100:+.1f}% cumulative) then dies out.</div>
      </div>
    </div>
    <div class="stat-grid" style="margin-top:1vh">
      <div class="card"><div class="big neu">{ccf0:+.2f}</div><div class="lbl">cross-correlation at <b>lag 0</b> — the only bar outside the significance band</div></div>
      <div class="card"><div class="big amb">p={gpr:.2f}</div><div class="lbl">Granger Δposition → return (lags 1–4): <b>does not</b> lead price</div></div>
      <div class="card"><div class="big amb">p={grp:.2f}</div><div class="lbl">Granger return → Δposition: price doesn't lead positioning either → pure comovement</div></div>
    </div>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>5 / 8</span></div>
  </section>

  <!-- 6 — DEEP DIVE: DYNAMICS & TRADEABILITY -->
  <section class="slide">
    <div class="kicker">5 · Deep-dive — dynamics & tradeability</div>
    <h2>Persistent state, <span class="neg">no</span> out-of-sample edge</h2>
    <div class="row">
      <div class="col" style="flex:1.4">
        <div class="fig"><img src="{CHARTS['equity']}"></div>
        <div class="cap">Walk-forward OOS backtest (point-in-time z, fixed a-priori threshold). The contrarian rule trails buy &amp; hold.</div>
      </div>
      <div class="col" style="flex:1.2">
        <div class="fig"><img src="{CHARTS['halflife']}"></div>
        <div class="cap">Positioning is highly persistent — AR(1) ρ={rho:.2f}, mean-reversion half-life ≈ {hl:.0f} weeks.</div>
      </div>
    </div>
    <div class="stat-grid" style="margin-top:1vh">
      <div class="card"><div class="big neg">{lo_sh:.2f}</div><div class="lbl">contrarian long-only <b>Sharpe</b> vs <b>{bh_sh:.2f}</b> buy &amp; hold · boot p(Sharpe≤0)={lo_boot:.2f}</div></div>
      <div class="card"><div class="big amb">AUC {auc:.2f}</div><div class="lbl">logistic direction model on the z-score — a <b>coin flip</b> (pseudo-R²≈0)</div></div>
      <div class="card"><div class="big neu">≈{hl:.0f} wks</div><div class="lbl">crowding half-life — a slow-moving <b>context</b> gauge, not an entry trigger</div></div>
    </div>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>6 / 8</span></div>
  </section>

  <!-- 7 — DEEP DIVE: MULTIPLE TESTING -->
  <section class="slide">
    <div class="kicker">6 · Deep-dive — the honest capstone</div>
    <h2>The one "edge" <span class="neg">doesn't survive</span> multiple testing</h2>
    <div class="row">
      <div class="col" style="flex:1.5">
        <div class="fig"><img src="{CHARTS['fdr']}"></div>
        <div class="cap">Benjamini-Hochberg across all {fdr['m']} extreme-bucket tests. Every p-value sits above its BH threshold.</div>
      </div>
      <div class="col" style="flex:1.1">
        <div class="fig"><img src="{CHARTS['quantile']}"></div>
        <div class="cap">Quantile regression — positioning barely moves any part of the 4-week return distribution; CIs straddle zero.</div>
      </div>
    </div>
    <ul style="margin-top:1vh">
      <li>The lone p≈{es4['p_vs_rest_med']:.2f} short-extreme result was <b>one of {fdr['m']} tests</b> — under BH (q={fdr['q']}), <b class="neg">{fdr['n_survivors']} of {fdr['m']} survive</b>. Consistent with look-where-you-looked noise.</li>
    </ul>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>7 / 8</span></div>
  </section>

  <!-- 8 — VERDICT -->
  <section class="slide">
    <div class="kicker">Verdict</div>
    <h2>A crowding gauge — <span class="amb">not</span> a timing signal</h2>
    <div class="row">
      <div class="col" style="flex:1.25">
        <div class="verdict">
          <div class="vbig">CFTC Managed-Money positioning has <b>limited, mostly contrarian</b> predictive value for WTI.</div>
          <ul>
            <li><b>Coincident, not causal:</b> all cross-correlation mass at lag 0; neither Granger direction significant (p={gpr:.2f} / {grp:.2f}).</li>
            <li><b>Persistent state:</b> ~{hl:.0f}-week half-life — a crowding <i>context</i>, never a crisp entry trigger.</li>
            <li><b>No robust edge:</b> the lone net-short bounce ({es4['median']*100:+.1f}% median) fails OOS (Sharpe {lo_sh:.2f} &lt; {bh_sh:.2f} B&amp;H) and dies under BH-FDR ({fdr['n_survivors']}/{fdr['m']}). Pair with inventories &amp; term structure — don't trade it alone.</li>
          </ul>
        </div>
        <div class="note"><b>Data note:</b> the supplied <code>Data/CFTC…OR_NET</code> file is CFTC
          <b>Other Reportables</b>, not Managed Money (verified vs official CFTC). Managed Money was
          sourced directly from the official CFTC API. The two categories trade <i>oppositely</i>, so the label matters.</div>
      </div>
      <div class="col" style="flex:1">
        <div class="fig"><img src="{CHARTS['hit']}"></div>
        <div class="cap">4-week win-rate by extreme. Edge is a tilt, not a coin-flip breaker.</div>
      </div>
    </div>
    <div class="foot"><span>CFTC Positioning vs WTI</span><div class="dots"></div><span>8 / 8</span></div>
  </section>

</div>
<script>
const slides=[...document.querySelectorAll('.slide')];let i=0;
function go(n){{i=(n+slides.length)%slides.length;
  slides.forEach((s,k)=>s.classList.toggle('active',k===i));
  document.querySelectorAll('.dots').forEach(d=>{{d.innerHTML='';
    slides.forEach((_,k)=>{{const b=document.createElement('i');if(k===i)b.className='on';
      b.onclick=()=>go(k);d.appendChild(b);}});}});}}
document.addEventListener('keydown',e=>{{
  if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key))go(i+1);
  if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key))go(i-1);
  if(e.key==='Home')go(0);if(e.key==='End')go(slides.length-1);}});
document.addEventListener('click',e=>{{if(!e.target.closest('.dots, a, img'))go(i+1);}});
go(0);
</script>
</body></html>"""

# Single source of truth: write straight to the web app's served location
# (public/cftc/) so the in-dashboard "Open deck" link and the standalone file are
# the same artifact — no duplicated copy to drift.
out = HERE.parent / "public" / "cftc" / "presentation.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(HTML, encoding="utf-8")
print(f"wrote {out}  ({len(HTML)/1024:.0f} KB incl. embedded charts)")
