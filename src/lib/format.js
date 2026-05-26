export const fmt = (n, d = 2) =>
  Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

export const fmtSigned = (n, d = 2) => (n >= 0 ? "+" : "") + fmt(n, d);
