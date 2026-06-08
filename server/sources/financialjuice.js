// ============================================================================
// Financial Juice — free real-time financial newswire (RSS, no key).
//   GET https://www.financialjuice.com/feed.ashx?xy=rss
// A fast, trader-oriented wire (central banks, data prints, OPEC, geopolitics,
// commodities). Items look like:
//   <item>
//     <title>FinancialJuice: OPEC+ signals possible production cut ...</title>
//     <link>https://www.financialjuice.com/News/123/....aspx</link>
//     <pubDate>Mon, 01 Jun 2026 02:01:01 GMT</pubDate>
//     <guid isPermaLink="false">123</guid>
//   </item>
// We strip the "FinancialJuice:" prefix and classify each headline into the
// dashboard's tag/severity taxonomy → { t, sev, src, txt, tag, url }.
// ============================================================================
import { cached, fetchText } from "../lib/cache.js";
import { scoreHeadlines } from "./finbert.js";

const FEED = "https://www.financialjuice.com/feed.ashx?xy=rss";

// Headline -> tag, in priority order (first match wins). Short ambiguous tokens
// use word boundaries so e.g. "warned" doesn't match "war".
const TAG_RULES = [
  ["GEOPOLITICS", /sanction|strike|attack|\bwar\b|hormuz|drone|tanker seiz|red sea|ukraine|israel|\biran\b|missile|conflict|embargo/i],
  ["OPEC", /\bopec\b|saudi|quota|\bjmmc\b|riyadh|abu dhabi/i],
  ["FREIGHT", /tanker|freight|shipping|vessel|suez|\bport\b|baltic|cargo/i],
  ["STOCKS", /inventor|stockpile|\beia\b|crude stocks?|oil stocks?|\bdrawdown\b|storage/i],
  ["WEATHER", /hurricane|storm|cold snap|heatwave|polar vortex|\bweather\b|freeze/i],
  ["PRODUCTS", /diesel|gasoline|petrol\b|refiner|crack|distillate|\bjet\b|ulsd|rbob|naphtha/i],
  ["CRUDE", /crude|brent|\bwti\b|\bopec\+|barrel|\boil\b|petroleum|\blng\b|natural gas|nat gas/i],
  ["MACRO", /\bfed\b|dollar|inflation|interest rate|\bgdp\b|economy|treasury|\bpmi\b|\becb\b|payroll|\bcpi\b|yield|central bank/i],
];

const HIGH_SEV = /surge|plunge|spike|soar|crash|\bwar\b|sanction|strike|attack|hormuz|halt|disrupt|\bcut\b|\bban\b|tumble|slump/i;
const MED_SEV = /\bopec\b|inventor|\bfed\b|\brate\b|forecast|\brise\b|\bfall\b|widen|tighten|\bpmi\b|\bcpi\b|beat|miss/i;

// Headlines that match no energy/markets tag are general market news → MACRO.
function classify(title) {
  for (const [tag, re] of TAG_RULES) if (re.test(title)) return tag;
  return "MACRO";
}
function severity(title) {
  if (HIGH_SEV.test(title)) return "high";
  if (MED_SEV.test(title)) return "med";
  return "low";
}

// Minimal XML entity decode for RSS titles.
function decode(s = "") {
  return s
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#0?39;|&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n))
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCharCode(parseInt(n, 16)))
    .trim();
}

const tagOf = (block, name) => {
  const m = new RegExp(`<${name}[^>]*>([\\s\\S]*?)<\\/${name}>`).exec(block);
  return m ? m[1] : "";
};

// "Mon, 01 Jun 2026 02:01:01 GMT" -> "02:01"
function hhmm(pubDate = "") {
  const m = /(\d{2}):(\d{2}):\d{2}/.exec(pubDate);
  return m ? `${m[1]}:${m[2]}` : "";
}

export async function news() {
  return cached("finjuice:wire", 4 * 60_000, async () => {
    const xml = await fetchText(FEED, { timeout: 15_000 });
    const items = xml.match(/<item>[\s\S]*?<\/item>/g) || [];
    const seen = new Set();
    const out = [];
    for (const block of items) {
      let txt = decode(tagOf(block, "title")).replace(/^FinancialJuice:\s*/i, "");
      if (!txt || seen.has(txt)) continue;
      seen.add(txt);
      out.push({
        t: hhmm(tagOf(block, "pubDate")),
        sev: severity(txt),
        src: "FINJUICE",
        txt,
        tag: classify(txt),
        url: decode(tagOf(block, "link")) || undefined,
      });
      if (out.length >= 24) break;
    }
    if (out.length === 0) throw new Error("Financial Juice: no items");

    // Score every headline with FinBERT (local model). On any failure this
    // resolves to null and each item simply carries `sent: null`, so the
    // downstream sentiment compute falls back to the keyword heuristic.
    const sents = await scoreHeadlines(out.map((n) => n.txt)).catch(() => null);
    out.forEach((n, i) => { n.sent = sents?.[i] ?? null; });

    return out;
  });
}
