// ============================================================================
// Tiny in-memory TTL cache + resilient JSON/text fetch helpers.
//
// Free upstream APIs (Yahoo, EIA, Financial Juice, Open-Meteo) are rate-limited and most
// of this data changes slowly (inventories weekly, weather every few hours).
// We cache aggressively so the dashboard can poll often while we hit upstreams
// rarely. Each cached entry also keeps the last *good* value so a transient
// upstream failure serves slightly-stale data instead of an error.
// ============================================================================

const store = new Map(); // key -> { value, expires, fetchedAt }

/**
 * Get a cached value or (re)compute it via `producer`.
 * @param {string} key
 * @param {number} ttlMs  how long a fresh value stays valid
 * @param {() => Promise<any>} producer
 */
export async function cached(key, ttlMs, producer) {
  const now = Date.now();
  const hit = store.get(key);
  if (hit && hit.expires > now) return hit.value;

  try {
    const value = await producer();
    store.set(key, { value, expires: now + ttlMs, fetchedAt: now });
    return value;
  } catch (err) {
    // Upstream failed — serve the last good value if we have one.
    if (hit) {
      console.warn(`[cache] ${key} refresh failed (${err.message}); serving stale`);
      return hit.value;
    }
    throw err;
  }
}

const DEFAULT_HEADERS = {
  // A browser-like UA keeps Yahoo's public chart endpoint from 403-ing.
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
  Accept: "application/json,text/csv,*/*",
};

async function withTimeout(url, opts = {}) {
  const ms = opts.timeout ?? 12000;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: ctrl.signal, headers: { ...DEFAULT_HEADERS, ...(opts.headers || {}) } });
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchJSON(url, opts = {}) {
  const res = await withTimeout(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

export async function fetchText(url, opts = {}) {
  const res = await withTimeout(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}
