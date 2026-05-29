import { useEffect, useRef, useState } from "react";

// ============================================================================
// useLive — poll a backend /api endpoint on an interval and keep the UI live.
//
//   const { data, live, stale } = useLive("/api/instruments", FALLBACK, 30_000);
//
// • `data`     always renderable: starts as `fallback`, swaps to live data on
//              the first successful fetch, and retains the last good value if a
//              later poll fails (so a flaky upstream never blanks the panel).
// • `live`     true once at least one real response has arrived.
// • `stale`    true when the most recent poll failed (showing last good/fallback).
//
// The backend returns 503 with `{fallback:true}` when a source is unavailable
// (e.g. EIA without a key) — we treat that as "keep the fallback", so panels
// degrade gracefully to the seeded mock data instead of erroring.
// ============================================================================
const REFRESH = { fast: 30_000, slow: 5 * 60_000, hourly: 15 * 60_000 };

export function useLive(path, fallback, intervalMs = REFRESH.fast) {
  const [data, setData] = useState(fallback);
  const [live, setLive] = useState(false);
  const [stale, setStale] = useState(false);
  const lastGood = useRef(fallback);

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      try {
        const res = await fetch(path, { headers: { Accept: "application/json" } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (cancelled) return;
        lastGood.current = json;
        setData(json);
        setLive(true);
        setStale(false);
      } catch {
        if (cancelled) return;
        // keep the last good value (or the fallback); just flag staleness
        setData(lastGood.current);
        setStale(true);
      }
    };

    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [path, intervalMs]);

  return { data, live, stale };
}

useLive.REFRESH = REFRESH;
