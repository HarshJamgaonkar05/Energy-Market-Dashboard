// Em-dash shown wherever a value has no real source (not free/open, not curated)
// — we render this instead of fabricating a number.
export const DASH = "—";

const isMissing = (n) => n == null || Number.isNaN(Number(n));

export const fmt = (n, d = 2) =>
  isMissing(n) ? DASH : Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

export const fmtSigned = (n, d = 2) => (isMissing(n) ? DASH : (n >= 0 ? "+" : "") + fmt(n, d));
