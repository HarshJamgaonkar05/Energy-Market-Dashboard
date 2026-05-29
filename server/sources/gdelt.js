// ============================================================================
// GDELT 2.0 DOC API — free, no key. Global news index updated every 15 min.
//   GET /api/v2/doc/doc?query=&mode=ArtList&maxrecords=&format=json&sort=datedesc
// We query energy-relevant English news, then classify each headline into the
// dashboard's tag/severity taxonomy so it drops straight into the NEWS shape:
//   { t, sev, src, txt, tag }
// ============================================================================
import { cached, fetchJSON } from "../lib/cache.js";

const QUERY =
  '(oil OR crude OR brent OR opec OR refinery OR diesel OR gasoline OR "natural gas" OR pipeline) sourcelang:english';
const URL =
  "https://api.gdeltproject.org/api/v2/doc/doc?query=" +
  encodeURIComponent(QUERY) +
  "&mode=ArtList&maxrecords=50&format=json&sort=datedesc&timespan=3d";

// Headline -> tag, in priority order (first match wins).
const TAG_RULES = [
  ["GEOPOLITICS", /sanction|strike|attack|war|hormuz|drone|tanker seiz|red sea|ukraine|israel|iran|missile|conflict/i],
  ["OPEC", /opec|saudi|quota|jmmc|riyadh|abu dhabi/i],
  ["FREIGHT", /tanker|freight|shipping|vessel|suez|\bport\b|baltic|cargo/i],
  ["STOCKS", /inventor|stockpile|\beia\b|stocks|storage|drawdown/i],
  ["MACRO", /\bfed\b|dollar|inflation|interest rate|\bgdp\b|economy|treasury/i],
  ["WEATHER", /hurricane|storm|cold snap|heatwave|polar vortex|weather|freeze/i],
  ["PRODUCTS", /diesel|gasoline|refiner|crack|distillate|\bjet\b|ulsd|rbob/i],
  ["CRUDE", /crude|brent|wti|barrel|\boil\b/i],
];

const HIGH_SEV = /surge|plunge|spike|soar|crash|war|sanction|strike|attack|hormuz|halt|disrupt|cut|ban/i;
const MED_SEV = /opec|inventor|\bfed\b|rate|forecast|rise|fall|widen|tighten/i;

function classify(title) {
  for (const [tag, re] of TAG_RULES) if (re.test(title)) return tag;
  return "CRUDE";
}
function severity(title) {
  if (HIGH_SEV.test(title)) return "high";
  if (MED_SEV.test(title)) return "med";
  return "low";
}
// reuters.com -> REUTERS, www.bloomberg.com -> BLOOMBERG
function srcLabel(domain = "") {
  const core = domain.replace(/^www\./, "").split(".")[0];
  return core.toUpperCase();
}
// "20260529T064500Z" -> "06:45"
function hhmm(seendate = "") {
  const m = /T(\d{2})(\d{2})/.exec(seendate);
  return m ? `${m[1]}:${m[2]}` : "";
}

export async function news() {
  return cached("gdelt:energy", 15 * 60_000, async () => {
    // GDELT's backend can be slow on broad OR-queries; give it more headroom.
    const json = await fetchJSON(URL, { timeout: 22_000 });
    const arts = json?.articles || [];
    const seen = new Set();
    const out = [];
    for (const a of arts) {
      const txt = (a.title || "").trim();
      if (!txt || seen.has(txt)) continue;
      seen.add(txt);
      out.push({
        t: hhmm(a.seendate),
        sev: severity(txt),
        src: srcLabel(a.domain),
        txt,
        tag: classify(txt),
        url: a.url,
      });
      if (out.length >= 24) break;
    }
    if (out.length === 0) throw new Error("GDELT: no articles");
    return out;
  });
}
